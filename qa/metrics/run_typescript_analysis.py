#!/usr/bin/env python3
"""Run TypeScript's static type analyzer and compare findings with a checked-in baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIAGNOSTIC = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\): "
    r"(?P<severity>error|warning) (?P<rule>TS\d+): (?P<message>.*)$"
)


def fingerprint(file: str, rule: str, message: str) -> str:
    stable_text = "|".join((file.replace("\\", "/"), rule, " ".join(message.split())))
    return hashlib.sha256(stable_text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    frontend = repo / "frontend"
    baseline_path = (args.baseline or repo / "qa/metrics/typescript-baseline.json").resolve()
    output_path = (args.output or frontend / "target/typescript-analysis.json").resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = ["node", "node_modules/typescript/bin/tsc", "--noEmit", "--pretty", "false", "--project", "tsconfig.app.json"]
    proc = subprocess.run(command, cwd=frontend, text=True, capture_output=True, check=False)
    version_proc = subprocess.run(
        ["node", "node_modules/typescript/bin/tsc", "--version"],
        cwd=frontend, text=True, capture_output=True, check=False,
    )
    raw = (proc.stdout + proc.stderr).splitlines()
    findings: list[dict[str, Any]] = []
    unparsed = []
    for line in raw:
        match = DIAGNOSTIC.match(line.strip())
        if not match:
            if line.strip():
                unparsed.append(line.strip())
            continue
        item = match.groupdict()
        relative_file = Path(item["file"]).as_posix()
        if relative_file.startswith("./"):
            relative_file = relative_file[2:]
        finding = {
            "file": relative_file,
            "line": int(item["line"]),
            "column": int(item["column"]),
            "severity": item["severity"],
            "rule": item["rule"],
            "message": item["message"],
        }
        finding["fingerprint"] = fingerprint(relative_file, finding["rule"], finding["message"])
        findings.append(finding)

    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {"findings": []}
    baseline_fingerprints = {item["fingerprint"] for item in baseline.get("findings", [])}
    for item in findings:
        item["baseline_status"] = "existing" if item["fingerprint"] in baseline_fingerprints else "new"
    new_findings = [item for item in findings if item["baseline_status"] == "new"]
    counts = Counter((item["severity"], item["rule"], item["baseline_status"]) for item in findings)
    report = {
        "schema_version": "1.0",
        "tool": "TypeScript Compiler",
        "tool_version": version_proc.stdout.strip() or "unknown",
        "project": "Dulce Miel Angular frontend",
        "command": "tsc --noEmit --pretty false --project tsconfig.app.json",
        "commit": os.getenv("GITHUB_SHA") or os.getenv("GIT_COMMIT"),
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "baseline_file": str(baseline_path.relative_to(repo)).replace("\\", "/") if baseline_path.is_relative_to(repo) else str(baseline_path),
        "exit_code": proc.returncode,
        "status": "failed" if proc.returncode != 0 else "passed",
        "finding_count": len(findings),
        "new_finding_count": len(new_findings),
        "counts_by_severity_rule_and_baseline": [
            {"severity": sev, "rule": rule, "baseline_status": status, "count": count}
            for (sev, rule, status), count in sorted(counts.items())
        ],
        "findings": findings,
        "unparsed_output": unparsed,
        "interpretation": "TS#### identifica la regla/diagnóstico del compilador; error es severidad reportada por el compilador, no severidad de impacto de negocio. La línea base permite separar diagnósticos conocidos de nuevos por archivo, regla y mensaje.",
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TypeScript static analysis: {len(findings)} diagnósticos; {len(new_findings)} nuevos; exit code {proc.returncode}")
    print(f"Report: {output_path}")
    if unparsed:
        print("Unparsed compiler output:")
        print("\n".join(unparsed))
    # Findings already present in the reviewed baseline remain visible without
    # blocking; only regressions (or an unparseable compiler failure) fail this stage.
    return 1 if new_findings or (proc.returncode != 0 and not findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
