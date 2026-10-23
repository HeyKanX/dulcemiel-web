from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CatalogPage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 12)

    def open(self):
        self.driver.get(f"{self.base_url}/productos")
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".catalog-header h2")))
        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".spinner-border")))

    def product(self, name):
        return self.wait.until(EC.visibility_of_element_located((By.XPATH, f"//article[contains(@class,'product-card')][.//h3[normalize-space()='{name}']]")))

    def open_detail(self, name):
        link = self.product(name).find_element(By.LINK_TEXT, "Ver")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        link.send_keys(Keys.ENTER)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
