# 🤖 Testing Agent - AI-Powered Multi-Agent Browser Automation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Supported-green.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent multi-agent browser automation framework that combines AI-powered decision making with robust web automation capabilities. The Testing Agent uses Large Language Models (LLM) to intelligently navigate, interact with, and test web applications with human-like reasoning through a sophisticated multi-agent architecture.

## 🚀 Features

### 🧠 **Multi-Agent AI Architecture**
- **Main Agent**: Core decision-making agent with LLM integration for intelligent action planning
- **Tool Agent**: Specialized agent for complex operations like form validation and login verification
- **Instruction Agent**: Handles system instructions and prompt engineering for optimal LLM interactions
- **Context-Aware**: Understands page structure and makes smart interaction decisions across agents
- **Goal-Oriented**: Executes complex multi-step automation plans based on natural language goals
- **Inter-Agent Communication**: Seamless communication between agents for complex task execution

### 🌐 **Advanced Browser Automation**
- **Multi-Tab Management**: Create, switch, and manage multiple browser tabs
- **Smart Element Detection**: Automatically identifies interactive elements (buttons, inputs, links)
- **Intelligent Selectors**: Uses both CSS selectors and XPath with fallback strategies
- **Cross-Browser Support**: Built on Playwright for reliable automation
- **Real-time DOM Analysis**: Dynamic page analysis and element mapping

### 🔍 **Intelligent Validation & Testing**
- **LLM-Powered Validation**: Uses AI to validate login success, form submissions, and page states
- **Smart Error Detection**: Automatically detects and reports validation failures
- **Context-Aware Testing**: Understands the intent behind tests and validates accordingly
- **Visual DOM Parsing**: Extracts only visible and interactive elements
- **Real-time State Tracking**: Maintains up-to-date page state and element maps

### 📝 **Comprehensive Logging & Memory**
- **Multi-Agent Logging**: Separate logging for each agent with synchronized debug files
- **Session Persistence**: Saves complete automation sessions with detailed logs
- **Memory System**: Remembers successful patterns and learns from failures
- **Debug Mode**: Detailed logging for development and troubleshooting
- **Execution History**: Complete audit trail of all actions and results across agents

## 🏗️ Multi-Agent Architecture

```
Testing Agent Multi-Agent System
├── 🤖 Main Agent             # Core orchestrator with LLM integration
│   ├── Decision Making       # Intelligent action planning and execution
│   ├── Session Management    # Tracks state and execution history
│   └── Browser Integration   # Coordinates with browser controller
├── 🔧 Tool Agent             # Specialized validation and analysis
│   ├── LLM-Powered Analysis  # Intelligent page state validation
│   ├── Login Verification    # Automated login success detection
│   └── Form Validation       # Smart form submission verification
├── 📋 Instruction Agent      # System prompts and instructions
│   ├── Prompt Engineering    # Optimized LLM prompts
│   ├── Context Building      # Dynamic context generation
│   └── Response Formatting   # Structured LLM responses
├── 🌐 Browser Controller     # High-level browser automation
│   ├── Multi-Tab Management  # Tab creation, switching, and closing
│   ├── Element Interaction   # Click, input, and navigation actions
│   └── DOM Tree Parsing      # Real-time page structure analysis
└── 📊 Shared Components      # Common utilities and logging
    ├── LLM Client           # Gemini Flash integration
    ├── Logging System      # Multi-agent synchronized logging
    └── Debug Tools          # Development and troubleshooting
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/mushfiqur-rahman/Testing-Agent.git
   cd Testing-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   **Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

## 🎯 Quick Start

### Basic Usage

```python
from src.agent.main_agent.agent import Agent
from src.agent.core_utils.llm import GeminiFlashClient
from src.controller.browser_controller import BrowserController

# Initialize the AI client
llm = GeminiFlashClient(
    api_key="your_gemini_api_key",
    model_name="models/gemini-1.5-flash"
)

# Create the agent
agent = Agent(llm, max_actions=20, debug=True)

# Set up browser automation
browser_controller = BrowserController()
agent.set_browser_controller(browser_controller)

## 🚀 Getting Started

1. **Clone and setup the project**
   ```bash
   git clone https://github.com/yourusername/Testing-Agent.git
   cd Testing-Agent
   pip install -r requirements.txt
   playwright install
   ```

2. **Configure your environment**
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

3. **Run your first test**
   ```bash
   python src/test_agent.py
   ```

4. **View the results**
   Check the `logs/` directory for detailed execution logs and session data.
goal = """
Navigate to example.com and:
1. Find the search box
2. Search for 'testing automation'
3. Click on the first result
4. Verify the page loaded successfully
"""

# Execute the automation plan
execution_log = agent.execute_plan(goal)

# Get results and save session
summary = agent.get_session_summary()
print(f"Completed: {summary['successful_steps']}/{summary['total_steps']} steps")
agent.save_session_log()

# Cleanup
browser_controller.close()
```

## 🚀 Getting Started

1. **Clone and setup the project**
   ```bash
   git clone https://github.com/yourusername/Testing-Agent.git
   cd Testing-Agent
   pip install -r requirements.txt
   playwright install
   ```

2. **Configure your environment**
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

3. **Run your first test**
   ```bash
   python src/test_agent.py
   ```

4. **View the results**
   Check the `logs/` directory for detailed execution logs and session data.

### Login Form Testing Example

```python
# Test a login form with multi-agent validation
login_goal = """
Test the login functionality:
1. Go to the login page
2. Fill in email field with 'test@example.com'
3. Fill in password field with 'password123'
4. Click the login button
5. Use tools to verify successful login
"""

execution_log = agent.execute_plan(login_goal)

# The Tool Agent will automatically:
# - Analyze the page state after login
# - Detect success/failure messages
# - Validate the user's email presence
# - Provide detailed validation results
```

## 🎮 Available Actions

The multi-agent system supports these browser actions:

| Action | Description | Agent | Parameters |
|--------|-------------|--------|------------|
| `navigate_to` | Navigate to a URL | Main Agent | `url` |
| `click_element` | Click an element by index | Main Agent | `index` |
| `input_text` | Input text into form fields | Main Agent | `index`, `text` |
| `switch_tab` | Switch between tabs | Main Agent | `index` |
| `open_tab` | Open new tab | Main Agent | `url` (optional) |
| `close_tab` | Close a tab | Main Agent | `index` |
| `go_back` | Navigate back in history | Main Agent | None |
| `tools` | Execute intelligent validation | Tool Agent | `reason` |
| `end` | Terminate the session | Main Agent | `reason` |

### 🔧 Tool Agent Capabilities

The Tool Agent provides specialized actions for complex validation:
- **Login Verification**: Automatically detects successful/failed logins
- **Form Validation**: Validates form submissions and error states
- **Page State Analysis**: Analyzes current page state and content
- **Error Detection**: Identifies and reports page errors or issues
- **Content Verification**: Validates expected content presence

## 📁 Project Structure

```
Testing-Agent/
├── src/                      # Source code
│   ├── agent/               # AI agent components
│   │   ├── core_utils/      # Core utilities
│   │   │   ├── llm.py       # Gemini Flash LLM client
│   │   │   └── logging_utils.py  # Logging utilities
│   │   ├── main_agent/      # Main agent logic
│   │   │   ├── agent.py     # Core agent class
│   │   │   └── prompt_generator.py  # Prompt generation
│   │   ├── tool_agent/      # Tool management
│   │   │   └── tools.py     # Tool implementations
│   │   └── instruction_agent/  # Instruction handling
│   │       └── initial.py   # Initial instructions
│   ├── browser/             # Browser automation
│   │   ├── browser_context.py     # Browser session management
│   │   ├── dom_tree_builder.py    # DOM tree construction
│   │   └── dom_tree_parser.py     # Element parsing
│   └── controller/          # High-level automation
│       └── browser_controller.py  # Main controller
├── tests/                   # Test suite
│   ├── browser_controller_test.py
│   ├── dom_tree_builder_test.py
│   ├── dom_tree_parser_test.py
│   └── main.py             # Test runner
├── html/                   # Test HTML files
│   ├── login_form.html     # Login form test page
│   ├── test_page.html      # Basic test page
│   └── test_page2.html     # Complex test page
├── logs/                   # Session logs and debug files
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
└── README.md              # This file
```

## 🔧 Configuration

### Multi-Agent Configuration

```python
# Initialize with custom settings
agent = Agent(
    llm=llm_client,
    max_actions=30,        # Max actions per plan
    debug=True            # Enable detailed logging for all agents
)

# The main agent automatically coordinates with:
# - Tool Agent for validation tasks
# - Instruction Agent for prompt optimization
# - Browser Controller for automation
```

### Tool Agent Configuration

```python
# Tool Agent is automatically initialized with LLM client
# and provides intelligent validation capabilities
# No manual configuration required
```

### Debug Mode for Multi-Agent System

```python
# Enable comprehensive logging across all agents
agent = Agent(llm, debug=True)

# This creates synchronized log files:
# - agent_debug_YYYYMMDD_HHMMSS.log (Main Agent decisions)
# - tools_debug_YYYYMMDD_HHMMSS.log (Tool Agent validations)
# - agent_session_YYYYMMDD_HHMMSS.json (Complete session data)
```

### Browser Configuration

The browser runs in headless mode by default. To see the browser:

```python
# In src/browser/browser_context.py, modify the launch parameters
browser = playwright.chromium.launch(headless=False)
```

## 📊 Logging and Debugging

### Debug Mode

Enable comprehensive logging:

```python
agent = Agent(llm, debug=True)
```

This creates timestamped log files in the `logs/` directory:
- `agent_debug_YYYYMMDD_HHMMSS.log` - Agent decision making
- `memory_debug_YYYYMMDD_HHMMSS.log` - Memory operations
- `agent_session_YYYYMMDD_HHMMSS.json` - Complete session data

### Session Analysis

```python
# Get detailed session summary
summary = agent.get_session_summary()
print(f"Duration: {summary['session_duration_seconds']:.2f} seconds")
print(f"Success Rate: {summary['successful_steps']}/{summary['total_steps']}")

# Save session for later analysis
filename = agent.save_session_log()
print(f"Session saved to: {filename}")
```

## 🧪 Testing

### Run the included tests:

```bash
# Run the test suite
python tests/main.py

# Or run individual test files
python tests/browser_controller_test.py
python tests/dom_tree_builder_test.py
python tests/dom_tree_parser_test.py

```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to automate? Start with the [Quick Start](#-quick-start) guide and build your first AI-powered browser automation!** 🚀
