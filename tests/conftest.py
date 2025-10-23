"""
Pytest configuration and shared fixtures for NexusAI testing suite.
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock

# Add backend to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini AI client for testing."""
    mock_client = Mock()
    mock_client.generate_content = AsyncMock()
    return mock_client

@pytest.fixture
def mock_socketio():
    """Mock SocketIO client for testing."""
    mock_socketio = Mock()
    mock_socketio.emit = AsyncMock()
    return mock_socketio

@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "id": "SIM-TEST123",
        "subject": "Test phishing email received",
        "status": "received",
        "created_at": "2024-01-15T10:30:00Z",
        "logs": []
    }

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    mock_client = AsyncMock()
    mock_client.call_tool = AsyncMock()
    mock_client.available_tools = ["log_action_for_ui", "analyze_email_for_iocs", "block_malicious_url", "search_and_destroy_email"]
    return mock_client