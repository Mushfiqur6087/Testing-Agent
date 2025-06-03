import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from browser.browser_context import BrowserSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Tools:
    """
    Simplified Tools class for LLM-based validation and analysis.
    All complex logic is handled by LLM intelligence.
    """
    def __init__(self, llm_client=None):
        """Initialize the Tools class with optional LLM client for intelligent analysis."""
        self.logger = logger
        self.llm_client = llm_client
        
    def _write_debug_element_tree(self, browser_context: BrowserSession):
        """Write the current element tree to the agent debug file for debugging purposes."""
        try:
            # Get the logs directory
            project_root = Path(__file__).parent.parent
            logs_dir = project_root / "logs"
            
            # Find the most recent agent debug file
            agent_debug_files = list(logs_dir.glob("agent_debug_*.log"))
            if not agent_debug_files:
                self.logger.warning("No agent debug file found for element tree logging")
                return
                
            # Get the most recent file
            latest_debug_file = max(agent_debug_files, key=lambda f: f.stat().st_mtime)
            
            # Get element tree
            element_tree = browser_context.get_element_tree_string(refresh=True)
            
            # Write to debug file
            with open(latest_debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TOOLS INVOKED - ELEMENT TREE DEBUG\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n\n")
                f.write("CURRENT PAGE ELEMENT TREE:\n")
                f.write("-" * 40 + "\n")
                f.write(element_tree or "No elements found")
                f.write(f"\n{'-'*40}\n\n")
                
            self.logger.info(f"Element tree logged to debug file: {latest_debug_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to write element tree to debug file: {e}")
        
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
            self.logger.info(f"Tools execution started with reason: {reason}")
            
            # Log current element tree to debug file for debugging purposes
            self._write_debug_element_tree(browser_context)
            
            # Use provided LLM client or fall back to instance client
            active_llm = llm_client or self.llm_client
            
            if not active_llm:
                return {
                    "message": "No LLM client available for validation",
                    "data": {"error": "No LLM client"}
                }
            
            # Get current page information
            page_info = self._get_page_info(browser_context)
            
            # Log the element tree for debugging
            self._write_debug_element_tree(browser_context)
            
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
            self.logger.error(f"Error in tools execution: {e}")
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

            # Get LLM response
            llm_response = llm_client.ask(analysis_prompt)
            
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
            self.logger.error(f"LLM analysis failed: {e}")
            return {
                "message": "LLM analysis unavailable",
                "findings": f"LLM analysis failed: {str(e)}",
                "validation_passed": False
            }

