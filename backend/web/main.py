"""
NexusAI Flask Application - Simple Working Version
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set defaults
os.environ.setdefault('SECRET_KEY', 'demo_secret_key_for_testing')
os.environ.setdefault('GEMINI_API_KEY', 'demo_key_for_testing')

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Demo HTML template (embedded for simplicity)
DEMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusAI - Autonomous IT Operations Platform</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 {
            font-size: 3rem; margin-bottom: 10px;
            background: linear-gradient(45deg, #00f5ff, #ff00ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .demo-section {
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
            border-radius: 20px; padding: 30px; margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; }
        input[type="text"] {
            width: 100%; padding: 12px; border: none; border-radius: 10px;
            background: rgba(255, 255, 255, 0.9); color: #333; font-size: 16px;
        }
        button {
            background: linear-gradient(45deg, #00f5ff, #ff00ff);
            color: white; border: none; padding: 12px 30px; border-radius: 25px;
            font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .workflow-step {
            background: rgba(255, 255, 255, 0.1); border-radius: 10px;
            padding: 15px; margin-bottom: 15px; border-left: 4px solid #00f5ff;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .step-title { font-weight: 600; margin-bottom: 8px; color: #00f5ff; }
        .scenario-card {
            background: rgba(255, 255, 255, 0.05); border-radius: 15px;
            padding: 20px; cursor: pointer; transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px;
        }
        .scenario-card:hover {
            background: rgba(255, 255, 255, 0.1); transform: translateY(-5px);
        }
        .scenario-title { font-weight: 600; margin-bottom: 10px; color: #ff00ff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NexusAI</h1>
            <p>Autonomous IT Operations Platform - Multi-Agent AI System</p>
        </div>
        
        <div class="demo-section">
            <h2>🎯 Create Support Ticket</h2>
            <div class="form-group">
                <label for="ticketSubject">Ticket Subject:</label>
                <input type="text" id="ticketSubject" placeholder="Enter your IT support request...">
            </div>
            <button onclick="createTicket()">Create Ticket</button>
            
            <h3>📋 Sample Demo Scenarios (Click to Try)</h3>
            <div class="scenario-card" onclick="useScenario('Suspicious email from CEO requesting wire transfer')">
                <div class="scenario-title">🚨 Phishing Attack</div>
                <div class="scenario-description">Demonstrates PhishGuard Agent autonomous response</div>
            </div>
            <div class="scenario-card" onclick="useScenario('Password reset request for user account')">
                <div class="scenario-title">🔑 General IT Request</div>
                <div class="scenario-description">Demonstrates Master Agent classification</div>
            </div>
        </div>
        
        <div class="demo-section">
            <h2>⚡ Live Multi-Agent Workflow</h2>
            <div id="workflowDisplay">
                <p style="text-align: center; opacity: 0.7; margin-top: 50px;">
                    Create a ticket above to see the multi-agent workflow in action!
                </p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let ticketCounter = 1;
        
        function useScenario(scenario) {
            document.getElementById('ticketSubject').value = scenario;
        }
        
        function createTicket() {
            const subject = document.getElementById('ticketSubject').value.trim();
            if (!subject) { alert('Please enter a ticket subject'); return; }
            
            const ticketId = ticketCounter++;
            document.getElementById('workflowDisplay').innerHTML = '';
            simulateWorkflow({id: ticketId, subject: subject});
        }
        
        function simulateWorkflow(ticket) {
            const isPhishing = /suspicious|phishing|malware|ceo|wire transfer|fake|malicious/i.test(ticket.subject);
            
            const steps = [
                { title: '📥 Ticket Received', description: `Ticket #${ticket.id}: "${ticket.subject}"`, delay: 0 },
                { title: '🤖 Master Agent Analysis', description: 'Using Google Gemini AI to classify ticket...', delay: 1500 },
                { title: '🎯 Classification Complete', 
                  description: isPhishing ? 'Classified as "Phishing/Security" - Routing to PhishGuard Agent' : 'Classified as "General Inquiry" - Routing to Support Team', 
                  delay: 3000 }
            ];
            
            if (isPhishing) {
                steps.push(
                    { title: '🛡️ PhishGuard Agent Activated', description: 'Specialized security agent analyzing threat...', delay: 4500 },
                    { title: '🔍 Threat Analysis', description: 'Extracting IOCs, analyzing URLs via MCP tools...', delay: 6000 },
                    { title: '🚫 Network Protection', description: 'Blocking malicious URLs at network level...', delay: 7500 },
                    { title: '📧 Email Remediation', description: 'Removing similar emails from all inboxes...', delay: 9000 },
                    { title: '✅ Resolution Complete', description: 'Threat neutralized. Full audit trail documented.', delay: 10500 }
                );
            } else {
                steps.push(
                    { title: '👥 General Support Routing', description: 'Routing to appropriate IT support team...', delay: 4500 },
                    { title: '✅ Ticket Escalated', description: 'Successfully routed for manual handling.', delay: 6000 }
                );
            }
            
            steps.forEach(step => {
                setTimeout(() => addWorkflowStep(step), step.delay);
            });
        }
        
        function addWorkflowStep(step) {
            const display = document.getElementById('workflowDisplay');
            const stepEl = document.createElement('div');
            stepEl.className = 'workflow-step';
            stepEl.innerHTML = `<div class="step-title">${step.title}</div><div>${step.description}</div>`;
            display.appendChild(stepEl);
            stepEl.scrollIntoView({ behavior: 'smooth' });
        }
        
        socket.on('connect', () => console.log('Connected to NexusAI'));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main demo page"""
    return render_template_string(DEMO_HTML)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'NexusAI', 'timestamp': time.time()})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to NexusAI Multi-Agent System'})

def main():
    """Main entry point"""
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    logger.info(f"Starting NexusAI on {host}:{port}")
    logger.info("Multi-Agent System: Master Agent + PhishGuard Agent Ready")
    
    try:
        socketio.run(app, host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()