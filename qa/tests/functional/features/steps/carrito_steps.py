import json
import sys
import uuid
from pathlib import Path

FUNCTIONAL_ROOT = Path(__file__).resolve().parents[2]
QA_ROOT = Path(__file__).resolve().parents[4]
for root in (str(QA_ROOT), str(FUNCTIONAL_ROOT)):
    if root not in sys.path:
        sys.path.insert(0, root)

import requests
from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.auth_page import AuthPage
from pages.catalog_page import CatalogPage

def synthetic_email(context):
    return f"qa-{context.run_id}-{uuid.uuid4().hex[:10]}@example.test"



@given("que un cliente sintético inicia sesión")
def logged_in_client(context):
    context.email = synthetic_email(context)
    data = {"nombre": "Cliente QA", "email": context.email, "password": "Prueba123!", "passwordConfirm": "Prueba123!"}
    response = requests.post(f"{context.api_url}/auth/register", json=data, timeout=10)
    assert response.status_code == 201, f"No se preparó el cliente: HTTP {response.status_code}"
    context.auth = AuthPage(context.browser, context.web_url)
    context.auth.open_login()
    context.auth.fill(email=context.email, password="Prueba123!")
    context.auth.submit()
    WebDriverWait(context.browser, 12).until(lambda browser: "/auth/login" not in browser.current_url)



@when("agrega Miel QA desde el catálogo")
def add_from_catalog(context):
    context.catalog = CatalogPage(context.browser, context.web_url)
    WebDriverWait(context.browser, 12).until(lambda browser: "/productos" in browser.current_url)
    card = context.catalog.product("Miel QA")
    button = card.find_element(By.XPATH, ".//button[normalize-space()='Agregar']")
    context.browser.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
    button.send_keys(Keys.ENTER)
    WebDriverWait(context.browser, 12).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".alert-success"), "agregado"))



@then("el carrito muestra una unidad y total correcto")
def verify_cart(context):
    context.browser.find_element(By.CSS_SELECTOR, 'a[href="/carrito"]').send_keys(Keys.ENTER)
    WebDriverWait(context.browser, 12).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".cart-item"), "Miel QA"))
    assert context.browser.find_element(By.CSS_SELECTOR, ".cart-item input[type='number']").get_attribute("value") == "1"
    assert "12.50" in context.browser.find_element(By.CSS_SELECTOR, ".summary .total").text



@when("abre el checkout sin productos")
def empty_checkout(context):
    context.browser.get(f"{context.web_url}/carrito/checkout")
    WebDriverWait(context.browser, 12).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1")))



@then("no puede confirmar un pedido")
def verify_empty_checkout(context):
    button = context.browser.find_element(By.XPATH, "//button[contains(., 'Confirmar pedido')]")
    assert not button.is_enabled()



@when("solicita directamente la administración")
def open_admin(context):
    context.browser.get(f"{context.web_url}/dashboard/productos")



@then("es redirigido fuera del panel")
def verify_admin_denial(context):
    WebDriverWait(context.browser, 12).until(lambda browser: "/dashboard" not in browser.current_url)
    assert not context.browser.find_elements(By.XPATH, "//h1[contains(.,'Gestion de productos')]")



@when("recarga el catálogo con la sesión activa")
def reload_catalog(context):
    # Aísla únicamente las solicitudes disparadas por esta recarga.
    context.browser.get_log("performance")
    previous_body = context.browser.find_element(By.TAG_NAME, "body")
    context.browser.refresh()
    WebDriverWait(context.browser, 12).until(EC.staleness_of(previous_body))
    WebDriverWait(context.browser, 12).until(
        lambda browser: browser.find_elements(By.CSS_SELECTOR, ".product-card")
        or browser.find_elements(By.CSS_SELECTOR, ".catalog-header + .alert-danger")
        or browser.find_elements(By.CSS_SELECTOR, ".empty-state")
    )
    context.catalog_reload_events = context.browser.get_log("performance")



@then("el catálogo continúa mostrando Miel QA")
def verify_reloaded_catalog(context):
    context.catalog = CatalogPage(context.browser, context.web_url)
    product_cards = context.browser.find_elements(By.CSS_SELECTOR, ".product-card")
    if not any("Miel QA" in card.text for card in product_cards):
        text = context.browser.find_element(By.TAG_NAME, "body").text
        api_probe = {}
        try:
            response = requests.get(f"{context.api_url}/productos", timeout=10)
            api_probe = {
                "status": response.status_code,
                "body": response.text[:500],
            }
        except requests.RequestException as exc:
            api_probe = {"error": type(exc).__name__, "detail": str(exc)[:300]}
        api_events = []
        request_urls = {}
        try:
            for entry in context.catalog_reload_events:
                event = json.loads(entry["message"])["message"]
                params = event.get("params", {})
                request_id = params.get("requestId")
                if event.get("method") == "Network.requestWillBeSent":
                    url = params.get("request", {}).get("url", "")
                    if "/api/productos" in url:
                        request_urls[request_id] = url.split("?", 1)[0]
                        api_events.append({"event": "request", "url": request_urls[request_id]})
                elif request_id in request_urls and event.get("method") == "Network.responseReceived":
                    response = params.get("response", {})
                    record = {"event": "response", "url": request_urls[request_id], "status": response.get("status")}
                    try:
                        body = context.browser.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                        payload = json.loads(body.get("body", "{}"))
                        products = payload.get("data", [])
                        record["product_count"] = len(products) if isinstance(products, list) else None
                        record["qa_product_present"] = any(
                            item.get("nombre") == "Miel QA" for item in products if isinstance(item, dict)
                        ) if isinstance(products, list) else False
                    except Exception as exc:
                        record["body_diagnostic"] = type(exc).__name__
                    api_events.append(record)
                elif request_id in request_urls and event.get("method") == "Network.loadingFailed":
                    api_events.append({"event": "failed", "url": request_urls[request_id], "reason": params.get("errorText")})
        except Exception as exc:
            api_events.append({"event": "diagnostic_error", "reason": type(exc).__name__})
        browser_errors = [
            {"level": item.get("level"), "message": item.get("message", "")[:240]}
            for item in context.browser.get_log("browser")
            if item.get("level") == "SEVERE" and "favicon.ico" not in item.get("message", "")
        ]
        assert False, (
            f"El catálogo no mostró Miel QA tras recargar; url={context.browser.current_url}; "
            f"api_probe={api_probe}; error_visible="
            f"{'No se pudieron cargar los productos.' in text}; api_events={api_events}; "
            f"browser_errors={browser_errors}"
        )
