#!/usr/bin/env python3
"""
SAIL Integration Bridge
Connects the SAIL web interface with your existing Testing Agent framework
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import requests
from typing import Dict, List, Optional

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from test_agent_main import TestAgentMain
    from agent.instruction_agent.agent import InstructionAgent
    from test_agent import TestAgent
except ImportError as e:
    print(f"⚠️  Could not import Testing Agent modules: {e}")
    print("Make sure you're running this from the Testing-Agent root directory")

class SAILIntegration:
    """Bridge between SAIL web interface and Testing Agent framework"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            print("⚠️  GEMINI_API_KEY not found. Some features may not work.")
        
        self.web_interface_path = Path(__file__).parent.parent.parent / "web_interface"
        self.logs_dir = Path(__file__).parent.parent.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize Testing Agent components
        self.test_agent_main = TestAgentMain()
        self.instruction_agent = InstructionAgent()
        self.test_agent = TestAgent()
        
    def start_web_interface(self):
        """Start the SAIL web interface"""
        print("🚀 Starting SAIL Web Interface...")
        
        if not self.web_interface_path.exists():
            print("❌ Web interface directory not found!")
            return False
            
        try:
            # Change to web_interface directory and start Next.js
            os.chdir(self.web_interface_path)
            
            # Check if dependencies are installed
            if not (self.web_interface_path / "node_modules").exists():
                print("📦 Installing dependencies...")
                subprocess.run(["npm", "install", "--legacy-peer-deps"], check=True)
            
            print("🌐 Starting development server...")
            print("📍 SAIL will be available at: http://localhost:3000")
            print("🔧 Use Ctrl+C to stop the server")
            
            # Start the development server
            subprocess.run(["npm", "run", "dev"])
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start web interface: {e}")
            return False
        except KeyboardInterrupt:
            print("\n🛑 SAIL web interface stopped")
            return True

    def execute_test(self, test_file: str) -> Dict:
        """Execute test cases from a JSON file"""
        try:
            with open(test_file, 'r') as f:
                test_cases = json.load(f)
            
            results = []
            for test_case in test_cases:
                # Execute test using TestAgent
                result = self.test_agent.execute_test(test_case)
                results.append(result)
                
                # Log result
                self._log_result(test_case, result)
            
            return {
                "status": "success",
                "total_tests": len(test_cases),
                "passed": sum(1 for r in results if r.get("status") == "passed"),
                "failed": sum(1 for r in results if r.get("status") == "failed"),
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def generate_tests(self, url: str, test_scenario: Optional[str] = None) -> Dict:
        """Generate test cases for a given URL and scenario"""
        try:
            # Use InstructionAgent to generate test cases
            test_cases = self.instruction_agent.generate_test_cases(url, test_scenario)
            
            # Save generated tests
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = self.logs_dir / f"generated_tests_{timestamp}.json"
            
            with open(test_file, 'w') as f:
                json.dump(test_cases, f, indent=2)
            
            return {
                "status": "success",
                "test_cases": test_cases,
                "test_file": str(test_file)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _log_result(self, test_case: Dict, result: Dict):
        """Log test execution result"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = self.logs_dir / "test_execution.log"
        
        with open(log_file, 'a') as f:
            f.write(f"\n[{timestamp}] Test: {test_case.get('test_name')}\n")
            f.write(f"Status: {result.get('status')}\n")
            if result.get("error"):
                f.write(f"Error: {result.get('error')}\n")
            f.write("-" * 50 + "\n")

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAIL Integration Bridge")
    parser.add_argument('command', choices=['start', 'execute', 'generate'], 
                       help='Command to run')
    parser.add_argument('--test-file', help='Path to test file for execution')
    parser.add_argument('--url', help='URL for test generation')
    parser.add_argument('--scenario', help='Test scenario description')
    
    args = parser.parse_args()
    
    integration = SAILIntegration()
    
    if args.command == 'start':
        print("🎯 SAIL Integration Bridge")
        print("=" * 50)
        integration.start_web_interface()
    elif args.command == 'execute':
        if not args.test_file:
            print("❌ --test-file is required for execute command")
            return 1
        result = integration.execute_test(args.test_file)
        print(json.dumps(result, indent=2))
    elif args.command == 'generate':
        if not args.url:
            print("❌ --url is required for generate command")
            return 1
        result = integration.generate_tests(args.url, args.scenario)
        print(json.dumps(result, indent=2))
    
    return 0

if __name__ == "__main__":
    exit(main())
