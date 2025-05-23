"""
Browser Agent with Memory

This module provides a simple browser automation agent that can:
1. Use language models to understand and execute tasks
2. Maintain a memory of past actions 
3. Execute browser actions using the browser controller
"""

import logging
import time
import json
import os
from typing import Dict, List, Optional, Any, Union
import sys

# Add the parent directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from controller.browser_controller import BrowserController
from browser.browser_context import BrowserSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Memory:
    """
    Simple memory system for the agent to track previous actions and their outcomes.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize memory with a maximum size to prevent unbounded growth.
        
        Args:
            max_size: Maximum number of memory entries to keep
        """
        self.actions: List[Dict[str, Any]] = []
        self.max_size = max_size
        self.summaries: List[str] = []
    
    def add_action(self, action_name: str, params: Any, success: bool, error: Optional[str] = None, 
                  content: Optional[str] = None, include_in_memory: bool = True, timestamp: float = None):
        """
        Record an action and its outcome in memory.
        
        Args:
            action_name: Name of the action executed
            params: Parameters used for the action
            success: Whether the action was successful
            error: Error message if action failed
            content: Content extracted from the action
            include_in_memory: Whether to include this action in memory summaries
            timestamp: When the action was executed (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
            
        memory_entry = {
            "timestamp": timestamp,
            "action": action_name,
            "params": params,
            "success": success,
            "error": error,
            "content": content,
            "include_in_memory": include_in_memory
        }
        
        self.actions.append(memory_entry)
        
        # Trim memory if it exceeds max size
        if len(self.actions) > self.max_size:
            self.actions = self.actions[-self.max_size:]
    
    def get_recent_actions(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent actions from memory.
        
        Args:
            count: Number of recent actions to retrieve
            
        Returns:
            List of recent memory entries
        """
        return self.actions[-count:] if self.actions else []
    
    def add_summary(self, summary: str):
        """
        Add a periodic summary of agent's progress.
        
        Args:
            summary: A condensed summary of recent activities
        """
        self.summaries.append(summary)
    
    def get_summaries(self) -> List[str]:
        """
        Get all memory summaries.
        
        Returns:
            List of memory summaries
        """
        return self.summaries
    
    def get_latest_summary(self) -> Optional[str]:
        """
        Get the most recent memory summary.
        
        Returns:
            Latest summary or None if no summaries exist
        """
        return self.summaries[-1] if self.summaries else None
    
    def clear(self):
        """Clear all entries from memory."""
        self.actions = []
        self.summaries = []
    
    def get_formatted_history(self, max_entries: int = None) -> str:
        """
        Format memory into a readable history string.
        
        Args:
            max_entries: Maximum number of entries to include
            
        Returns:
            Formatted history string
        """
        if not self.actions:
            return "No actions recorded yet."
        
        entries = self.actions[-max_entries:] if max_entries else self.actions
        
        lines = []
        for i, entry in enumerate(entries):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["timestamp"]))
            status = "✓" if entry["success"] else "✗"
            
            if entry["params"] is None:
                params_str = "None"
            elif hasattr(entry["params"], "__dict__"):
                params_str = str(entry["params"].__dict__)
            else:
                params_str = str(entry["params"])
            
            lines.append(f"{i+1}. [{timestamp}] {status} {entry['action']}: {params_str}")
            
            if entry["content"]:
                lines.append(f"   Result: {entry['content']}")
            if entry["error"]:
                lines.append(f"   Error: {entry['error']}")
        
        if self.summaries:
            lines.append("\nSummaries:")
            for i, summary in enumerate(self.summaries):
                lines.append(f"Summary {i+1}: {summary}")
                
        return "\n".join(lines)
    
    def save_to_file(self, filename: str):
        """
        Save memory to a JSON file.
        
        Args:
            filename: Path to save the memory file
        """
        # Convert memory entries to serializable format
        serializable_actions = []
        for entry in self.actions:
            serialized_entry = entry.copy()
            
            # Handle non-serializable params
            if hasattr(entry["params"], "__dict__"):
                serialized_entry["params"] = entry["params"].__dict__
            
            serializable_actions.append(serialized_entry)
        
        memory_data = {
            "actions": serializable_actions,
            "summaries": self.summaries
        }
        
        with open(filename, "w") as f:
            json.dump(memory_data, f, indent=2)
            
    def load_from_file(self, filename: str):
        """
        Load memory from a JSON file.
        
        Args:
            filename: Path to the memory file
        """
        try:
            with open(filename, "r") as f:
                memory_data = json.load(f)
                
            self.actions = memory_data.get("actions", [])
            self.summaries = memory_data.get("summaries", [])
            
        except Exception as e:
            logger.error(f"Failed to load memory from {filename}: {e}")


class Agent:
    """
    Browser automation agent with memory capabilities.
    """
    def __init__(self, browser_context=None, llm_api_key=None):
        """
        Initialize the agent with a browser controller and memory system.
        
        Args:
            browser_context: Optional browser context to use
            llm_api_key: API key for language model service
        """
        self.browser_controller = BrowserController()
        self.memory = Memory()
        self.llm_api_key = llm_api_key
        self.current_task = None
        self.max_steps = 10  # Default maximum steps
        self.current_step = 0
    
    def execute_command(self, command: str, *args) -> Union[bool, Dict[str, Any], str]:
        """
        Execute a browser command and record it in memory.
        
        Args:
            command: Name of the command to execute
            *args: Arguments for the command
            
        Returns:
            Result of the command
        """
        start_time = time.time()
        result = self.browser_controller.execute_command(command, *args)
        end_time = time.time()
        
        # Determine success and extract error/content
        success = False
        error = None
        content = None
        
        # Process results based on return type
        if isinstance(result, bool):
            success = result
            if not success:
                error = f"Command '{command}' failed"
        elif isinstance(result, dict):
            success = True
            content = str(result)
        elif isinstance(result, str):
            success = bool(result)
            content = result
        
        # Record in memory
        self.memory.add_action(
            action_name=command,
            params=args,
            success=success,
            error=error,
            content=content,
            include_in_memory=True,
            timestamp=start_time
        )
        
        # Log execution time
        logger.debug(f"Command '{command}' executed in {end_time - start_time:.2f}s")
        
        return result
    
    def get_available_commands(self) -> List[str]:
        """
        Get list of available browser commands.
        
        Returns:
            List of command names
        """
        return [
            "go_back",
            "click_element",
            "input_text",
            "switch_tab",
            "open_tab",
            "close_tab", 
            "navigate_to",
            "get_selector_map"
        ]
    
    def set_task(self, task: str, max_steps: int = 10):
        """
        Set the current task and reset progress.
        
        Args:
            task: Task description
            max_steps: Maximum number of steps to execute
        """
        self.current_task = task
        self.max_steps = max_steps
        self.current_step = 0
        
        logger.info(f"Task set: {task} (max steps: {max_steps})")
        
        # Add task to memory
        self.memory.add_summary(f"Started new task: {task}")
    
    def create_memory_summary(self) -> str:
        """
        Create a summary of recent actions to preserve memory.
        
        Returns:
            Summary text
        """
        recent_actions = self.memory.get_recent_actions(5)
        
        if not recent_actions:
            return "No recent actions to summarize."
        
        success_count = sum(1 for action in recent_actions if action["success"])
        
        summary_lines = [
            f"Completed {success_count}/{len(recent_actions)} recent actions successfully.",
            f"Current progress: Step {self.current_step}/{self.max_steps}"
        ]
        
        # Add details about the most recent successful and failed actions
        for action in recent_actions:
            if action["success"] and action["include_in_memory"]:
                summary_lines.append(f"✓ {action['action']}: {action['content']}")
            elif not action["success"]:
                summary_lines.append(f"✗ {action['action']}: {action['error']}")
        
        summary = " ".join(summary_lines)
        self.memory.add_summary(summary)
        
        return summary
    
    def get_memory_history(self, max_entries: int = None) -> str:
        """
        Get formatted history of agent actions.
        
        Args:
            max_entries: Maximum number of entries to include
            
        Returns:
            Formatted history string
        """
        return self.memory.get_formatted_history(max_entries)
    
    def save_memory(self, filename: str):
        """
        Save agent memory to file.
        
        Args:
            filename: Path to save the memory
        """
        self.memory.save_to_file(filename)
        logger.info(f"Memory saved to {filename}")
    
    def load_memory(self, filename: str):
        """
        Load agent memory from file.
        
        Args:
            filename: Path to load memory from
        """
        self.memory.load_from_file(filename)
        logger.info(f"Memory loaded from {filename}")


