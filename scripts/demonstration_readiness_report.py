#!/usr/bin/env python3
"""
NexusAI Demonstration Readiness Report
Comprehensive assessment of system readiness for demonstration.
"""

import json
import time
import sys
import os
from pathlib import Path
import psutil

class DemonstrationReadinessAssessment:
    """Comprehensive assessment for demonstration readiness."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.assessment_results = {}
        
    def assess_file_structure(self):
        """Assess project file structure completeness."""
        print("Assessing file structure...")
        
        critical_files = {
            'Backend Core': [
                'backend/agents/master_agent.py',
                'backend/agents/phishguard_agent.py',
                'backend/workflow/ticket_processor.py',
                'backend/web/main.py',
                'backend/web/routes.py'
            ],
            'Frontend': [
                'frontend/src/App.svelte',
                'frontend/src/components/TicketForm.svelte',
                'frontend/src/components/WorkflowCard.svelte',
                'frontend/package.json'
            ],
            'Configuration': [
                '.env',
                'requirements.txt',
                'README.md'
            ],
            'Tools & Scripts': [
                'backend/tools/security_mcp_server.py',
                'run_nexusai.py',
                'scripts/start_nexusai.py'
            ]
        }
        
        structure_results = {}
        
        for category, files in critical_files.items():
            category_results = {}
            for file_path in files:
                full_path = self.project_root / file_path
                exists = full_path.exists()
                category_results[file_path] = exists
                
                status = "✓" if exists else "✗"
                print(f"  {status} {file_path}")
                
            structure_results[category] = category_results
            
        self.assessment_results['file_structure'] = structure_results
        
        # Calculate completeness
        all_files = [file for files in critical_files.values() for file in files]
        existing_files = sum(1 for file in all_files if (self.project_root / file).exists())
        completeness = existing_files / len(all_files)
        
        print(f"File Structure Completeness: {completeness:.1%} ({existing_files}/{len(all_files)})")
        return completeness > 0.9
        
    def assess_frontend_build(self):
        """Assess frontend build status."""
        print("\nAssessing frontend build...")
        
        static_dir = self.project_root / 'backend' / 'web' / 'static'
        
        build_files = {
            'HTML': list(static_dir.glob('*.html')),
            'JavaScript': list(static_dir.glob('*.js')),
            'CSS': list(static_dir.glob('*.css'))
        }
        
        build_status = {}
        
        for file_type, files in build_files.items():
            has_files = len(files) > 0
            build_status[file_type] = {
                'present': has_files,
                'count': len(files),
                'files': [f.name for f in files]
            }
            
            status = "✓" if has_files else "✗"
            print(f"  {status} {file_type}: {len(files)} files")
            
        self.assessment_results['frontend_build'] = build_status
        
        # Frontend is ready if we have HTML, JS, and CSS
        frontend_ready = all(build_status[ft]['present'] for ft in ['HTML', 'JavaScript', 'CSS'])
        
        if frontend_ready:
            print("Frontend Build Status: READY")
        else:
            print("Frontend Build Status: NEEDS BUILD")
            
        return frontend_ready
        
    def assess_configuration(self):
        """Assess configuration completeness."""
        print("\nAssessing configuration...")
        
        env_file = self.project_root / '.env'
        config_status = {}
        
        if env_file.exists():
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
                
                for var in required_vars:
                    present = var in env_content
                    config_status[var] = present
                    
                    status = "✓" if present else "✗"
                    print(f"  {status} {var}")
                    
            except Exception as e:
                print(f"  ✗ Error reading .env: {e}")
                config_status['error'] = str(e)
        else:
            print("  ✗ .env file not found")
            config_status['env_file_exists'] = False
            
        self.assessment_results['configuration'] = config_status
        
        # Configuration is ready if all required vars are present
        config_ready = all(config_status.get(var, False) for var in [
            'GEMINI_API_KEY', 'SECRET_KEY', 'FLASK_HOST', 'FLASK_PORT'
        ])
        
        return config_ready
        
    def assess_demonstration_scenarios(self):
        """Assess demonstration scenario readiness."""
        print("\nAssessing demonstration scenarios...")
        
        demo_scenarios = [
            {
                'name': 'Phishing Email Detection',
                'ticket': 'URGENT: Suspicious email from CEO requesting wire transfer',
                'expected_classification': 'Phishing/Security',
                'expected_actions': ['analyze', 'block', 'remove', 'document']
            },
            {
                'name': 'Malware Remediation',
                'ticket': 'Malware detected in email attachment - immediate action required',
                'expected_classification': 'Phishing/Security',
                'expected_actions': ['quarantine', 'scan', 'remove', 'notify']
            },
            {
                'name': 'General IT Support',
                'ticket': 'Password reset request for user account',
                'expected_classification': 'General Inquiry',
                'expected_actions': ['route', 'assign', 'respond']
            }
        ]
        
        scenario_results = {}
        
        for scenario in demo_scenarios:
            # Test classification logic
            ticket_lower = scenario['ticket'].lower()
            security_keywords = ['suspicious', 'malware', 'phishing', 'security', 'urgent', 'ceo']
            
            if any(keyword in ticket_lower for keyword in security_keywords):
                predicted_classification = 'Phishing/Security'
            else:
                predicted_classification = 'General Inquiry'
                
            classification_correct = predicted_classification == scenario['expected_classification']
            
            scenario_results[scenario['name']] = {
                'ticket': scenario['ticket'],
                'expected_classification': scenario['expected_classification'],
                'predicted_classification': predicted_classification,
                'classification_correct': classification_correct,
                'expected_actions': scenario['expected_actions']
            }
            
            status = "✓" if classification_correct else "✗"
            print(f"  {status} {scenario['name']}: {predicted_classification}")
            
        self.assessment_results['demonstration_scenarios'] = scenario_results
        
        # All scenarios should classify correctly
        all_correct = all(result['classification_correct'] for result in scenario_results.values())
        return all_correct
        
    def assess_system_performance(self):
        """Assess system performance for demonstration."""
        print("\nAssessing system performance...")
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        performance_metrics = {
            'cpu_usage_percent': cpu_percent,
            'memory_usage_percent': memory.percent,
            'available_memory_gb': memory.available / (1024**3),
            'disk_usage_percent': disk.percent,
            'total_memory_gb': memory.total / (1024**3)
        }
        
        # Performance thresholds for smooth demonstration
        performance_ok = (
            cpu_percent < 80 and
            memory.percent < 85 and
            memory.available > 2 * (1024**3)  # At least 2GB available
        )
        
        print(f"  CPU Usage: {cpu_percent:.1f}%")
        print(f"  Memory Usage: {memory.percent:.1f}% ({performance_metrics['available_memory_gb']:.1f}GB available)")
        print(f"  Disk Usage: {disk.percent:.1f}%")
        
        status = "✓" if performance_ok else "⚠️"
        print(f"  {status} Performance: {'GOOD' if performance_ok else 'MARGINAL'}")
        
        self.assessment_results['system_performance'] = performance_metrics
        return performance_ok
        
    def assess_demonstration_readiness(self):
        """Assess overall demonstration readiness."""
        print("\nAssessing demonstration readiness...")
        
        # Key readiness factors
        readiness_factors = {
            'Core Files Present': self.assessment_results.get('file_structure_ready', False),
            'Frontend Built': self.assessment_results.get('frontend_ready', False),
            'Configuration Complete': self.assessment_results.get('configuration_ready', False),
            'Demo Scenarios Work': self.assessment_results.get('scenarios_ready', False),
            'System Performance OK': self.assessment_results.get('performance_ready', False)
        }
        
        # Calculate readiness score
        ready_count = sum(1 for ready in readiness_factors.values() if ready)
        total_factors = len(readiness_factors)
        readiness_score = ready_count / total_factors
        
        print("Readiness Factors:")
        for factor, ready in readiness_factors.items():
            status = "✓" if ready else "✗"
            print(f"  {status} {factor}")
            
        print(f"\nReadiness Score: {readiness_score:.1%} ({ready_count}/{total_factors})")
        
        # Determine overall readiness level
        if readiness_score >= 0.8:
            readiness_level = "READY FOR DEMONSTRATION"
            readiness_color = "🟢"
        elif readiness_score >= 0.6:
            readiness_level = "MOSTLY READY - MINOR ISSUES"
            readiness_color = "🟡"
        else:
            readiness_level = "NEEDS ATTENTION"
            readiness_color = "🔴"
            
        print(f"\n{readiness_color} Overall Status: {readiness_level}")
        
        self.assessment_results['overall_readiness'] = {
            'factors': readiness_factors,
            'score': readiness_score,
            'level': readiness_level,
            'ready_for_demo': readiness_score >= 0.8
        }
        
        return readiness_score >= 0.8
        
    def generate_recommendations(self):
        """Generate recommendations for improving demonstration readiness."""
        print("\nGenerating recommendations...")
        
        recommendations = []
        
        # Check each assessment area
        if not self.assessment_results.get('file_structure_ready', True):
            recommendations.append("Complete missing core files before demonstration")
            
        if not self.assessment_results.get('frontend_ready', True):
            recommendations.append("Build frontend: cd frontend && npm run build")
            
        if not self.assessment_results.get('configuration_ready', True):
            recommendations.append("Complete .env configuration with all required variables")
            
        if not self.assessment_results.get('scenarios_ready', True):
            recommendations.append("Review and fix demonstration scenario classification logic")
            
        if not self.assessment_results.get('performance_ready', True):
            recommendations.append("Close unnecessary applications to improve system performance")
            
        # Add positive recommendations
        if self.assessment_results.get('overall_readiness', {}).get('ready_for_demo', False):
            recommendations.extend([
                "System is ready for demonstration!",
                "Test the complete workflow with sample tickets",
                "Prepare demonstration script with key scenarios",
                "Have backup plans for any technical issues"
            ])
        else:
            recommendations.extend([
                "Focus on critical issues first (file structure, configuration)",
                "Test individual components before full system test",
                "Consider demo mode if external dependencies are unavailable"
            ])
            
        self.assessment_results['recommendations'] = recommendations
        
        print("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
            
        return recommendations
        
    def run_complete_assessment(self):
        """Run complete demonstration readiness assessment."""
        print("NexusAI Demonstration Readiness Assessment")
        print("=" * 50)
        
        # Run all assessments
        assessments = [
            ('file_structure_ready', self.assess_file_structure),
            ('frontend_ready', self.assess_frontend_build),
            ('configuration_ready', self.assess_configuration),
            ('scenarios_ready', self.assess_demonstration_scenarios),
            ('performance_ready', self.assess_system_performance)
        ]
        
        for key, assessment_func in assessments:
            try:
                result = assessment_func()
                self.assessment_results[key] = result
            except Exception as e:
                print(f"Assessment error: {e}")
                self.assessment_results[key] = False
                
        # Overall readiness assessment
        overall_ready = self.assess_demonstration_readiness()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Create final report
        final_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'assessment_results': self.assessment_results,
            'summary': {
                'ready_for_demonstration': overall_ready,
                'readiness_level': self.assessment_results.get('overall_readiness', {}).get('level', 'UNKNOWN'),
                'readiness_score': self.assessment_results.get('overall_readiness', {}).get('score', 0)
            }
        }
        
        # Save report
        report_file = self.project_root / 'demonstration_readiness_report.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2)
            print(f"\nDetailed report saved to: {report_file}")
        except Exception as e:
            print(f"Warning: Could not save report: {e}")
            
        return overall_ready


def main():
    """Main assessment function."""
    assessor = DemonstrationReadinessAssessment()
    ready = assessor.run_complete_assessment()
    
    print(f"\n{'='*50}")
    if ready:
        print("🎉 NexusAI is READY for demonstration!")
    else:
        print("⚠️  NexusAI needs attention before demonstration")
        
    return ready


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)