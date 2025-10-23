#!/usr/bin/env python3
"""
Simple startup script for NexusAI demo
Bypasses MCP server issues for presentation purposes
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Start the Flask web server directly"""
    try:
        # Import Flask app
        from web.main import app, socketio
        
        print("🚀 Starting NexusAI Demo Server...")
        print("📱 Dashboard will be available at: http://localhost:5000")
        print("⚡ Press Ctrl+C to stop")
        
        # Start the Flask app with SocketIO
        socketio.run(
            app,
            host='127.0.0.1',
            port=5000,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    exit(main())