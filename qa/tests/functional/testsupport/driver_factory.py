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
    return webdriver.Chrome(options=options)
