# NexusAI Testing Suite

This directory contains the comprehensive testing suite for the NexusAI autonomous IT operations platform.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and shared fixtures
├── test_health_check.py     # Basic health checks and infrastructure tests
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for component interactions
└── frontend/                # Frontend component and UI tests
```

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test categories
python scripts/run_tests.py --type health
python scripts/run_tests.py --type unit
python scripts/run_tests.py --type integration
python scripts/run_tests.py --type frontend

# Verbose output
python scripts/run_tests.py --verbose
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_health_check.py -v

# Run tests with specific markers
pytest -m unit -v
pytest -m integration -v
pytest -m frontend -v
```

## Test Configuration

The testing suite is configured via:
- `pytest.ini` - Main pytest configuration
- `tests/conftest.py` - Shared fixtures and test setup

## Available Fixtures

- `mock_gemini_client` - Mock Gemini AI client for testing
- `mock_socketio` - Mock SocketIO client for testing  
- `sample_ticket_data` - Sample ticket data for testing
- `mock_mcp_client` - Mock MCP client for testing
- `event_loop` - Async event loop for async tests

## Test Categories

### Health Check Tests
Basic infrastructure tests to verify the testing environment is working correctly.

### Unit Tests (Optional)
Tests for individual components in isolation:
- Agent classification logic
- Tool functionality
- Data validation
- Error handling

### Integration Tests (Optional)  
Tests for component interactions:
- End-to-end workflows
- WebSocket communication
- Agent coordination
- Error scenarios

### Frontend Tests (Optional)
Tests for UI components and functionality:
- Component behavior
- State management
- WebSocket integration
- User interactions

## Test Markers

- `unit` - Unit tests
- `integration` - Integration tests  
- `frontend` - Frontend component tests
- `slow` - Slow running tests

Use markers to run specific test categories:
```bash
pytest -m unit
pytest -m "not slow"
```

## Writing Tests

### Unit Test Example
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.unit
def test_master_agent_classification(mock_gemini_client):
    # Test implementation
    pass

@pytest.mark.asyncio
async def test_async_functionality():
    # Async test implementation
    pass
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ticket_workflow(mock_socketio, sample_ticket_data):
    # Integration test implementation
    pass
```

## Notes

- All optional test implementations are marked with `*` in the task list
- The testing infrastructure is set up but actual test implementations are optional
- Tests use mocking to avoid external dependencies during testing
- Async tests are supported via pytest-asyncio