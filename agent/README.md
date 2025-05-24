# Agent Class - Complete Browser Automation Agent

The `Agent` class is a comprehensive browser automation agent that integrates with your existing LLM, memory, prompt builder, and browser controller components to perform automated browser testing and interaction tasks.

## Features

- **LLM Integration**: Uses GeminiFlashClient for intelligent decision making
- **Memory Management**: Tracks execution history and learns from past actions
- **Browser Control**: Integrates with BrowserController for web page interactions
- **Action Planning**: Plans and executes multi-step browser automation sequences
- **State Management**: Maintains browser state including URLs, tabs, and interactive elements
- **Error Handling**: Comprehensive error handling and recovery mechanisms
- **Session Logging**: Detailed logging and session persistence

## Architecture

The Agent class integrates several components:

1. **Memory**: Stores execution history and context
2. **LLM Client**: Provides intelligent action planning via Gemini Flash
3. **Prompt Builder**: Constructs system prompts for the LLM
4. **Browser Controller**: Executes browser actions via Playwright
5. **DOM Parser**: Extracts interactive elements from web pages

## Key Methods

### Initialization
```python
# Basic initialization
agent = Agent(llm_client, max_actions=10)

# With debug logging enabled
agent = Agent(llm_client, max_actions=10, debug=True)

agent.set_browser_controller(browser_controller)
```

**Debug Mode**: When `debug=True` is passed to the constructor, the agent will log all LLM requests and responses to a timestamped file (`agent_debug_YYYYMMDD_HHMMSS.log`). This is useful for debugging LLM interactions and understanding the decision-making process.

### Core Execution
- `execute_plan(user_goal)`: Execute a complete automation plan
- `get_next_action(user_goal)`: Get the next action from LLM
- `execute_action(action_item)`: Execute a single browser action
- `refresh_browser_state()`: Update current page state

### State Management
- `update_browser_state()`: Update URL, tabs, elements, actions
- `add_step()`: Record completed actions in history and memory
- `reset_session()`: Reset session while keeping memory

### Context Building
- `build_context_prompt()`: Build complete LLM context
- `_format_memory_context()`: Format recent memory entries
- `_format_previous_steps()`: Format execution history
- `_format_browser_state()`: Format current browser state

### Session Management
- `get_session_summary()`: Get execution statistics
- `save_session_log()`: Save session to JSON file

## Supported Actions

The agent supports the following browser actions:

- **navigate_to**: Navigate to a URL
- **click_element**: Click an element by index
- **input_text**: Input text into form fields
- **switch_tab**: Switch between browser tabs
- **open_tab**: Open new browser tab
- **close_tab**: Close a browser tab
- **go_back**: Navigate back in browser history
- **stop/complete/error**: Termination actions

## Action Format

Actions are formatted as JSON following this structure:

```json
{
  "current_state": {
    "evaluation_previous_goal": "Success|Failed|Unknown - evaluation text",
    "memory": "What has been done and what to remember",
    "next_goal": "What needs to be done next"
  },
  "action": [
    {"action_name": {"parameter": "value"}},
    {"another_action": {"param": "value"}}
  ]
}
```

## Example Usage

```python
from agent import Agent
from llm import GeminiFlashClient
from controller.browser_controller import BrowserController

# Initialize components
llm = GeminiFlashClient(api_key="your_key", model_name="models/gemini-1.5-flash")
agent = Agent(llm, max_actions=20)
browser_controller = BrowserController()
agent.set_browser_controller(browser_controller)

# Define automation goal
user_goal = """
Test the login functionality:
1. Navigate to the login form
2. Fill in email and password
3. Click login button
4. Verify successful login
"""

# Execute the plan
execution_log = agent.execute_plan(user_goal)

# Get results
summary = agent.get_session_summary()
print(f"Completed {summary['successful_steps']} out of {summary['total_steps']} steps")

# Save session
agent.save_session_log("login_test_session.json")

# Cleanup
browser_controller.close()
```

## Error Handling

The agent includes comprehensive error handling:

- **JSON Parsing**: Handles malformed LLM responses
- **Action Validation**: Validates action structure and parameters
- **Browser Errors**: Catches and reports browser interaction failures
- **Timeout Handling**: Manages action timeouts and retries
- **State Consistency**: Maintains consistent browser state

## Memory and Learning

The agent maintains memory across sessions:

- **Action History**: Records all executed actions and results
- **Success Patterns**: Learns from successful action sequences
- **Error Recovery**: Remembers common failure patterns
- **Context Retrieval**: Retrieves relevant past experiences

## Configuration

Key configuration options:

- `max_actions`: Maximum actions per execution plan (default: 10)
- `memory.capacity`: Maximum memory entries to retain (default: 20)
- `system_prompt`: Customize LLM behavior via SystemPromptBase

## Integration Notes

### With Browser Controller
The agent automatically refreshes browser state before each action and clears DOM caches after state-changing actions.

### With LLM
The agent constructs comprehensive prompts including system instructions, current state, memory context, and available actions.

### With Memory
All actions are recorded in structured format for future reference and learning.

## Session Persistence

Sessions can be saved and loaded:

```python
# Save current session
filename = agent.save_session_log()

# Session data includes:
# - Execution summary
# - Step-by-step history
# - Memory entries
# - Final browser state
```

## Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This provides detailed information about:
- LLM interactions
- Browser state changes
- Action execution results
- Error conditions

## Best Practices

1. **Clear Goals**: Provide specific, actionable goals to the agent
2. **Reasonable Limits**: Set appropriate `max_actions` limits
3. **State Management**: Let the agent refresh browser state automatically
4. **Error Recovery**: Review execution logs to understand failures
5. **Memory Management**: Periodically review memory capacity settings

## Troubleshooting

Common issues and solutions:

1. **LLM Response Errors**: Check API key and model availability
2. **Browser Interaction Failures**: Ensure elements are visible and interactive
3. **Memory Overflow**: Adjust memory capacity for long sessions
4. **Action Timeouts**: Check network connectivity and page load times

The completed Agent class provides a robust foundation for browser automation with intelligent decision-making capabilities.
