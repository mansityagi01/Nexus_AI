#!/usr/bin/env python3
"""
Performance optimization script for NexusAI demonstration.
Ensures smooth operation and optimal user experience.
"""

import os
import sys
import time
import json
import psutil
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Optimizes system performance for demonstration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.optimization_results = {}
        
    def check_system_resources(self):
        """Check available system resources."""
        logger.info("Checking system resources...")
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.optimization_results['cpu_usage'] = cpu_percent
        
        # Check memory usage
        memory = psutil.virtual_memory()
        self.optimization_results['memory_usage'] = memory.percent
        self.optimization_results['available_memory'] = memory.available / (1024**3)  # GB
        
        # Check disk usage
        disk = psutil.disk_usage('/')
        self.optimization_results['disk_usage'] = disk.percent
        
        logger.info(f"CPU Usage: {cpu_percent}%")
        logger.info(f"Memory Usage: {memory.percent}% ({self.optimization_results['available_memory']:.1f}GB available)")
        logger.info(f"Disk Usage: {disk.percent}%")
        
        return self.optimization_results
        
    def optimize_frontend_build(self):
        """Optimize frontend build for performance."""
        logger.info("Optimizing frontend build...")
        
        frontend_dir = self.project_root / 'frontend'
        static_dir = self.project_root / 'backend' / 'web' / 'static'
        
        # Check if build exists and is recent
        build_files = list(static_dir.glob('*.js')) + list(static_dir.glob('*.css'))
        
        if build_files:
            # Check build age
            newest_build = max(build_files, key=lambda f: f.stat().st_mtime)
            build_age = time.time() - newest_build.stat().st_mtime
            
            if build_age < 3600:  # Less than 1 hour old
                logger.info("Frontend build is recent, skipping rebuild")
                self.optimization_results['frontend_build'] = 'current'
                return True
                
        # Build frontend if needed
        try:
            import subprocess
            
            # Change to frontend directory
            os.chdir(frontend_dir)
            
            # Run npm build
            result = subprocess.run(['npm', 'run', 'build'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("Frontend build completed successfully")
                self.optimization_results['frontend_build'] = 'success'
                return True
            else:
                logger.warning(f"Frontend build failed: {result.stderr}")
                self.optimization_results['frontend_build'] = 'failed'
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Frontend build timed out")
            self.optimization_results['frontend_build'] = 'timeout'
            return False
        except Exception as e:
            logger.error(f"Frontend build error: {e}")
            self.optimization_results['frontend_build'] = 'error'
            return False
        finally:
            # Return to project root
            os.chdir(self.project_root)
            
    def optimize_python_imports(self):
        """Pre-import heavy Python modules to reduce startup time."""
        logger.info("Pre-loading Python modules...")
        
        start_time = time.time()
        
        try:
            # Import heavy modules
            import flask
            import flask_socketio
            import asyncio
            import json
            import requests
            
            # Try to import AI modules (may fail in demo mode)
            try:
                import google.generativeai as genai
                self.optimization_results['ai_modules'] = 'available'
            except ImportError:
                logger.warning("AI modules not available - using demo mode")
                self.optimization_results['ai_modules'] = 'demo_mode'
                
            # Try to import MCP modules
            try:
                import mcp
                self.optimization_results['mcp_modules'] = 'available'
            except ImportError:
                logger.warning("MCP modules not available - using simulation")
                self.optimization_results['mcp_modules'] = 'simulation'
                
            load_time = time.time() - start_time
            logger.info(f"Module pre-loading completed in {load_time:.2f}s")
            self.optimization_results['module_load_time'] = load_time
            
            return True
            
        except Exception as e:
            logger.error(f"Module pre-loading failed: {e}")
            self.optimization_results['module_load_time'] = 'failed'
            return False
            
    def optimize_demo_data(self):
        """Prepare optimized demo data for smooth demonstration."""
        logger.info("Preparing demo data...")
        
        # Create demo ticket subjects for quick testing
        demo_tickets = [
            "URGENT: Suspicious email from CEO requesting wire transfer",
            "Malware detected in email attachment - immediate action required",
            "Phishing attempt: fake Microsoft login page detected",
            "Security alert: unusual login activity detected",
            "Password reset request for user account",
            "Network connectivity issues in conference room",
            "Printer not working in accounting department"
        ]
        
        # Pre-generate expected responses for demo mode
        demo_responses = {
            "master_agent_responses": {
                "phishing": "Phishing/Security",
                "malware": "Phishing/Security", 
                "security": "Phishing/Security",
                "password": "General Inquiry",
                "network": "General Inquiry",
                "printer": "General Inquiry"
            },
            "phishguard_responses": {
                "analysis": "IOCs detected: malicious URLs, suspicious attachments",
                "containment": "Blocking malicious domains at network level",
                "eradication": "Removed 15 malicious emails from user inboxes",
                "documentation": "Incident logged with security team notification"
            }
        }
        
        # Save demo data for quick access
        demo_data_file = self.project_root / 'backend' / 'demo_data.json'
        
        try:
            with open(demo_data_file, 'w') as f:
                json.dump({
                    'tickets': demo_tickets,
                    'responses': demo_responses
                }, f, indent=2)
                
            logger.info(f"Demo data saved to {demo_data_file}")
            self.optimization_results['demo_data'] = 'prepared'
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare demo data: {e}")
            self.optimization_results['demo_data'] = 'failed'
            return False
            
    def validate_demonstration_readiness(self):
        """Validate that system is ready for demonstration."""
        logger.info("Validating demonstration readiness...")
        
        checks = {
            'environment_file': self.project_root / '.env',
            'frontend_build': self.project_root / 'backend' / 'web' / 'static' / 'index.html',
            'backend_modules': self.project_root / 'backend' / 'agents' / 'master_agent.py',
            'mcp_server': self.project_root / 'backend' / 'tools' / 'security_mcp_server.py'
        }
        
        validation_results = {}
        
        for check_name, file_path in checks.items():
            if file_path.exists():
                validation_results[check_name] = 'ready'
                logger.info(f"✓ {check_name}: Ready")
            else:
                validation_results[check_name] = 'missing'
                logger.warning(f"✗ {check_name}: Missing - {file_path}")
                
        self.optimization_results['validation'] = validation_results
        
        # Check if all critical components are ready
        critical_components = ['environment_file', 'backend_modules', 'mcp_server']
        all_ready = all(validation_results.get(comp) == 'ready' for comp in critical_components)
        
        if all_ready:
            logger.info("✓ System is ready for demonstration")
            return True
        else:
            logger.warning("✗ System has missing components")
            return False
            
    def generate_performance_report(self):
        """Generate a performance optimization report."""
        logger.info("Generating performance report...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_resources': {
                'cpu_usage': self.optimization_results.get('cpu_usage', 'unknown'),
                'memory_usage': self.optimization_results.get('memory_usage', 'unknown'),
                'available_memory_gb': self.optimization_results.get('available_memory', 'unknown')
            },
            'optimization_status': {
                'frontend_build': self.optimization_results.get('frontend_build', 'unknown'),
                'module_loading': self.optimization_results.get('module_load_time', 'unknown'),
                'demo_data': self.optimization_results.get('demo_data', 'unknown'),
                'ai_modules': self.optimization_results.get('ai_modules', 'unknown'),
                'mcp_modules': self.optimization_results.get('mcp_modules', 'unknown')
            },
            'validation_results': self.optimization_results.get('validation', {}),
            'recommendations': []
        }
        
        # Add recommendations based on results
        if self.optimization_results.get('cpu_usage', 0) > 80:
            report['recommendations'].append("High CPU usage detected - close unnecessary applications")
            
        if self.optimization_results.get('memory_usage', 0) > 85:
            report['recommendations'].append("High memory usage - consider restarting system")
            
        if self.optimization_results.get('frontend_build') != 'success':
            report['recommendations'].append("Frontend build issues - run manual build")
            
        if not report['recommendations']:
            report['recommendations'].append("System is optimized for demonstration")
            
        return report
        
    def run_full_optimization(self):
        """Run complete optimization process."""
        logger.info("Starting full performance optimization...")
        
        start_time = time.time()
        
        # Run all optimization steps
        steps = [
            ('System Resources', self.check_system_resources),
            ('Python Modules', self.optimize_python_imports),
            ('Demo Data', self.optimize_demo_data),
            ('Frontend Build', self.optimize_frontend_build),
            ('Validation', self.validate_demonstration_readiness)
        ]
        
        results = {}
        
        for step_name, step_function in steps:
            logger.info(f"Running: {step_name}")
            try:
                results[step_name] = step_function()
            except Exception as e:
                logger.error(f"Failed: {step_name} - {e}")
                results[step_name] = False
                
        total_time = time.time() - start_time
        logger.info(f"Optimization completed in {total_time:.2f}s")
        
        # Generate final report
        report = self.generate_performance_report()
        
        return results, report


def main():
    """Main optimization function."""
    print("NexusAI Performance Optimization")
    print("=" * 40)
    
    optimizer = PerformanceOptimizer()
    
    try:
        results, report = optimizer.run_full_optimization()
        
        print("\nOptimization Results:")
        print("-" * 20)
        
        for step, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{step}: {status}")
            
        print(f"\nSystem Status: {'READY' if all(results.values()) else 'NEEDS ATTENTION'}")
        
        # Save report
        report_file = Path(__file__).parent.parent / 'optimization_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        return all(results.values())
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)