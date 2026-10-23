import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from selenium import webdriver

from utils.config import API_URL, WEB_URL, require_isolated_db


def before_all(context):
    context.api_url = API_URL
    context.web_url = WEB_URL
    context.run_id = os.getenv("QA_RUN_ID", "manual")
    context.artifacts = Path(os.getenv("QA_ARTIFACTS", "artifacts"))
    context.artifacts.mkdir(parents=True, exist_ok=True)


def before_scenario(context, scenario):
    if "writes" in scenario.tags:
        require_isolated_db()
    options = webdriver.ChromeOptions()
    if os.getenv("QA_HEADLESS", "1") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1365,900")
    context.browser = webdriver.Chrome(options=options)


def after_scenario(context, scenario):
    if scenario.status.name != "passed":
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", scenario.name)[:80]
        context.browser.save_screenshot(str(context.artifacts / f"{safe}.png"))
        (context.artifacts / f"{safe}.txt").write_text(context.browser.find_element("tag name", "body").text[-3000:], encoding="utf-8")
    context.browser.quit()
