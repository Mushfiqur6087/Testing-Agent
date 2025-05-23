#!/usr/bin/env python3
"""
DOMTreeParser module

Parses a Playwright page into a tree of DOMElementNode/DOMTextNode,
and extracts a flat selector-map of interactive elements.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright
from dom_tree_builder import DomTreeBuilder  # assume this is on your PYTHONPATH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class DOMTextNode:
    text: str
    is_visible: bool
    parent: Optional["DOMElementNode"] = None


@dataclass
class DOMElementNode:
    tag_name: str
    xpath: str
    attributes: Dict[str, str]
    children: List[Any]
    is_visible: bool
    is_interactive: bool
    parent: Optional["DOMElementNode"] = None


class DOMTreeParser:
    """Wrap a Playwright page to build a DOM tree and extractor selector map."""

    def __init__(self, page) -> None:
        if page is None:
            logger.error("A Playwright 'page' object is required.")
            raise ValueError("No page object provided for parsing.")
        self.page = page
        self.dom_tree: Optional[DOMElementNode] = None
        self._raw_json: Optional[Dict[str, Any]] = None
        self._counts: Dict[str, int] = {}

    def parse(self) -> DOMElementNode:
        """
        Crawl the page via DomTreeBuilder, store raw JSON, and
        build the in-memory tree of DOMElementNode/DOMTextNode.
        """
        data = DomTreeBuilder(self.page, debug_mode=False).get_dom_tree()
        self._raw_json = data["tree"]
        self._counts.clear()
        self.dom_tree = self._build_element(self._raw_json, parent_xpath="/", parent=None)
        return self.dom_tree

    def _build_element(
        self,
        node: Dict[str, Any],
        parent_xpath: str,
        parent: Optional[DOMElementNode],
    ) -> DOMElementNode:
        """Recursively construct DOMElementNode (and its text-node children)."""
        tag = node["nodeName"]
        key = f"{parent_xpath}{tag}"
        self._counts[key] = self._counts.get(key, 0) + 1
        xpath = f"{parent_xpath}{tag}[{self._counts[key]}]"

        is_visible = node.get("isVisible", True)
        is_interactive = node.get("isInteractive", False)

        elm = DOMElementNode(
            tag_name=tag,
            xpath=xpath,
            attributes=node.get("attributes", {}),
            children=[],
            is_visible=is_visible,
            is_interactive=is_interactive,
            parent=parent,
        )

        for child in node.get("children", []):
            if isinstance(child, dict) and child.get("nodeName") == "#text":
                text = child.get("textContent", "").strip()
                if text:
                    elm.children.append(DOMTextNode(text=text, is_visible=is_visible, parent=elm))
            elif isinstance(child, dict):
                elm.children.append(self._build_element(child, xpath + "/", elm))

        return elm

    def get_dom_string(self) -> str:
        """
        Return an indented string representation of the DOM tree.
        """
        if not self.dom_tree:
            raise ValueError("DOM tree not built, call parse() first.")
        lines: List[str] = []
        self._dump(self.dom_tree, indent="", lines=lines)
        return "\n".join(lines)

    def _dump(self, node: Any, indent: str, lines: List[str]) -> None:
        """Helper to serialize tree into a list of lines."""
        if isinstance(node, DOMTextNode):
            lines.append(f"{indent}└── DOMTextNode(text={node.text!r}, is_visible={node.is_visible})")
        else:
            lines.append(
                f"{indent}DOMElementNode(tag={node.tag_name!r}, xpath={node.xpath!r}, "
                f"is_visible={node.is_visible}, is_interactive={node.is_interactive})"
            )
            for i, child in enumerate(node.children):
                last = i == len(node.children) - 1
                self._dump(child, indent + ("    " if last else "│   "), lines)

    def selector_map(self) -> Dict[int, DOMElementNode]:
        """
        Flatten and return only the interactive elements in encounter order:
        {0: <button node>, 1: <input node>, …}
        """
        if not self.dom_tree:
            raise ValueError("DOM tree not built, call parse() first.")
        self._flat_index = 0
        self._flat_map: Dict[int, DOMElementNode] = {}
        self._flatten(self.dom_tree)
        return self._flat_map

    def _flatten(self, node: DOMElementNode) -> None:
        """Recursively collect interactive nodes into _flat_map."""
        if node.is_interactive:
            self._flat_map[self._flat_index] = node
            self._flat_index += 1
        for child in node.children:
            if isinstance(child, DOMElementNode):
                self._flatten(child)

    def selector_map_json(self) -> str:
        """
        Return a JSON‐dumpable map of interactive elements, including:
          tag_name, xpath, attributes, is_visible, is_interactive,
          text‐node children, and parent xpath.
        """
        sel_map = self.selector_map()
        out: Dict[int, Dict[str, Any]] = {}
        for idx, node in sel_map.items():
            out[idx] = {
                "tag_name": node.tag_name,
                "xpath": node.xpath,
                "attributes": node.attributes,
                "is_visible": node.is_visible,
                "is_interactive": node.is_interactive,
                "children": [
                    {
                        "text": child.text,
                        "is_visible": child.is_visible,
                        "parent": child.parent.xpath if child.parent else None
                    }
                    for child in node.children
                    if isinstance(child, DOMTextNode)
                ],
                "parent": node.parent.xpath if node.parent else None
            }
        return json.dumps(out, indent=2)
    def get_selector_map_string(self) -> str:
        """
        Return a simple, human-readable list of all interactive elements:
        index, tag name, xpath, and attributes only.
        Omits parent/child, is_visible, is_interactive flags.
        """
        sel_map = self.selector_map()
        lines: List[str] = []
        for idx, node in sel_map.items():
            # format attributes as key='value', …
            if node.attributes:
                attrs_str = ", ".join(f"{k}='{v}'" for k, v in node.attributes.items())
                attr_part = f", attrs={{ {attrs_str} }}"
            else:
                attr_part = ""
            lines.append(f"{idx}: tag={node.tag_name}, xpath={node.xpath}{attr_part}")
        return "\n".join(lines)



# def run_demo(html_file: Path) -> None:
#     """Demo entry: load HTML, parse DOM, and print both tree and selector map."""
#     with sync_playwright() as pw:
#         browser = pw.chromium.launch()
#         page = browser.new_page()
#         page.goto(html_file.as_uri())

#         parser = DOMTreeParser(page)
#         parser.parse()

#         print("\n=== DOM Tree ===")
#         print(parser.get_dom_string())

#         print("\n=== Selector Map ===")
#         print(parser.selector_map_json())

#         print("\n=== Selector Map String ===")
#         print(parser.get_selector_map_string())

#         browser.close()


# if __name__ == "__main__":
#     project_root = Path(__file__).parent.parent
#     demo_html = project_root / "html" / "login_form.html"
#     run_demo(demo_html)
