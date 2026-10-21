"""Escaneo de apoyo; cada violación requiere revisión humana antes de declararse defecto."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from playwright.sync_api import sync_playwright

from utils.config import WEB_URL


def main():
    root = Path(__file__).resolve().parents[2]
    axe_script = root / "node_modules" / "axe-core" / "axe.min.js"
    if not axe_script.exists():
        raise SystemExit("Falta axe-core. Ejecuta npm install en qa/.")
    output = Path(os.getenv("QA_ARTIFACTS", "artifacts"))
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for case_id, route in (("CA21", "/auth/register"), ("CA22", "/auth/login"), ("CA34", "/productos")):
            page = browser.new_page(viewport={"width": 1365, "height": 900})
            page.goto(f"{WEB_URL}{route}", wait_until="networkidle")
            page.add_script_tag(path=str(axe_script))
            scan = page.evaluate("async () => await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']}})")
            results.append({
                "case": case_id,
                "route": route,
                "violations": [{"id": v["id"], "impact": v["impact"], "description": v["description"], "nodes": [{"target": n["target"], "failureSummary": n["failureSummary"]} for n in v["nodes"]]} for v in scan["violations"]],
                "incomplete": [{"id": v["id"], "count": len(v["nodes"])} for v in scan["incomplete"]],
                "passes": len(scan["passes"]),
            })
            page.screenshot(path=str(output / f"{case_id}.png"), full_page=True)
            page.close()
        browser.close()
    destination = output / "axe-results.json"
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        print(f"{result['case']}: {len(result['violations'])} reglas con hallazgos automáticos; {len(result['incomplete'])} revisiones manuales")
    print(f"Informe: {destination}")


if __name__ == "__main__":
    main()
