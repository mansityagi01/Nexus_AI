#!/usr/bin/env python3
"""
Frontend build script for NexusAI
Handles Svelte compilation to Flask static directory with proper asset optimization
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def check_node_modules():
    """Check if node_modules exists and install dependencies if needed"""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    else:
        print("Frontend dependencies already installed")

def clean_static_dir():
    """Clean the Flask static directory"""
    static_dir = Path(__file__).parent.parent / "backend" / "web" / "static"
    
    if static_dir.exists():
        print("Cleaning static directory...")
        shutil.rmtree(static_dir)
    
    static_dir.mkdir(parents=True, exist_ok=True)

def build_frontend(mode="production"):
    """Build the frontend with specified mode"""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    
    print(f"Building frontend in {mode} mode...")
    
    if mode == "development":
        run_command("npm run build:dev", cwd=frontend_dir)
    else:
        run_command("npm run build:prod", cwd=frontend_dir)
    
    print("Frontend build completed successfully!")

def verify_build():
    """Verify that the build output exists"""
    static_dir = Path(__file__).parent.parent / "backend" / "web" / "static"
    
    required_files = ["index.html"]
    
    for file in required_files:
        file_path = static_dir / file
        if not file_path.exists():
            print(f"Error: Required file {file} not found in static directory")
            sys.exit(1)
    
    # Check for JS and CSS files
    js_files = list(static_dir.glob("**/*.js"))
    css_files = list(static_dir.glob("**/*.css"))
    
    if not js_files:
        print("Warning: No JavaScript files found in build output")
    
    if not css_files:
        print("Warning: No CSS files found in build output")
    
    print(f"Build verification passed. Found {len(js_files)} JS files and {len(css_files)} CSS files")

def main():
    """Main build process"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build NexusAI frontend")
    parser.add_argument(
        "--mode", 
        choices=["development", "production"], 
        default="production",
        help="Build mode (default: production)"
    )
    parser.add_argument(
        "--clean", 
        action="store_true",
        help="Clean static directory before building"
    )
    parser.add_argument(
        "--skip-install", 
        action="store_true",
        help="Skip dependency installation check"
    )
    
    args = parser.parse_args()
    
    try:
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        print("Starting frontend build process...")
        
        if not args.skip_install:
            check_node_modules()
        
        if args.clean:
            clean_static_dir()
        
        build_frontend(args.mode)
        verify_build()
        
        print("Frontend build process completed successfully!")
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()