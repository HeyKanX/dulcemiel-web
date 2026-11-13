#!/usr/bin/env python3
"""Consolida métricas de calidad de una sola corrida de Dulce Miel.

Solo usa reportes/evidencia de la corrida actual. Valores sin fuente verificable
se publican como null/N/A en lugar de inferirse de pruebas fallidas.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CASE_RE = re.compile(r"TC-(?:F-\d{3}|NF-[A-Z]+-\d{3})")
K6_PROFILES = {
    "smoke": "humo",
    "baseline": "línea base",
    "moderate": "carga moderada",
    "stress": "estrés progresivo",
    "spike": "pico repentino",
    "sustained": "carga sostenida",
}


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def git_value(repo: Path, *args: str) -> str | None:
    try:
        value = subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
        return value or None
    except (OSError, subprocess.CalledProcessError):
        return None


def pct(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(float(numerator) / float(denominator) * 100, 2)


def counts_summary(total: int, passed: int, failed: int, skipped: int = 0, blocked: int = 0) -> dict[str, Any]:
    executed = passed + failed
    return {
        "total": total,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "skipped": skipped,
        "pass_rate_pct": pct(passed, executed),
        "fail_rate_pct": pct(failed, executed),
    }


def no_report_suite(name: str, tool: str, outcome: str, evidence: str | None = None) -> dict[str, Any]:
    status = "blocked" if outcome == "failure" else "not_run" if outcome == "skipped" else "no_report"
    return {
        "suite": name,
        "tool": tool,
        "status": status,
        "counts": counts_summary(0, 0, 0),
        "note": "No se encontró reporte de prueba válido para esta corrida.",
        "ci_step_outcome": outcome or "unknown",
        "evidence": [evidence] if evidence else [],
    }


def suite_from_counts(
    name: str, tool: str, total: int, passed: int, failed: int, skipped: int = 0,
    outcome: str = "unknown", evidence: list[str] | None = None, note: str | None = None,
) -> dict[str, Any]:
    status = "failed" if failed else "passed" if total else "no_report"
    return {
        "suite": name,
        "tool": tool,
        "status": status,
        "counts": counts_summary(total, passed, failed, skipped),
        "ci_step_outcome": outcome or "unknown",
        "evidence": evidence or [],
        **({"note": note} if note else {}),
    }


def junit_counts(paths: list[Path]) -> tuple[int, int, int, int]:
    total = passed = failed = skipped = 0
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        for case in root.iter("testcase"):
            total += 1
            if case.find("skipped") is not None:
                skipped += 1
            elif case.find("failure") is not None or case.find("error") is not None:
                failed += 1
            else:
                passed += 1
    return total, passed, failed, skipped


def parse_frontend_log(path: Path) -> tuple[int, int, int] | None:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # Karma prints cumulative "Executed x of n" lines; the final summary is authoritative.
    matches = re.findall(r"TOTAL:\s*(\d+)\s+(SUCCESS|FAILED)", content, flags=re.IGNORECASE)
    if matches:
        total, result = matches[-1]
        total = int(total)
        if result.upper() == "SUCCESS":
            return total, total, 0
        failed = len(re.findall(r"FAILED\s*\([^\n]*\)", content, flags=re.IGNORECASE))
        failed = min(total, failed or 1)
        return total, total - failed, failed
    executed = re.findall(r"Executed\s+(\d+)\s+of\s+(\d+)\s+(SUCCESS|FAILED)", content, flags=re.IGNORECASE)
    if not executed:
        return None
    done, total, result = executed[-1]
    total, done = int(total), int(done)
    if result.upper() == "SUCCESS" and done == total:
        return total, total, 0
    failed = max(1, total - done) if result.upper() == "FAILED" else 0
    return total, max(0, total - failed), failed


def frontend_coverage(repo: Path) -> dict[str, Any]:
    index = repo / "frontend/coverage/ihc-frontend/index.html"
    if not index.is_file():
        return {"status": "not_reported", "reason": "No se encontró el informe HTML de cobertura Angular."}
    content = index.read_text(encoding="utf-8", errors="replace")
    metrics = {}
    for label, key in (("Statements", "statements"), ("Branches", "branches"),
                       ("Functions", "functions"), ("Lines", "lines")):
        match = re.search(
            rf"<span class=['\"]quiet['\"]>{label}</span>\s*<span class=['\"][^'\"]*fraction[^'\"]*['\"]>(\d+)/(\d+)</span>",
            content,
        )
        if match:
            covered, total = map(int, match.groups())
            metrics[key] = {"covered": covered, "total": total, "coverage_pct": pct(covered, total)}
    return {
        "status": "reported" if metrics else "invalid_report",
        "component": "frontend Angular",
        "tool": "Karma/Istanbul HTML",
        "metrics": metrics,
        "evidence": "frontend/coverage/ihc-frontend/index.html",
    }


def jacoco_coverage(repo: Path) -> dict[str, Any]:
    path = repo / "backend/target/site/jacoco/jacoco.xml"
    if not path.is_file():
        return {"status": "not_reported", "reason": "No se encontró JaCoCo XML; el pipeline debe ejecutar el objetivo de reporte."}
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return {"status": "invalid_report", "reason": str(exc)}
    mapping = {"INSTRUCTION": "instructions", "LINE": "lines", "BRANCH": "branches", "METHOD": "methods"}
    metrics = {}
    for counter in root.findall("counter"):
        kind = counter.get("type")
        if kind not in mapping:
            continue
        missed, covered = int(counter.get("missed", "0")), int(counter.get("covered", "0"))
        total = missed + covered
        metrics[mapping[kind]] = {
            "covered": covered,
            "total": total,
            "coverage_pct": pct(covered, total),
        }
    return {
        "status": "reported" if metrics else "invalid_report",
        "component": "backend Java",
        "tool": "JaCoCo",
        "metrics": metrics,
        "evidence": "backend/target/site/jacoco/jacoco.xml",
    }


def read_newman(run_dir: Path, outcome: str) -> dict[str, Any]:
    path = run_dir / "api/newman.json"
    data = read_json(path)
    if not data:
        return no_report_suite("API", "Newman", outcome, "api/newman.json")
    stats = data.get("run", {}).get("stats", {})
    assertions = stats.get("assertions", {})
    total = int(assertions.get("total", 0))
    failed = int(assertions.get("failed", 0))
    pending = int(assertions.get("pending", 0))
    requests = stats.get("requests", {})
    return suite_from_counts(
        "API", "Newman", total, max(0, total - failed - pending), failed, pending,
        outcome, ["api/newman.json"],
        f"{requests.get('total', 0)} solicitudes; pass/fail se calcula sobre aserciones Newman.",
    )


def read_compatibility(run_dir: Path, outcome: str) -> dict[str, Any]:
    result_path = run_dir / "compatibility/result.json"
    item = read_json(result_path)
    log_path = run_dir / "compatibility/playwright.log"
    if not item and log_path.is_file():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        entries = re.findall(r"\(engine='[^']+',\s*width=\d+\)\s+\.\.\.\s+(ok|FAIL|ERROR)", text)
        if entries:
            failed = sum(value != "ok" for value in entries)
            total = len(entries)
            return suite_from_counts("Compatibilidad", "Playwright", total, total - failed, failed, 0,
                                     outcome, ["compatibility/playwright.log"])
    if not item:
        return no_report_suite("Compatibilidad", "Playwright", outcome, "compatibility/result.json")
    total = int(item.get("tests_total", 1))
    failed = int(item.get("tests_failed", 0 if item.get("status") == "p" else total))
    passed = int(item.get("tests_passed", max(0, total - failed)))
    return suite_from_counts("Compatibilidad", "Playwright", total, passed, failed, 0,
                             outcome, [item.get("evidence", "compatibility/playwright.log")])


def read_accessibility(run_dir: Path, outcome: str) -> dict[str, Any]:
    path = run_dir / "accessibility-axe/axe-results.json"
    data = read_json(path)
    if not data:
        return no_report_suite("Accesibilidad automática", "axe-core", outcome, "accessibility-axe/axe-results.json")
    pages = data.get("pages", [])
    total = len(pages)
    passed = failed = 0
    errors = []
    for page in pages:
        if page.get("error") or not page.get("axe"):
            failed += 1
            errors.append(page.get("route", "?"))
        elif page.get("axe", {}).get("violations"):
            failed += 1
        else:
            passed += 1
    return suite_from_counts(
        "Accesibilidad automática", "axe-core", total, passed, failed, 0,
        outcome, ["accessibility-axe/axe-results.json"],
        f"Rutas con error o sin escaneo: {', '.join(errors)}." if errors else None,
    )


def read_k6(run_dir: Path) -> list[dict[str, Any]]:
    profiles = []
    for slug, label in K6_PROFILES.items():
        path = run_dir / f"k6-{slug}/summary.json"
        data = read_json(path)
        if not data:
            outcome = os.getenv(f"CI_OUTCOME_K6_{slug.upper()}", "unknown").lower()
            status = "blocked" if outcome == "failure" else "not_run"
            profiles.append({"profile": slug, "label": label, "status": status, "evidence": None,
                             "note": "La etapa falló sin producir resumen." if status == "blocked" else "La etapa no produjo resumen."})
            continue
        metrics = data.get("metrics", {})
        thresholds = [threshold for metric in metrics.values() for threshold in metric.get("thresholds", {}).values()]
        passed = bool(thresholds) and all(bool(item.get("ok")) for item in thresholds)
        http_duration = metrics.get("http_req_duration", {}).get("values", {})
        api_duration = metrics.get("api_latency", {}).get("values", {})
        page_duration = metrics.get("page_latency", {}).get("values", {})
        request_rate = metrics.get("http_req_failed", {}).get("values", {}).get("rate")
        if request_rate is None:
            request_rate = metrics.get("request_errors", {}).get("values", {}).get("rate")
        check_metric = metrics.get("checks", {}).get("values", {})
        state = data.get("state", {})
        profiles.append({
            "profile": slug,
            "label": label,
            "status": "passed" if passed else "failed" if thresholds else "incomplete",
            "thresholds_defined": len(thresholds),
            "thresholds_passed": sum(bool(item.get("ok")) for item in thresholds),
            "duration_seconds": round(float(state.get("testRunDurationMs", 0)) / 1000, 3) or None,
            "vus_max": metrics.get("vus_max", metrics.get("vus", {})).get("values", {}).get("max"),
            "iterations": metrics.get("iterations", {}).get("values", {}).get("count"),
            "requests_total": metrics.get("http_reqs", {}).get("values", {}).get("count"),
            "throughput_requests_per_second": metrics.get("http_reqs", {}).get("values", {}).get("rate"),
            "request_error_rate_pct": round(float(request_rate) * 100, 4) if request_rate is not None else None,
            "check_success_rate_pct": round(float(check_metric["rate"]) * 100, 4) if check_metric.get("rate") is not None else pct(check_metric.get("passes"), int(check_metric.get("passes", 0)) + int(check_metric.get("fails", 0)))
            if (int(check_metric.get("passes", 0)) + int(check_metric.get("fails", 0))) else None,
            "http_req_duration_ms": {"p95": http_duration.get("p(95)"), "p99": http_duration.get("p(99)")},
            "api_latency_ms": {"p95": api_duration.get("p(95)"), "p99": api_duration.get("p(99)")},
            "page_latency_ms": {"p95": page_duration.get("p(95)"), "p99": page_duration.get("p(99)")},
            "evidence": str(path).replace("\\", "/"),
        })
    return profiles


def catalog_metrics(repo: Path, current_run: dict[str, Any] | None) -> dict[str, Any]:
    case_map = read_json(repo / "qa/testlink/results/case-id-map.json") or {}
    catalog = case_map.get("cases", [])
    results = (current_run or {}).get("results", [])
    known = {item.get("case_id") for item in catalog if item.get("case_id")}
    # A TestLink case contributes once per build even if the summary contains duplicate rows.
    by_id: dict[str, dict[str, Any]] = {}
    for item in results:
        case_id = item.get("case_id")
        if case_id in known and item.get("status") in ("p", "f"):
            by_id[str(case_id)] = item
    ids = set(by_id)
    passed = sum(item.get("status") == "p" for item in by_id.values())
    failed = sum(item.get("status") == "f" for item in by_id.values())
    other = sum(item.get("status") not in ("p", "f") for item in results)
    classification = read_json(repo / "qa/metrics/automation-classification.json") or {}
    classification_counts = classification.get("counts", {})
    automated = int(classification_counts.get("automated_linked", 0))
    gaps = int(classification_counts.get("automation_gap", 0))
    manual_only = int(classification_counts.get("manual_only", 0))
    applicable = automated + gaps
    return {
        "catalog_case_count": len(known),
        "unique_cases_with_automated_result_this_build": len(ids),
        "cases_not_represented_this_build": max(0, len(known) - len(ids)),
        "execution_coverage_pct": pct(len(ids), len(known)),
        "classification_status": "classified" if classification_counts else "not_classified",
        "automation_classification": {
            "automated_linked": automated,
            "automation_gap": gaps,
            "manual_only": manual_only,
            "applicable_cases": applicable,
            "automation_rate_pct": pct(automated, applicable),
            "source": "qa/metrics/automation-classification.json",
        },
        "automation_rate_pct": pct(automated, applicable),
        "automation_rate_reason": "Casos automatizados trazados / casos automatizables; los manual_only se excluyen del denominador y los automation_gap permanecen en él.",
        "linked_result_cases": {"passed": passed, "failed": failed, "other_status": other},
        "interpretation": "execution_coverage_pct es la fracción del catálogo con resultado automatizado en este build; no representa la tasa de automatización del catálogo.",
    }


def build_summary(repo: Path, run_dir: Path, testlink_summary: Path | None = None) -> dict[str, Any]:
    outcomes = {key.removeprefix("CI_OUTCOME_").lower(): value.lower()
                for key, value in os.environ.items() if key.startswith("CI_OUTCOME_")}
    current_run_path = testlink_summary or (repo / "qa/testlink/results/current-run.json")
    current_run = read_json(current_run_path)
    suites: list[dict[str, Any]] = []

    # Maven may leave XMLs from old classes in target when it runs without clean.
    # Only count reports written after this run's artifact directory was created.
    run_started_at = run_dir.stat().st_mtime if run_dir.exists() else datetime.now().timestamp()
    backend_paths = [path for path in (repo / "backend/target/surefire-reports").glob("TEST-*.xml")
                     if path.stat().st_mtime >= run_started_at]
    total, passed, failed, skipped = junit_counts(backend_paths)
    suites.append(suite_from_counts("Backend", "Maven/Surefire", total, passed, failed, skipped,
                                    outcomes.get("backend", "unknown"),
                                    [str(path.relative_to(repo)).replace("\\", "/") for path in backend_paths]))
    if not backend_paths:
        suites[-1] = no_report_suite("Backend", "Maven/Surefire", outcomes.get("backend", "unknown"), "backend/target/surefire-reports")

    frontend_log = repo / "frontend/coverage/frontend-tests.log"
    frontend_counts = parse_frontend_log(frontend_log)
    if frontend_counts:
        ft, fp, ff = frontend_counts
        suites.append(suite_from_counts("Frontend", "Angular/Karma", ft, fp, ff, 0,
                                        outcomes.get("frontend_tests", "unknown"), ["frontend/coverage/frontend-tests.log"]))
    else:
        suites.append(no_report_suite("Frontend", "Angular/Karma", outcomes.get("frontend_tests", "unknown"), "frontend/coverage/frontend-tests.log"))

    newman = read_newman(run_dir, outcomes.get("newman", "unknown"))
    suites.append(newman)
    behave_paths = list((run_dir / "ui-behave").glob("*.xml"))
    bt, bp, bf, bs = junit_counts(behave_paths)
    suites.append(suite_from_counts("Interfaz", "Behave/Selenium", bt, bp, bf, bs,
                                    outcomes.get("behave", "unknown"),
                                    [str(path.relative_to(repo)).replace("\\", "/") if path.is_relative_to(repo) else path.name for path in behave_paths],
                                    "Los errores de UI requieren triage; no se clasifican automáticamente como defectos del producto."))
    if not behave_paths:
        suites[-1] = no_report_suite("Interfaz", "Behave/Selenium", outcomes.get("behave", "unknown"), "ui-behave/*.xml")

    pending_playwright_paths = list((run_dir / "pending-playwright").glob("*.xml"))
    pt, pp, pf, ps = junit_counts(pending_playwright_paths)
    suites.append(suite_from_counts(
        "Casos Fase 1 seleccionados", "Playwright", pt, pp, pf, ps,
        outcomes.get("pending_playwright", "unknown"),
        [str(path.relative_to(repo)).replace("\\", "/") if path.is_relative_to(repo) else path.name
         for path in pending_playwright_paths],
        "Ocho casos del registro; el estado se calcula desde JUnit de esta corrida, no desde resultados manuales previos.",
    ))
    if not pending_playwright_paths:
        suites[-1] = no_report_suite(
            "Casos Fase 1 seleccionados", "Playwright", outcomes.get("pending_playwright", "unknown"),
            "pending-playwright/junit.xml",
        )

    suites.append(read_compatibility(run_dir, outcomes.get("compatibility", "unknown")))
    suites.append(read_accessibility(run_dir, outcomes.get("accessibility", "unknown")))
    k6_profiles = read_k6(run_dir)
    for profile in k6_profiles:
        status = profile["status"]
        suites.append({
            "suite": f"K6 — {profile['label']}",
            "tool": "K6",
            "status": status,
            "counts": counts_summary(1, 1 if status == "passed" else 0, 1 if status == "failed" else 0,
                                     blocked=1 if status == "blocked" else 0),
            "ci_step_outcome": outcomes.get(f"k6_{profile['profile']}", "unknown"),
            "evidence": [profile["evidence"]] if profile.get("evidence") else [],
            "note": profile.get("note") or ("No hubo resumen K6 válido." if status in ("not_run", "incomplete", "blocked") else None),
        })

    cases = catalog_metrics(repo, current_run)
    linked = cases["linked_result_cases"]
    total_linked = linked["passed"] + linked["failed"]
    pass_rate = pct(linked["passed"], total_linked)
    fail_rate = pct(linked["failed"], total_linked)

    coverage = {"backend": jacoco_coverage(repo), "frontend": frontend_coverage(repo)}
    static_path = repo / "backend/target/spotbugsXml.xml"
    static_analysis: dict[str, Any] = {
        "status": "partial",
        "tools": ["SpotBugs"],
        "ci_step_outcome": outcomes.get("static_analysis", "unknown"),
        "scope": "Bytecode Java del backend; el frontend TypeScript no tiene analizador estático dedicado conectado.",
        "findings_by_priority": {},
        "finding_count": None,
        "evidence": "backend/target/spotbugsXml.xml" if static_path.is_file() else None,
    }
    if static_path.is_file():
        try:
            spotbugs_root = ET.parse(static_path).getroot()
            findings: dict[str, int] = {}
            for item in spotbugs_root.findall("BugInstance"):
                priority = item.get("priority", "unknown")
                findings[priority] = findings.get(priority, 0) + 1
            static_analysis["findings_by_priority"] = findings
            static_analysis["finding_count"] = sum(findings.values())
            static_analysis["status"] = "reported"
            static_analysis["note"] = "Prioridad del analizador, no severidad confirmada; cada hallazgo requiere triage."
        except (ET.ParseError, OSError) as exc:
            static_analysis["status"] = "invalid_report"
            static_analysis["reason"] = str(exc)
    else:
        static_analysis["status"] = "not_reported"
        static_analysis["reason"] = "No existe reporte SpotBugs en esta corrida."

    defect_register = read_json(repo / "qa/metrics/defect-register.json") or {}
    confirmed = [item for item in defect_register.get("defects", []) if item.get("status") == "confirmed_open"]
    current_results = (current_run or {}).get("results", [])
    failed_ids = {str(item.get("case_id")) for item in current_results if item.get("status") == "f"}
    executed_ids = {str(item.get("case_id")) for item in current_results if item.get("status") in ("p", "f")}
    matched_defects = [item for item in confirmed if failed_ids.intersection(map(str, item.get("case_ids", [])))]
    severity_distribution: dict[str, int] = {}
    for item in matched_defects:
        severity = str(item.get("severity", "Sin clasificar"))
        severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

    stability_data = read_json(repo / "qa/metrics/stability-baseline.json") or {}
    expected_fingerprint = stability_data.get("application_and_test_fingerprint", {})
    current_fingerprint: dict[str, str] = {}
    for relative in expected_fingerprint:
        path = repo / relative
        if path.exists():
            try:
                current_fingerprint[relative] = subprocess.check_output(
                    ["git", "rev-parse", f"HEAD:{relative}"], cwd=repo, text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
            except (OSError, subprocess.CalledProcessError):
                current_fingerprint[relative] = "uncommitted-or-unavailable"
    fingerprint_matches = bool(expected_fingerprint) and current_fingerprint == expected_fingerprint
    runs = stability_data.get("runs", [])
    per_case: dict[str, set[str]] = {}
    for run in runs:
        for case_id, status in run.get("statuses", {}).items():
            per_case.setdefault(case_id, set()).add(status)
    repeated_cases = len(per_case)
    flaky_cases = sum(len(statuses) > 1 for statuses in per_case.values())
    flaky_rate = pct(flaky_cases, repeated_cases) if fingerprint_matches else None
    publication = read_json(repo / "qa/testlink/results/publication-report.json")
    publication_outcome = os.getenv("CI_OUTCOME_TESTLINK_PUBLICATION", "skipped").lower()
    if publication:
        publication_outcome = str(publication.get("status", publication_outcome)).lower()

    declared_build_result = os.getenv("CI_BUILD_RESULT", "").upper()
    overall = "failure" if declared_build_result in ("FAILURE", "UNSTABLE", "ABORTED") else "success"
    if any(value == "failure" for value in outcomes.values()):
        overall = "failure"
    if any(suite.get("status") in ("failed", "blocked") for suite in suites):
        overall = "failure"
    if outcomes.get("prepare_qa") not in (None, "success"):
        overall = "failure"
    github_run_url = ""
    if os.getenv("GITHUB_SERVER_URL") and os.getenv("GITHUB_REPOSITORY") and os.getenv("GITHUB_RUN_ID"):
        github_run_url = (
            f"{os.environ['GITHUB_SERVER_URL'].rstrip('/')}/{os.environ['GITHUB_REPOSITORY']}"
            f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        )
    return {
        "schema_version": "1.0",
        "metadata": {
            "project": "Dulce Miel",
            "provider": os.getenv("CI_PROVIDER", "local"),
            "build_id": os.getenv("BUILD_TAG") or os.getenv("BUILD_NUMBER") or run_dir.name,
            "build_number": os.getenv("BUILD_NUMBER") or os.getenv("CI_RUN_NUMBER"),
            "run_id": os.getenv("CI_RUN_ID") or run_dir.name,
            "commit": os.getenv("CI_COMMIT") or os.getenv("GIT_COMMIT") or os.getenv("GITHUB_SHA") or git_value(repo, "rev-parse", "HEAD"),
            "branch": os.getenv("CI_BRANCH") or os.getenv("GIT_BRANCH") or os.getenv("GITHUB_REF_NAME") or git_value(repo, "rev-parse", "--abbrev-ref", "HEAD"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "environment": "QA aislado",
            "build_result": overall,
            "run_url": os.getenv("CI_RUN_URL") or os.getenv("BUILD_URL") or github_run_url or None,
            "trigger": os.getenv("CI_EVENT") or os.getenv("GITHUB_EVENT_NAME"),
        },
        "summary": {
            "automated_linked_cases": {"total_executed": total_linked, "passed": linked["passed"], "failed": linked["failed"], "pass_rate_pct": pass_rate, "fail_rate_pct": fail_rate},
            "counts_not_in_denominator": {"catalog_cases_not_represented_this_build": cases["cases_not_represented_this_build"], "no_status": linked["other_status"]},
            "interpretation": "Tasas calculadas sobre IDs únicos automatizados con resultado en current-run.json. No son tasa de defectos ni cubren las pruebas manuales.",
        },
        "suites": suites,
        "coverage": coverage,
        "static_analysis": static_analysis,
        "defects": {
            "confirmed_count": len(matched_defects),
            "triaged_confirmed_open_total": len(confirmed),
            "rate_per_100_executed_cases": pct(len(matched_defects), len(executed_ids)),
            "severity_distribution": severity_distribution,
            "candidate_failed_cases": linked["failed"],
            "evidence_register": "qa/metrics/defect-register.json",
            "denominator_executed_unique_cases": len(executed_ids),
            "reason": "Cuenta defectos únicos confirmados y vinculados a casos fallidos del resumen de esta corrida; no todos los fallos de suite se cuentan automáticamente como defectos.",
        },
        "defect_leakage": {
            "rate_pct": None,
            "reason": "Falta una fuente de incidencias posliberación vinculadas a versión y periodo de observación.",
        },
        "flaky_tests": {
            "status": "measured" if fingerprint_matches and len(runs) >= 2 else "not_comparable",
            "rate_pct": flaky_rate,
            "cases_repeated": repeated_cases if fingerprint_matches else None,
            "cases_flaky": flaky_cases if fingerprint_matches else None,
            "runs": len(runs),
            "fingerprint_matches": fingerprint_matches,
            "reason": "Mismo fingerprint de código de aplicación y runner; tasa = casos con estados distintos / casos repetidos." if fingerprint_matches else "El código/runner actual difiere del fingerprint de la línea base; repetir con versión y entorno constantes.",
        },
        "automation": cases,
        "k6": k6_profiles,
        "testlink": {
            "summary_generated": bool(current_run),
            "summary_file": (current_run_path.relative_to(repo).as_posix()
                             if current_run and current_run_path.is_relative_to(repo) else str(current_run_path) if current_run else None),
            "publication_status": publication_outcome,
            "publication_report_file": "qa/testlink/results/publication-report.json" if publication else None,
        },
        "evidence": {
            "run_directory": str(run_dir.relative_to(repo)).replace("\\", "/") if run_dir.is_relative_to(repo) else str(run_dir),
            "artifact_files": [
                "backend/target/surefire-reports/",
                "backend/target/site/jacoco/",
                "frontend/coverage/",
                str(run_dir.relative_to(repo)).replace("\\", "/") if run_dir.is_relative_to(repo) else str(run_dir),
                (current_run_path.relative_to(repo).as_posix()
                 if current_run and current_run_path.is_relative_to(repo) else str(current_run_path)),
            ],
        },
    }


def html_report(summary: dict[str, Any]) -> str:
    meta = summary["metadata"]
    rates = summary["summary"]["automated_linked_cases"]
    suites = summary["suites"]
    suite_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(row["suite"]), html.escape(row["tool"]), html.escape(row["status"]),
            row["counts"]["passed"], row["counts"]["failed"],
            "N/A" if row["counts"]["pass_rate_pct"] is None else f"{row['counts']['pass_rate_pct']:.2f}%",
        ) for row in suites
    )
    k6_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(item["label"]), html.escape(item["status"]), item.get("vus_max") or "N/A",
            item.get("duration_seconds") or "N/A", item.get("api_latency_ms", {}).get("p95") or "N/A",
            "N/A" if item.get("request_error_rate_pct") is None else f"{item['request_error_rate_pct']:.4f}%",
        ) for item in summary["k6"]
    )
    coverage_cards = []
    for component, data in summary["coverage"].items():
        if data.get("status") == "reported":
            values = " · ".join(f"{name}: {metric['coverage_pct']:.2f}% ({metric['covered']}/{metric['total']})"
                                for name, metric in data.get("metrics", {}).items() if metric.get("coverage_pct") is not None)
            coverage_cards.append(f"<li><b>{html.escape(data['component'])}:</b> {html.escape(values)}</li>")
        else:
            coverage_cards.append(f"<li><b>{html.escape(component)}:</b> N/A — {html.escape(data.get('reason', 'Reporte no disponible.'))}</li>")
    static = summary["static_analysis"]
    priorities = ", ".join(f"P{priority}: {count}" for priority, count in sorted(static.get("findings_by_priority", {}).items())) or "sin hallazgos reportados"
    automation_class = summary["automation"].get("automation_classification", {})
    defects = summary["defects"]
    flaky = summary["flaky_tests"]
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Métricas de calidad — Dulce Miel — {html.escape(str(meta.get('build_id')))}</title>
<style>
body{{font:15px/1.5 system-ui,Segoe UI,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#24292f}}
h1,h2{{color:#6b3e24}} .meta,.card{{background:#f6f8fa;padding:1rem;border-radius:8px;margin:.7rem 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.7rem}}
.metric{{font-size:1.5rem;font-weight:700}} table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th,td{{text-align:left;border-bottom:1px solid #d8dee4;padding:.55rem;vertical-align:top}}
th{{background:#f6f8fa}} .failure{{color:#b42318}} .success{{color:#18794e}} .na{{color:#57606a}}
</style></head><body>
<h1>Métricas de calidad — Dulce Miel</h1>
<div class="meta"><b>Build:</b> {html.escape(str(meta.get('build_id')))} · <b>Proveedor:</b> {html.escape(str(meta.get('provider')))} ·
<b>Resultado:</b> <span class="{html.escape(meta.get('build_result',''))}">{html.escape(str(meta.get('build_result')))}</span><br>
<b>Commit:</b> {html.escape(str(meta.get('commit') or 'N/A'))} · <b>Rama:</b> {html.escape(str(meta.get('branch') or 'N/A'))} ·
<b>Entorno:</b> {html.escape(str(meta.get('environment')))} · <b>UTC:</b> {html.escape(str(meta.get('timestamp_utc')))}<br>
<b>Ejecución:</b> {('<a href="' + html.escape(meta['run_url'], quote=True) + '">abrir build</a>') if meta.get('run_url') else 'N/A'}</div>
<div class="grid">
<div class="card"><div>Casos automatizados trazables ejecutados</div><div class="metric">{rates['total_executed']}</div></div>
<div class="card"><div>Aprobados</div><div class="metric">{rates['passed']}</div></div>
<div class="card"><div>No aprobados</div><div class="metric">{rates['failed']}</div></div>
<div class="card"><div>Pass rate / fail rate</div><div class="metric">{('N/A' if rates['pass_rate_pct'] is None else f"{rates['pass_rate_pct']:.2f}% / {rates['fail_rate_pct']:.2f}%")}</div></div>
</div>
<p class="na">Los porcentajes anteriores usan IDs únicos automatizados con estado en el resumen de esta corrida. No son tasa de defectos ni incluyen pruebas manuales.</p>
<h2>Resultados por suite</h2><table><thead><tr><th>Suite</th><th>Herramienta</th><th>Estado</th><th>Aprobados</th><th>Fallidos</th><th>Pass rate</th></tr></thead><tbody>{suite_rows}</tbody></table>
<h2>Cobertura</h2><ul>{''.join(coverage_cards)}</ul><p>No se promedian componentes con denominadores distintos.</p>
<h2>K6</h2><table><thead><tr><th>Perfil</th><th>Estado</th><th>VUs máx.</th><th>Duración (s)</th><th>API p95 (ms)</th><th>Error de solicitudes</th></tr></thead><tbody>{k6_rows}</tbody></table>
<h2>Métricas calculadas y límites de evidencia</h2><ul>
<li><b>Análisis estático:</b> {html.escape(str(static.get('finding_count') if static.get('finding_count') is not None else 'N/A'))} hallazgos SpotBugs ({html.escape(priorities)}); alcance: {html.escape(static.get('scope', 'N/A'))} Las prioridades del analizador no equivalen a severidad confirmada.</li>
<li><b>Defectos confirmados:</b> {defects['confirmed_count']} asociados a fallos del resumen ({defects['rate_per_100_executed_cases'] if defects['rate_per_100_executed_cases'] is not None else 'N/A'} por cada 100 casos automatizados ejecutados; distribución: {html.escape(json.dumps(defects['severity_distribution'], ensure_ascii=False))}). Total triado abierto: {defects['triaged_confirmed_open_total']}.</li>
<li><b>Defect leakage:</b> No medible; falta un registro de defectos posliberación asociado a versión y periodo de observación. No se interpreta ausencia de reporte como cero.</li>
<li><b>Flaky rate:</b> {('N/A por cambio de fingerprint' if flaky['rate_pct'] is None else f"{flaky['rate_pct']:.2f}% ({flaky['cases_flaky']}/{flaky['cases_repeated']} casos; {flaky['runs']} corridas)")}.</li>
<li><b>Automatización del catálogo:</b> {('N/A' if summary['automation']['automation_rate_pct'] is None else f"{summary['automation']['automation_rate_pct']:.2f}% ({automation_class.get('automated_linked', 0)}/{automation_class.get('applicable_cases', 0)} casos automatizables)")}; {automation_class.get('automation_gap', 0)} brechas y {automation_class.get('manual_only', 0)} solo manuales.</li>
<li><b>Cobertura de ejecución del catálogo en este build:</b> {('N/A' if summary['automation']['execution_coverage_pct'] is None else f"{summary['automation']['execution_coverage_pct']:.2f}% ({summary['automation']['unique_cases_with_automated_result_this_build']}/{summary['automation']['catalog_case_count']})")}.</li>
</ul>
<p><b>TestLink:</b> resumen {html.escape(str(summary['testlink']['summary_generated']))}; publicación {html.escape(str(summary['testlink']['publication_status']))}.</p>
<p>Artefactos originales y resumen JSON se conservan bajo <code>{html.escape(summary['evidence']['run_directory'])}</code>.</p>
</body></html>"""


def main() -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_repo)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--testlink-summary", type=Path,
                        help="Resumen de esta corrida; permite generar el reporte sin sobrescribir el habitual.")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    if args.run_dir:
        run_dir = args.run_dir if args.run_dir.is_absolute() else repo / args.run_dir
    else:
        state = read_json(repo / "qa/.local/jenkins-run.json") or {}
        run_dir = repo / "qa/artifacts" / state.get("runId", "no-qa-stack")
    run_dir = run_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else run_dir / "metrics"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.testlink_summary
    if summary_path and not summary_path.is_absolute():
        summary_path = repo / summary_path
    summary = build_summary(repo, run_dir, summary_path)
    json_path = output_dir / "quality-summary.json"
    html_path = output_dir / "quality-report.html"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(html_report(summary), encoding="utf-8")
    print(f"Resumen JSON: {json_path}")
    print(f"Reporte HTML: {html_path}")
    print(f"Casos automatizados trazables: {summary['summary']['automated_linked_cases']['total_executed']} "
          f"({summary['summary']['automated_linked_cases']['passed']} aprobados, "
          f"{summary['summary']['automated_linked_cases']['failed']} no aprobados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
