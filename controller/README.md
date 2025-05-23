# Browser Controller Module

The Browser Controller module provides a high-level interface for browser automation and control. It wraps the browser context functionality and provides a command-based interface for common browser operations.

## Components

### BrowserController

The main controller class that provides high-level browser operations through a command pattern interface.

```python
from controller.browser_controller import BrowserController

controller = BrowserController()
```

#### Available Commands

- `go_back`: Navigate back in browser history
- `click_element`: Click an element by its index in the selector map
- `input_text`: Input text into a form element
- `switch_tab`: Switch between browser tabs
- `open_tab`: Open a new browser tab
- `close_tab`: Close a specific browser tab
- `navigate_to`: Navigate to a URL

#### Example Usage

```python
# Initialize controller
controller = BrowserController()

# Navigate to a URL
controller.execute_command("navigate_to", "https://example.com")

# Click an element (using its index from selector map)
controller.execute_command("click_element", 1)

# Input text into a form
controller.execute_command("input_text", 2, "Hello World!")

# Switch tabs
controller.execute_command("switch_tab", 1)
```

## Testing

The module includes a comprehensive test suite in `testing.py` that demonstrates and verifies all functionality:

- Controller initialization
- Command dispatching
- Navigation commands
- Tab management
- DOM interaction

To run the tests:

```bash
python controller/testing.py
```

## Dependencies

- `browser.browser_context`: Provides the core browser session management
- `browser.dom_tree_parser`: Handles DOM parsing and element selection
- `playwright`: Used for browser automation (via browser_context)

## Error Handling

All commands include comprehensive error handling and logging:
- Invalid commands are caught and reported
- DOM interaction failures are logged
- Network and browser errors are handled gracefully

## Integration

The controller module integrates with the browser module to provide a complete browser automation solution:

1. Browser Context: Manages the underlying browser session
2. DOM Parser: Provides element selection and interaction capabilities
3. Command Interface: Simplifies browser control through a unified command pattern 