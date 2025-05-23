import logging
import os
import time
from typing import Optional, List, Dict, Any

from playwright.sync_api import Page, BrowserContext, sync_playwright, Browser

from .dom_tree_parser import DOMTreeParser, DOMElementNode

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserSession:
    """
    Simple browser session manager using Playwright.
    For controlled environments with no security concerns.
    """

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._current_page: Optional[Page] = None
        self._tabs: List[Page] = []

        # Caches for DOM/tree + selector map
        self._parser: Optional[DOMTreeParser] = None
        self._selector_map: Optional[Dict[int, DOMElementNode]] = None

    def _initialize_session(self, headless: bool = False) -> Browser:
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=headless)
        return self._browser

    def _create_context(self) -> BrowserContext:
        if self._browser is None:
            self._initialize_session()
        self._context = self._browser.new_context()
        return self._context

    def get_session(self) -> dict:
        return {
            "playwright": self._playwright,
            "browser": self._browser,
            "context": self._context,
            "current_page": self._current_page,
            "tab_count": len(self._tabs),
        }

    def get_current_page(self) -> Optional[Page]:
        if self._current_page:
            return self._current_page
        # initialize from context
        if self._context:
            pages = self._context.pages
            if pages:
                self._tabs = pages.copy()
                self._current_page = self._tabs[0]
                return self._current_page
        # else open new context + page
        self._create_context()
        return self.create_new_page()

    def create_new_page(self) -> Page:
        if self._context is None:
            self._create_context()
        page = self._context.new_page()
        self._tabs.append(page)
        self._current_page = page
        page.once("close", lambda _: self._on_close(page))
        return page

    def _on_close(self, page: Page):
        if page in self._tabs:
            self._tabs.remove(page)
        if self._current_page == page:
            self._current_page = self._tabs[0] if self._tabs else None

    def navigate_to(self, url: str) -> None:
        page = self.get_current_page()
        page.goto(url)
        # clear DOM/selector caches
        self._parser = None
        self._selector_map = None

    def refresh_page(self) -> None:
        page = self.get_current_page()
        if page:
            page.reload()
            self._parser = None
            self._selector_map = None

    def go_back(self) -> None:
        page = self.get_current_page()
        if page:
            page.go_back()
            self._parser = None
            self._selector_map = None

    def go_forward(self) -> None:
        page = self.get_current_page()
        if page:
            page.go_forward()
            self._parser = None
            self._selector_map = None

    def get_tabs_info(self) -> List[Dict[str, Any]]:
        infos = []
        for idx, page in enumerate(self._tabs):
            try:
                infos.append({
                    "page_id": idx,
                    "url": page.url,
                    "title": page.title(),
                    "is_current": page is self._current_page
                })
            except Exception:
                infos.append({
                    "page_id": idx,
                    "url": "about:blank",
                    "title": "Unknown",
                    "is_current": False
                })
        return infos

    def switch_to_tab(self, page_id: int) -> bool:
        if 0 <= page_id < len(self._tabs):
            self._current_page = self._tabs[page_id]
            self._parser = None
            self._selector_map = None
            return True
        return False

    def create_new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        page = self.create_new_page()
        if url:
            page.goto(url)
        self._parser = None
        self._selector_map = None
        return {
            "page_id": len(self._tabs) - 1,
            "url": page.url,
            "title": page.title() if url else "New Tab",
            "is_current": True
        }

    def close_tab(self, page_id: int) -> bool:
        if 0 <= page_id < len(self._tabs):
            page = self._tabs[page_id]
            if page is self._current_page:
                # pick a fallback current tab
                if len(self._tabs) > 1:
                    self._current_page = self._tabs[1] if page_id == 0 else self._tabs[0]
                else:
                    self._current_page = None
            self._tabs.remove(page)
            page.close()
            self._parser = None
            self._selector_map = None
            return True
        return False

    def get_element_tree(self, refresh: bool = True) -> Optional[DOMElementNode]:
        """
        Returns the root DOMElementNode. Builds or reuses the cached tree.
        """
        page = self.get_current_page()
        if page is None:
            return None

        if self._parser is None or refresh:
            self._parser = DOMTreeParser(page)
            try:
                self._parser.parse()
            except Exception as e:
                logger.error(f"Failed to parse DOM: {e}")
                self._parser = None
                return None

        return self._parser.dom_tree

    def get_selector_map(self, refresh: bool = True) -> Optional[Dict[int, DOMElementNode]]:
        """
        Returns a flat map of interactive elements.
        """
        # if already built and not refreshing, return cache
        if self._selector_map is not None and not refresh:
            return self._selector_map

        # ensure we have parsed DOM
        parser = self._parser if self._parser else None
        if parser is None:
            root = self.get_element_tree(refresh=refresh)
            if root is None or self._parser is None:
                logger.error("Cannot build selector map: no DOM available")
                return None
            parser = self._parser

        try:
            self._selector_map = parser.selector_map()
            logger.info(f"Selector map built with {len(self._selector_map)} items.")
            return self._selector_map
        except Exception as e:
            logger.error(f"Error building selector map: {e}")
            return None
        

    def get_selector_map_string(self, refresh: bool = True) -> str:
        """
        Returns a human-readable string of interactive elements.
        """
        if self._parser is None:
            self.get_element_tree(refresh=refresh)
        if not self._parser:
            return ""

        try:
            return self._parser.get_selector_map_string()
        except Exception as e:
            logger.error(f"Error serializing selector map: {e}")
            return ""
        
    def get_element_tree_string(self, refresh: bool = True) -> str:
        """
        Returns a human-readable string of the element tree.
        """
        if self._parser is None:
            self.get_element_tree(refresh=refresh)
        if not self._parser:
            return ""
        try:
            return self._parser.get_dom_string()
        except Exception as e:
            logger.error(f"Error getting element tree: {e}")
            return ""
            

    def close(self) -> None:
        self._tabs.clear()
        self._parser = None
        self._selector_map = None
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._browser = None
        self._context = None
        self._current_page = None
        self._playwright = None


# if __name__ == "__main__":

    # bs = BrowserSession()

    # try:
    #     print("\n=== 1) Open initial page (should launch browser + create first tab) ===")
    #     page = bs.get_current_page()
    #     print(" Session:", bs.get_session())
    #     print("\n=== 2) Navigate to example.com ===")
    #     bs.navigate_to("https://example.com")
    #     print("  → URL is now:", bs.get_current_page().url)
    #     print("\n=== 3) Refresh page ===")
    #     bs.refresh_page()
    #     print("  → Page reloaded.")
    #     print("\n=== 4) Navigate to example.org ===")
    #     bs.navigate_to("https://example.org")
    #     print("  → URL is now:", bs.get_current_page().url)

    #     print("\n=== 5) Go back ===")
    #     bs.go_back()
    #     print("  → URL after back():", bs.get_current_page().url)

    #     print("\n=== 6) Go forward ===")
    #     bs.go_forward()
    #     print("  → URL after forward():", bs.get_current_page().url)

    #     print("\n=== 7) Create a brand-new tab (python.org) ===")
    #     new_tab_info = bs.create_new_tab("https://python.org")
    #     print("  → New tab info:", new_tab_info)

    #     print("\n=== 8) List all tabs ===")
    #     tabs = bs.get_tabs_info()
    #     for t in tabs:
    #         print("   ", t)

        # print("\n=== 9) Switch back to tab 0 ===")
        # success = bs.switch_to_tab(0)
        # print("  → switch_to_tab(0) returned", success, "current URL:", bs.get_current_page().url)

        # print("\n=== 10) Build DOM tree ===")
        # root = bs.get_element_tree()
        # print("  → Root node:", getattr(root, "tag_name", None))

        # print("\n=== 11) Build selector map ===")
        # sel_map = bs.get_selector_map()
        # print("  → Selector map size:", len(sel_map) if sel_map else 0)

        # print("\n=== 12) Selector map string ===")
        # print(bs.get_selector_map_string())

        # print("\n=== 13) Element tree string ===")
        # print(bs.get_element_tree_string())

        # print("\n=== 13) Close tab 1 ===")
        # closed = bs.close_tab(1)
        # print("  → close_tab(1) returned", closed)
        # print("  → Tabs now:", bs.get_tabs_info())

    # except Exception as e:
    #     print("‼️  Something went wrong during testing:", e)

    # finally:
    #     print("\n=== 14) Close entire session ===")
    #     bs.close()
        # print("  → Final session:", bs.get_session())


