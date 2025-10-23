# NexusAI Setup and Execution Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn package manager
- Git (for cloning repository)
- 4GB RAM minimum (8GB recommended)
- Internet connection for initial setup

### Required API Keys
- Google Gemini API key (free tier available)
- Optional: Additional AI service keys for extended functionality

## Installation Steps

### 1. Clone and Navigate to Repository
```bash
git clone <repository-url>
cd nexusai-autonomous-operations
```

### 2. Backend Setup
```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build frontend for production
npm run build

# Return to root directory
cd ..
```

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your configuration
# Required variables:
# GEMINI_API_KEY=your_gemini_api_key_here
# MCP_SERVER_HOST=localhost
# MCP_SERVER_PORT=8001
# FLASK_HOST=localhost
# FLASK_PORT=5000
```

## Execution Instructions

### Method 1: Automated Startup (Recommended)
```bash
# Run the main application
python run_nexusai.py
```

This will:
- Start the MCP security tools server
- Launch the Flask web server with SocketIO
- Serve the Svelte frontend
- Display startup status and URLs

### Method 2: Manual Component Startup
```bash
# Terminal 1: Start MCP Server
python -m backend.tools.security_mcp_server

# Terminal 2: Start Flask Server
python -m backend.web.main
```

### Method 3: Using Batch Scripts (Windows)
```bash
# Start the complete system
run_nexusai.bat
```

## Accessing the Application

1. **Web Dashboard**: Open browser to `http://localhost:5000`
2. **Health Check**: Visit `http://localhost:5000/health` to verify system status
3. **MCP Server**: Running on `http://localhost:8001` (internal use)

## Demonstration Execution

### Pre-Demo Checklist
- [ ] All services started successfully
- [ ] Web dashboard loads without errors
- [ ] Environment variables configured
- [ ] Internet connection available for AI API calls
- [ ] Browser supports WebSocket connections

### Demo Steps
1. **Open Dashboard**: Navigate to `http://localhost:5000`
2. **Create Ticket**: Use one of the sample phishing subjects from `demo_scenarios.md`
3. **Watch Workflow**: Observe real-time agent execution and tool usage
4. **Review Results**: Check final resolution and logged actions
5. **Repeat**: Create additional tickets to show concurrent processing

### Key Demo Points to Highlight
- **Autonomous Operation**: No human intervention required
- **Real-time Visualization**: Live workflow updates and status changes
- **Multi-agent Coordination**: Master Agent → PhishGuard Agent handoff
- **Tool Integration**: MCP-based security tool execution
- **Professional UI**: Modern, responsive dashboard with animations

## Verification Steps

### System Health Check
```bash
# Run comprehensive health check
python scripts/health_check.py
```

### End-to-End Testing
```bash
# Run complete test suite
python scripts/run_tests.py
```

### Performance Validation
```bash
# Run performance optimization check
python scripts/optimize_performance.py
```

## Configuration Options

### Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `MCP_SERVER_HOST`: MCP server host (default: localhost)
- `MCP_SERVER_PORT`: MCP server port (default: 8001)
- `FLASK_HOST`: Flask server host (default: localhost)
- `FLASK_PORT`: Flask server port (default: 5000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEMO_MODE`: Enable demo optimizations (default: true)

### Customization Options
- Modify agent prompts in `backend/agents/`
- Adjust tool responses in `backend/tools/security_mcp_server.py`
- Customize UI styling in `frontend/src/components/`
- Configure workflow timing in `backend/workflow/ticket_processor.py`

## Shutdown Instructions

### Graceful Shutdown
- Press `Ctrl+C` in the terminal running `run_nexusai.py`
- All services will shut down automatically

### Manual Shutdown
- Stop each service individually with `Ctrl+C`
- Deactivate Python virtual environment: `deactivate`

## Next Steps

After successful setup and demonstration:
1. Review system logs for any issues
2. Explore code structure for customization
3. Consider production deployment requirements
4. Plan integration with existing IT infrastructure