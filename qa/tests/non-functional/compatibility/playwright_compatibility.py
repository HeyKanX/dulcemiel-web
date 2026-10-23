"""Cobertura complementaria RNF04/CA32: motores y ancho móvil, sin repetir los flujos Behave."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from playwright.sync_api import sync_playwright
from playwright.sync_api import expect

from utils.config import WEB_URL


class CompatibilityAudit(unittest.TestCase):
    def test_catalogo_y_registro_en_motores_y_viewports(self):
        browsers = [x.strip() for x in os.getenv("QA_BROWSERS", "chromium,firefox,webkit").split(",") if x.strip()]
        with sync_playwright() as playwright:
            for engine_name in browsers:
                engine = getattr(playwright, engine_name)
                with self.subTest(engine=engine_name):
                    browser = engine.launch(headless=True)
                    try:
                        for width in (390, 1365):
                            with self.subTest(engine=engine_name, width=width):
                                page = browser.new_page(viewport={"width": width, "height": 850})
                                page.goto(f"{WEB_URL}/productos", wait_until="networkidle")
                                self.assertTrue(page.get_by_role("heading", name="Productos de la colmena").is_visible())
                                self.assertTrue(page.get_by_text("Miel QA", exact=True).first.is_visible())
                                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                                self.assertFalse(overflow, f"Desbordamiento horizontal en {engine_name} {width}px")
                                page.goto(f"{WEB_URL}/auth/register", wait_until="domcontentloaded")
                                expect(page.get_by_role("heading", name="Crear cuenta")).to_be_visible(timeout=10000)
                                page.close()
                    finally:
                        browser.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
