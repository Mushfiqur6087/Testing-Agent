"""
Simple Test Result Analyzer for Testing Agent
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from src.agent.core_utils.llm import GeminiFlashClient
from src.agent.core_utils.memory import EnhancedMemory

class TestResultAnalyzer:
    """
    Simple analyzer that tells you if test passed or failed and why.
    """
    
    def __init__(self, llm_client: GeminiFlashClient):
        """Initialize with LLM client."""
        self.llm = llm_client
        
    def analyze_test_execution(self, memory: EnhancedMemory, 
                             original_test_goal: str,
                             expected_outcome: str) -> Dict[str, Any]:
        """
        Analyze test execution and generate comprehensive summary.
        
        Returns:
            Dict with detailed test analysis
        """
        # Create comprehensive analysis prompt
        analysis_prompt = self._create_analysis_prompt(original_test_goal, expected_outcome, memory)
        
        try:
            # Get LLM analysis
            llm_response = self.llm.ask(analysis_prompt)
            
            # Try to parse as JSON, handle markdown code blocks
            try:
                # First try direct JSON parsing
                analysis = json.loads(llm_response)
            except json.JSONDecodeError:
                try:
                    # Try to extract JSON from markdown code blocks
                    if "```json" in llm_response:
                        # Extract content between ```json and ```
                        start = llm_response.find("```json") + 7
                        end = llm_response.find("```", start)
                        json_content = llm_response[start:end].strip()
                        analysis = json.loads(json_content)
                    else:
                        # Fallback to text response
                        analysis = {"summary": llm_response}
                except json.JSONDecodeError:
                    # Final fallback
                    analysis = {"summary": llm_response}
            
            # Prepare complete result
            result = {
                "original_goal": original_test_goal,
                "expected_outcome": expected_outcome,
                "llm_analysis": analysis
            }
            
            # Save to logs
            self._save_analysis_to_logs(result)
            
            return result
            
        except Exception as e:
            error_result = {
                "original_goal": original_test_goal,
                "expected_outcome": expected_outcome,
                "llm_analysis": {"error": f"Analysis failed: {str(e)}"}
            }
            
            # Save error result to logs
            self._save_analysis_to_logs(error_result)
            
            return error_result
    
    def _save_analysis_to_logs(self, analysis_result: Dict[str, Any]) -> None:
        """Save analysis result to log file."""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_analysis_{timestamp}.json"
            filepath = os.path.join(logs_dir, filename)
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(analysis_result, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save analysis to logs: {e}")
    
    def _create_analysis_prompt(self, test_goal: str, expected_outcome: str, memory: EnhancedMemory) -> str:
        """Create comprehensive analysis prompt from memory data."""
        
        prompt = f"""
You are analyzing a test execution. Be concise and direct.

ORIGINAL TEST GOAL:
{test_goal}

ORIGINAL EXPECTED OUTCOME:
{expected_outcome}

EXECUTION FLOW:
"""
        
        # Add LLM states progression
        for state in memory.llm_states:
            step_num = state.get("step_number")
            current_state = state.get("current_state", {})
            
            prompt += f"\nStep {step_num}:\n"
            prompt += f"  Goal: {current_state.get('next_goal', 'N/A')}\n"
            prompt += f"  Evaluation of previous: {current_state.get('evaluation_previous_goal', 'N/A')}\n"
            prompt += f"  Memory: {current_state.get('memory', 'N/A')}\n"
        
        # Add expected outcome in the middle of execution flow
        prompt += f"""

"""
        
        # Add tool validation results
        if memory.tool_outputs:
            prompt += "\nTOOL VALIDATIONS:\n"
            for output in memory.tool_outputs:
                step_num = output.get("step_number")
                tool_data = output.get("tool_output", {})
                
                prompt += f"\nStep {step_num} Tool Result:\n"
                prompt += f"  Validation Passed: {tool_data.get('validation_passed')}\n"
                prompt += f"  Findings: {tool_data.get('findings', 'N/A')}\n"
                prompt += f"  Reason: {tool_data.get('request_reason', 'N/A')}\n"
        
        prompt += """

Please analyze this and respond in JSON format:

{
  "test_result": "PASSED" | "FAILED",   // true ⇨ `test_result` matches the original expected outcome the test *expected*; false otherwise
  "success": true | false,              // actual test result based on the execution
  "summary": "Brief narrative (2-4 lines) + optional bullet list describing the steps taken and why the test passed or failed",
  "errors": "Describe any errors encountered, or 'None' if there were none"
}

Give detailed explanation. Focus on whether the test goal was achieved.
"""
        
        return prompt
