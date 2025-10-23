#!/usr/bin/env python3
"""
NexusAI Application Runner
Main entry point for starting the complete NexusAI application with proper coordination
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point that delegates to the startup coordinator"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Path to the startup coordinator script
    startup_script = project_root / "scripts" / "start_nexusai.py"
    
    if not startup_script.exists():
        print("Error: Startup coordinator script not found")
        print(f"Expected: {startup_script}")
        sys.exit(1)
    
    # Pass all arguments to the startup coordinator
    cmd = [sys.executable, str(startup_script)] + sys.argv[1:]
    
    try:
        # Execute the startup coordinator
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Application startup failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nApplication shutdown requested by user")
        sys.exit(0)

if __name__ == "__main__":
    main()