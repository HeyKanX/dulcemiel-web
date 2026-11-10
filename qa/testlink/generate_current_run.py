#!/usr/bin/env python3
"""Build a fresh TestLink payload from automated reports of one Jenkins build."""
from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

CASE_RE = re.compile(r"TC-(?:F-\d{3}|NF-[A-Z]+-\d{3})")
K6_CASES = {
    "smoke": ("TC-NF-REN-001", "TC-NF-REN-002"),
    "baseline": ("TC-NF-REN-001", "TC-NF-REN-002"),
    "moderate": ("TC-NF-REN-001", "TC-NF-REN-002"),
    "stress": ("TC-NF-REN-003",),
    "spike": ("TC-NF-REN-004",),
    "sustained": ("TC-NF-REN-005",),
}
BACKEND_CASES = {
    ("CarritoControllerAuditTest", "cantidadCeroDebeRechazarseAntesDeEscribir"): ("TC-F-010",),
    ("CarritoControllerAuditTest", "cantidadMayorQueStockSeRechaza"): ("TC-F-012",),
    ("CarritoControllerAuditTest", "acumuladoMayorQueStockDebeRechazarseSinActualizar_CA11"): ("TC-F-012",),
    ("CarritoCa11TddTest", "stockCincoConCuatroEnCarritoRechazaAgregarDosSinActualizar"): ("TC-F-012",),
    ("ApiSqlServerIntegrationTest", "registroYLoginConPersistenciaReal"): ("TC-F-001", "TC-F-003"),
    ("ApiSqlServerIntegrationTest", "pedidoCreaDetalleReduceStockYVaciaCarrito"): ("TC-F-013",),
    ("ApiSqlServerIntegrationTest", "pedidoConTelefonoInvalidoNoCambiaDatos"): ("TC-NF-INT-001",),
    ("ApiSqlServerIntegrationTest", "carritoAgregarYRechazarCantidadSuperiorAlStock"): ("TC-F-012",),
}


def add_result(results: dict, case_id: str, status: str, tool: str, detail: str, evidence: str) -> None:
    previous = results.get(case_id)
    if previous:
        previous["status"] = "f" if "f" in (previous["status"], status) else "p"
        previous["tool"] = f"{previous['tool']}; {tool}"
        previous["detail"] = f"{previous['detail']} | {detail}"
        previous["evidence"] = f"{previous['evidence']}; {evidence}"
    else:
        results[case_id] = {
            "case_id": case_id, "status": status, "tool": tool,
            "detail": detail, "evidence": evidence,
        }


def junit_status(case: ET.Element) -> str | None:
    if case.find("skipped") is not None:
        return None
    return "f" if case.find("failure") is not None or case.find("error") is not None else "p"


def read_junit(results: dict, path: Path, source: str, method_map: dict | None = None) -> None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return
    cases = root.iter("testcase") if root.tag != "testcase" else (root,)
    for case in cases:
        status = junit_status(case)
        if status is None:
            continue
        name = case.get("name", "")
        classname = case.get("classname", "")
        ids = set(CASE_RE.findall(name))
        if method_map:
            ids.update(method_map.get((classname.rsplit(".", 1)[-1], name), ()))
        if not ids:
            continue
        detail_node = case.find("failure")
        if detail_node is None:
            detail_node = case.find("error")
        detail = (detail_node.get("message", "fallo de aserción") if detail_node is not None else "Prueba automatizada aprobada.")
        for case_id in sorted(ids):
            add_result(results, case_id, status, source, detail, str(path).replace("\\", "/"))


def read_newman(results: dict, path: Path) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return
    for execution in payload.get("run", {}).get("executions", []):
        request_name = execution.get("item", {}).get("name", "")
        ids = set(CASE_RE.findall(request_name))
        assertions = execution.get("assertions", [])
        request_error = execution.get("requestError")
        if not ids or (not assertions and not request_error):
            continue
        failures = [a.get("assertion", "aserción") for a in assertions if a.get("error")]
        status = "f" if request_error or failures else "p"
        detail = "Fallo de solicitud" if request_error else (
            "Aserciones fallidas: " + ", ".join(failures) if failures else f"{len(assertions)} aserciones aprobadas."
        )
        for case_id in sorted(ids):
            add_result(results, case_id, status, "Newman", detail, str(path).replace("\\", "/"))


def read_k6(results: dict, run_dir: Path) -> None:
    for profile, cases in K6_CASES.items():
        path = run_dir / f"k6-{profile}" / "summary.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        metrics = data.get("metrics", {})
        checked = []
        if profile in {"smoke", "baseline", "moderate"}:
            metric_groups = {
                "TC-NF-REN-001": ("page_latency", "page_errors"),
                "TC-NF-REN-002": ("api_latency", "api_errors"),
            }
        else:
            metric_groups = {case_id: ("api_latency", "page_latency", "api_errors", "page_errors", "request_errors") for case_id in cases}
        for case_id, names in metric_groups.items():
            threshold_checks = []
            for metric_name in names:
                for label, threshold in metrics.get(metric_name, {}).get("thresholds", {}).items():
                    threshold_checks.append((metric_name, label, bool(threshold.get("ok"))))
            if not threshold_checks:
                continue
            passed = all(ok for _, _, ok in threshold_checks)
            failures = [f"{metric} {label}" for metric, label, ok in threshold_checks if not ok]
            detail = f"Perfil {profile}; " + ("umbrales cumplidos" if passed else "umbrales incumplidos: " + ", ".join(failures))
            add_result(results, case_id, "p" if passed else "f", f"k6/{profile}", detail, str(path).replace("\\", "/"))
            checked.append(case_id)


def read_compatibility(results: dict, path: Path) -> None:
    try:
        item = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return
    add_result(results, item["case_id"], item["status"], item["tool"], item["detail"], item["evidence"])


def read_axe(results: dict, path: Path) -> None:
    """Map only automated color-contrast findings to the matching TestLink case."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return
    scanned = [page for page in payload.get("pages", []) if page.get("axe")]
    if not scanned:
        return
    violations = [
        (page.get("route", "?"), violation)
        for page in scanned
        for violation in page["axe"].get("violations", [])
        if violation.get("id") == "color-contrast"
    ]
    detail = (
        "Contraste insuficiente detectado por axe-core: " + "; ".join(
            f"{route} ({len(item.get('nodes', []))} elementos)" for route, item in violations
        )
        if violations else
        f"axe-core no encontró violaciones de contraste en {len(scanned)} páginas escaneadas."
    )
    add_result(
        results, "TC-NF-ACC-014", "f" if violations else "p", "axe-core/WCAG AA",
        detail, str(path).replace("\\", "/"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results/current-run.json")
    parser.add_argument("--build", default=os.getenv("BUILD_TAG", "Jenkins"))
    args = parser.parse_args()
    run_dir = args.run_dir
    results = {}

    for path in Path("backend/target/surefire-reports").glob("TEST-*.xml"):
        read_junit(results, path, "Maven/JUnit", BACKEND_CASES)
    for path in (run_dir / "ui-behave").glob("*.xml"):
        read_junit(results, path, "Behave/Selenium")
    read_newman(results, run_dir / "api/newman.json")
    read_k6(results, run_dir)
    read_compatibility(results, run_dir / "compatibility/result.json")
    read_axe(results, run_dir / "accessibility-axe/axe-results.json")

    if not results:
        print("No hay resultados automatizados trazables para TestLink en esta corrida.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": "Dulce Miel",
        "plan": os.getenv("TESTLINK_PLAN_NAME", "Plan de pruebas - Dulce Miel"),
        "build": f"{args.build}",
        "results": sorted(results.values(), key=lambda item: item["case_id"]),
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(item["status"] == "p" for item in results.values())
    failed = sum(item["status"] == "f" for item in results.values())
    print(f"Resumen actual de TestLink: {len(results)} casos trazables ({passed} aprobados, {failed} no aprobados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
