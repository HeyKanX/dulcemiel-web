"""Consolida solo las corridas finales; conserva los XML y JSON originales."""
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def junit_counts(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {
        "tests": sum(int(s.get("tests", 0)) for s in suites),
        "failures": sum(int(s.get("failures", 0)) for s in suites),
        "errors": sum(int(s.get("errors", 0)) for s in suites),
        "skipped": sum(int(s.get("skipped", 0)) for s in suites),
    }


def metric(data, name):
    return data.get("metrics", {}).get(name, {}).get("values", {})


def main():
    evidence = Path(sys.argv[1] if len(sys.argv) > 1 else "../../evidencias-criterio5").resolve()
    behavior_files = sorted(evidence.glob("TESTS-*.xml"))
    behave = {p.name: junit_counts(p) for p in behavior_files}
    api = junit_counts(evidence / "api-newman.xml") if (evidence / "api-newman.xml").exists() else None
    api_requests = len(list(ET.parse(evidence / "api-newman.xml").getroot().iter("testsuite"))) if api else 0
    axe = json.loads((evidence / "axe-results.json").read_text(encoding="utf-8")) if (evidence / "axe-results.json").exists() else []
    loads = {}
    for path in sorted(evidence.glob("k6-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        loads[path.stem] = {key: metric(data, key) for key in ("api_latency", "page_latency", "request_errors", "http_reqs", "checks")}
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "behave": behave,
        "newman": api,
        "newman_requests": api_requests,
        "playwright_log": "playwright.log",
        "axe": [{"case": x["case"], "route": x["route"], "violations": [{"id": v["id"], "impact": v["impact"], "nodes": len(v["nodes"])} for v in x["violations"]], "incomplete_rules": x["incomplete"]} for x in axe],
        "k6": loads,
    }
    output = evidence / "summary.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
