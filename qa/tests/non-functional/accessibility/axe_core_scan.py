"""Escanea rutas públicas con axe-core sin modificar datos de la aplicación."""

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


QA_ROOT = Path(__file__).resolve().parents[3]
AXE_SCRIPT = QA_ROOT / "node_modules" / "axe-core" / "axe.min.js"
DEFAULT_ROUTES = ("/", "/auth/register", "/auth/login", "/productos")
PROTECTED_ROUTES = ("/carrito", "/carrito/checkout", "/seguimiento", "/dashboard")
WCAG_TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")


def scan_page(browser, base_url, route, output_dir):
    page = browser.new_page(viewport={"width": 1365, "height": 900}, locale="es-PE")
    requested_url = urljoin(base_url, route)
    slug = re.sub(r"[^a-z0-9]+", "-", route.lower()).strip("-") or "inicio"
    record = {"route": route, "requested_url": requested_url}
    try:
        response = page.goto(requested_url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_function(
            "document.querySelector('app-root')?.textContent?.trim().length > 0",
            timeout=15000,
        )
        record.update(
            final_url=page.url,
            http_status=response.status if response else None,
            title=page.title(),
            body_excerpt=page.locator("body").inner_text()[:400],
        )
        if urlparse(page.url).path.rstrip("/") != route.rstrip("/"):
            record["redirected"] = True
            return record

        if route == "/productos":
            record["detail_links"] = page.locator('a[href*="/productos/"]').evaluate_all(
                "links => [...new Set(links.map(a => a.getAttribute('href')))].filter(Boolean)"
            )

        page.add_script_tag(path=str(AXE_SCRIPT))
        result = page.evaluate(
            """async tags => await axe.run(document, {
                runOnly: {type: 'tag', values: tags},
                resultTypes: ['violations', 'incomplete', 'passes', 'inapplicable']
            })""",
            list(WCAG_TAGS),
        )
        record["axe"] = result
        page.screenshot(path=str(output_dir / f"{slug}.png"), full_page=True)
        record["screenshot"] = f"{slug}.png"
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        page.close()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Origen HTTP(S) que se revisará")
    parser.add_argument("--output", type=Path, required=True, help="Carpeta de evidencia de la corrida")
    args = parser.parse_args()
    if urlparse(args.base_url).scheme not in ("http", "https"):
        parser.error("--base-url debe comenzar por http:// o https://")
    if not AXE_SCRIPT.is_file():
        parser.error(f"Falta {AXE_SCRIPT}; ejecuta npm ci en qa/")

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            detail_route = None
            for route in DEFAULT_ROUTES:
                record = scan_page(browser, args.base_url, route, output_dir)
                records.append(record)
                if route == "/productos":
                    for link in record.get("detail_links", []):
                        path = urlparse(urljoin(args.base_url, link)).path
                        if re.fullmatch(r"/productos/\d+", path):
                            detail_route = path
                            break
            for route in ([detail_route] if detail_route else []) + list(PROTECTED_ROUTES):
                records.append(scan_page(browser, args.base_url, route, output_dir))
        finally:
            browser.close()

    run = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "axe_version": next((r["axe"]["testEngine"]["version"] for r in records if "axe" in r), None),
        "wcag_tags": WCAG_TAGS,
        "pages": records,
    }
    (output_dir / "axe-results.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "violations.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ruta", "regla", "impacto", "ayuda", "elementos", "selectores", "wcag"])
        for record in records:
            for violation in record.get("axe", {}).get("violations", []):
                writer.writerow([
                    record["route"], violation["id"], violation.get("impact"), violation["help"],
                    len(violation["nodes"]),
                    " | ".join(" ".join(node["target"]) for node in violation["nodes"]),
                    " ".join(tag for tag in violation["tags"] if tag.startswith("wcag")),
                ])
    for record in records:
        print(json.dumps({
            "route": record["route"], "final_url": record.get("final_url"),
            "redirected": record.get("redirected", False),
            "violations": len(record.get("axe", {}).get("violations", [])),
            "incomplete": len(record.get("axe", {}).get("incomplete", [])),
            "error": record.get("error"),
        }, ensure_ascii=False))
    print(f"Evidencia: {output_dir}")


if __name__ == "__main__":
    main()
