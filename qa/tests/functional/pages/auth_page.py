from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class AuthPage(BasePage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url)

    def open_register(self):
        self.open("/auth/register")
        self.wait_visible((By.CSS_SELECTOR, "h1"))

    def open_login(self):
        self.open("/auth/login")
        self.wait_visible((By.CSS_SELECTOR, "h1"))

    def fill(self, **fields):
        for key, value in fields.items():
            element = self.wait_visible((By.CSS_SELECTOR, f'[formcontrolname="{key}"]'))
            element.clear()
            element.send_keys(value)

    def submit(self):
        self.wait_clickable((By.CSS_SELECTOR, 'button[type="submit"]')).click()

    def alert(self):
        return self.wait_visible((By.CSS_SELECTOR, ".alert")).text
