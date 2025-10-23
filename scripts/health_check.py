#!/usr/bin/env python3
"""
NexusAI Health Check Script
Validates that all services are running and healthy
"""

import os
import sys
import time
import socket
import requests
from pathlib import Path
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Performs health checks on NexusAI services"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config()
        self.checks: List[Dict[str, Any]] = []
    
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
            'flask_port': int(os.getenv('FLASK_PORT', '5000'))
        }
    
    def check_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if a port is open and accepting connections"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, ConnectionRefusedError, OSError):
            return False
    
    def check_http_endpoint(self, url: str, timeout: int = 5) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        try:
            response = requests.get(url, timeout=timeout)
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        required_vars = ['GEMINI_API_KEY', 'SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return {
            'success': len(missing_vars) == 0,
            'missing_vars': missing_vars
        }
    
    def check_python_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        required_modules = [
            'flask',
            'flask_socketio',
            'google.generativeai',
            'mcp',
            'dotenv'
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        return {
            'success': len(missing_modules) == 0,
            'missing_modules': missing_modules
        }
    
    def check_frontend_build(self) -> Dict[str, Any]:
        """Check if frontend is built"""
        static_dir = self.project_root / 'backend' / 'web' / 'static'
        index_file = static_dir / 'index.html'
        
        return {
            'success': index_file.exists(),
            'static_dir_exists': static_dir.exists(),
            'index_file_exists': index_file.exists()
        }
    
    def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks"""
        results = {}
        
        logger.info("Running health checks...")
        
        # Environment variables check
        logger.info("Checking environment variables...")
        results['environment'] = self.check_environment_variables()
        
        # Python dependencies check
        logger.info("Checking Python dependencies...")
        results['dependencies'] = self.check_python_dependencies()
        
        # Frontend build check
        logger.info("Checking frontend build...")
        results['frontend'] = self.check_frontend_build()
        
        # MCP server port check
        logger.info(f"Checking MCP server port {self.config['mcp_host']}:{self.config['mcp_port']}...")
        results['mcp_port'] = {
            'success': self.check_port_open(self.config['mcp_host'], self.config['mcp_port'])
        }
        
        # Flask server check
        logger.info(f"Checking Flask server {self.config['flask_host']}:{self.config['flask_port']}...")
        flask_url = f"http://{self.config['flask_host']}:{self.config['flask_port']}/"
        results['flask_server'] = self.check_http_endpoint(flask_url)
        
        return results
    
    def print_results(self, results: Dict[str, Dict[str, Any]]) -> bool:
        """Print health check results"""
        all_passed = True
        
        print("\n" + "="*60)
        print("NexusAI Health Check Results")
        print("="*60)
        
        for check_name, result in results.items():
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            print(f"\n{check_name.upper()}: {status}")
            
            if not result['success']:
                all_passed = False
                
                if 'missing_vars' in result and result['missing_vars']:
                    print(f"  Missing environment variables: {', '.join(result['missing_vars'])}")
                
                if 'missing_modules' in result and result['missing_modules']:
                    print(f"  Missing Python modules: {', '.join(result['missing_modules'])}")
                
                if 'error' in result:
                    print(f"  Error: {result['error']}")
                
                if check_name == 'frontend' and not result['success']:
                    print("  Frontend not built. Run: python scripts/build_frontend.py")
            
            else:
                if 'status_code' in result:
                    print(f"  HTTP Status: {result['status_code']}")
                if 'response_time' in result:
                    print(f"  Response Time: {result['response_time']:.3f}s")
        
        print("\n" + "="*60)
        
        if all_passed:
            print("✓ All health checks passed! NexusAI is ready.")
        else:
            print("✗ Some health checks failed. Please address the issues above.")
        
        print("="*60)
        
        return all_passed

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NexusAI Health Check")
    parser.add_argument(
        "--wait", 
        type=int, 
        default=0,
        help="Wait for services to be ready (timeout in seconds)"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Only show final result"
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    checker = HealthChecker()
    
    if args.wait > 0:
        logger.info(f"Waiting up to {args.wait} seconds for services to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < args.wait:
            results = checker.run_all_checks()
            
            # Check if critical services are ready
            if (results.get('mcp_port', {}).get('success', False) and 
                results.get('flask_server', {}).get('success', False)):
                logger.info("Services are ready!")
                break
            
            time.sleep(2)
        else:
            logger.warning("Timeout waiting for services to be ready")
    
    # Run final health check
    results = checker.run_all_checks()
    all_passed = checker.print_results(results)
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()