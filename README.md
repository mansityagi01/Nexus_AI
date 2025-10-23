# NexusAI - Autonomous IT Operations Platform

## Overview

NexusAI represents the future of IT operations through a comprehensive multi-agent AI architecture. Our grand vision encompasses a complete ecosystem where the Master Agent intelligently delegates tasks to a full suite of specialist agents: **PhishGuard** (security threats), **AccessControl** (identity management), **PatchMaster** (system updates), and **InfraHeal** (infrastructure monitoring).

**This hackathon prototype demonstrates the power of this architecture** by implementing two key components as proof-of-concept:
- ✅ **PhishGuard Agent**: Autonomous security threat response specialist
- ✅ **General Inquiry Agent**: Handles all non-security IT requests
- 🔮 **Future Agents**: AccessControl, PatchMaster, InfraHeal (roadmap)

## Features

### 🎯 Current Prototype Capabilities
- **Intelligent Ticket Triage**: Master Agent (Google Gemini AI) classifies and routes all tickets
- **Autonomous Security Response**: PhishGuard Agent handles phishing threats with zero human intervention
- **General IT Support**: Seamless routing of non-security requests to appropriate teams
- **Real-time Dashboard**: Live visualization of multi-agent workflows and status updates
- **Production-Ready Architecture**: Built for enterprise scalability and reliability

### 🚀 Multi-Agent Architecture Vision
Our comprehensive platform will include specialized agents for every IT domain:
- **PhishGuard Agent** ✅ (Implemented): Security threat analysis and response
- **AccessControl Agent** 🔮 (Roadmap): Identity and access management automation
- **PatchMaster Agent** 🔮 (Roadmap): Automated system updates and vulnerability management  
- **InfraHeal Agent** 🔮 (Roadmap): Infrastructure monitoring and self-healing systems
- **ComplianceGuard Agent** 🔮 (Roadmap): Automated compliance monitoring and reporting

## Architecture

### 🏗️ Multi-Agent System Design
NexusAI implements a sophisticated multi-agent architecture where intelligent AI agents collaborate to handle IT operations:

```
Ticket Input → Master Agent → Specialist Agents → Tool Execution → Resolution
```

**Current Implementation (Hackathon Prototype):**
- **Master Agent**: Central intelligence using Google Gemini AI for ticket classification
- **PhishGuard Agent**: Specialized security threat response with autonomous remediation
- **General Inquiry Agent**: Handles all non-security IT requests with proper routing

**Full Vision (Production Roadmap):**
- **Master Agent**: Orchestrates the complete ecosystem of specialist agents
- **PhishGuard Agent**: Security threats and incident response
- **AccessControl Agent**: Identity management and access provisioning
- **PatchMaster Agent**: System updates and vulnerability management
- **InfraHeal Agent**: Infrastructure monitoring and self-healing
- **ComplianceGuard Agent**: Regulatory compliance and audit automation

### 🔧 Technical Architecture
- **Frontend**: Modern Svelte dashboard with real-time WebSocket communication
- **Web Service**: Python Flask server with SocketIO for live updates
- **Agent Orchestration**: Multi-agent workflow management and coordination
- **Tool Integration**: MCP (Model Context Protocol) for AI-native tool execution
- **AI Engine**: Google Gemini Pro for intelligent decision-making

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher (for frontend development)
- Google Gemini API key

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd nexusai-autonomous-operations

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your configuration
# At minimum, set your GEMINI_API_KEY
```

### 4. Build Frontend (Optional)

```bash
# Build frontend for production
python scripts/build_frontend.py

# Or build for development
python scripts/build_frontend.py --mode development
```

### 5. Run the Application

#### Option 1: Using the Startup Coordinator (Recommended)

```bash
# Start the complete application with health checks
python run_nexusai.py

# Or on Windows
run_nexusai.bat

# Validate environment only
python run_nexusai.py --validate-only
```

#### Option 2: Manual Startup

```bash
# Start the application manually
python backend/web/main.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
nexusai-autonomous-operations/
├── backend/                    # Python backend code
│   ├── agents/                # AI agents (Master, PhishGuard)
│   ├── tools/                 # MCP security tools server
│   ├── workflow/              # Ticket processing orchestration
│   └── web/                   # Flask web server and routes
├── frontend/                  # Svelte frontend application
│   ├── src/                   # Svelte source code
│   │   ├── components/        # Reusable UI components
│   │   ├── App.svelte         # Main application component
│   │   └── main.js            # Application entry point
│   └── static/                # Static assets and build output
├── .kiro/                     # Kiro IDE specifications
│   └── specs/                 # Feature specifications and tasks
├── requirements.txt           # Python dependencies
├── .env.template             # Environment configuration template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Development Setup

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for development
npm run build:dev

# Build for production
npm run build:prod

# Clean build output
npm run clean
```

### Build Scripts

```bash
# Build frontend with Python script
python scripts/build_frontend.py --mode production

# Build frontend on Windows
scripts\build_frontend.bat --mode production

# Health check all services
python scripts/health_check.py

# Wait for services to be ready
python scripts/health_check.py --wait 30
```

### Backend Development

```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run tests
python scripts/run_tests.py --type all --verbose

# Run specific test types
python scripts/run_tests.py --type health    # Basic health checks
python scripts/run_tests.py --type unit      # Unit tests (when implemented)
python scripts/run_tests.py --type integration  # Integration tests (when implemented)
python scripts/run_tests.py --type frontend  # Frontend tests (when implemented)

# Or use pytest directly
pytest tests/ -v

# Run with debug mode
export FLASK_DEBUG=True
python backend/web/main.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `FLASK_HOST` | Flask server host | 127.0.0.1 |
| `FLASK_PORT` | Flask server port | 5000 |
| `MCP_HOST` | MCP server host | 127.0.0.1 |
| `MCP_PORT` | MCP server port | 8080 |
| `LOG_LEVEL` | Logging level | INFO |
| `SECRET_KEY` | Flask secret key | - |

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY=your_key_here`

## Usage

### Creating Tickets

1. Open the dashboard at `http://localhost:5000`
2. Enter a ticket subject in the form
3. Click "Create Ticket" to start the workflow
4. Watch real-time updates as agents process the ticket

### Example Ticket Subjects

- "Suspicious email with malicious link received" (triggers PhishGuard)
- "Password reset request" (general inquiry)
- "Phishing attempt detected in inbox" (triggers security workflow)

## Agent Workflows

### Master Agent
- Analyzes ticket subjects using AI
- Classifies tickets as 'Phishing/Security' or 'General Inquiry'
- Routes tickets to appropriate specialist agents

### PhishGuard Agent
- Investigates phishing and security threats
- Follows structured remediation protocol:
  1. **Analyze**: Extract indicators of compromise (IOCs)
  2. **Contain**: Block malicious URLs at network level
  3. **Eradicate**: Remove malicious emails from all inboxes
  4. **Document**: Log resolution summary and actions taken

## Troubleshooting

### Health Checks

Run the health check script to diagnose issues:

```bash
# Check all services
python scripts/health_check.py

# Wait for services to be ready
python scripts/health_check.py --wait 30

# Quiet mode (only show results)
python scripts/health_check.py --quiet
```

### Common Issues

**Application won't start:**
- Run `python run_nexusai.py --validate-only` to check environment
- Check that all environment variables are set in `.env`
- Verify Python virtual environment is activated
- Ensure all dependencies are installed with `pip install -r requirements.txt`

**Frontend not loading:**
- Build the frontend: `python scripts/build_frontend.py`
- Check that `backend/web/static/index.html` exists

**MCP server connection issues:**
- Verify MCP server is running on the configured port
- Check firewall settings for the MCP port (default: 8080)

**Gemini API errors:**
- Verify your API key is correct and has quota available
- Check network connectivity to Google services

**WebSocket connection issues:**
- Ensure Flask-SocketIO is properly installed
- Check that no other service is using the configured ports

### Process Management

The startup coordinator provides proper process management:

- **Graceful Shutdown**: Ctrl+C stops all services cleanly
- **Health Monitoring**: Automatic detection of failed services
- **Startup Validation**: Environment and dependency checks before starting
- **Port Conflict Detection**: Validates ports are available before binding

### Logs

Application logs are written to the console with configurable log levels. Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed debugging information.

Individual service logs:
- **Flask Server**: Main application logs
- **MCP Server**: Tool execution and security operation logs
- **Agents**: AI model interactions and decision logs

## Contributing

This is a hackathon prototype. For development:

1. Follow the task list in `.kiro/specs/nexusai-autonomous-operations/tasks.md`
2. Implement features incrementally according to the design document
3. Test each component thoroughly before integration
4. Maintain the real-time UI updates for demonstration purposes

## License

This project is created for hackathon demonstration purposes.

## Support

For issues or questions, refer to the design document and requirements in the `.kiro/specs/` directory.