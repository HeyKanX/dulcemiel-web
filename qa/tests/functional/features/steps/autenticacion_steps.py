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
from pages.auth_page import AuthPage

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
