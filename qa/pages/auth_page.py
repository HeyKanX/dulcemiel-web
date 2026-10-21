from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class AuthPage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 12)

    def open_register(self):
        self.driver.get(f"{self.base_url}/auth/register")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1")))

    def open_login(self):
        self.driver.get(f"{self.base_url}/auth/login")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1")))

    def fill(self, **fields):
        for key, value in fields.items():
            element = self.driver.find_element(By.CSS_SELECTOR, f'[formcontrolname="{key}"]')
            element.clear()
            element.send_keys(value)

    def submit(self):
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    def alert(self):
        return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert"))).text
