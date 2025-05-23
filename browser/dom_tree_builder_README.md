# Dom Tree Builder

A synchronous Python utility for constructing a DOM tree representation of a web page using Playwright (or a compatible `page`-based API). It includes optional performance metrics to profile tree-building, visibility checks, and interactive-element detection.

---

## Table of Contents

1. [Overview](#overview)
2. [Class: `DomTreeBuilder`](#class-domtreebuilder)
   - [Constructor: `__init__`](#constructor-init)
   - [Private Method: `_init_js_functions`](#private-method-_init_js_functions)
   - [Private Method: `measure_time`](#private-method-measure_time)
   - [Visibility Methods](#visibility-methods)
     - [`is_element_visible`](#is_element_visible)
     - [`is_interactive_element`](#is_interactive_element)
     - [`is_in_viewport`](#is_in_viewport)
   - [Core Tree Builder](#core-tree-builder)
     - [`build_dom_tree`](#build_dom_tree)
     - [`get_dom_tree`](#get_dom_tree)
3. [Usage Example](#usage-example)

---

## Overview

`DomTreeBuilder` provides a way to crawl a page’s DOM synchronously, filtering out invisible or off-screen nodes, and capturing attributes, text content, and interactivity flags. Enabling `debug_mode` collects detailed performance and node-count metrics.

---

## Class: `DomTreeBuilder`

### Constructor: `__init__(self, page, debug_mode=False)`

Initializes the builder.

- **Parameters**:
  - `page`: A Playwright (or similar) page object with `.evaluate()`, `.query_selector()`, and `.query_selector_all()` methods.
  - `debug_mode` (`bool`): If `True`, enables metrics gathering.

- **Behavior**:
  1. Stores `page` and `debug_mode`.
  2. Initializes `perf_metrics` dict if `debug_mode` is `True`.
  3. Calls `_init_js_functions()` to inject helper functions into the page context.

### Private Method: `_init_js_functions(self)`

Injects a `window.domTreeHelpers` object into the browser context defining three JavaScript helpers:

- **`isElementVisible(element)`**: Checks that the element has non-zero width/height, is displayed, visible, and has non-zero opacity.
- **`isInteractiveElement(element)`**: Detects interactivity via tag names (`a`, `button`, etc.), ARIA roles, attached event handlers, or cursor style.
- **`isInViewport(element)`**: Verifies the element’s bounding rectangle intersects the viewport.

These helpers are called via `element_handle.evaluate()`.

### Private Method: `measure_time(self, fn, metric_name=None)`

Wraps and times a synchronous function call.

- **Parameters**:
  - `fn` (`callable`): The function to execute.
  - `metric_name` (`str`, optional): Key under `perf_metrics['timings']` to accumulate time.

- **Returns**: The result of `fn()`.

- **Behavior**:
  - If `debug_mode` is `False`, immediately returns `fn()`.
  - Otherwise, measures execution time in milliseconds, updates metrics, and returns the result.

### Visibility Methods

#### `is_element_visible(self, element_handle)`

Checks if a given `element_handle` is visible.

- **Returns**: `False` if `None` or on error; otherwise boolean from the JS helper.

#### `is_interactive_element(self, element_handle)`

Determines if the element is interactive.

- **Returns**: `False` if `None` or on error; otherwise boolean from the JS helper.

#### `is_in_viewport(self, element_handle)`

Checks if the element is within the viewport.

- **Returns**: Boolean result or `False` on error.

### Core Tree Builder

#### `build_dom_tree(self, element_handle=None)`

Recursively constructs a nested dict representing the visible subtree rooted at `element_handle`.

- **Behavior**:
  1. Defaults to `<body>` if no handle provided.
  2. In debug mode, increments `build_dom_tree_calls` and `total_nodes`.
  3. Skips nodes failing visibility or viewport checks (tracks `skipped_nodes`).
  4. Processes visible nodes (tracks `processed_nodes`), capturing:
     - `nodeName`, `textContent`, `attributes`, `isInteractive`, `isVisible`.
  5. Recurses on direct children (`:scope > *`).
  6. Accumulates timing in `timings['build_dom_tree']` if debug.

- **Returns**: A dict with node data or `None` if skipped.

#### `get_dom_tree(self)`

Entry point to build the full DOM tree and reset/return metrics.

- **Behavior**:
  1. Resets timing and node counts if in debug mode.
  2. Calls `build_dom_tree()` at `<body>`.
  3. Returns a dict:
     - `tree`: The nested DOM tree dict.
     - `perfMetrics` (in debug mode): Timing and node-count metrics.

---

## Usage Example

```python
from playwright.sync_api import sync_playwright
from dom_tree_builder import DomTreeBuilder
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://example.com')

    # Instantiate with debug_mode=True to collect metrics
    builder = DomTreeBuilder(page, debug_mode=True)
    result = builder.get_dom_tree()

    # Pretty-print the DOM tree
    print(json.dumps(result['tree'], indent=2))

    # Print performance metrics
    print('Performance Metrics:', result.get('perfMetrics'))

    browser.close()
```

This example:

1. Launches a headless Chromium browser.
2. Navigates to `https://example.com`.
3. Builds the DOM tree while gathering metrics.
4. Prints both the tree structure and performance data.
