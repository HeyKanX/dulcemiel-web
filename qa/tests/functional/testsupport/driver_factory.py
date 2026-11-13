import os

from selenium import webdriver


def create_driver():
    options = webdriver.ChromeOptions()
    chrome_binary = os.getenv("CHROME_BIN")
    if chrome_binary:
        options.binary_location = chrome_binary
    if os.getenv("QA_HEADLESS", "1") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1365,900")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "SEVERE"})
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Network.enable", {})
    return driver
