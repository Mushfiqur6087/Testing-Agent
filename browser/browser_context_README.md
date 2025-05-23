# BrowserSession

`BrowserSession` is a simple session manager for Playwright-based browser automation in Python. It provides easy-to-use methods for creating and managing browser contexts, tabs, and DOM parsing.

## Features

- **Session Initialization**: Launch Chromium with optional headless mode.
- **Tab Management**: Create, switch, list, and close tabs programmatically.
- **Navigation Controls**: `navigate_to`, `refresh_page`, `go_back`, `go_forward`.
- **DOM Inspection**: Parse the DOM tree and extract interactive elements via `dom_tree_parser`.
- **Selector Map**: Build and serialize a map of clickable/interactable elements on the page.
- **Resource Cleanup**: Gracefully close browser, context, and Playwright processes.

## Installation

1. Ensure you have Python 3.7 or higher.
2. Install dependencies:
   ```bash
   pip install playwright
   playwright install
   ```
3. Place `browser_context.py` and `dom_tree_parser.py` in your project directory.

## Usage

```python
from browser_context import BrowserSession

# Initialize session
bs = BrowserSession()

# Open a new page and navigate
bs.navigate_to("https://example.com")

# Work with tabs
info = bs.create_new_tab("https://python.org")
print(info)

# DOM parsing
root = bs.get_element_tree()
print("Root tag:", root.tag_name)

# Selector map
sel_map = bs.get_selector_map()
print("Interactive elements:", len(sel_map))

# Cleanup
bs.close()
```

## API Reference

### `get_session()`
Returns a dictionary with current session details: playwright instance, browser, context, current page, and tab count.

### `get_current_page()`
Gets or creates the current active `Page` object.

### `create_new_page()`
Creates a new blank tab within the current context.

### `navigate_to(url: str)`
Navigates the current page to the specified URL.

### `refresh_page()`
Reloads the current page.

### `go_back()`, `go_forward()`
Navigate browser history.

### `get_tabs_info()`
Returns a list of dicts describing each tab (`page_id`, `url`, `title`, `is_current`).

### `switch_to_tab(page_id: int)`
Switches the active tab to the given `page_id`.

### `create_new_tab(url: Optional[str])`
Creates a new tab and optionally navigates to a URL.

### `close_tab(page_id: int)`
Closes the specified tab.

### `get_element_tree(refresh: bool = True)`
Parses and returns the root of the DOM tree.

### `get_selector_map(refresh: bool = True)`
Returns a mapping of interactive element indices to `DOMElementNode` instances.

### `get_selector_map_string(refresh: bool = True)`
Returns a human-readable string of interactive elements.

### `get_element_tree_string(refresh: bool = True)`
Returns a serialized string representation of the DOM tree.

### `close()`
Closes all browser resources and stops Playwright.
