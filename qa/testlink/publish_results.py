#!/usr/bin/env python3
"""Publishes verified Dulce Miel results to TestLink XML-RPC.

Dry-run is the default. Pass --publish only after TESTLINK_URL and
TESTLINK_DEVKEY are configured and the project/plan exist in TestLink.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from xmlrpc.client import Fault, ProtocolError, ServerProxy

HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "results" / "current-run.json"
DEFAULT_OUTPUT = HERE / "results" / "publication-report.json"
CASE_MAP = HERE / "results" / "case-id-map.json"
ID_PATTERN = re.compile(r"^TC-(?:F|NF-[A-Z]+)-\d{3}$")


def error_response(value):
    return isinstance(value, list) and bool(value) and isinstance(value[0], dict) and "code" in value[0]


def load_results(input_path: Path):
    payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
    results = payload.get("results", [])
    seen = set()
    for item in results:
        case_id = item.get("case_id", "")
        if not ID_PATTERN.fullmatch(case_id):
            raise ValueError(f"Identificador de caso inválido: {case_id!r}")
        if case_id in seen:
            raise ValueError(f"Caso duplicado en resultados: {case_id}")
        if item.get("status") not in {"p", "f", "b"}:
            raise ValueError(f"Estado TestLink inválido para {case_id}")
        if not item.get("detail"):
            raise ValueError(f"Falta detalle de ejecución para {case_id}")
        seen.add(case_id)
    if not results:
        raise ValueError("No hay resultados verificados para publicar")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_INPUT,
                        help="JSON de resultados de la ejecución actual de QA")
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT,
                        help="ruta del reporte de publicación")
    parser.add_argument("--publish", action="store_true", help="envía resultados realmente a TestLink")
    args = parser.parse_args()
    if not args.results.is_file():
        print(f"No existe el resumen de resultados de esta corrida: {args.results}", file=sys.stderr)
        return 2
    payload = load_results(args.results)
    project = os.getenv("TESTLINK_PROJECT_NAME", payload.get("project", "Dulce Miel"))
    plan_name = os.getenv("TESTLINK_PLAN_NAME", payload.get("plan", "Plan de pruebas - Dulce Miel"))
    build_name = os.getenv("TESTLINK_BUILD_NAME", payload.get("build", "QA local"))
    results = payload["results"]
    case_map_payload = json.loads(CASE_MAP.read_text(encoding="utf-8-sig"))
    case_map = {item["case_id"]: item for item in case_map_payload.get("cases", [])}
    missing = sorted({item["case_id"] for item in results} - set(case_map))
    if missing:
        print(f"Faltan casos en el mapa de TestLink: {missing}", file=sys.stderr)
        return 2
    if not args.publish:
        print(f"Simulación TestLink válida: {len(results)} casos mapeados; "
              f"{sum(x['status']=='p' for x in results)} aprobados, "
              f"{sum(x['status']=='f' for x in results)} no aprobados.")
        return 0
    url, key = os.getenv("TESTLINK_URL", "").strip(), os.getenv("TESTLINK_DEVKEY", "").strip()
    if not url or not key:
        print("Faltan TESTLINK_URL y TESTLINK_DEVKEY; no se envió ningún resultado.", file=sys.stderr)
        return 2
    server = ServerProxy(url, allow_none=True)
    try:
        plan = server.tl.getTestPlanByName({"devKey":key,"testprojectname":project,"testplanname":plan_name})
        if error_response(plan) or not plan:
            raise RuntimeError(str(plan))
        if isinstance(plan, list): plan = plan[0]
        plan_id = plan["id"]
        builds = server.tl.getBuildsForTestPlan({"devKey":key,"testplanid":plan_id}) or []
        build = next((b for b in builds if b.get("name")==build_name), None)
        if build is None:
            build_response = server.tl.createBuild({"devKey":key,"testplanid":plan_id,"buildname":build_name,
                "buildnotes":"Resultados verificados en ejecución QA local; publicados por el flujo de calidad Dulce Miel.",
                "active":1,"open":1})
            if error_response(build_response) or not build_response:
                raise RuntimeError(f"No se pudo crear el build: {build_response}")
            build_id = build_response[0].get("id")
            if not build_id: raise RuntimeError(f"TestLink no devolvió id del build: {build_response}")
        else:
            build_id = build["id"]
    except (Fault, ProtocolError, OSError, KeyError, RuntimeError) as exc:
        print(f"No fue posible preparar TestLink: {exc}", file=sys.stderr)
        return 3
    published, failed = [], []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    for item in results:
        notes = (f"Herramienta: {item['tool']}\nFecha: {stamp}\nDetalle: {item['detail']}\n"
                 f"Evidencia: {item.get('evidence','')}")
        try:
            response = server.tl.reportTCResult({"devKey":key,"testplanid":plan_id,"buildid":build_id,
                "testcaseid":int(case_map[item["case_id"]]["testcaseid"]),"status":item["status"],"notes":notes,"overwrite":True})
            if error_response(response) or not response or not response[0].get("status"):
                raise RuntimeError(str(response))
            published.append(item["case_id"])
        except (Fault, ProtocolError, OSError, RuntimeError) as exc:
            failed.append({"case_id":item["case_id"],"error":str(exc)})
    report={"project":project,"plan":plan_name,"build":build_name,"published":published,"failed":failed}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"TestLink: {len(published)} publicados; {len(failed)} errores. Reporte: {args.report}")
    return 0 if not failed else 4

if __name__ == "__main__": raise SystemExit(main())
