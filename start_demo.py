#!/usr/bin/env python3
"""
Simple NexusAI Demo Startup
Starts the demo server directly without complex process management
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start the demo server"""
    
    # Set default environment variables if not present
    os.environ.setdefault('SECRET_KEY', 'demo_secret_key_for_testing')
    os.environ.setdefault('FLASK_HOST', '127.0.0.1')
    os.environ.setdefault('FLASK_PORT', '5000')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print("🚀 Starting NexusAI Demo Server...")
    print("📊 Dashboard will be available at: http://127.0.0.1:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Import and run the demo server
    try:
        from demo_server import main as demo_main
        demo_main()
    except KeyboardInterrupt:
        print("\n👋 Demo server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting demo server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()