# 🤖 Testing Agent - AI-Powered Browser Automation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Supported-green.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent browser automation framework that combines AI-powered decision making with robust web automation capabilities. The Testing Agent uses Large Language Models (LLM) to intelligently navigate, interact with, and test web applications with human-like reasoning.

## 🚀 Features

### 🧠 **AI-Powered Decision Making**
- **LLM Integration**: Uses Google's Gemini Flash for intelligent action planning
- **Context-Aware**: Understands page structure and makes smart interaction decisions
- **Goal-Oriented**: Executes complex multi-step automation plans based on natural language goals
- **Adaptive Learning**: Learns from previous actions and improves over time

### 🌐 **Advanced Browser Automation**
- **Multi-Tab Management**: Create, switch, and manage multiple browser tabs
- **Smart Element Detection**: Automatically identifies interactive elements (buttons, inputs, links)
- **Intelligent Selectors**: Uses both CSS selectors and XPath with fallback strategies
- **Cross-Browser Support**: Built on Playwright for reliable automation

### 🔍 **DOM Intelligence**
- **Visual DOM Parsing**: Extracts only visible and interactive elements
- **Smart Indexing**: Automatically indexes clickable elements for easy interaction
- **Element Validation**: Validates element visibility and interactivity before actions
- **Real-time State Tracking**: Maintains up-to-date page state and element maps

### 📝 **Comprehensive Logging & Memory**
- **Session Persistence**: Saves complete automation sessions with detailed logs
- **Memory System**: Remembers successful patterns and learns from failures
- **Debug Mode**: Detailed logging for development and troubleshooting
- **Execution History**: Complete audit trail of all actions and results

## 🏗️ Architecture

```
Testing Agent
├── 🤖 Agent Core          # Main AI agent with LLM integration
├── 🧠 Memory System       # Learning and context management
├── 🌐 Browser Controller  # High-level browser automation
├── 📄 DOM Parser          # Intelligent page structure analysis
├── 🔧 Prompt Builder      # LLM prompt construction
└── 📊 Logging Utils       # Comprehensive logging system
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Testing-Agent.git
   cd Testing-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install playwright
   playwright install
   ```

3. **Install additional requirements**
   ```bash
   pip install google-generativeai
   pip install pathlib
   ```

4. **Set up your API key**
   ```python
   # Replace with your actual Gemini API key
   api_key = "your_gemini_api_key_here"
   ```

## 🎯 Quick Start

### Basic Usage

```python
from agent.agent import Agent
from agent.llm import GeminiFlashClient
from controller.browser_controller import BrowserController

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

# Define your automation goal
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

### Login Form Testing Example

```python
# Test a login form
login_goal = """
Test the login functionality:
1. Go to the login page
2. Fill in email field with 'test@example.com'
3. Fill in password field with 'password123'
4. Click the login button
5. Verify successful login
"""

execution_log = agent.execute_plan(login_goal)
```

## 🎮 Available Actions

The agent supports these browser actions:

| Action | Description | Parameters |
|--------|-------------|------------|
| `navigate_to` | Navigate to a URL | `url` |
| `click_element` | Click an element by index | `index` |
| `input_text` | Input text into form fields | `index`, `text` |
| `switch_tab` | Switch between tabs | `index` |
| `open_tab` | Open new tab | `url` (optional) |
| `close_tab` | Close a tab | `index` |
| `go_back` | Navigate back in history | None |

## 📁 Project Structure

```
Testing-Agent/
├── agent/                 # Core AI agent components
│   ├── agent.py          # Main agent class with LLM integration
│   ├── llm.py            # Gemini Flash client
│   ├── memory.py         # Memory and learning system
│   ├── prompt_builder.py # LLM prompt construction
│   ├── logging_utils.py  # Centralized logging utilities
│   └── testing.py        # Agent usage examples
├── browser/              # Browser automation engine
│   ├── browser_context.py    # Browser session management
│   ├── dom_tree_builder.py   # DOM tree construction
│   └── dom_tree_parser.py    # Element parsing and indexing
├── controller/           # High-level automation interface
│   ├── browser_controller.py # Main controller class
│   └── testing.py            # Controller usage examples
├── html/                 # Test HTML files
│   ├── login_form.html   # Login form test page
│   ├── test_page.html    # Basic test page
│   └── test_page2.html   # Complex test page
└── logs/                 # Session logs and debug files
```

## 🔧 Configuration

### Agent Configuration

```python
# Initialize with custom settings
agent = Agent(
    llm=llm_client,
    max_actions=30,        # Max actions per plan
    debug=True            # Enable detailed logging
)
```

### Memory Configuration

```python
# Configure memory capacity
agent.memory.capacity = 50  # Max memory entries
```

### Browser Configuration

The browser runs in headless mode by default. To see the browser:

```python
# In browser_context.py, modify the launch parameters
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
# Test the browser controller
python controller/testing.py

# Test the agent
python agent/testing.py
```

### Create your own tests:

```python
# Define test scenarios
test_scenarios = [
    "Navigate to a website and fill out a contact form",
    "Search for products and add items to cart",
    "Test user registration flow",
    "Verify responsive navigation menu"
]

for scenario in test_scenarios:
    execution_log = agent.execute_plan(scenario)
    # Analyze results...
```

## 🎯 Use Cases

### 🔍 **Web Application Testing**
- Automated regression testing
- User journey validation
- Form submission testing
- Cross-browser compatibility

### 🕷️ **Web Scraping & Data Collection**
- Intelligent content extraction
- Multi-page navigation
- Dynamic content handling
- Form-based data submission

### 🤖 **Process Automation**
- Repetitive web tasks
- Data entry automation
- Report generation
- System integration testing

### 📊 **Quality Assurance**
- End-to-end testing
- User experience validation
- Performance monitoring
- Accessibility testing

## 🔒 Best Practices

### 🎯 **Goal Definition**
- Be specific and actionable in your goals
- Break complex tasks into clear steps
- Include success criteria and validation points

### ⚡ **Performance**
- Use appropriate `max_actions` limits
- Enable debug mode only when needed
- Regular memory cleanup for long sessions

### 🛡️ **Reliability**
- Handle network timeouts gracefully
- Validate element presence before interaction
- Use fallback strategies for element selection

### 🔧 **Maintenance**
- Review execution logs regularly
- Update selectors as websites change
- Monitor API usage and limits

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright Team** - For the excellent browser automation framework
- **Google AI** - For providing the Gemini Flash LLM
- **Open Source Community** - For inspiration and best practices

## 📞 Support

- 📖 **Documentation**: Check the README files in each module
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Join our GitHub Discussions
- 📧 **Contact**: [Your contact information]

---

**Ready to automate? Start with the [Quick Start](#-quick-start) guide and build your first AI-powered browser automation!** 🚀
