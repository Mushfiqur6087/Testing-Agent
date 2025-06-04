#!/usr/bin/env python3
"""
Clean up script for Testing Agent project.
Removes all __pycache__ directories and .pyc files.
"""

import os
import shutil
import sys
from pathlib import Path


def clean_pycache(root_dir=None):
    """Remove all __pycache__ directories, .pyc files, and log files from the project."""
    if root_dir is None:
        root_dir = Path(__file__).parent
    else:
        root_dir = Path(root_dir)
    
    print(f"🧹 Cleaning cache and log files from: {root_dir}")
    
    # Count removed items
    removed_dirs = 0
    removed_files = 0
    
    # Remove __pycache__ directories
    for pycache_dir in root_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            print(f"  📁 Removing: {pycache_dir.relative_to(root_dir)}")
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
    
    # Remove .pyc files
    for pyc_file in root_dir.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"  🗑️  Removing: {pyc_file.relative_to(root_dir)}")
            pyc_file.unlink()
            removed_files += 1
    
    # Remove .pyo files (optimized Python files)
    for pyo_file in root_dir.rglob("*.pyo"):
        if pyo_file.is_file():
            print(f"  🗑️  Removing: {pyo_file.relative_to(root_dir)}")
            pyo_file.unlink()
            removed_files += 1
    
    # Remove log files
    logs_dir = root_dir / "logs"
    if logs_dir.exists() and logs_dir.is_dir():
        for log_file in logs_dir.rglob("*.log"):
            if log_file.is_file():
                print(f"  📄 Removing log: {log_file.relative_to(root_dir)}")
                log_file.unlink()
                removed_files += 1
    
    print(f"✅ Cleanup complete!")
    print(f"   📁 Removed {removed_dirs} __pycache__ directories")
    print(f"   🗑️  Removed {removed_files} cache and log files")
    
    if removed_dirs == 0 and removed_files == 0:
        print("   🎉 No cache or log files found - project is already clean!")


if __name__ == "__main__":
    try:
        # Allow custom root directory as command line argument
        root_dir = sys.argv[1] if len(sys.argv) > 1 else None
        clean_pycache(root_dir)
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)
