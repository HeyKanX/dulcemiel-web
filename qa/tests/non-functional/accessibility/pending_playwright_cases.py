#!/usr/bin/env python3
"""Automatiza los ocho casos Playwright antes pendientes y produce JUnit trazable."""
from __future__ import annotations

import json
import os
import subprocess
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import Page, sync_playwright


QA_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = QA_ROOT.parent
DEFAULT_WEB = "http://127.0.0.1:4200"
DEFAULT_API = "http://127.0.0.1:5000/api"
WEB = os.getenv("QA_WEB_URL", DEFAULT_WEB).rstrip("/")
API = os.getenv("QA_API_URL", DEFAULT_API).rstrip("/")
ARTIFACTS = Path(os.getenv("QA_ARTIFACTS", str(QA_ROOT / "artifacts" / "pending-playwright-local")))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
SYNTHETIC_EMAILS: list[str] = []


@dataclass
class CaseContext:
    page: Page
    email: str
    password: str = "QA-Playwright-Only-123!"
    evidence_files: list[str] = field(default_factory=list)
    detail: str = ""


def sql_command(query: str) -> str:
    """Run SQL only against the active Jenkins QA stack or the named local QA container."""
    state_path = QA_ROOT / ".local" / "jenkins-run.json"
    compose_env = QA_ROOT / ".local" / "compose.env"
    local_connection = QA_ROOT / ".local" / "connection.json"
    if state_path.is_file() and compose_env.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        project = str(state.get("project", ""))
        if not project.startswith("dmqa-") or not state.get("ready"):
            raise RuntimeError("El stack Compose no está listo o no pertenece a QA.")
        values = {}
        for line in compose_env.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip("'").strip('"')
        password = values.get("QA_SQL_PASSWORD")
        if not password:
            raise RuntimeError("Falta la contraseña SQL del stack QA efímero.")
        command = [
            "docker", "compose", "--project-name", project, "--env-file", str(compose_env),
            "-f", str(REPO_ROOT / "compose.qa.yaml"), "exec", "-T", "-e",
            "SQLCMDPASSWORD", "sql", "/opt/mssql-tools18/bin/sqlcmd",
            "-S", "localhost", "-U", "sa", "-C", "-b", "-h", "-1", "-W", "-Q", query,
        ]
        command_env = os.environ.copy()
        command_env["SQLCMDPASSWORD"] = password
    elif local_connection.is_file():
        cfg = json.loads(local_connection.read_text(encoding="utf-8-sig"))
        if cfg.get("container") != "dulce-miel-qa-c5" or int(cfg.get("port", 0)) != 14333:
            raise RuntimeError("La configuración local no apunta al contenedor SQL QA esperado.")
        command = [
            "docker", "exec", "-e", "SQLCMDPASSWORD", cfg["container"],
            "/opt/mssql-tools18/bin/sqlcmd", "-S", "localhost", "-U", "sa", "-C", "-b",
            "-h", "-1", "-W", "-Q", query,
        ]
        command_env = os.environ.copy()
        command_env["SQLCMDPASSWORD"] = cfg["password"]
    else:
        raise RuntimeError("No se encontró una base QA aislada; no se ejecutan escrituras.")
    completed = subprocess.run(command, cwd=REPO_ROOT, env=command_env, capture_output=True, text=True, timeout=40)
    if completed.returncode:
        raise RuntimeError("SQL QA falló: " + completed.stderr[-800:])
    return completed.stdout.strip()


def register(ctx: CaseContext, role: str = "cliente") -> None:
    response = requests.post(
        f"{API}/auth/register",
        json={"nombre": "Cuenta QA Playwright", "email": ctx.email,
              "password": ctx.password, "passwordConfirm": ctx.password},
        timeout=20,
    )
    if response.status_code != 201:
        raise AssertionError(f"No se pudo preparar la cuenta sintética: HTTP {response.status_code}.")
    SYNTHETIC_EMAILS.append(ctx.email)
    if role == "admin":
        email_sql = ctx.email.replace("'", "''")
        sql_command(
            "USE DulceMielBD; "
            f"UPDATE dbo.usuarios SET rol='admin' WHERE email=N'{email_sql}'; "
            "IF @@ROWCOUNT<>1 THROW 51000,'No se actualizó exactamente la cuenta sintética QA',1;"
        )


def login(ctx: CaseContext) -> None:
    page = ctx.page
    page.goto(f"{WEB}/auth/login", wait_until="domcontentloaded")
    page.locator('input[formcontrolname="email"]').fill(ctx.email)
    page.locator('input[formcontrolname="password"]').fill(ctx.password)
    page.get_by_role("button", name="Ingresar").click()
    page.wait_for_url(lambda url: "/auth/login" not in url, timeout=20000)


def product_card(page: Page):
    return page.locator("article.product-card").filter(
        has=page.get_by_role("heading", name="Miel QA", exact=True)
    ).first


def open_products(page: Page) -> None:
    if urlparse(page.url).path.rstrip("/") != "/productos":
        page.goto(f"{WEB}/productos", wait_until="domcontentloaded")
    page.get_by_role("heading", name="Productos de la colmena").wait_for(timeout=20000)
    product_card(page).wait_for(timeout=20000)


def add_miel_qa(page: Page) -> None:
    card = product_card(page)
    card.get_by_role("button", name="Agregar").click()
    page.get_by_text("Miel QA agregado al carrito.").wait_for(timeout=15000)


def cleanup_synthetic_accounts() -> None:
    if not SYNTHETIC_EMAILS:
        return
    # Remove only the synthetic accounts created by this exact run.
    emails = ",".join("N'" + email.replace("'", "''") + "'" for email in SYNTHETIC_EMAILS)
    sql_command(
        "USE DulceMielBD; SET XACT_ABORT ON; BEGIN TRAN; "
        "DECLARE @ids TABLE(id INT); "
        f"INSERT INTO @ids SELECT id FROM dbo.usuarios WHERE email IN ({emails}); "
        "DELETE FROM dbo.carrito WHERE usuario_id IN (SELECT id FROM @ids); "
        "DELETE FROM dbo.usuarios WHERE id IN (SELECT id FROM @ids); COMMIT;"
    )
    SYNTHETIC_EMAILS.clear()


def case_tc_f_006(ctx: CaseContext) -> None:
    # Seeded QA fixture starts with stock=5; restore it even when the assertion fails.
    sql_command(
        "USE DulceMielBD; UPDATE dbo.productos SET stock=0 WHERE nombre=N'Miel QA'; "
        "IF @@ROWCOUNT<>1 THROW 51000,'No se encontró el producto sintético Miel QA',1;"
    )
    try:
        open_products(ctx.page)
        card = product_card(ctx.page)
        card.get_by_text("0 und.", exact=True).wait_for()
        assert card.get_by_role("button", name="Agregar").is_disabled(), "Agregar debería estar deshabilitado con stock cero."
        ctx.detail = "Con stock cero el catálogo muestra 0 und. y deshabilita Agregar."
        evidence = "TC-F-006-stock-cero.png"
        ctx.page.screenshot(path=str(ARTIFACTS / evidence), full_page=True)
        ctx.evidence_files.append(evidence)
    finally:
        sql_command(
            "USE DulceMielBD; UPDATE dbo.productos SET stock=5 WHERE nombre=N'Miel QA'; "
            "IF @@ROWCOUNT<>1 THROW 51000,'No se restauró la existencia sintética de QA',1;"
        )


def case_tc_f_011(ctx: CaseContext) -> None:
    register(ctx)
    login(ctx)
    open_products(ctx.page)
    add_miel_qa(ctx.page)
    ctx.page.get_by_role("link", name="Carrito").click()
    quantity = ctx.page.locator(".cart-item input[type=number]")
    quantity.wait_for()
    quantity.fill("2")
    quantity.press("Tab")
    ctx.page.wait_for_function("document.querySelector('.summary .total strong')?.textContent?.includes('25.00')")
    quantity = ctx.page.locator(".cart-item input[type=number]")
    quantity.fill("3")
    quantity.press("Tab")
    ctx.page.wait_for_function("document.querySelector('.summary .total strong')?.textContent?.includes('37.50')")
    ctx.page.screenshot(path=str(ARTIFACTS / "TC-F-011-carrito-editado.png"), full_page=True)
    ctx.evidence_files.append("TC-F-011-carrito-editado.png")
    ctx.page.locator(".cart-item button").get_by_text("Eliminar").click()
    ctx.page.get_by_text("Tu carrito esta vacio").wait_for()
    ctx.detail = "Se modificó cantidad 1→2→3, se verificaron S/ 25.00 y S/ 37.50, y el producto se quitó del carrito."


def case_tc_acc_004(ctx: CaseContext) -> None:
    open_products(ctx.page)
    controls = ctx.page.locator('input[placeholder="Buscar producto"], select').evaluate_all(
        "els => els.map(e => ({name: e.getAttribute('aria-label'), labels: e.labels?.length || 0}))"
    )
    images = ctx.page.locator(".product-grid img").evaluate_all(
        "els => els.map(e => ({alt: e.getAttribute('alt'), src: e.getAttribute('src')}))"
    )
    missing = [item for item in controls if item["labels"] == 0 and not item["name"]]
    missing.extend(item for item in images if not item["alt"])
    ctx.detail = f"Controles/imágenes sin nombre accesible: {len(missing)}."
    assert not missing, f"Elementos del catálogo sin nombre accesible/texto alternativo: {len(missing)}."


def case_tc_acc_005(ctx: CaseContext) -> None:
    open_products(ctx.page)
    card = product_card(ctx.page)
    assert card.get_by_text("5 und.", exact=True).is_visible(), "El stock disponible no se comunica como texto."
    assert card.get_by_text("Stock bajo", exact=True).is_visible(), "La alerta de stock bajo solo podría percibirse por color."
    ctx.detail = "El stock 5 und. y la alerta Stock bajo aparecen como texto visible."


def case_tc_acc_008(ctx: CaseContext) -> None:
    register(ctx)
    login(ctx)
    open_products(ctx.page)
    add_miel_qa(ctx.page)
    ctx.page.get_by_role("link", name="Carrito").click()
    quantity = ctx.page.locator(".cart-item input[type=number]")
    quantity.wait_for()
    quantity.fill("2")
    quantity.press("Tab")
    ctx.page.wait_for_function("document.querySelector('.summary .total strong')?.textContent?.includes('25.00')")
    announced = ctx.page.locator('[aria-live], [role="status"], [role="alert"]').count()
    ctx.detail = f"Regiones de anuncio después del cambio de cantidad: {announced}."
    assert announced > 0, "El cambio de cantidad no tiene región viva/status/alert para tecnología asistiva."


def case_tc_acc_009(ctx: CaseContext) -> None:
    register(ctx)
    login(ctx)
    open_products(ctx.page)
    add_miel_qa(ctx.page)
    ctx.page.get_by_role("link", name="Carrito").click()
    ctx.page.get_by_role("link", name="Proceder al checkout").click()
    ctx.page.get_by_role("heading", name="Checkout").wait_for()
    ctx.page.locator(".list-group-item").wait_for()
    fields = ctx.page.locator("form.delivery-form input, form.delivery-form textarea").evaluate_all(
        "els => els.map(e => ({name: e.getAttribute('formcontrolname'), labels: e.labels?.length || 0, "
        "aria: e.getAttribute('aria-label'), described: e.getAttribute('aria-describedby')}))"
    )
    ctx.page.get_by_role("button", name="Confirmar pedido").click()
    ctx.page.locator(".alert-danger").wait_for()
    missing = [f for f in fields if f["labels"] == 0 and not f["aria"]]
    ctx.detail = f"Controles sin etiqueta programática: {len(missing)}/{len(fields)}; el formulario vacío mostró validación."
    assert not missing, f"{len(missing)}/{len(fields)} controles no tienen etiqueta programática."
    assert all(f["described"] for f in fields), "Hay campos de checkout sin asociación a mensaje de error."


def case_tc_acc_012(ctx: CaseContext) -> None:
    register(ctx, role="admin")
    login(ctx)
    ctx.page.get_by_role("heading", name="Dashboard").wait_for()
    reached = False
    for _ in range(50):
        ctx.page.keyboard.press("Tab")
        active = ctx.page.evaluate("({href:document.activeElement?.getAttribute('href'), text:(document.activeElement?.innerText||'').trim()})")
        if active.get("href") == "/dashboard/productos" and "Productos" in active.get("text", ""):
            ctx.page.keyboard.press("Enter")
            reached = True
            break
    ctx.page.get_by_role("heading", name="Gestion de productos").wait_for()
    found: set[str] = set()
    visible_focus = False
    for _ in range(40):
        ctx.page.keyboard.press("Tab")
        item = ctx.page.evaluate(
            "(()=>{const e=document.activeElement,s=getComputedStyle(e);return {field:e?.getAttribute('formcontrolname'),"
            "tag:e?.tagName,outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow}})()"
        )
        if item.get("field"):
            found.add(item["field"])
        if item.get("outline") not in (None, "none", "") and item.get("width") not in (None, "0px"):
            visible_focus = True
        if item.get("shadow") not in (None, "none"):
            visible_focus = True
        if len(found) == 6:
            break
    expected = {"nombre", "descripcion", "precio", "stock", "categoria", "estado"}
    assert reached and expected.issubset(found) and visible_focus, (
        f"Ruta keyboard={reached}; controles={sorted(found)}; foco visible={visible_focus}."
    )
    ctx.detail = "Tab/Enter llegó a Gestión de productos, recorrió los seis controles y mostró foco visible; no se guardó ningún cambio."


def case_tc_acc_013(ctx: CaseContext) -> None:
    ctx.page.set_viewport_size({"width": 683, "height": 900})
    open_products(ctx.page)
    overflow = ctx.page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    count = ctx.page.locator("article.product-card").count()
    add_count = ctx.page.get_by_role("button", name="Agregar").count()
    assert not overflow and count > 0 and add_count == count, (
        f"Viewport equivalente a 200%: overflow={overflow}, tarjetas={count}, botones={add_count}."
    )
    ctx.detail = f"Viewport CSS 683px equivalente al reflujo 200%; sin overflow y {count} tarjetas con botones visibles."


CASES = [
    ("TC-F-006", case_tc_f_006),
    ("TC-F-011", case_tc_f_011),
    ("TC-NF-ACC-004", case_tc_acc_004),
    ("TC-NF-ACC-005", case_tc_acc_005),
    ("TC-NF-ACC-008", case_tc_acc_008),
    ("TC-NF-ACC-009", case_tc_acc_009),
    ("TC-NF-ACC-012", case_tc_acc_012),
    ("TC-NF-ACC-013", case_tc_acc_013),
]


def main() -> int:
    if os.getenv("QA_ISOLATED_DB") != "1":
        raise SystemExit("Refusing to run: QA_ISOLATED_DB=1 is required.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        suite = ET.Element("testsuite", name="DulceMiel.PendingPlaywright", tests=str(len(CASES)), failures="0", errors="0", skipped="0")
        results = []
        failures = 0
        try:
            for case_id, function in CASES:
                email = f"qa-ci-{case_id.lower().replace('-', '')}-{uuid.uuid4().hex[:12]}@example.test"
                page = browser.new_page(viewport={"width": 1365, "height": 900}, locale="es-PE")
                page.set_default_timeout(15000)
                context = CaseContext(page=page, email=email)
                started = datetime.now(timezone.utc)
                case_result = {"case_id": case_id, "status": "p", "tool": "Playwright Chromium", "detail": "", "evidence_files": []}
                testcase = ET.SubElement(suite, "testcase", classname="DulceMiel.PendingPlaywright", name=f"{case_id} - automated QA flow")
                try:
                    function(context)
                except Exception as exc:  # Every case is reported; known defects do not stop later cases.
                    failures += 1
                    case_result.update(status="f", detail=context.detail or f"{type(exc).__name__}: {exc}")
                    failure = ET.SubElement(testcase, "failure", message=case_result["detail"][:500], type=type(exc).__name__)
                    failure.text = str(exc)
                finally:
                    try:
                        default_evidence = f"{case_id}.png"
                        page.screenshot(path=str(ARTIFACTS / default_evidence), full_page=True)
                        context.evidence_files.append(default_evidence)
                    except Exception:
                        pass
                    case_result["detail"] = context.detail or case_result.get("detail") or "Recorrido Playwright completado."
                    case_result["evidence_files"] = context.evidence_files
                    system_out = ET.SubElement(testcase, "system-out")
                    system_out.text = json.dumps(case_result, ensure_ascii=False)
                    duration = (datetime.now(timezone.utc) - started).total_seconds()
                    testcase.set("time", f"{duration:.3f}")
                    page.close()
                results.append(case_result)
                print(f"{case_id}: {'PASS' if case_result['status']=='p' else 'FAIL'} — {case_result['detail']}")
        finally:
            browser.close()
            suite.set("failures", str(failures))
            ET.ElementTree(suite).write(ARTIFACTS / "junit.xml", encoding="utf-8", xml_declaration=True)
            payload = {
                "run_id": os.getenv("QA_RUN_ID", "local"), "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "web_url": WEB, "api_url": API, "cases": results,
            }
            (ARTIFACTS / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                cleanup_synthetic_accounts()
            except Exception as exc:
                print(f"WARNING: synthetic QA cleanup failed: {type(exc).__name__}: {exc}")
    print(f"JUnit: {ARTIFACTS / 'junit.xml'}; results: {ARTIFACTS / 'results.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
