import os
import re
import sys
from pathlib import Path

FUNCTIONAL_ROOT = Path(__file__).resolve().parents[1]
QA_ROOT = FUNCTIONAL_ROOT.parents[1]
for root in (str(QA_ROOT), str(FUNCTIONAL_ROOT)):
    if root not in sys.path:
        sys.path.insert(0, root)

from testsupport.driver_factory import create_driver
from utils.config import API_URL, WEB_URL, require_isolated_db


def before_all(context):
    context.api_url = API_URL
    context.web_url = WEB_URL
    context.run_id = os.getenv("QA_RUN_ID", "manual")
    context.artifacts = Path(os.getenv("QA_ARTIFACTS", "artifacts"))
    context.artifacts.mkdir(parents=True, exist_ok=True)


def before_scenario(context, scenario):
    context.browser = None
    if "writes" in scenario.tags:
        require_isolated_db()
    context.browser = create_driver()


def after_scenario(context, scenario):
    browser = getattr(context, "browser", None)
    if browser is None:
        return

    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", scenario.name)[:80]
    status = getattr(scenario.status, "name", str(scenario.status)).lower()
    evidence_name = f"{context.run_id}_{status}_{safe}"
    try:
        browser.save_screenshot(str(context.artifacts / f"{evidence_name}.png"))
        body = browser.find_element("tag name", "body").text[-3000:]
        (context.artifacts / f"{evidence_name}.txt").write_text(body, encoding="utf-8")
    finally:
        browser.quit()
