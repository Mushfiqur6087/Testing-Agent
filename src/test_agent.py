import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.agent.main_agent.agent import Agent
from src.agent.core_utils.llm import LLMClient
from src.agent.core_utils.test_result_analyzer import TestResultAnalyzer
from src.agent.core_utils.logging_utils import debug_logger
from src.controller.browser_controller import BrowserController


class TestAgent:
    """
    Persistent test agent that shares one browser session and one LLM client
    across all test cases in a run.

    Multi-agent pipeline lifecycle:
      1. initialize()                                 — launch browser once
      2. execute_plan(goal, outcome, name, metadata)  — run test case N
         prepare_for_next_task(name, ctx)             — (called between cases)
      3. execute_plan(...)                            — run test case N+1 …
      4. cleanup()                                    — close browser once at end

    The pipeline within execute_plan():
      ① InteractionAgent executes steps from the structured goal block
         – direct_link + requires_auth + test_data guide navigation
         – Indexed DOM actions drive step execution
      ② ExecutionOutcomeValidator (tools) captures before/after state and
         validates whether the expected_result was achieved
      ③ TestResultAnalyzer produces the final PASSED/FAILED verdict using
         outcome validations + state snapshots + enriched metadata
    """

    def __init__(self, model: str = "openai/gpt-5-mini", provider: str = None,
                 max_actions: int = 10, debug: bool = False, headless: bool = True,
                 test_case_name: str = "test_case",
                 analyzer_model: str = None, analyzer_provider: str = None):
        self.model = model
        self.provider = provider
        self.max_actions = max_actions
        self.debug = debug
        self.headless = headless
        self.test_case_name = test_case_name
        # Analyzer uses same model as main agent (vision-capable, no cheaper fallback)
        self.analyzer_model = analyzer_model or model
        self.analyzer_provider = analyzer_provider or provider

        # Core components — created once, shared across all test cases
        self.llm: LLMClient = None
        self.agent: Agent = None
        self.browser_controller: BrowserController = None
        self.test_analyzer: TestResultAnalyzer = None

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def initialize(self):
        """Launch browser and create all shared components (called once per run)."""
        try:
            self.llm = LLMClient(model=self.model, provider=self.provider)

            # Analyzer uses the same model — vision-capable, consistent with agent
            if self.analyzer_model != self.model or self.analyzer_provider != self.provider:
                analyzer_llm = LLMClient(model=self.analyzer_model, provider=self.analyzer_provider)
            else:
                analyzer_llm = self.llm

            self.test_analyzer = TestResultAnalyzer(
                llm_client=self.llm, analyzer_llm_client=analyzer_llm
            )
            self.browser_controller = BrowserController(
                llm_client=self.llm, headless=self.headless
            )

            # Point the first debug log to the first test case's folder
            tc_dir = debug_logger.get_test_case_dir(self.test_case_name)
            initial_debug_file = (
                debug_logger.get_debug_file_path(
                    "agent", debug_file_prefix=self.test_case_name, output_dir=tc_dir
                )
                if self.debug else None
            )

            self.agent = Agent(
                llm=self.llm,
                max_actions=self.max_actions,
                debug=self.debug,
            )
            if self.debug:
                self.agent.debug_file = initial_debug_file
                from src.agent.core_utils.memory import EnhancedMemory
                self.agent.memory = EnhancedMemory(debug_file_path=initial_debug_file)

            self.agent.set_browser_controller(self.browser_controller)

        except Exception as e:
            print(f"❌ Failed to initialize TestAgent: {e}")
            raise

    def cleanup(self):
        """Close the browser (called once after all test cases are done)."""
        try:
            if self.browser_controller:
                self.browser_controller.close_browser()
        except Exception:
            pass

    def prepare_for_next_task(self, test_case_name: str, prior_context: str = "") -> None:
        """
        Soft-reset the agent between test cases.
        - Browser stays open on the current page
        - Debug log is redirected to the new test case's subfolder
        - Per-task step history, memory, task_metadata, and before_state are cleared
        - Prior test results are injected into the LLM prompt as context
        """
        self.test_case_name = test_case_name
        self.agent.prepare_for_next_task(test_case_name, prior_context)

    def execute_plan(
        self,
        user_goal: str,
        expected_outcome: str,
        test_case_name: str = None,
        task_metadata: dict = None,
    ) -> dict:
        """
        Execute the multi-agent pipeline for one test case.

        Args:
            user_goal:        Structured goal block (built from enriched TC fields)
            expected_outcome: The expected_result from the enriched test case
            test_case_name:   Name used for log file routing
            task_metadata:    Full enriched test case dict (all fields)

        Returns:
            Analysis dict from TestResultAnalyzer
        """
        if not self.agent:
            self.initialize()

        name = test_case_name or self.test_case_name

        try:
            # ① InteractionAgent executes steps
            #    task_metadata is stored on the agent so execute_action('tools') can
            #    read expected_result and before_state automatically
            self.agent.execute_plan(user_goal, task_metadata=task_metadata)

            # ② TestResultAnalyzer produces PASSED/FAILED verdict
            analysis: dict = {}
            if hasattr(self.agent, 'memory') and self.agent.memory:
                analysis = self.test_analyzer.analyze_test_execution(
                    memory=self.agent.memory,
                    original_test_goal=user_goal,
                    expected_outcome=expected_outcome,
                    test_case_name=name,
                    task_metadata=task_metadata,
                )
            return analysis

        except Exception as e:
            raise
