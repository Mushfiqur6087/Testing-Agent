"""
Memory summarization utilities for the browser agent.

This module provides functions to summarize and organize the agent's memory
to maintain context over long-running sessions.
"""

import time
from typing import List, Dict, Any, Optional

class MemorySummarizer:
    """
    Utility class for summarizing agent memory.
    """
    
    @staticmethod
    def summarize_actions(actions: List[Dict[str, Any]], max_items: int = 5) -> str:
        """
        Create a concise summary of recent actions.
        
        Args:
            actions: List of action memory entries
            max_items: Maximum number of items to include in summary
            
        Returns:
            Summary text
        """
        if not actions:
            return "No actions to summarize."
            
        # Get the most recent actions, limited by max_items
        recent_actions = actions[-max_items:]
        
        # Count successful and failed actions
        success_count = sum(1 for action in recent_actions if action["success"])
        fail_count = len(recent_actions) - success_count
        
        # Create summary string
        summary = [f"Completed {success_count} actions successfully, with {fail_count} failures."]
        
        # Add details about successful actions first
        successful = [a for a in recent_actions if a["success"] and a.get("include_in_memory", True)]
        if successful:
            summary.append("Successful actions:")
            for action in successful:
                action_name = action["action"]
                if action["content"]:
                    # Truncate content if too long
                    content = action["content"]
                    if len(content) > 100:
                        content = content[:97] + "..."
                    summary.append(f"- {action_name}: {content}")
                else:
                    # For actions without content, show parameters
                    params = action["params"]
                    if params:
                        if isinstance(params, tuple) and len(params) > 0:
                            # Format tuple parameters
                            params_str = ", ".join(str(p) for p in params)
                        elif hasattr(params, "__dict__"):
                            params_str = str(params.__dict__)
                        else:
                            params_str = str(params)
                            
                        # Truncate params if too long
                        if len(params_str) > 80:
                            params_str = params_str[:77] + "..."
                            
                        summary.append(f"- {action_name}: {params_str}")
                    else:
                        summary.append(f"- {action_name}: (no parameters)")
        
        # Add details about failures
        failures = [a for a in recent_actions if not a["success"]]
        if failures:
            summary.append("Failed actions:")
            for action in failures:
                error_msg = action["error"] or "Unknown error"
                # Truncate error message if too long
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                summary.append(f"- {action['action']}: {error_msg}")
        
        return "\n".join(summary)
    
    @staticmethod
    def create_periodic_summary(
        actions: List[Dict[str, Any]], 
        current_step: int,
        max_steps: int,
        task: str,
        interval: int = 5
    ) -> Optional[str]:
        """
        Create periodic summaries at specified intervals.
        
        Args:
            actions: List of action memory entries
            current_step: Current step number
            max_steps: Maximum number of steps
            task: Current task description
            interval: Create summary every N steps
            
        Returns:
            Summary text or None if no summary should be created
        """
        # Only create summaries at specified intervals
        if current_step % interval != 0:
            return None
            
        # Create progress information
        progress_pct = (current_step / max_steps) * 100 if max_steps > 0 else 0
        
        # Get actions since the last summary interval
        recent_actions = actions[-interval:]
        
        summary_parts = [
            f"MEMORY SUMMARY (Step {current_step}/{max_steps}, {progress_pct:.1f}%)",
            f"Task: {task}",
            "",
            MemorySummarizer.summarize_actions(recent_actions)
        ]
        
        return "\n".join(summary_parts)
        
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format a timestamp into a readable string.
        
        Args:
            timestamp: Unix timestamp
            format_str: Format string for time
            
        Returns:
            Formatted time string
        """
        return time.strftime(format_str, time.localtime(timestamp))
