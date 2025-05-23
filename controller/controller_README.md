# Browser Automation Controller

A Python utility that wraps a Playwright-based `BrowserSession` to expose high-level browser commands through a `BrowserController`.

## Features

- Navigate to URLs
- Go back in history
- Open, switch, and close tabs
- Click DOM elements by index
- Input text into DOM elements by index
- Clear parser and selector map cache automatically

## Prerequisites

- Python 3.8+
- Playwright installed (`pip install playwright`)
- Access to `browser_context.py` module within a `browser` package

## Overview

This controller provides a simple `execute_command` interface for automating browser interactions. Behind the scenes, it uses Playwright to manage browser sessions, allowing you to:

1. **Navigate** to any URL.
2. **Manage tabs**: open, switch, and close.
3. **Interact with page elements** by index:
   - Click buttons, links, or any element found in the page’s DOM.
   - Fill text inputs.
4. **Automatically clear internal caches** after each action to ensure the page state remains in sync.

Use it to script end-to-end browser workflows, test web pages, or automate repetitive browsing tasks without worrying about low-level Playwright calls.

## Usage

Import and initialize the controller:

```python
from controller.browser_controller import BrowserController

ctrl = BrowserController()
```

Dispatch commands via `execute_command`:

| Command        | Arguments                           | Description                         |
|----------------|-------------------------------------|-------------------------------------|
| `navigate_to`  | `url: str`                          | Navigate to a URL                   |
| `go_back`      |                                     | Go back in browser history          |
| `open_tab`     | `url: Optional[str]`                | Open a new tab (optionally navigate)|
| `switch_tab`   | `tab_index: int`                    | Switch to a tab by index            |
| `close_tab`    | `tab_index: int`                    | Close a tab by index                |
| `click_element`| `element_index: int`                | Click DOM element by selector index |
| `input_text`   | `element_index: int, text: str`     | Fill text into DOM element          |

## Testing

See `testing.py` in the `controller` folder for a comprehensive test suite.

## License

This project is licensed under the MIT License.
