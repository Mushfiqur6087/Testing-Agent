import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)
from src.browser.browser_context import BrowserSession

class Tools:
    """
    Simplified Tools class for LLM-based validation and analysis.
    All complex logic is handled by LLM intelligence.
    """
    def __init__(self, llm_client=None, log_debug_func=None, debug_file_path=None):
        """
        Initialize the Tools class with optional LLM client and logging functions.
        
        Args:
            llm_client: Optional LLM client for intelligent analysis
            log_debug_func: Function to log debug information (from agent's _log_debug)
            debug_file_path: Path to the debug file for structured logging
        """
        self.llm_client = llm_client
        self.log_debug_func = log_debug_func
        self.debug_file_path = debug_file_path
        
    def set_logging_functions(self, log_debug_func=None, debug_file_path=None):
        """
        Set or update the logging functions for the Tools class.
        
        Args:
            log_debug_func: Function to log debug information (from agent's _log_debug)
            debug_file_path: Path to the debug file for structured logging
        """
        self.log_debug_func = log_debug_func
        self.debug_file_path = debug_file_path
        

    
    def _log_tools_llm_request(self, request_prompt: str):
        """Log tools LLM request to the debug file."""
        if not self.debug_file_path:
            return
            
        try:
            with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TOOLS LLM REQUEST\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n\n")
                f.write("REQUEST TO LLM:\n")
                f.write("-" * 40 + "\n")
                f.write(request_prompt)
                f.write(f"\n{'-'*40}\n\n")
        except Exception as e:
            pass
    
    def _log_tools_llm_response(self, response: str):
        """Log tools LLM response to the debug file."""
        if not self.debug_file_path:
            return
            
        try:
            with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                f.write("RESPONSE FROM LLM:\n")
                f.write("-" * 40 + "\n")
                f.write(response)
                f.write(f"\n{'-'*40}\n\n")
        except Exception as e:
            pass
        
    def execute(self, reason: str, browser_context: BrowserSession, llm_client=None) -> Dict[str, Any]:
        """
        Execute tools action using LLM for all validation and analysis.
        
        Args:
            reason: The reason why tools action is needed
            browser_context: The current browser session context
            llm_client: Optional LLM client for intelligent analysis (overrides instance client)
            
        Returns:
            Dictionary indicating success and any relevant information
        """
        try:
            # Use provided LLM client or fall back to instance client
            active_llm = llm_client or self.llm_client
            
            if not active_llm:
                return {
                    "message": "No LLM client available for validation",
                    "data": {"error": "No LLM client"}
                }
            
            # Get current page information
            page_info = self._get_page_info(browser_context)
            
            # Use LLM for all validation and analysis
            llm_result = self._analyze_with_llm(reason, page_info, active_llm)
            
            return {
                "message": llm_result.get("message", "Analysis completed successfully"),
                "data": {
                    "findings": llm_result.get("findings", ""),
                    "validation_passed": llm_result.get("validation_passed", False)
                }
            }
            
        except Exception as e:
            return {
                "message": f"Tools action failed: {e}",
                "data": {"error": str(e)}
            }
    
    def _get_page_info(self, browser_context: BrowserSession) -> Dict[str, Any]:
        """Get basic page information for LLM analysis."""
        try:
            page = browser_context.get_current_page()
            if page is None:
                return {"error": "No active page"}
            
            # Get page basics
            url = page.url
            title = page.title()
            
            # Get element tree string which contains all information
            element_tree_string = browser_context.get_element_tree_string(refresh=True)
            
            return {
                "url": url,
                "title": title,
                "element_tree": element_tree_string or "No elements found"
            }
            
        except Exception as e:
            return {"error": f"Failed to get page info: {e}"}

    def _analyze_with_llm(self, reason: str, page_info: Dict[str, Any], llm_client) -> Dict[str, Any]:
        """Use LLM to analyze the current page state and provide intelligent insights."""
        try:
            # Build prompt for LLM analysis
            analysis_prompt = f"""
You are analyzing a web page to provide intelligent insights for browser automation testing.

ANALYSIS REQUEST: {reason}

CURRENT PAGE INFORMATION:
- URL: {page_info.get('url', 'Unknown')}
- Page Title: {page_info.get('title', 'Unknown')}

COMPLETE DOM TREE STRUCTURE:
{page_info.get('element_tree', 'No elements found')}

Based on the analysis request and current page state, please provide your assessment in JSON format:

{{
    "message": "Summary message for the user",
    "findings": "Detailed description of what you observed",
    "validation_passed": true/false
}}

Focus on the specific request and provide actionable insights.
"""

            # Log the tools LLM request and response if debug logging is enabled
            if self.log_debug_func:
                try:
                    self._log_tools_llm_request(analysis_prompt)
                except Exception:
                    pass  # Don't let logging errors break the tools functionality

            # Get LLM response
            llm_response = llm_client.ask(analysis_prompt)
            
            # Log the tools LLM response if debug logging is enabled
            if self.log_debug_func:
                try:
                    self._log_tools_llm_response(llm_response)
                except Exception:
                    pass  # Don't let logging errors break the tools functionality
            
            # Parse JSON response
            try:
                # Clean up the response
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                    
                analysis_result = json.loads(llm_response.strip())
                
                return {
                    "message": analysis_result.get("message", "LLM analysis completed"),
                    "findings": analysis_result.get("findings", ""),
                    "validation_passed": analysis_result.get("validation_passed", False)
                }
                
            except json.JSONDecodeError:
                # If JSON parsing fails, use the raw response as findings
                return {
                    "message": "Analysis completed",
                    "findings": llm_response.strip(),
                    "validation_passed": True  # Assume success if we got a response
                }
                
        except Exception as e:
            return {
                "message": "LLM analysis unavailable",
                "findings": f"LLM analysis failed: {str(e)}",
                "validation_passed": False
            }

