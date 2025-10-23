#!/usr/bin/env python3
"""
NexusAI Demo Server
Simple Flask server for demonstration purposes
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

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'demo_secret_key_for_testing')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Demo HTML template
DEMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusAI - Autonomous IT Operations Platform</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00f5ff, #ff00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .demo-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .ticket-form {
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 16px;
        }
        
        button {
            background: linear-gradient(45deg, #00f5ff, #ff00ff);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        .workflow-display {
            min-height: 300px;
        }
        
        .workflow-step {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #00f5ff;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .step-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #00f5ff;
        }
        
        .step-description {
            opacity: 0.9;
        }
        
        .status-completed {
            border-left-color: #00ff88;
        }
        
        .status-completed .step-title {
            color: #00ff88;
        }
        
        .demo-scenarios {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .scenario-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .scenario-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-5px);
        }
        
        .scenario-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #ff00ff;
        }
        
        .scenario-description {
            opacity: 0.8;
            font-size: 14px;
        }
        
        .architecture-info {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
        }
        
        .tech-stack {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        
        .tech-badge {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
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
            <div class="ticket-form">
                <div class="form-group">
                    <label for="ticketSubject">Ticket Subject:</label>
                    <input type="text" id="ticketSubject" placeholder="Enter your IT support request...">
                </div>
                <button onclick="createTicket()">Create Ticket</button>
            </div>
            
            <h3>📋 Sample Demo Scenarios (Click to Try)</h3>
            <div class="demo-scenarios">
                <div class="scenario-card" onclick="useScenario('Suspicious email from CEO requesting wire transfer')">
                    <div class="scenario-title">🚨 Phishing Attack</div>
                    <div class="scenario-description">Demonstrates PhishGuard Agent autonomous response</div>
                </div>
                <div class="scenario-card" onclick="useScenario('Multiple users reporting fake Microsoft login page')">
                    <div class="scenario-title">🔒 Credential Harvesting</div>
                    <div class="scenario-description">Shows URL analysis and network blocking</div>
                </div>
                <div class="scenario-card" onclick="useScenario('Password reset request for user account')">
                    <div class="scenario-title">🔑 General IT Request</div>
                    <div class="scenario-description">Demonstrates Master Agent classification</div>
                </div>
                <div class="scenario-card" onclick="useScenario('Malicious attachment in payroll department emails')">
                    <div class="scenario-title">🦠 Malware Distribution</div>
                    <div class="scenario-description">Shows IOC extraction and system scanning</div>
                </div>
            </div>
        </div>
        
        <div class="demo-section">
            <h2>⚡ Live Workflow Visualization</h2>
            <div id="workflowDisplay" class="workflow-display">
                <p style="text-align: center; opacity: 0.7; margin-top: 100px;">
                    Create a ticket above to see the multi-agent workflow in action!
                </p>
            </div>
        </div>
        
        <div class="architecture-info">
            <h3>🏗️ Multi-Agent Architecture</h3>
            <p><strong>Master Agent</strong> (Google Gemini AI) → <strong>PhishGuard Agent</strong> (Security Specialist) → <strong>MCP Tools</strong> (Autonomous Actions)</p>
            
            <div class="tech-stack">
                <span class="tech-badge">Python Flask</span>
                <span class="tech-badge">Google Gemini AI</span>
                <span class="tech-badge">WebSocket Real-time</span>
                <span class="tech-badge">MCP Protocol</span>
                <span class="tech-badge">Multi-Agent System</span>
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
            if (!subject) {
                alert('Please enter a ticket subject');
                return;
            }
            
            const ticketId = ticketCounter++;
            const ticketData = {
                id: ticketId,
                subject: subject,
                timestamp: new Date().toISOString()
            };
            
            // Clear previous workflow
            document.getElementById('workflowDisplay').innerHTML = '';
            
            // Start the demo workflow
            simulateWorkflow(ticketData);
        }
        
        function simulateWorkflow(ticket) {
            const steps = [
                {
                    title: '📥 Ticket Received',
                    description: `Ticket #${ticket.id}: "${ticket.subject}"`,
                    delay: 0
                },
                {
                    title: '🤖 Master Agent Analysis',
                    description: 'Using Google Gemini AI to classify ticket type and determine routing...',
                    delay: 1500
                },
                {
                    title: '🎯 Classification Complete',
                    description: isSecurityTicket(ticket.subject) ? 
                        'Classified as "Phishing/Security" - Routing to PhishGuard Agent' :
                        'Classified as "General Inquiry" - Routing to General Support',
                    delay: 3000
                }
            ];
            
            if (isSecurityTicket(ticket.subject)) {
                steps.push(
                    {
                        title: '🛡️ PhishGuard Agent Activated',
                        description: 'Specialized security agent analyzing threat indicators...',
                        delay: 4500
                    },
                    {
                        title: '🔍 Threat Analysis',
                        description: 'Extracting IOCs, analyzing URLs, checking threat intelligence...',
                        delay: 6000
                    },
                    {
                        title: '🚫 Network Protection',
                        description: 'Blocking malicious URLs at network level via MCP tools...',
                        delay: 7500
                    },
                    {
                        title: '📧 Email Remediation',
                        description: 'Searching and removing similar emails from all inboxes...',
                        delay: 9000
                    },
                    {
                        title: '✅ Resolution Complete',
                        description: 'Threat neutralized. Incident documented with full audit trail.',
                        delay: 10500,
                        completed: true
                    }
                );
            } else {
                steps.push(
                    {
                        title: '👥 General Support Agent',
                        description: 'Routing to appropriate IT support team for manual handling...',
                        delay: 4500
                    },
                    {
                        title: '✅ Ticket Escalated',
                        description: 'Ticket successfully routed to IT support for resolution.',
                        delay: 6000,
                        completed: true
                    }
                );
            }
            
            // Execute workflow steps
            steps.forEach(step => {
                setTimeout(() => {
                    addWorkflowStep(step);
                }, step.delay);
            });
        }
        
        function addWorkflowStep(step) {
            const workflowDisplay = document.getElementById('workflowDisplay');
            const stepElement = document.createElement('div');
            stepElement.className = `workflow-step ${step.completed ? 'status-completed' : ''}`;
            stepElement.innerHTML = `
                <div class="step-title">${step.title}</div>
                <div class="step-description">${step.description}</div>
            `;
            workflowDisplay.appendChild(stepElement);
            
            // Scroll to bottom
            stepElement.scrollIntoView({ behavior: 'smooth' });
        }
        
        function isSecurityTicket(subject) {
            const securityKeywords = [
                // Phishing & Scams
                'suspicious', 'phishing', 'scam', 'fraud', 'fake', 'spoofed',
                'won', 'congratulations', 'winner', 'prize', 'lottery', 'jackpot',
                'money', 'cash', 'reward', 'refund', 'payment', 'transfer', 'wire',
                '$', 'dollar', 'euro', 'pound',
                
                // Urgency & Social Engineering  
                'urgent', 'immediate', 'expires', 'limited time', 'act now', 'hurry',
                'click here', 'verify', 'confirm', 'update', 'suspended', 'locked',
                'notification', 'alert', 'warning', 'notice',
                
                // Fake Authorities
                'ceo', 'manager', 'director', 'boss', 'executive', 'president',
                'bank', 'irs', 'government', 'police', 'legal', 'microsoft', 'google',
                
                // Malware & Threats
                'malware', 'virus', 'trojan', 'ransomware', 'infected', 'attachment',
                'download', 'install', 'hack', 'breach', 'unauthorized', 'compromised',
                'attack', 'threat', 'malicious', 'dangerous', 'harmful',
                
                // Credential Theft
                'login', 'password', 'account', 'security', 'verification', 'credentials',
                
                // Suspicious Indicators
                'unusual', 'strange', 'weird', 'odd', 'unknown', 'www.', 'http', 
                '.com', 'link', 'url', 'site', 'bitcoin', 'crypto', 'investment',
                'free', 'gift', 'bonus', 'discount', 'offer', 'deal'
            ];
            
            const lowerSubject = subject.toLowerCase();
            return securityKeywords.some(keyword => lowerSubject.includes(keyword));
        }
        
        // Socket.IO event handlers
        socket.on('connect', function() {
            console.log('Connected to NexusAI server');
        });
        
        socket.on('workflow_update', function(data) {
            console.log('Workflow update:', data);
        });
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
    return jsonify({
        'status': 'healthy',
        'service': 'NexusAI Demo Server',
        'timestamp': time.time()
    })

@app.route('/api/ticket', methods=['POST'])
def create_ticket():
    """Create a new ticket (demo endpoint)"""
    data = request.get_json()
    
    # Simulate ticket processing
    ticket = {
        'id': int(time.time()),
        'subject': data.get('subject', ''),
        'status': 'processing',
        'timestamp': time.time()
    }
    
    # Emit real-time update
    socketio.emit('ticket_created', ticket)
    
    return jsonify(ticket)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to NexusAI'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NexusAI Demo Server")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting NexusAI Demo Server on {args.host}:{args.port}")
    
    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()