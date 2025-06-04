import os
import sys

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from typing import Optional, List, Dict, Any
from playwright.sync_api import Page, BrowserContext, sync_playwright, Browser
from src.browser.dom_tree_parser import DOMTreeParser, DOMElementNode


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
                return None
            parser = self._parser

        try:
            self._selector_map = parser.selector_map()
            return self._selector_map
        except Exception as e:
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





