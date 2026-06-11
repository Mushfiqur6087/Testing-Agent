# Testing Agent

An autonomous, AI-powered browser test execution engine for web applications. Built as the execution counterpart to the **AutoTestGenX** test generation framework, the Testing Agent physically runs enriched test cases against a live application and produces structured, evidence-backed pass/fail verdicts.

---

## Overview

The Testing Agent implements a **multi-agent pipeline** inspired by the AutoTestGenX Phase 3 (Live-Validation and Refinement) architecture. Rather than a single monolithic agent, it coordinates five specialized agents to plan, execute, validate, and self-heal across an entire test suite.

```
TraversalPlanner → InteractionAgent → ExecutionOutcomeValidator → AdaptivePlanner
```

### Key capabilities

| Feature | Description |
|---|---|
| 🧭 **Traversal Planning** | Automatically orders test cases: public → authenticated → destructive (logout/reset last) |
| 🌐 **Structured Execution** | Agent reads `direct_link`, `requires_auth`, `test_data`, and `steps` from enriched test cases |
| 📸 **Before/After State Capture** | DOM snapshot + screenshot captured at TC start; compared after execution against `expected_result` |
| ✅ **Execution Outcome Validation** | LLM+vision verifies whether the application state actually changed as expected |
| 🔄 **Adaptive Replanning** | Between test cases, checks if the next TC's prerequisites are still met; navigates to recover if not |
| 📊 **Rich Run Summary** | `test_run_summary.json` with PASSED / FAILED / ERROR / SKIPPED per TC and `phase3_note` for adjusted steps |
| 🔌 **LiteLLM — Any Provider** | Works with OpenAI, Anthropic, Google Gemini, OpenRouter, Azure, and 100+ more via a single flag |

---

## Architecture

```
src/
├── test_agent_main.py              # CLI entry point & orchestrator
├── test_agent.py                   # TestAgent — pipeline coordinator
└── agent/
    ├── planning_agent/
    │   ├── traversal_planner.py    # Phase A/B/C ordering (no LLM call)
    │   └── adaptive_planner.py     # Inter-test prerequisite check (LLM)
    ├── main_agent/
    │   ├── agent.py                # InteractionAgent — browser execution loop
    │   └── prompt_generator.py     # System prompt with structured task block
    ├── tool_agent/
    │   └── tools.py                # ExecutionOutcomeValidator (before/after diff)
    └── core_utils/
        ├── llm.py                  # Unified LiteLLM client (any provider)
        ├── memory.py               # Per-TC state: steps, snapshots, validations
        ├── test_result_analyzer.py # Post-execution PASSED/FAILED verdict
        └── logging_utils.py        # Structured debug log routing
```

### Multi-Agent Pipeline

```
dataset/enriched_test_cases_*.json
        │
        ▼
 load_test_cases()
   • Auto-detect enriched {"test_cases":[...]} vs legacy [...] format
   • Filter dropped=true → SKIPPED entries in run summary
        │
        ▼
 TraversalPlanner.plan()                    [heuristic, no LLM call]
   • Phase A: requires_auth=False, non-destructive
   • Phase B: requires_auth=True,  non-destructive
   • Phase C: Logout / Reset App State (always last)
   • Within each phase: High → Medium → Low priority
        │
        ▼  (for each TC in planned order)
 AdaptivePlanner.evaluate_next()            [1 LLM call between TCs]
   • Are the next TC's prerequisites still met?
   • If session drifted (e.g. prior logout): navigate to recovery URL
        │
        ▼
 InteractionAgent (Agent.execute_plan)      [browser execution loop]
   • Reads structured goal block:
       direct_link   → first navigation (with auth if requires_auth=Yes)
       test_data     → exact credentials / form inputs
       steps         → numbered steps executed via indexed DOM actions
   • Indexed DOM map (not raw HTML) → LLM uses numeric element references
   • Multimodal vision screenshots for spatial awareness
   • Before-state captured automatically at TC start
        │
   [tools call — ExecutionOutcomeValidator]
   • Before-state (TC start) vs After-state (now)
   • LLM+vision: does current state match expected_result?
   • Returns: {validation_passed, state_changed, findings}
        │
        ▼
 TestResultAnalyzer.analyze_test_execution()
   • Enriched prompt: outcome validations + state diff + Phase 3 metadata
   • Final PASSED / FAILED verdict
        │
        ▼
 test_run_summary.json
```

---

## Dataset Format

The Testing Agent is designed to consume the **enriched test case format** produced by AutoTestGenX Phase 3.

### Enriched format (recommended)

```json
{
  "test_cases": [
    {
      "tc_id": "TC-001",
      "module": "Login",
      "title": "Successful login with valid credentials",
      "type": "Positive",
      "priority": "High",
      "direct_link": "https://www.saucedemo.com/login",
      "requires_auth": false,
      "preconditions": "User is on the Login page; user is not authenticated",
      "steps": [
        "1. Enter 'standard_user' in the Username field",
        "2. Enter 'secret_sauce' in the Password field",
        "3. Click the Login button"
      ],
      "expected_result": "User is redirected to the Product Inventory page; no error banner is displayed",
      "test_data": {
        "username": "standard_user",
        "password": "secret_sauce"
      },
      "verdict": "valid",
      "dropped": false,
      "drop_reason": "",
      "notes": "All referenced UI elements confirmed present in live DOM."
    }
  ]
}
```

| Field | Used by | Purpose |
|---|---|---|
| `direct_link` | InteractionAgent | First URL to navigate to |
| `requires_auth` | InteractionAgent | Whether to log in first using `test_data` credentials |
| `test_data` | InteractionAgent | Exact values for form inputs — never hallucinated |
| `preconditions` | AdaptivePlanner | Pre-flight state check before step execution |
| `steps` | InteractionAgent | Numbered steps to execute in order |
| `expected_result` | ExecutionOutcomeValidator | Ground truth for before/after validation |
| `verdict` | TestResultAnalyzer | Phase 3 pre-audit context (flagged if `invalid_steps`) |
| `dropped` | Loader | If `true`, TC is recorded as SKIPPED and not executed |

### Legacy format (backward compatible)

```json
[
  {
    "test_name": "my_test",
    "steps_or_input": "Go to https://example.com and fill the form...",
    "expected_outcome": "Form submits successfully"
  }
]
```

---

## Setup

### 1. Prerequisites

- Python 3.9+
- A supported LLM API key (OpenAI, Anthropic, Gemini, OpenRouter, etc.)

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure API keys

Copy the example env file and add your key:

```bash
cp env/.env.example env/.env
```

Edit `env/.env`:

```env
# Add the key for whichever provider you use — only one required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
```

---

## Usage

### Running against an enriched dataset

```bash
# OpenAI GPT-4o (default)
python -m src.test_agent_main \
  --dataset dataset/enriched_test_cases_swaglab.json \
  --model openai/gpt-5-mini

# Anthropic Claude
python -m src.test_agent_main \
  --dataset dataset/enriched_test_cases_swaglab.json \
  --model anthropic/claude-sonnet-4-5

# Google Gemini
python -m src.test_agent_main \
  --dataset dataset/enriched_test_cases_swaglab.json \
  --model gemini/gemini-2.0-flash

# OpenRouter (any open-source model)
python -m src.test_agent_main \
  --dataset dataset/enriched_test_cases_swaglab.json \
  --model openrouter/meta-llama/llama-3.1-8b-instruct

# Show the browser window while running
python -m src.test_agent_main \
  --dataset dataset/enriched_test_cases_swaglab.json \
  --model openai/gpt-5-mini \
  --no-headless
```

### All CLI flags

| Flag | Default | Description |
|---|---|---|
| `--model` | `openai/gpt-5-mini` | LiteLLM model string (`provider/model-name`) |
| `--provider` | _(none)_ | Optional provider prefix if model string has no `/` |
| `--dataset` | `dataset/enriched_test_cases_swaglab.json` | Path to enriched JSON dataset |
| `--test-file` | _(none)_ | Path to legacy flat JSON (overrides `--dataset`) |
| `--max-actions` | `15` | Max browser actions per test case |
| `--no-headless` | _(headless)_ | Show the browser window |
| `--test-timeout` | `300` | Seconds per test case before it is killed |
| `--debug` | `True` | Enable detailed per-step debug logs |

### Supported model strings (LiteLLM)

```bash
# OpenAI
openai/gpt-5-mini
openai/gpt-5-mini

# Anthropic
anthropic/claude-sonnet-4-5
anthropic/claude-haiku-3-5

# Google
gemini/gemini-2.0-flash
gemini/gemini-1.5-pro

# OpenRouter (access to 200+ models via one key)
openrouter/meta-llama/llama-3.1-8b-instruct
openrouter/mistralai/mixtral-8x7b-instruct

# Azure OpenAI
azure/<your-deployment-name>
```

Full list: [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers)

---

## Output

After a run, logs are written to `logs/<run-id>/`:

```
logs/
└── run_20260611_082213/
    ├── test_run_summary.json          # Top-level pass/fail summary
    ├── Login_TC-001/
    │   ├── agent_debug.log            # Full LLM request/response trace
    │   ├── analysis_result.json       # TestResultAnalyzer verdict + evidence
    │   └── memory_export.json         # State snapshots + outcome validations
    └── Shopping_Cart_TC-001/
        └── ...
```

### `test_run_summary.json` example

```json
{
  "run_id": "run_20260611_082213",
  "model": "openai/gpt-5-mini",
  "total": 12,
  "passed": 9,
  "failed": 2,
  "error": 0,
  "skipped": 1,
  "test_cases": [
    {
      "test_name": "Login_TC-001",
      "result": "PASSED",
      "llm_verdict": "PASSED",
      "summary": "Agent navigated to login page, entered credentials, and was redirected to the inventory page as expected."
    },
    {
      "test_name": "Shopping_Cart_TC-006",
      "result": "SKIPPED",
      "skip_reason": "Requires a product with 200+ character description not in seed data."
    },
    {
      "test_name": "Product_Detail_TC-007",
      "result": "PASSED",
      "phase3_note": "⚠ Steps were adjusted during Phase 3 verification (verdict: invalid_steps). Execution used the adjusted steps."
    }
  ]
}
```

---

## How the Validation Works

The `ExecutionOutcomeValidator` (`tools` action) validates execution outcomes — **not** step correctness. Steps are already verified by AutoTestGenX Phase 3. The validator answers:

> *"After the agent executed the steps, did the application state change as `expected_result` describes?"*

**Before-state** is captured automatically at the start of every test case (URL, DOM snapshot, screenshot).

When the agent calls `tools` (after completing a critical step or the full test sequence), the validator:
1. Captures the **after-state** (current URL, DOM, screenshot)
2. Builds a before→after comparison prompt with the `expected_result` as ground truth
3. Uses LLM + vision to determine `validation_passed` and `state_changed`
4. Stores the result in memory for the `TestResultAnalyzer`

---

## Development

### Project structure

```
Testing-Agent/
├── dataset/                        # Enriched test case datasets
│   ├── enriched_test_cases_swaglab.json
│   └── enriched_test_cases_parabank.json
├── src/
│   ├── test_agent_main.py
│   ├── test_agent.py
│   ├── agent/
│   │   ├── planning_agent/         # TraversalPlanner, AdaptivePlanner
│   │   ├── main_agent/             # InteractionAgent, prompt
│   │   ├── tool_agent/             # ExecutionOutcomeValidator
│   │   └── core_utils/             # LLMClient, Memory, Analyzer, Logging
│   ├── browser/                    # BrowserSession, DOM parser
│   └── controller/                 # BrowserController
├── test_cases/                     # Legacy test case files
├── env/
│   └── .env                        # API keys (not committed)
├── logs/                           # Run output (auto-created)
├── requirements.txt
└── README.md
```

### Adding a new dataset

1. Place your enriched JSON in `dataset/`
2. Run with `--dataset dataset/your_file.json`

The `TraversalPlanner` automatically handles ordering based on `requires_auth`, `module`, and `priority` fields.

---

## Research Context

This agent is the execution component of the **AutoTestGenX** framework, developed as part of a thesis on autonomous AI-driven software testing. The framework implements a two-phase pipeline:

- **Phase 1–2 (Generation):** LLM-based test case generation from functional requirements
- **Phase 3 (Validation):** AutoTestGenX audits theoretical test cases against the live application → produces enriched dataset
- **Phase 4 (Execution — this agent):** Runs the enriched test suite and validates execution outcomes

The enriched dataset fields (`direct_link`, `test_data`, `verdict`, `notes`) are the direct output of Phase 3 and serve as structured, hallucination-free inputs for the Testing Agent.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
