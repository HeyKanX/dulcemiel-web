"""Escanea rutas públicas con axe-core sin modificar datos de la aplicación."""

import argparse
import csv
import json
import os
import re
import shlex
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


QA_ROOT = Path(__file__).resolve().parents[3]
AXE_SCRIPT = QA_ROOT / "node_modules" / "axe-core" / "axe.min.js"
DEFAULT_ROUTES = ("/", "/auth/register", "/auth/login", "/productos")
PROTECTED_ROUTES = ("/carrito", "/carrito/checkout", "/seguimiento", "/dashboard")
WCAG_TAGS = ("wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa")


def qa_sql(query):
    """Run only against this workflow's disposable Compose database."""
    state_path = QA_ROOT / ".local" / "jenkins-run.json"
    env_path = QA_ROOT / ".local" / "compose.env"
    if not state_path.is_file() or not env_path.is_file():
        raise RuntimeError("No se encontró el estado de la base QA aislada.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    project = str(state.get("project", ""))
    if not state.get("ready") or not project.startswith("dmqa-"):
        raise RuntimeError("La base identificada no pertenece a una ejecución QA efímera activa.")
    values = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = shlex.split(value)[0] if value else ""
    password = values.get("QA_SQL_PASSWORD")
    if not password:
        raise RuntimeError("Falta la clave SQL del stack QA efímero.")
    env = os.environ.copy()
    env["SQLCMDPASSWORD"] = password
    command = [
        "docker", "compose", "--project-name", project, "--env-file", str(env_path),
        "-f", str(QA_ROOT.parent / "compose.qa.yaml"), "exec", "-T", "-e",
        "SQLCMDPASSWORD", "sql", "/opt/mssql-tools18/bin/sqlcmd", "-S", "localhost",
        "-U", "sa", "-C", "-b", "-Q", query,
    ]
    result = subprocess.run(command, cwd=QA_ROOT.parent, env=env, capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError("La preparación sintética de QA falló: " + result.stderr[-500:])


def create_account(api_url, role):
    email = f"axe-{role}-{uuid.uuid4().hex[:12]}@example.test"
    password = f"Axe-QA-{uuid.uuid4().hex[:16]}!"
    response = requests.post(
        f"{api_url.rstrip('/')}/auth/register",
        json={"nombre": "Auditoria accesibilidad QA", "email": email,
              "password": password, "passwordConfirm": password},
        timeout=20,
    )
    if response.status_code != 201:
        raise RuntimeError(f"No se pudo crear la cuenta sintética de accesibilidad: HTTP {response.status_code}.")
    if role == "admin":
        safe_email = email.replace("'", "''")
        qa_sql(
            "USE DulceMielBD; SET XACT_ABORT ON; "
            f"UPDATE dbo.usuarios SET rol='admin' WHERE email=N'{safe_email}'; "
            "IF @@ROWCOUNT<>1 THROW 51000,'No se actualizó exactamente la cuenta admin sintética',1;"
        )
    login = requests.post(
        f"{api_url.rstrip('/')}/auth/login", json={"email": email, "password": password}, timeout=20,
    )
    if login.status_code != 200 or not login.json().get("token"):
        raise RuntimeError(f"No se pudo iniciar sesión con la cuenta sintética {role}.")
    return {"email": email, "password": password}


def remove_accounts(accounts):
    if not accounts:
        return
    emails = ",".join("N'" + account["email"].replace("'", "''") + "'" for account in accounts)
    qa_sql(
        "USE DulceMielBD; SET XACT_ABORT ON; BEGIN TRAN; "
        "DECLARE @ids TABLE(id INT); "
        f"INSERT INTO @ids SELECT id FROM dbo.usuarios WHERE email IN ({emails}); "
        "DELETE FROM dbo.carrito WHERE usuario_id IN (SELECT id FROM @ids); "
        "DELETE FROM dbo.usuarios WHERE id IN (SELECT id FROM @ids); COMMIT;"
    )


def authenticate(page, base_url, account):
    page.goto(urljoin(base_url, "/auth/login"), wait_until="domcontentloaded")
    page.locator('input[formcontrolname="email"]').fill(account["email"])
    page.locator('input[formcontrolname="password"]').fill(account["password"])
    page.get_by_role("button", name="Ingresar").click()
    page.wait_for_url(lambda url: "/auth/login" not in url, timeout=20000)


def scan_page(browser, base_url, route, output_dir, account=None):
    page = browser.new_page(viewport={"width": 1365, "height": 900}, locale="es-PE")
    requested_url = urljoin(base_url, route)
    slug = re.sub(r"[^a-z0-9]+", "-", route.lower()).strip("-") or "inicio"
    record = {"route": route, "requested_url": requested_url}
    try:
        response = None
        if account:
            authenticate(page, base_url, account)
            current_path = urlparse(page.url).path.rstrip("/") or "/"
            expected_path = "/productos" if route == "/" else route.rstrip("/")
            if current_path != expected_path:
                response = page.goto(requested_url, wait_until="domcontentloaded", timeout=30000)
        else:
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
        final_path = urlparse(page.url).path.rstrip("/") or "/"
        expected_path = "/productos" if route == "/" else route.rstrip("/")
        if final_path != expected_path:
            record["redirected"] = True
            return record
        if route == "/":
            record["canonical_route"] = "/productos"

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
    parser.add_argument(
        "--fail-on-violations", action="store_true",
        help="Devuelve código distinto de cero si hay violaciones WCAG o errores de navegación.",
    )
    args = parser.parse_args()
    if urlparse(args.base_url).scheme not in ("http", "https"):
        parser.error("--base-url debe comenzar por http:// o https://")
    if not AXE_SCRIPT.is_file():
        parser.error(f"Falta {AXE_SCRIPT}; ejecuta npm ci en qa/")

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    api_url = os.getenv("QA_API_URL", "http://127.0.0.1:5000/api").rstrip("/")
    accounts = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            client = create_account(api_url, "cliente")
            accounts.append(client)
            admin = create_account(api_url, "admin")
            accounts.append(admin)
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
                account = admin if route == "/dashboard" else client
                records.append(scan_page(browser, args.base_url, route, output_dir, account=account))
        finally:
            browser.close()
            remove_accounts(accounts)

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
    if args.fail_on_violations and any(
        record.get("error") or record.get("axe", {}).get("violations")
        for record in records
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
