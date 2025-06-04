import os
import sys

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from playwright.sync_api import sync_playwright
from src.browser.dom_tree_parser import DOMTreeParser

def run_demo(html_file: str) -> None:
    """Demo entry: load HTML, parse DOM, and print both tree and selector map."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_file}")

        parser = DOMTreeParser(page)
        parser.parse()

        print("\n=== DOM Tree ===")
        print(parser.get_dom_string())

        print("\n=== Selector Map ===")
        print(parser.selector_map_json())

        print("\n=== Selector Map String ===")
        print(parser.get_selector_map_string())

        browser.close()


if __name__ == "__main__":
    demo_html = os.path.join(PROJECT_ROOT, "html", "login_form.html")
    run_demo(demo_html)