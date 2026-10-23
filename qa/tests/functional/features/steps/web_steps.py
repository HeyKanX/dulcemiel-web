import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import requests
from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from pages.auth_page import AuthPage
from pages.catalog_page import CatalogPage


def synthetic_email(context):
    return f"qa-{context.run_id}-{uuid.uuid4().hex[:10]}@example.test"


@given("que el visitante abre el registro")
def open_registration(context):
    context.auth = AuthPage(context.browser, context.web_url)
    context.auth.open_register()


@when("registra una cuenta sintética nueva")
def register_account(context):
    context.email = synthetic_email(context)
    context.auth.fill(nombre="Caso QA", email=context.email, password="Prueba123!", passwordConfirm="Prueba123!")
    context.auth.submit()


@then("ve la confirmación de registro")
def verify_register(context):
    assert "Cuenta creada" in context.auth.alert()


@given("que existe una cuenta sintética para la prueba")
def existing_account(context):
    context.email = synthetic_email(context)
    data = {"nombre": "Caso QA", "email": context.email, "password": "Prueba123!", "passwordConfirm": "Prueba123!"}
    response = requests.post(f"{context.api_url}/auth/register", json=data, timeout=10)
    assert response.status_code == 201, f"No se pudo preparar la cuenta: HTTP {response.status_code}"
    context.auth = AuthPage(context.browser, context.web_url)
    context.auth.open_register()


@when("intenta registrar de nuevo el mismo correo")
def repeat_registration(context):
    context.auth.fill(nombre="Nombre reutilizable", email=context.email, password="Prueba123!", passwordConfirm="Prueba123!")
    context.auth.submit()


@then("ve un error de correo duplicado y conserva el nombre ingresado")
def verify_duplicate(context):
    assert "registrado" in context.auth.alert().lower()
    assert context.browser.find_element(By.CSS_SELECTOR, '[formcontrolname="nombre"]').get_attribute("value") == "Nombre reutilizable"


@given("que el visitante abre el inicio de sesión")
def open_login(context):
    context.auth = AuthPage(context.browser, context.web_url)
    context.auth.open_login()


@when("introduce credenciales sintéticas incorrectas")
def wrong_login(context):
    context.auth.fill(email="inexistente-qa@example.test", password="ClaveIncorrecta123!")
    context.auth.submit()


@then("el acceso se rechaza sin mostrar datos sensibles")
def verify_wrong_login(context):
    message = context.auth.alert().lower()
    assert "incorrect" in message or "credencial" in message
    assert "ClaveIncorrecta123!" not in context.browser.page_source
    assert "/auth/login" in context.browser.current_url


@given("que el visitante abre el catálogo")
def open_catalog(context):
    context.catalog = CatalogPage(context.browser, context.web_url)
    context.catalog.open()


@then("encuentra el producto sintético con nombre precio y disponibilidad")
def verify_catalog(context):
    card = context.catalog.product("Miel QA")
    text = card.text
    assert "Miel QA" in text and "S/" in text and "5 und." in text


@when("abre el detalle del producto sintético")
def open_detail(context):
    context.catalog.open_detail("Miel QA")


@then("ve su descripción precio stock y categoría")
def verify_detail(context):
    page = context.browser.page_source
    for expected in ("Miel QA", "Miel de prueba", "S/", "5", "Alimentos"):
        assert expected in page, expected


@given("que el visitante abre un detalle inexistente")
def absent_product(context):
    context.browser.get(f"{context.web_url}/productos/2147483647")


@then("encuentra un mensaje comprensible y un enlace de regreso")
def verify_missing_product(context):
    wait = WebDriverWait(context.browser, 12)
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Producto no encontrado"))
    assert context.browser.find_element(By.LINK_TEXT, "Volver a productos").is_displayed()


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
    context.browser.refresh()
    WebDriverWait(context.browser, 12).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".catalog-header h2")))


@then("el catálogo continúa mostrando Miel QA")
def verify_reloaded_catalog(context):
    context.catalog = CatalogPage(context.browser, context.web_url)
    try:
        context.catalog.product("Miel QA")
    except TimeoutException:
        text = context.browser.find_element(By.TAG_NAME, "body").text
        assert False, f"El catálogo no mostró Miel QA tras recargar: {'No se pudieron cargar los productos.' in text=}"
