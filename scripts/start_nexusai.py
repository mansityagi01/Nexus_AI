#!/usr/bin/env python3
"""
NexusAI Application Startup Coordinator
Handles proper process management for MCP server and Flask server with health checks
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
import socket
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessManager:
    """Manages application processes with health monitoring and graceful shutdown"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.health_checks: Dict[str, callable] = {}
        self.shutdown_event = threading.Event()
        self.health_monitor_thread: Optional[threading.Thread] = None
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def add_process(self, name: str, command: list, cwd: Optional[str] = None, 
                   env: Optional[Dict[str, str]] = None, health_check: Optional[callable] = None):
        """Add a process to be managed"""
        try:
            logger.info(f"Starting process: {name}")
            logger.debug(f"Command: {' '.join(command)}")
            
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[name] = process
            
            if health_check:
                self.health_checks[name] = health_check
            
            logger.info(f"Process {name} started with PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start process {name}: {e}")
            return False
    
    def wait_for_port(self, host: str, port: int, timeout: int = 30) -> bool:
        """Wait for a port to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (socket.error, ConnectionRefusedError):
                time.sleep(0.5)
        return False
    
    def check_http_health(self, url: str, timeout: int = 5) -> bool:
        """Check HTTP endpoint health"""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_process_health(self, name: str) -> bool:
        """Check if a process is still running"""
        if name not in self.processes:
            return False
        
        process = self.processes[name]
        return process.poll() is None
    
    def start_health_monitoring(self):
        """Start health monitoring thread"""
        def monitor():
            while not self.shutdown_event.is_set():
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"Process {name} has died (exit code: {process.returncode})")
                        # Could implement restart logic here
                    
                    # Run custom health checks
                    if name in self.health_checks:
                        try:
                            if not self.health_checks[name]():
                                logger.warning(f"Health check failed for {name}")
                        except Exception as e:
                            logger.error(f"Health check error for {name}: {e}")
                
                time.sleep(10)  # Check every 10 seconds
        
        self.health_monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.health_monitor_thread.start()
        logger.info("Health monitoring started")
    
    def shutdown(self):
        """Gracefully shutdown all processes"""
        logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        # Stop processes in reverse order
        for name, process in reversed(list(self.processes.items())):
            logger.info(f"Stopping process: {name}")
            
            try:
                # Try graceful termination first
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"Process {name} terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning(f"Force killing process {name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                logger.error(f"Error stopping process {name}: {e}")
        
        logger.info("All processes stopped")

class NexusAICoordinator:
    """Coordinates NexusAI application startup and management"""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment"""
        from dotenv import load_dotenv
        
        # Load environment variables
        env_file = self.project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        
        return {
            'mcp_host': os.getenv('MCP_HOST', '127.0.0.1'),
            'mcp_port': int(os.getenv('MCP_PORT', '8080')),
            'flask_host': os.getenv('FLASK_HOST', '127.0.0.1'),
            'flask_port': int(os.getenv('FLASK_PORT', '5000')),
            'flask_debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
    
    def validate_environment(self) -> bool:
        """Validate environment and dependencies"""
        logger.info("Validating environment...")
        
        # Check required environment variables
        required_vars = ['GEMINI_API_KEY', 'SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check Python dependencies
        try:
            import flask
            import flask_socketio
            import google.generativeai
            logger.info("Python dependencies validated")
        except ImportError as e:
            logger.error(f"Missing Python dependency: {e}")
            return False
        
        # Check if frontend is built
        static_dir = self.project_root / 'backend' / 'web' / 'static'
        if not (static_dir / 'index.html').exists():
            logger.warning("Frontend not built. Run build script first for full functionality.")
        
        logger.info("Environment validation completed")
        return True
    
    def start_mcp_server(self) -> bool:
        """Start MCP server process"""
        mcp_script = self.project_root / 'demo_server.py'
        
        command = [
            sys.executable, str(mcp_script),
            '--host', self.config['mcp_host'],
            '--port', str(self.config['mcp_port'])
        ]
        
        def mcp_health_check():
            return self.process_manager.wait_for_port(
                self.config['mcp_host'], 
                self.config['mcp_port'], 
                timeout=1
            )
        
        success = self.process_manager.add_process(
            'mcp-server',
            command,
            cwd=str(self.project_root),
            health_check=mcp_health_check
        )
        
        if success:
            # Wait for MCP server to be ready
            logger.info("Waiting for MCP server to be ready...")
            if self.process_manager.wait_for_port(
                self.config['mcp_host'], 
                self.config['mcp_port'], 
                timeout=30
            ):
                logger.info("MCP server is ready")
                return True
            else:
                logger.error("MCP server failed to start within timeout")
                return False
        
        return False
    
    def start_flask_server(self) -> bool:
        """Start Flask server process"""
        flask_script = self.project_root / 'backend' / 'web' / 'main.py'
        
        command = [sys.executable, str(flask_script)]
        
        flask_env = {
            'FLASK_HOST': self.config['flask_host'],
            'FLASK_PORT': str(self.config['flask_port']),
            'FLASK_DEBUG': str(self.config['flask_debug']).lower()
        }
        
        def flask_health_check():
            url = f"http://{self.config['flask_host']}:{self.config['flask_port']}/"
            return self.process_manager.check_http_health(url)
        
        success = self.process_manager.add_process(
            'flask-server',
            command,
            cwd=str(self.project_root),
            env=flask_env,
            health_check=flask_health_check
        )
        
        if success:
            # Wait for Flask server to be ready
            logger.info("Waiting for Flask server to be ready...")
            if self.process_manager.wait_for_port(
                self.config['flask_host'], 
                self.config['flask_port'], 
                timeout=30
            ):
                logger.info("Flask server is ready")
                return True
            else:
                logger.error("Flask server failed to start within timeout")
                return False
        
        return False
    
    def start(self):
        """Start the complete NexusAI application"""
        logger.info("Starting NexusAI application...")
        
        # Validate environment
        if not self.validate_environment():
            logger.error("Environment validation failed")
            sys.exit(1)
        
        # Start MCP server first
        if not self.start_mcp_server():
            logger.error("Failed to start MCP server")
            sys.exit(1)
        
        # Start Flask server
        if not self.start_flask_server():
            logger.error("Failed to start Flask server")
            self.process_manager.shutdown()
            sys.exit(1)
        
        # Start health monitoring
        self.process_manager.start_health_monitoring()
        
        logger.info("NexusAI application started successfully!")
        logger.info(f"Dashboard available at: http://{self.config['flask_host']}:{self.config['flask_port']}")
        logger.info(f"MCP server running on: {self.config['mcp_host']}:{self.config['mcp_port']}")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            self.process_manager.shutdown()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start NexusAI application")
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Only validate environment, don't start services"
    )
    
    args = parser.parse_args()
    
    coordinator = NexusAICoordinator()
    
    if args.validate_only:
        if coordinator.validate_environment():
            print("Environment validation passed")
            sys.exit(0)
        else:
            print("Environment validation failed")
            sys.exit(1)
    else:
        coordinator.start()

if __name__ == "__main__":
    main()