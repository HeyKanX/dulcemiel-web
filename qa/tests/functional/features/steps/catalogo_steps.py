import sys
from pathlib import Path

FUNCTIONAL_ROOT = Path(__file__).resolve().parents[2]
if str(FUNCTIONAL_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTIONAL_ROOT))

from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from pages.catalog_page import CatalogPage



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
