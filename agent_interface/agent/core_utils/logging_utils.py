"""
Centralized logging utilities for the Testing Agent project.
Ensures all debug logs are stored in the logs directory.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Set up project root and add to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logger = logging.getLogger(__name__)

class DebugLogger:
    """Centralized debug logging utility for consistent log file management."""
    
    def __init__(self):
        # Get the project root directory using the PROJECT_ROOT variable
        self.project_root = Path(PROJECT_ROOT)
        self.logs_dir = self.project_root / "logs"
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
    def _get_project_root(self) -> Path:
        """Find the project root directory containing the logs folder."""
        current = Path(__file__).resolve()
        
        # Go up the directory tree until we find the Testing Agent directory
        while current.parent != current:
            if (current / "logs").exists() and current.name == "Testing Agent":
                return current
            current = current.parent
            
        # Fallback: go up one level from agent folder
        agent_dir = Path(__file__).resolve().parent
        project_root = agent_dir.parent
        
        # Create logs directory if it doesn't exist
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        return project_root
    
    def get_debug_file_path(self, component: str, debug_file_prefix: str = None) -> str:
        """
        Generate a debug file path in the logs directory.
        
        Args:
            component: The component name (e.g., 'agent', 'memory')
            debug_file_prefix: Optional prefix for the debug file
            
        Returns:
            Full path to the debug file in the logs directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if debug_file_prefix:
            filename = f"{debug_file_prefix}_{component}_{timestamp}.log"
        else:
            filename = f"{component}_debug_{timestamp}.log"
            
        return str(self.logs_dir / filename)
    
    def get_session_log_path(self, filename: str = None) -> str:
        """
        Generate a session log file path in the logs directory.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Full path to the session log file in the logs directory
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_session_{timestamp}.json"
            
        return str(self.logs_dir / filename)
    
    def clean_old_logs(self, max_age_days: int = 7):
        """
        Clean up old log files older than specified days.
        
        Args:
            max_age_days: Maximum age of log files to keep
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.is_file():
                    file_age = current_time - log_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        log_file.unlink()
                        logger.info(f"Cleaned up old log file: {log_file.name}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def get_logs_directory(self) -> Path:
        """Get the logs directory path."""
        return self.logs_dir
    
    def list_log_files(self, pattern: str = "*.log") -> list:
        """
        List all log files in the logs directory matching the pattern.
        
        Args:
            pattern: Glob pattern to match files (default: "*.log")
            
        Returns:
            List of log file paths
        """
        return list(self.logs_dir.glob(pattern))
    
    def get_log_file_info(self) -> dict:
        """
        Get information about log files in the logs directory.
        
        Returns:
            Dictionary with log file statistics
        """
        log_files = self.list_log_files("*.log")
        session_files = self.list_log_files("*.json")
        
        total_log_size = sum(f.stat().st_size for f in log_files if f.is_file())
        total_session_size = sum(f.stat().st_size for f in session_files if f.is_file())
        
        return {
            "log_files_count": len(log_files),
            "session_files_count": len(session_files),
            "total_log_size_bytes": total_log_size,
            "total_session_size_bytes": total_session_size,
            "total_size_mb": (total_log_size + total_session_size) / (1024 * 1024),
            "logs_directory": str(self.logs_dir)
        }

# Global instance for use across the project
debug_logger = DebugLogger()
