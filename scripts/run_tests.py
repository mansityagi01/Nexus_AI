#!/usr/bin/env python3
"""
Test runner script for NexusAI testing suite.
"""
import subprocess
import sys
import os

def run_tests(test_type="all", verbose=False):
    """Run tests based on specified type."""
    
    # Change to project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add specific test paths based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "frontend":
        cmd.append("tests/frontend/")
    elif test_type == "health":
        cmd.append("tests/test_health_check.py")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Add run flag to ensure tests complete
    cmd.append("--tb=short")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run NexusAI tests")
    parser.add_argument("--type", choices=["all", "unit", "integration", "frontend", "health"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    exit_code = run_tests(args.type, args.verbose)
    sys.exit(exit_code)