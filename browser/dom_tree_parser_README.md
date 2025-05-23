# DOMTreeParser README

A Python module that wraps a Playwright page to:

1. Build an in-memory tree of `DOMElementNode` and `DOMTextNode` objects.
2. Provide human- and machine-readable representations of the DOM.
3. Extract a flat selector map of interactive elements (e.g. buttons, links, inputs).

---

## Table of Contents

1. [Overview](#overview)
2. [Data Classes](#data-classes)
   - `DOMTextNode`
   - `DOMElementNode`
3. [Class: `DOMTreeParser`](#class-domtreeparser)
   - Constructor: `__init__`
   - `parse`
   - `_build_element`
   - `get_dom_string`
   - `_dump`
   - `selector_map`
   - `_flatten`
   - `selector_map_json`
   - `get_selector_map_string`
4. [Demo Function](#demo-function)
5. [Usage Example](#usage-example)

---

## Overview

`DOMTreeParser` leverages the `DomTreeBuilder` to retrieve a raw JSON tree of the page’s visible DOM. It then builds Python data objects for elements and text nodes, offers methods to serialize the tree to a readable string, and flattens interactive elements into a selector map.

---

## Data Classes

### `DOMTextNode`

- **Fields**:
  - `text: str` — Text content (trimmed).
  - `is_visible: bool` — Visibility flag inherited from parent.
  - `parent: Optional[DOMElementNode]` — Reference to parent element node.

### `DOMElementNode`

- **Fields**:
  - `tag_name: str` — Lowercase tag name (e.g. 'button').
  - `xpath: str` — Computed XPath within the tree.
  - `attributes: Dict[str, str]` — Element attributes.
  - `children: List[Union[DOMElementNode, DOMTextNode]]` — Child nodes.
  - `is_visible: bool` — Visibility flag.
  - `is_interactive: bool` — Interactivity flag.
  - `parent: Optional[DOMElementNode]` — Reference to parent.

---

## Class: `DOMTreeParser`

### Constructor: `__init__(self, page)`

- **Parameters**:
  - `page`: A Playwright `page` object.

- **Behavior**:
  - Validates `page` is not `None`, else raises `ValueError`.
  - Initializes internal placeholders:
    - `self.dom_tree` — will hold the parsed root.
    - `self._raw_json` — stores raw JSON from `DomTreeBuilder`.
    - `self._counts` — counters for XPath generation.

### `parse(self) -> DOMElementNode`

- **Behavior**:
  1. Calls `DomTreeBuilder(page, debug_mode=False).get_dom_tree()` to obtain `data["tree"]`.
  2. Stores the raw JSON in `self._raw_json`.
  3. Clears `self._counts` and builds the data-object tree by calling `_build_element(raw, "/", None)`.
  4. Returns the root `DOMElementNode`.

### `_build_element(self, node, parent_xpath, parent) -> DOMElementNode`

- **Parameters**:
  - `node`: A dict from the JSON tree.
  - `parent_xpath`: XPath prefix for this node.
  - `parent`: Parent `DOMElementNode` or `None` for root.

- **Behavior**:
  1. Increments `self._counts` for this tag under `parent_xpath`.
  2. Computes `xpath = f"{parent_xpath}{tag}[count]"`.
  3. Creates a `DOMElementNode` with visibility and interactivity.
  4. Iterates over children:
     - Wraps text nodes (`nodeName == '#text'`) into `DOMTextNode` if non-empty.
     - Recurses into nested element nodes.
  5. Returns the constructed `DOMElementNode`.

### `get_dom_string(self) -> str`

- **Behavior**:
  - Raises `ValueError` if `parse()` hasn’t been called.
  - Uses helper `_dump` to walk the tree and generate an indented string.

### `_dump(self, node, indent, lines)`

- **Parameters**:
  - `node`: `DOMElementNode` or `DOMTextNode`.
  - `indent`: Current indentation string.
  - `lines`: Accumulator list of lines.

- **Behavior**:
  - Appends a formatted line for the node.
  - Recurses on element children, adjusting `indent`.

### `selector_map(self) -> Dict[int, DOMElementNode]`

- **Behavior**:
  - Raises if `parse()` not called.
  - Initializes flat index, then calls `_flatten` on the root.
  - Returns a map of `{0: firstInteractiveNode, 1: next, ...}`.

### `_flatten(self, node)`

- **Behavior**:
  - If `node.is_interactive`, adds it to `self._flat_map`.
  - Recurses over element children.

### `selector_map_json(self) -> str`

- **Behavior**:
  - Builds the flat map, then serializes each `DOMElementNode` to JSON-friendly dict:
    - `tag_name`, `xpath`, `attributes`, `is_visible`, `is_interactive`, `children` (text nodes), and `parent` xpath.
  - Returns a pretty-printed JSON string.

### `get_selector_map_string(self) -> str`

- **Behavior**:
  - Builds the flat map, then iterates to output lines like:
    0: tag=button, xpath=/html[1]/body[1]/button[2], attrs={ type='submit' }
  - Omits visibility/interactivity flags in the summary.

---

## Demo Function

### `run_demo(html_file: Path) -> None`

- **Behavior**:
  1. Launches Playwright chromium browser.
  2. Opens the given HTML file URI.
  3. Instantiates `DOMTreeParser` and calls `parse()`.
  4. Prints:
     - The indented DOM tree (`get_dom_string()`).
     - The JSON selector map (`selector_map_json()`).
     - The human-readable selector summary (`get_selector_map_string()`).

---

## Usage Example

```python
from pathlib import Path
from playwright.sync_api import sync_playwright
from dom_tree_parser import DOMTreeParser

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://example.com')

    parser = DOMTreeParser(page)
    parser.parse()

    # Print the tree
    print(parser.get_dom_string())

    # Get interactive elements as JSON
    json_map = parser.selector_map_json()
    print(json_map)

    # Human-readable list
    print(parser.get_selector_map_string())

    browser.close()
```
