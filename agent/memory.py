import json
import logging
from datetime import datetime
from typing import Optional
from agent.logging_utils import debug_logger

# Configure logging
logger = logging.getLogger(__name__)

class Memory:
    """
    Memory class stores task progress and history.
    """
    
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.history = []  # list of dicts or entries
        self.debug_enabled = False
        self.debug_file = None

    def enable_debug(self, debug_file: str = None):
        """Enable debug mode with optional custom debug file path."""
        self.debug_enabled = True
        if debug_file is None:
            self.debug_file = debug_logger.get_debug_file_path("memory")
        else:
            self.debug_file = debug_file
        logger.info(f"Memory debug mode enabled. Logging to: {self.debug_file}")

    def disable_debug(self):
        """Disable debug mode."""
        self.debug_enabled = False
        self.debug_file = None
        logger.info("Memory debug mode disabled")

    def add(self, entry: dict):
        """Add a new entry to memory, keeping within capacity."""
        self.history.append(entry)
        if len(self.history) > self.capacity:
            self.history.pop(0)
        
        # Log memory state if debug is enabled
        if self.debug_enabled:
            self._log_memory_state(f"Added entry: {entry}")

    def _log_memory_state(self, action_description: str = "Memory state update"):
        """Log current memory contents to debug file with timestamp."""
        if not self.debug_enabled or not self.debug_file:
            return
            
        try:
            timestamp = datetime.now().isoformat()
            
            debug_entry = f"""
{'='*80}
MEMORY DEBUG LOG
TIMESTAMP: {timestamp}
ACTION: {action_description}
{'='*80}

CURRENT MEMORY STATE:
{'-'*40}
Total entries: {len(self.history)}
Capacity: {self.capacity}
Memory usage: {len(self.history)}/{self.capacity}

MEMORY CONTENTS:
{json.dumps(self.history, indent=2, ensure_ascii=False)}
{'-'*40}

"""
            
            with open(self.debug_file, 'a', encoding='utf-8') as f:
                f.write(debug_entry)
                
        except Exception as e:
            logger.error(f"Failed to write memory debug log: {e}")

    def log_memory_snapshot(self, step_number: Optional[int] = None, custom_message: str = ""):
        """Manually log a memory snapshot with optional step number and custom message."""
        if not self.debug_enabled:
            return
            
        step_info = f" (Step {step_number})" if step_number is not None else ""
        message = f"Manual snapshot{step_info}"
        if custom_message:
            message += f" - {custom_message}"
            
        self._log_memory_state(message)

    def to_summary(self) -> str:
        """Return a summary string of the last entries in memory."""
        return json.dumps(self.history[-10:], indent=2)

    def __len__(self):
        return len(self.history)

