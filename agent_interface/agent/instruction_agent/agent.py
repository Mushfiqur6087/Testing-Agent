import os
import sys
import json
from typing import Optional, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.agent.core_utils.llm import GeminiFlashClient
from src.agent.instruction_agent.instruction_prompt import prompt


class InstructionAgent:
    """
    An agent that generates test cases from requirements using LLM.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the InstructionAgent with API key.
        
        Args:
            api_key (str): The API key for Gemini Flash client
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.llm_client = GeminiFlashClient(api_key=api_key)
        self.test_case = None
        self.output = None
        self.test_cases_list = []
    
    def process_test_case(self, test_case: str) -> str:
        """
        Process a test case requirement and generate test cases.
        New test case will replace the previous one.
        
        Args:
            test_case (str): The test case requirement description
            
        Returns:
            str: Generated test cases in JSON format
        """
        if not test_case.strip():
            raise ValueError("Test case cannot be empty")
        
        # Store the current test case (replaces previous one)
        self.test_case = test_case
        
        # Combine the general prompt template with the specific test-case instruction
        full_prompt = f"{prompt}\n{test_case}"
        
        # Send the combined prompt to the LLM and get the response
        response_text = self.llm_client.ask(full_prompt)
        
        # Store the output (replaces previous one)
        self.output = response_text
        
        # Parse and store test cases as list
        self._parse_and_store_test_cases()
        
        return response_text
    
    def get_output(self) -> Optional[str]:
        """
        Get the generated output.
        
        Returns:
            str: The generated test cases output, or None if no processing done yet
        """
        return self.output
    
    def get_test_case(self) -> Optional[str]:
        """
        Get the current test case.
        
        Returns:
            str: The current test case, or None if no processing done yet
        """
        return self.test_case
    
    def parse_output_as_json(self) -> Optional[Dict[Any, Any]]:
        """
        Attempt to parse the output as JSON.
        
        Returns:
            dict: Parsed JSON if successful, None if parsing fails
        """
        if not self.output:
            return None
        
        try:
            # Try to find JSON content in the response
            output = self.output.strip()
            
            # If the response contains markdown code blocks, extract JSON from them
            if "```json" in output:
                start = output.find("```json") + 7
                end = output.find("```", start)
                if end != -1:
                    output = output[start:end].strip()
            elif "```" in output:
                start = output.find("```") + 3
                end = output.find("```", start)
                if end != -1:
                    output = output[start:end].strip()
            
            return json.loads(output)
        except json.JSONDecodeError:
            return None
    
    def get_test_cases_list(self) -> list:
        """
        Get the test cases as a list for iteration.
        
        Returns:
            list: List of test case dictionaries, empty list if no test cases or parsing failed
        """
        return self.test_cases_list.copy()
    
    def get_test_case_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a single test case by its index.
        
        Args:
            index (int): The index of the test case (0-based)
            
        Returns:
            dict: Test case dictionary if found, None if index is out of range
        """
        if 0 <= index < len(self.test_cases_list):
            return self.test_cases_list[index].copy()
        return None
    
    def get_test_case_by_name(self, test_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single test case by its name.
        
        Args:
            test_name (str): The name of the test case to find
            
        Returns:
            dict: Test case dictionary if found, None if not found
        """
        for test_case in self.test_cases_list:
            if test_case.get('test_name') == test_name:
                return test_case.copy()
        return None
    
    def _parse_and_store_test_cases(self) -> None:
        """
        Parse the output and store test cases as a list.
        """
        self.test_cases_list = []  # Reset the list
        
        parsed_json = self.parse_output_as_json()
        if parsed_json and isinstance(parsed_json, list):
            self.test_cases_list = parsed_json
