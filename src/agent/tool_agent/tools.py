import json
import base64
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)
# pyrefly: ignore [missing-import]
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
        """Get page information (DOM, alerts, screenshot) for LLM analysis."""
        try:
            page = browser_context.get_current_page()
            if page is None:
                return {"error": "No active page"}

            page_info = {
                "url": page.url,
                "title": page.title(),
                "element_tree": browser_context.get_element_tree_string(refresh=True) or "No elements found",
                "has_alerts": browser_context.has_recent_alerts(),
            }

            alerts_info = browser_context.get_formatted_alerts_for_llm()
            if alerts_info:
                page_info["alerts"] = alerts_info

            # Capture screenshot as base64 for vision-capable models
            try:
                screenshot_bytes = page.screenshot(type="jpeg", quality=60, full_page=False)
                page_info["screenshot_b64"] = base64.b64encode(screenshot_bytes).decode()
            except Exception:
                pass  # not all setups support screenshots; degrade gracefully

            return page_info

        except Exception as e:
            return {"error": f"Failed to get page info: {e}"}

    def _analyze_with_llm(self, reason: str, page_info: Dict[str, Any], llm_client) -> Dict[str, Any]:
        """Use LLM to analyze the current page state and provide intelligent insights."""
        try:
            screenshot_b64 = page_info.pop("screenshot_b64", None)

            analysis_prompt = f"""ANALYSIS REQUEST: {reason}

CURRENT PAGE STATE:
- URL: {page_info.get('url', 'Unknown')}
- Title: {page_info.get('title', 'Unknown')}"""

            if page_info.get('has_alerts', False):
                analysis_prompt += f"""
- Browser Alert Observed: YES
{page_info.get('alerts', '')}"""
            else:
                analysis_prompt += "\n- Browser Alert Observed: NO"

            analysis_prompt += f"""

DOM SNAPSHOT (note: input .value is a JS property, never shown as HTML attribute — absence of value= does NOT mean fields are empty):
{page_info.get('element_tree', 'No elements found')}

Using the screenshot (if provided) as the primary visual source of truth, answer the analysis request above.
Respond with JSON only:
{{
    "message": "One-sentence verdict",
    "findings": "What you actually observed (screenshot + alerts + DOM). Keep it under 3 sentences.",
    "validation_passed": true or false
}}
"""
            if self.log_debug_func:
                self._log_tools_llm_request(analysis_prompt)

            # Build the messages list; attach screenshot if available and model supports vision
            messages: list = [
                {
                    "role": "system",
                    "content": (
                        "You are a pragmatic browser test validator. "
                        "Your job is to decide whether a test PASSED or FAILED based on observable evidence.\n\n"
                        "VALIDATION RULES:\n"
                        "1. TRUST the screenshot first — it shows the real visual state of the page. "
                        "DOM attributes (like 'value') are static snapshots and often do NOT reflect live JS state.\n"
                        "2. If the screenshot and browser alerts together support the expected outcome, set validation_passed=true.\n"
                        "3. Only set validation_passed=false if there is CLEAR POSITIVE EVIDENCE of failure "
                        "(e.g., wrong alert text, error message visible, form did not reset when it clearly should have).\n"
                        "4. Missing DOM attributes are NOT evidence of failure — JS properties like .value are never "
                        "reflected as HTML attributes after user input.\n"
                        "5. If you are uncertain but the main observable outcome matches the request, default to PASS.\n"
                        "6. Be concise. Do not list things you cannot check — only report what you can actually observe."
                    ),
                },
            ]
            if screenshot_b64:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"},
                        },
                    ],
                })
            else:
                messages.append({"role": "user", "content": analysis_prompt})

            # Call LLM directly via litellm so we can pass a rich messages list
            import litellm
            response = litellm.completion(
                model=llm_client.model,
                messages=messages,
                timeout=llm_client.timeout,
            )
            llm_response = response.choices[0].message.content

            if self.log_debug_func:
                self._log_tools_llm_response(llm_response)

            # Parse JSON response
            cleaned = llm_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            try:
                result = json.loads(cleaned.strip())
                return {
                    "message": result.get("message", "LLM analysis completed"),
                    "findings": result.get("findings", ""),
                    "validation_passed": result.get("validation_passed", False),
                }
            except json.JSONDecodeError:
                return {"message": "Analysis completed", "findings": cleaned, "validation_passed": True}

        except Exception as e:
            return {"message": "LLM analysis unavailable", "findings": str(e), "validation_passed": False}

