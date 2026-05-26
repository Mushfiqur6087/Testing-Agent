"""
Centralized logging utilities for the Testing Agent project.
Ensures all debug logs are stored in a structured directory hierarchy:

  logs/
  └── test_run_YYYYMMDD_HHMMSS/          ← one folder per run
      ├── <test_case_name>/              ← one folder per test case
      │   ├── <test_case_name>_debug.log
      │   └── <test_case_name>_analysis.json
      └── ...
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
        self.project_root = Path(PROJECT_ROOT)
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Set once per process start — shared across all test cases in a run
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._run_dir: Path = self.logs_dir / f"test_run_{run_timestamp}"
        self._run_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Public: run-level directory
    # ------------------------------------------------------------------
    def get_run_dir(self) -> Path:
        """Return the top-level directory for the current test run."""
        return self._run_dir

    # ------------------------------------------------------------------
    # Public: per-test-case directory
    # ------------------------------------------------------------------
    def get_test_case_dir(self, test_case_name: str) -> Path:
        """
        Create (if needed) and return the directory for a specific test case.

        Layout:  logs/test_run_<ts>/<test_case_name>/
        """
        safe_name = self._safe_name(test_case_name)
        tc_dir = self._run_dir / safe_name
        tc_dir.mkdir(exist_ok=True)
        return tc_dir

    # ------------------------------------------------------------------
    # Public: file paths
    # ------------------------------------------------------------------
    def get_debug_file_path(self, component: str,
                            debug_file_prefix: str = None,
                            output_dir: Path = None) -> str:
        """
        Generate a debug .log file path.

        Args:
            component:         component name, e.g. 'agent'
            debug_file_prefix: test case name used as folder + filename prefix
            output_dir:        directory to write into (defaults to run dir)
        """
        if debug_file_prefix:
            # Put it inside the test case subfolder
            directory = output_dir if output_dir is not None else self.get_test_case_dir(debug_file_prefix)
            filename = f"{self._safe_name(debug_file_prefix)}_{component}_debug.log"
        else:
            directory = output_dir if output_dir is not None else self._run_dir
            filename = f"{component}_debug.log"

        return str(directory / filename)

    def get_analysis_file_path(self, test_case_name: str) -> str:
        """
        Return the path for a test case's analysis JSON file.

        Layout:  logs/test_run_<ts>/<test_case_name>/<test_case_name>_analysis.json
        """
        tc_dir = self.get_test_case_dir(test_case_name)
        filename = f"{self._safe_name(test_case_name)}_analysis.json"
        return str(tc_dir / filename)

    def get_session_log_path(self, filename: str = None,
                             output_dir: Path = None) -> str:
        """
        Generate a session log JSON file path.

        Args:
            filename:   optional custom filename
            output_dir: directory to write into (defaults to run dir)
        """
        directory = output_dir if output_dir is not None else self._run_dir

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_session_{timestamp}.json"

        return str(directory / filename)

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------
    def clean_old_logs(self, max_age_days: int = 7):
        """Clean up run directories older than *max_age_days*."""
        try:
            import time
            import shutil
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            for entry in self.logs_dir.iterdir():
                if entry.is_dir() and entry.name.startswith("test_run_"):
                    age = current_time - entry.stat().st_mtime
                    if age > max_age_seconds:
                        shutil.rmtree(entry)
                        logger.info(f"Cleaned up old run directory: {entry.name}")

        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

    def get_logs_directory(self) -> Path:
        """Return the base logs directory."""
        return self.logs_dir

    def list_log_files(self, pattern: str = "**/*.log") -> list:
        """List all log files under the logs directory (recursive)."""
        return list(self.logs_dir.glob(pattern))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_name(name: str) -> str:
        """Convert a test case name to a filesystem-safe string."""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


# Global instance for use across the project
debug_logger = DebugLogger()
