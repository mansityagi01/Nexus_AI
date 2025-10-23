"""
NexusAI Flask Routes and WebSocket Events
Handles HTTP routes and real-time WebSocket communication
"""

import os
import sys
import uuid
import logging
from flask import request
from flask_socketio import emit
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from workflow.ticket_processor import TicketProcessor

logger = logging.getLogger(__name__)

# Global ticket processor instance
ticket_processor = None

def generate_ticket_id():
    """Generate a unique ticket ID in the format SIM-XXXXXXXX"""
    # Generate 8 character alphanumeric ID
    short_uuid = str(uuid.uuid4()).replace('-', '')[:8].upper()
    return f"SIM-{short_uuid}"

def register_routes(app, socketio):
    """Register Flask routes and SocketIO event handlers"""
    global ticket_processor
    
    # Initialize ticket processor with SocketIO for real-time updates
    ticket_processor = TicketProcessor(socketio)
    
    # HTTP Routes
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'service': 'NexusAI',
            'version': '1.0.0'
        }
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint"""
        return {
            'api': 'online',
            'mcp_server': 'running',
            'agents': {
                'master_agent': 'ready',
                'phishguard_agent': 'ready'
            }
        }
    
    # WebSocket Events
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_status', {
            'status': 'connected',
            'message': 'Connected to NexusAI server'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('create_ticket')
    def handle_create_ticket(data):
        """
        Handle ticket creation WebSocket event
        Expected data: {'subject': 'ticket subject'}
        """
        try:
            # Validate input data
            if not data or 'subject' not in data:
                emit('ticket_error', {
                    'error': 'Missing ticket subject',
                    'message': 'Please provide a ticket subject'
                })
                return
            
            subject = data['subject'].strip()
            if not subject:
                emit('ticket_error', {
                    'error': 'Empty ticket subject',
                    'message': 'Ticket subject cannot be empty'
                })
                return
            
            logger.info(f"Creating ticket with subject: {subject}")
            
            # Start ticket processing workflow
            if ticket_processor:
                # Use the async process_ticket method which creates and processes the ticket
                import asyncio
                
                # Create a task to process the ticket asynchronously
                async def process_ticket_wrapper():
                    try:
                        ticket_id = await ticket_processor.process_ticket(subject)
                        
                        # Emit ticket created event with the actual ticket ID
                        socketio.emit('ticket_created', {
                            'ticket_id': ticket_id,
                            'subject': subject,
                            'status': 'received',
                            'message': f'Ticket {ticket_id} created successfully'
                        })
                        
                        logger.info(f"Ticket {ticket_id} processing initiated")
                        
                    except Exception as e:
                        logger.error(f"Error in ticket processing: {e}")
                        socketio.emit('ticket_error', {
                            'error': 'Processing failed',
                            'message': str(e)
                        })
                
                # Schedule the async task
                asyncio.create_task(process_ticket_wrapper())
                
            else:
                logger.error("Ticket processor not initialized")
                emit('ticket_error', {
                    'error': 'System error',
                    'message': 'Ticket processor not available'
                })
        
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            emit('ticket_error', {
                'error': 'Internal server error',
                'message': 'Failed to create ticket. Please try again.'
            })
    
    @socketio.on('get_ticket_status')
    def handle_get_ticket_status(data):
        """
        Handle ticket status request
        Expected data: {'ticket_id': 'SIM-XXXXXXXX'}
        """
        try:
            if not data or 'ticket_id' not in data:
                emit('ticket_error', {
                    'error': 'Missing ticket ID',
                    'message': 'Please provide a ticket ID'
                })
                return
            
            ticket_id = data['ticket_id']
            
            # Get ticket status from processor
            if ticket_processor:
                status = ticket_processor.get_workflow_status(ticket_id)
                if status:
                    emit('ticket_status', status)
                else:
                    emit('ticket_error', {
                        'error': 'Ticket not found',
                        'message': f'Ticket {ticket_id} not found'
                    })
            else:
                emit('ticket_error', {
                    'error': 'System error',
                    'message': 'Ticket processor not available'
                })
        
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            emit('ticket_error', {
                'error': 'Internal server error',
                'message': 'Failed to get ticket status'
            })
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection testing"""
        emit('pong', {'timestamp': str(uuid.uuid4())})
    
    logger.info("Routes and WebSocket events registered successfully")