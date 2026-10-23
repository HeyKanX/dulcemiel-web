import os

from selenium import webdriver


def create_driver():
    options = webdriver.ChromeOptions()
    if os.getenv("QA_HEADLESS", "1") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1365,900")
    return webdriver.Chrome(options=options)
