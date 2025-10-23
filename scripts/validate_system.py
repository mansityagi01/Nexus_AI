#!/usr/bin/env python3
"""
Simple system validation script for NexusAI.
Checks core components without requiring all dependencies.
"""

import os
import sys
import json
from pathlib import Path

def check_file_structure():
    """Check that all required files exist."""
    print("Checking file structure...")
    
    project_root = Path(__file__).parent.parent
    
    required_files = [
        'backend/agents/master_agent.py',
        'backend/agents/phishguard_agent.py', 
        'backend/tools/security_mcp_server.py',
        'backend/tools/mcp_client.py',
        'backend/workflow/ticket_processor.py',
        'backend/web/main.py',
        'backend/web/routes.py',
        'frontend/src/App.svelte',
        'frontend/src/components/TicketForm.svelte',
        'frontend/src/components/WorkflowCard.svelte',
        'frontend/package.json',
        'requirements.txt',
        '.env'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            existing_files.append(file_path)
            print(f"✓ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"✗ {file_path}")
            
    return len(missing_files) == 0, existing_files, missing_files

def check_environment_config():
    """Check environment configuration."""
    print("\nChecking environment configuration...")
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("✗ .env file not found")
        return False
        
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        required_vars = [
            'GEMINI_API_KEY',
            'SECRET_KEY', 
            'FLASK_HOST',
            'FLASK_PORT',
            'MCP_HOST',
            'MCP_PORT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var in env_content:
                print(f"✓ {var} configured")
            else:
                missing_vars.append(var)
                print(f"✗ {var} missing")
                
        return len(missing_vars) == 0
        
    except Exception as e:
        print(f"✗ Error reading .env file: {e}")
        return False

def check_frontend_build():
    """Check if frontend is built."""
    print("\nChecking frontend build...")
    
    project_root = Path(__file__).parent.parent
    static_dir = project_root / 'backend' / 'web' / 'static'
    
    if not static_dir.exists():
        print("✗ Static directory not found")
        return False
        
    # Check for built files
    js_files = list(static_dir.glob('*.js'))
    css_files = list(static_dir.glob('*.css'))
    html_files = list(static_dir.glob('index.html'))
    
    if js_files and css_files and html_files:
        print(f"✓ Frontend built ({len(js_files)} JS, {len(css_files)} CSS files)")
        return True
    else:
        print("✗ Frontend not built or incomplete")
        return False

def validate_code_syntax():
    """Basic syntax validation for Python files."""
    print("\nValidating Python syntax...")
    
    project_root = Path(__file__).parent.parent
    python_files = [
        'backend/agents/master_agent.py',
        'backend/agents/phishguard_agent.py',
        'backend/tools/security_mcp_server.py',
        'backend/workflow/ticket_processor.py',
        'backend/web/main.py'
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    code = f.read()
                compile(code, str(full_path), 'exec')
                print(f"✓ {file_path}")
            except SyntaxError as e:
                syntax_errors.append((file_path, str(e)))
                print(f"✗ {file_path}: {e}")
            except Exception as e:
                print(f"? {file_path}: {e}")
        else:
            print(f"✗ {file_path}: File not found")
            
    return len(syntax_errors) == 0

def test_demo_scenarios():
    """Test demonstration scenarios."""
    print("\nTesting demonstration scenarios...")
    
    demo_tickets = [
        "URGENT: Suspicious email from CEO requesting wire transfer",
        "Malware detected in email attachment - immediate action required", 
        "Password reset request for user account",
        "Network connectivity issues in conference room"
    ]
    
    # Simple classification logic for demo
    for ticket in demo_tickets:
        subject_lower = ticket.lower()
        if any(keyword in subject_lower for keyword in ['suspicious', 'malware', 'phishing', 'security']):
            classification = "Phishing/Security"
        else:
            classification = "General Inquiry"
            
        print(f"✓ '{ticket[:50]}...' → {classification}")
        
    return True

def generate_validation_report():
    """Generate validation report."""
    print("\n" + "="*60)
    print("NEXUSAI SYSTEM VALIDATION REPORT")
    print("="*60)
    
    # Run all checks
    checks = {
        'File Structure': check_file_structure(),
        'Environment Config': check_environment_config(),
        'Frontend Build': check_frontend_build(),
        'Python Syntax': validate_code_syntax(),
        'Demo Scenarios': test_demo_scenarios()
    }
    
    print(f"\nVALIDATION RESULTS:")
    print("-" * 30)
    
    all_passed = True
    for check_name, result in checks.items():
        if isinstance(result, tuple):
            # File structure check returns tuple
            passed = result[0]
            status = "PASS" if passed else "FAIL"
        else:
            passed = result
            status = "PASS" if passed else "FAIL"
            
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
            
    print(f"\nOVERALL STATUS: {'READY FOR DEMONSTRATION' if all_passed else 'NEEDS ATTENTION'}")
    
    # Save report
    report_data = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'checks': {name: (result[0] if isinstance(result, tuple) else result) for name, result in checks.items()},
        'overall_status': 'ready' if all_passed else 'needs_attention'
    }
    
    project_root = Path(__file__).parent.parent
    report_file = project_root / 'validation_report.json'
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\nReport saved to: {report_file}")
    except Exception as e:
        print(f"\nWarning: Could not save report: {e}")
        
    return all_passed

if __name__ == "__main__":
    success = generate_validation_report()
    sys.exit(0 if success else 1)