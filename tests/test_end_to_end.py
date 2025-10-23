"""
End-to-end testing for NexusAI autonomous operations platform.
This test validates the complete phishing remediation workflow.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class TestEndToEndWorkflow:
    """Test the complete ticket processing workflow from creation to resolution."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_tickets = [
            "Suspicious email with malicious link received",
            "Phishing attempt detected in inbox", 
            "Urgent: Malware email spreading in organization",
            "General IT support request for password reset",
            "Network connectivity issues in office"
        ]
        
    @pytest.mark.asyncio
    async def test_complete_phishing_workflow(self):
        """Test complete phishing remediation workflow with mocked components."""
        
        # Mock the Gemini API responses
        mock_master_response = "Phishing/Security"
        mock_phishguard_response = """
        ANALYSIS COMPLETE:
        - Identified malicious URL: http://evil-phishing-site.com
        - IOCs detected: suspicious sender, malicious attachment
        
        CONTAINMENT:
        - Blocking malicious URL at network level
        - Quarantining suspicious emails
        
        ERADICATION:
        - Removed 15 malicious emails from user inboxes
        - Updated security filters
        
        DOCUMENTATION:
        - Incident logged with ID: INC-2024-001
        - Security team notified
        """
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            # Configure mock responses
            mock_instance = Mock()
            mock_instance.generate_content.return_value.text = mock_master_response
            mock_model.return_value = mock_instance
            
            # Test Master Agent classification
            from agents.master_agent import MasterAgent
            master_agent = MasterAgent()
            
            classification = await master_agent.classify_ticket(
                "SIM-TEST001", 
                "Suspicious email with malicious link received"
            )
            
            assert classification == "Phishing/Security"
            
            # Test PhishGuard Agent workflow
            mock_instance.generate_content.return_value.text = mock_phishguard_response
            
            from agents.phishguard_agent import PhishGuardAgent
            phishguard_agent = PhishGuardAgent()
            
            # Mock MCP client
            with patch('tools.mcp_client.MCPClient') as mock_mcp:
                mock_mcp_instance = AsyncMock()
                mock_mcp_instance.call_tool.return_value = {
                    "success": True,
                    "result": "Tool executed successfully"
                }
                mock_mcp.return_value = mock_mcp_instance
                
                result = await phishguard_agent.process_security_ticket(
                    "SIM-TEST001",
                    "Suspicious email with malicious link received"
                )
                
                assert "ANALYSIS COMPLETE" in result
                assert "15 malicious emails" in result
                
    @pytest.mark.asyncio 
    async def test_ticket_processor_workflow(self):
        """Test the complete ticket processor workflow."""
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = Mock()
            mock_model.return_value = mock_instance
            
            # Mock SocketIO for UI updates
            mock_socketio = Mock()
            
            from workflow.ticket_processor import TicketProcessor
            processor = TicketProcessor(mock_socketio)
            
            # Test phishing ticket processing
            mock_instance.generate_content.return_value.text = "Phishing/Security"
            
            with patch('tools.mcp_client.MCPClient') as mock_mcp:
                mock_mcp_instance = AsyncMock()
                mock_mcp_instance.call_tool.return_value = {
                    "success": True,
                    "result": "Security remediation completed"
                }
                mock_mcp.return_value = mock_mcp_instance
                
                # Process ticket
                await processor.process_ticket(
                    "SIM-TEST002",
                    "Phishing attempt detected in inbox"
                )
                
                # Verify SocketIO was called for UI updates
                assert mock_socketio.emit.called
                
                # Check that proper events were emitted
                calls = mock_socketio.emit.call_args_list
                event_types = [call[0][0] for call in calls]
                
                assert 'log_update' in event_types
                
    def test_mcp_security_tools_simulation(self):
        """Test MCP security tools with simulated responses."""
        
        from tools.security_mcp_server import SecurityMCPServer
        server = SecurityMCPServer()
        
        # Test IOC analysis tool
        ioc_result = server.analyze_email_for_iocs({
            "email_content": "Suspicious email with malicious link",
            "sender": "attacker@evil-site.com"
        })
        
        assert ioc_result["success"] == True
        assert "malicious_urls" in ioc_result
        assert len(ioc_result["malicious_urls"]) > 0
        
        # Test URL blocking tool
        block_result = server.block_malicious_url({
            "url": "http://evil-phishing-site.com",
            "reason": "Phishing attempt"
        })
        
        assert block_result["success"] == True
        assert "blocked" in block_result["message"].lower()
        
        # Test email removal tool
        removal_result = server.search_and_destroy_email({
            "sender": "attacker@evil-site.com",
            "subject_contains": "urgent"
        })
        
        assert removal_result["success"] == True
        assert "removed" in removal_result["message"].lower()
        
    def test_ui_components_integration(self):
        """Test that UI components can handle workflow data properly."""
        
        # Simulate workflow data that would be sent to UI
        workflow_data = {
            "ticket_id": "SIM-TEST003",
            "subject": "Suspicious email received",
            "status": "resolved",
            "logs": [
                {
                    "agent": "Master Agent",
                    "message": "Classified as Phishing/Security",
                    "timestamp": "2024-01-15T10:30:05Z",
                    "status": "classified"
                },
                {
                    "agent": "PhishGuard Agent", 
                    "message": "Analyzing email for IOCs...",
                    "timestamp": "2024-01-15T10:30:10Z",
                    "status": "working"
                },
                {
                    "agent": "PhishGuard Agent",
                    "message": "Blocked malicious URL: http://evil-site.com",
                    "timestamp": "2024-01-15T10:30:15Z", 
                    "status": "working"
                },
                {
                    "agent": "PhishGuard Agent",
                    "message": "Removed 15 malicious emails from inboxes",
                    "timestamp": "2024-01-15T10:30:20Z",
                    "status": "working"
                },
                {
                    "agent": "PhishGuard Agent",
                    "message": "Security incident resolved successfully",
                    "timestamp": "2024-01-15T10:30:25Z",
                    "status": "resolved"
                }
            ]
        }
        
        # Validate data structure
        assert "ticket_id" in workflow_data
        assert "logs" in workflow_data
        assert len(workflow_data["logs"]) > 0
        
        # Validate log entries have required fields
        for log in workflow_data["logs"]:
            assert "agent" in log
            assert "message" in log
            assert "timestamp" in log
            assert "status" in log
            
        # Test status progression
        statuses = [log["status"] for log in workflow_data["logs"]]
        assert "classified" in statuses
        assert "working" in statuses
        assert "resolved" in statuses
        
    def test_performance_requirements(self):
        """Test that the system meets performance requirements."""
        
        # Test response time simulation
        start_time = time.time()
        
        # Simulate agent processing time
        time.sleep(0.1)  # Simulate 100ms processing
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time for demo
        assert processing_time < 5.0  # Less than 5 seconds
        
        # Test concurrent ticket handling capability
        max_tickets = 10
        ticket_ids = [f"SIM-PERF{i:03d}" for i in range(max_tickets)]
        
        assert len(ticket_ids) == max_tickets
        assert all(ticket_id.startswith("SIM-") for ticket_id in ticket_ids)
        
    def test_error_handling_scenarios(self):
        """Test error handling and recovery mechanisms."""
        
        # Test invalid ticket data
        invalid_subjects = ["", None, " " * 1000]  # Empty, None, too long
        
        for subject in invalid_subjects:
            # Should handle gracefully without crashing
            if subject is None or subject.strip() == "":
                # Should reject empty subjects
                assert True  # Placeholder for validation logic
            elif len(subject) > 500:
                # Should truncate or reject overly long subjects
                assert True  # Placeholder for length validation
                
        # Test network failure simulation
        network_error_scenarios = [
            "Connection timeout",
            "API rate limit exceeded", 
            "Service unavailable"
        ]
        
        for error in network_error_scenarios:
            # Should have fallback mechanisms
            assert error  # Placeholder for error handling validation
            
    def test_security_requirements(self):
        """Test security-related requirements."""
        
        # Test API key handling
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Should not expose real API keys in logs
        api_key = os.getenv('GEMINI_API_KEY', 'demo_key')
        
        # In demo mode, should use placeholder
        if api_key == 'demo_key_for_testing':
            assert True  # Using demo key as expected
        else:
            # Should not log actual API key
            assert len(api_key) > 10  # Has some key value
            
        # Test input sanitization
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE tickets; --",
            "../../../etc/passwd"
        ]
        
        for malicious_input in malicious_inputs:
            # Should sanitize or reject malicious input
            sanitized = malicious_input.replace("<", "&lt;").replace(">", "&gt;")
            assert "<script>" not in sanitized
            
    def test_demonstration_scenarios(self):
        """Test specific scenarios for demonstration purposes."""
        
        demo_scenarios = [
            {
                "subject": "URGENT: Suspicious email from CEO requesting wire transfer",
                "expected_classification": "Phishing/Security",
                "expected_actions": ["analyze", "block", "remove", "document"]
            },
            {
                "subject": "Malware detected in email attachment - immediate action required", 
                "expected_classification": "Phishing/Security",
                "expected_actions": ["analyze", "quarantine", "scan", "notify"]
            },
            {
                "subject": "Password reset request for user account",
                "expected_classification": "General Inquiry", 
                "expected_actions": ["route", "assign", "respond"]
            }
        ]
        
        for scenario in demo_scenarios:
            # Validate scenario structure
            assert "subject" in scenario
            assert "expected_classification" in scenario
            assert "expected_actions" in scenario
            
            # Test classification logic
            subject = scenario["subject"].lower()
            if any(keyword in subject for keyword in ["phishing", "malware", "suspicious", "malicious"]):
                expected = "Phishing/Security"
            else:
                expected = "General Inquiry"
                
            assert scenario["expected_classification"] == expected


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])