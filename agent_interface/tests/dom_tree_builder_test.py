import os
import sys

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.browser.browser_context import BrowserSession

if __name__ == "__main__":

    bs = BrowserSession()

    try:
        print("\n=== 1) Open initial page (should launch browser + create first tab) ===")
        page = bs.get_current_page()
        print(" Session:", bs.get_session())
        print("\n=== 2) Navigate to example.com ===")
        bs.navigate_to("https://example.com")
        print("  → URL is now:", bs.get_current_page().url)
        print("\n=== 3) Refresh page ===")
        bs.refresh_page()
        print("  → Page reloaded.")
        print("\n=== 4) Navigate to example.org ===")
        bs.navigate_to("https://example.org")
        print("  → URL is now:", bs.get_current_page().url)

        print("\n=== 5) Go back ===")
        bs.go_back()
        print("  → URL after back():", bs.get_current_page().url)

        print("\n=== 6) Go forward ===")
        bs.go_forward()
        print("  → URL after forward():", bs.get_current_page().url)

        print("\n=== 7) Create a brand-new tab (python.org) ===")
        new_tab_info = bs.create_new_tab("https://python.org")
        print("  → New tab info:", new_tab_info)

        print("\n=== 8) List all tabs ===")
        tabs = bs.get_tabs_info()
        for t in tabs:
            print("   ", t)

        print("\n=== 9) Switch back to tab 0 ===")
        success = bs.switch_to_tab(0)
        print("  → switch_to_tab(0) returned", success, "current URL:", bs.get_current_page().url)

        print("\n=== 10) Build DOM tree ===")
        root = bs.get_element_tree()
        print("  → Root node:", getattr(root, "tag_name", None))

        print("\n=== 11) Build selector map ===")
        sel_map = bs.get_selector_map()
        print("  → Selector map size:", len(sel_map) if sel_map else 0)

        print("\n=== 12) Selector map string ===")
        print(bs.get_selector_map_string())

        print("\n=== 13) Element tree string ===")
        print(bs.get_element_tree_string())

        print("\n=== 13) Close tab 1 ===")
        closed = bs.close_tab(1)
        print("  → close_tab(1) returned", closed)
        print("  → Tabs now:", bs.get_tabs_info())

    except Exception as e:
        print("‼️  Something went wrong during testing:", e)

    finally:
        print("\n=== 14) Close entire session ===")
        bs.close()
        print("  → Final session:", bs.get_session())