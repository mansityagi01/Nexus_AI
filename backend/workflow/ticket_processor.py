"""
Ticket Processor for workflow orchestration and management.

This module orchestrates the complete ticket workflow from creation to resolution,
coordinating between Master Agent and specialist agents with real-time UI updates.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from backend.utils.error_handling import (
    WorkflowError, AgentError, RetryableError, CircuitBreaker,
    retry_with_backoff, handle_error, graceful_shutdown_handler
)

# Configure logging
logger = logging.getLogger("nexusai.workflow.processor")

class TicketProcessor:
    """
    Orchestrates ticket processing workflow with agent coordination and real-time updates.
    
    Manages the complete lifecycle:
    1. Ticket creation and ID generation
    2. Master Agent triage and classification
    3. Specialist agent routing and execution
    4. Workflow state management and status tracking
    5. Real-time UI updates via SocketIO
    """
    
    def __init__(self, socketio_client=None, mcp_client=None):
        """
        Initialize the TicketProcessor with communication clients and error handling.
        
        Args:
            socketio_client: SocketIO client for real-time UI updates
            mcp_client: MCP client for agent tool access
        """
        self.socketio_client = socketio_client
        self.mcp_client = mcp_client
        
        # Active workflows tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Agent instances (will be injected)
        self.master_agent = None
        self.phishguard_agent = None
        
        # Workflow status definitions
        self.status_definitions = {
            'received': 'Ticket created and queued for processing',
            'processing': 'Master Agent analyzing ticket',
            'classified': 'Ticket categorized by Master Agent',
            'delegating': 'Routing to specialist agent',
            'working': 'Specialist agent executing remediation',
            'resolved': 'Workflow completed successfully',
            'escalated': 'Manual intervention required',
            'failed': 'Workflow failed with errors'
        }
        
        # Error tracking and circuit breakers
        self.workflow_failures = {}
        self.agent_circuit_breakers = {}
        
        # Performance metrics
        self.workflow_metrics = {
            'total_processed': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'escalated_workflows': 0,
            'average_processing_time': 0.0
        }
        
        logger.info("TicketProcessor initialized with comprehensive error handling")
    
    def set_agents(self, master_agent, phishguard_agent):
        """
        Inject agent instances for workflow coordination.
        
        Args:
            master_agent: Master Agent instance for ticket triage
            phishguard_agent: PhishGuard Agent instance for security remediation
        """
        self.master_agent = master_agent
        self.phishguard_agent = phishguard_agent
        
        # Configure agents with MCP client if available
        if self.mcp_client:
            if hasattr(self.phishguard_agent, 'mcp_client'):
                self.phishguard_agent.mcp_client = self.mcp_client
        
        # Configure agents with SocketIO client if available
        if self.socketio_client:
            if hasattr(self.phishguard_agent, 'socketio_client'):
                self.phishguard_agent.socketio_client = self.socketio_client
        
        logger.info("Agents configured for TicketProcessor")
    
    def generate_ticket_id(self) -> str:
        """
        Generate a unique ticket ID for tracking.
        
        Returns:
            Unique ticket identifier in format SIM-XXXXXXXX
        """
        # Generate a short UUID-based ID for simulation
        short_uuid = str(uuid.uuid4()).replace('-', '').upper()[:8]
        return f"SIM-{short_uuid}"
    
    async def emit_workflow_update(self, ticket_id: str, message: str, 
                                 agent: str = "System", status: str = "processing") -> None:
        """
        Emit a workflow update to the UI via SocketIO with error handling.
        
        Args:
            ticket_id: The ticket ID being processed
            message: Update message to display
            agent: Name of the agent or system component
            status: Current workflow status
        """
        try:
            if self.socketio_client:
                update_data = {
                    'ticket_id': ticket_id,
                    'agent': agent,
                    'message': message,
                    'status': status,
                    'timestamp': time.time()
                }
                
                self.socketio_client.emit('workflow_update', update_data)
                logger.debug(f"Emitted workflow update for {ticket_id}: {message}")
            else:
                logger.warning("SocketIO client not available for workflow updates")
                
        except Exception as e:
            # Don't let UI update failures break the workflow
            logger.warning(f"Non-critical error emitting workflow update: {str(e)}")
            
            # Try to emit a fallback update
            try:
                if self.socketio_client:
                    fallback_data = {
                        'ticket_id': ticket_id,
                        'agent': 'System',
                        'message': f'Update failed: {message[:50]}...',
                        'status': status,
                        'timestamp': time.time(),
                        'update_error': True
                    }
                    self.socketio_client.emit('workflow_update', fallback_data)
            except:
                # If even the fallback fails, just log it
                logger.error(f"Critical: Both primary and fallback UI updates failed for ticket {ticket_id}")
    
    async def update_workflow_status(self, ticket_id: str, status: str, 
                                   message: Optional[str] = None) -> None:
        """
        Update the workflow status and emit UI update.
        
        Args:
            ticket_id: The ticket ID to update
            status: New workflow status
            message: Optional custom message (uses default if not provided)
        """
        try:
            if ticket_id in self.active_workflows:
                self.active_workflows[ticket_id]['status'] = status
                self.active_workflows[ticket_id]['updated_at'] = datetime.utcnow().isoformat()
                
                # Use custom message or default status description
                update_message = message or self.status_definitions.get(status, f"Status: {status}")
                
                await self.emit_workflow_update(
                    ticket_id=ticket_id,
                    message=update_message,
                    agent="System",
                    status=status
                )
                
                logger.info(f"Updated workflow {ticket_id} to status: {status}")
            else:
                logger.warning(f"Attempted to update non-existent workflow: {ticket_id}")
                
        except Exception as e:
            logger.error(f"Error updating workflow status: {str(e)}")
    
    async def create_ticket(self, subject: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new ticket and initialize workflow tracking.
        
        Args:
            subject: The ticket subject line
            additional_data: Optional additional ticket data
            
        Returns:
            Created ticket data with ID and initial status
        """
        try:
            # Generate unique ticket ID
            ticket_id = self.generate_ticket_id()
            
            # Create ticket data structure
            ticket_data = {
                'id': ticket_id,
                'subject': subject,
                'status': 'received',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'logs': []
            }
            
            # Add any additional data
            if additional_data:
                ticket_data.update(additional_data)
            
            # Add to active workflows
            self.active_workflows[ticket_id] = ticket_data
            
            # Emit initial workflow update
            await self.emit_workflow_update(
                ticket_id=ticket_id,
                message=f"Ticket created: {subject}",
                agent="System",
                status="received"
            )
            
            logger.info(f"Created ticket {ticket_id}: {subject}")
            return ticket_data
            
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            raise
    
    @graceful_shutdown_handler()
    async def process_ticket_async(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket through the complete workflow asynchronously with comprehensive error handling.
        
        Args:
            ticket_data: Ticket data to process
            
        Returns:
            Processed ticket data with final results
        """
        ticket_id = ticket_data.get('id', 'Unknown')
        workflow_start_time = time.time()
        
        try:
            logger.info(f"Starting asynchronous processing for ticket {ticket_id}")
            
            # Initialize workflow tracking
            ticket_data['workflow_start_time'] = workflow_start_time
            ticket_data['processing_attempts'] = ticket_data.get('processing_attempts', 0) + 1
            
            # Update metrics
            self.workflow_metrics['total_processed'] += 1
            
            # Update status to processing
            await self.update_workflow_status(ticket_id, 'processing', 
                                            "Master Agent analyzing ticket...")
            
            # Phase 1: Master Agent Classification with error handling
            classified_ticket = await self._process_with_master_agent(ticket_data)
            classification = classified_ticket.get('classification', 'General Inquiry')
            assigned_agent = classified_ticket.get('assigned_agent', 'General Support Agent')
            
            await self.emit_workflow_update(
                ticket_id=ticket_id,
                message=f"✅ Classified as '{classification}' → Assigned to {assigned_agent}",
                agent="Master Agent",
                status="classified"
            )
            
            # Update workflow status
            await self.update_workflow_status(ticket_id, 'classified')
            
            # Phase 2: Specialist Agent Processing with error handling
            final_ticket = await self._process_with_specialist_agent(classified_ticket, classification)
            
            # Calculate processing time
            processing_time = time.time() - workflow_start_time
            final_ticket['processing_time'] = processing_time
            
            # Update metrics
            self._update_workflow_metrics(final_ticket, processing_time)
            
            # Update final workflow status
            final_status = final_ticket.get('status', 'resolved')
            await self._finalize_workflow_status(ticket_id, final_status)
            
            # Update active workflows
            self.active_workflows[ticket_id] = final_ticket
            
            logger.info(f"Successfully processed ticket {ticket_id} with status: {final_status} "
                       f"in {processing_time:.2f}s")
            return final_ticket
            
        except Exception as e:
            processing_time = time.time() - workflow_start_time
            
            error_context = {
                "ticket_id": ticket_id,
                "processing_time": processing_time,
                "processing_attempts": ticket_data.get('processing_attempts', 1),
                "workflow_phase": "unknown"
            }
            
            logger.error(f"Critical error processing ticket {ticket_id}: {str(e)}")
            handle_error(WorkflowError(ticket_id, f"Workflow processing failed: {str(e)}"), error_context)
            
            # Update workflow to failed status
            await self.update_workflow_status(ticket_id, 'failed', 
                                            f"❌ Workflow failed: {str(e)}")
            
            # Update metrics
            self.workflow_metrics['failed_workflows'] += 1
            
            # Update ticket data with comprehensive error information
            if ticket_id in self.active_workflows:
                self.active_workflows[ticket_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'processing_time': processing_time,
                    'failed_at': time.time(),
                    'requires_manual_intervention': True
                })
            
            # Don't re-raise for workflow stability - return failed ticket instead
            return self.active_workflows.get(ticket_id, ticket_data)
    
    async def _process_with_master_agent(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process ticket with Master Agent with error handling and circuit breaker.
        
        Args:
            ticket_data: Ticket data to process
            
        Returns:
            Classified ticket data
        """
        ticket_id = ticket_data.get('id', 'Unknown')
        
        try:
            if not self.master_agent:
                raise WorkflowError(ticket_id, "Master Agent not configured", "AGENT_NOT_CONFIGURED")
            
            await self.emit_workflow_update(
                ticket_id=ticket_id,
                message="🤖 Master Agent activated for ticket triage",
                agent="Master Agent",
                status="processing"
            )
            
            # Use circuit breaker for agent calls
            if "master_agent" not in self.agent_circuit_breakers:
                self.agent_circuit_breakers["master_agent"] = CircuitBreaker(
                    service_name="master_agent",
                    failure_threshold=3,
                    recovery_timeout=30.0
                )
            
            # Process with Master Agent
            classified_ticket = await self.agent_circuit_breakers["master_agent"](
                self.master_agent.process_ticket
            )(ticket_data)
            
            return classified_ticket
            
        except Exception as e:
            logger.error(f"Master Agent processing failed for ticket {ticket_id}: {str(e)}")
            
            # Provide fallback classification
            fallback_ticket = ticket_data.copy()
            fallback_ticket.update({
                'classification': 'General Inquiry',
                'assigned_agent': 'General Support Agent',
                'status': 'classified',
                'priority': 'normal',
                'processing_error': str(e),
                'fallback_used': True
            })
            
            await self.emit_workflow_update(
                ticket_id=ticket_id,
                message=f"⚠️ Master Agent failed, using fallback classification: General Inquiry",
                agent="System",
                status="classified"
            )
            
            return fallback_ticket
    
    async def _process_with_specialist_agent(self, ticket_data: Dict[str, Any], classification: str) -> Dict[str, Any]:
        """
        Process ticket with appropriate specialist agent.
        
        Args:
            ticket_data: Classified ticket data
            classification: Ticket classification
            
        Returns:
            Processed ticket data
        """
        ticket_id = ticket_data.get('id', 'Unknown')
        
        try:
            # Phase 2: Specialist Agent Routing
            await self.update_workflow_status(ticket_id, 'delegating', 
                                            f"Routing to specialist agent...")
            
            if classification == "Phishing/Security":
                return await self._process_security_ticket(ticket_data)
            else:
                return await self._process_general_ticket(ticket_data)
                
        except Exception as e:
            logger.error(f"Specialist agent processing failed for ticket {ticket_id}: {str(e)}")
            
            # Mark for escalation
            ticket_data.update({
                'status': 'escalated',
                'escalation_reason': f'Specialist agent processing failed: {str(e)}',
                'requires_manual_intervention': True
            })
            
            await self.emit_workflow_update(
                ticket_id=ticket_id,
                message=f"⚠️ Specialist processing failed - escalating for manual review",
                agent="System",
                status="escalated"
            )
            
            return ticket_data
    
    async def _process_security_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process security ticket with PhishGuard Agent."""
        ticket_id = ticket_data.get('id', 'Unknown')
        
        if not self.phishguard_agent:
            raise WorkflowError(ticket_id, "PhishGuard Agent not configured", "AGENT_NOT_CONFIGURED")
        
        await self.emit_workflow_update(
            ticket_id=ticket_id,
            message="🛡️ Delegating to PhishGuard Agent for security remediation",
            agent="System",
            status="delegating"
        )
        
        # Update workflow status to working
        await self.update_workflow_status(ticket_id, 'working')
        
        # Use circuit breaker for PhishGuard
        if "phishguard_agent" not in self.agent_circuit_breakers:
            self.agent_circuit_breakers["phishguard_agent"] = CircuitBreaker(
                service_name="phishguard_agent",
                failure_threshold=2,
                recovery_timeout=60.0
            )
        
        # Process with PhishGuard Agent
        return await self.agent_circuit_breakers["phishguard_agent"](
            self.phishguard_agent.process_security_ticket
        )(ticket_data)
    
    async def _process_general_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general inquiry ticket (simulated)."""
        ticket_id = ticket_data.get('id', 'Unknown')
        
        await self.emit_workflow_update(
            ticket_id=ticket_id,
            message="📋 Processing general inquiry (simulated)",
            agent="General Support Agent",
            status="working"
        )
        
        # Simulate general processing
        await asyncio.sleep(2.0)
        
        await self.emit_workflow_update(
            ticket_id=ticket_id,
            message="✅ General inquiry processed successfully",
            agent="General Support Agent",
            status="resolved"
        )
        
        ticket_data['status'] = 'resolved'
        return ticket_data
    
    def _update_workflow_metrics(self, ticket_data: Dict[str, Any], processing_time: float):
        """Update workflow performance metrics."""
        status = ticket_data.get('status', 'unknown')
        
        if status == 'resolved':
            self.workflow_metrics['successful_workflows'] += 1
        elif status == 'escalated':
            self.workflow_metrics['escalated_workflows'] += 1
        elif status == 'failed':
            self.workflow_metrics['failed_workflows'] += 1
        
        # Update average processing time
        total_successful = self.workflow_metrics['successful_workflows']
        if total_successful > 0:
            current_avg = self.workflow_metrics['average_processing_time']
            self.workflow_metrics['average_processing_time'] = (
                (current_avg * (total_successful - 1) + processing_time) / total_successful
            )
    
    async def _finalize_workflow_status(self, ticket_id: str, final_status: str):
        """Finalize workflow status with appropriate messaging."""
        if final_status == 'resolved':
            await self.update_workflow_status(ticket_id, 'resolved', 
                                            "🎉 Workflow completed successfully")
        elif final_status == 'escalated':
            await self.update_workflow_status(ticket_id, 'escalated', 
                                            "⚠️ Escalated for manual review")
        elif final_status == 'failed':
            await self.update_workflow_status(ticket_id, 'failed',
                                            "❌ Workflow failed - manual intervention required")
        else:
            await self.update_workflow_status(ticket_id, final_status)
    
    async def process_ticket(self, subject: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create and process a ticket through the complete workflow.
        
        Args:
            subject: The ticket subject line
            additional_data: Optional additional ticket data
            
        Returns:
            The ticket ID for tracking
        """
        try:
            # Create the ticket
            ticket_data = await self.create_ticket(subject, additional_data)
            ticket_id = ticket_data['id']
            
            # Start asynchronous processing (fire and forget)
            asyncio.create_task(self.process_ticket_async(ticket_data))
            
            logger.info(f"Initiated processing for ticket {ticket_id}")
            return ticket_id
            
        except Exception as e:
            logger.error(f"Error initiating ticket processing: {str(e)}")
            raise
    
    def get_workflow_status(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a workflow.
        
        Args:
            ticket_id: The ticket ID to check
            
        Returns:
            Workflow data or None if not found
        """
        return self.active_workflows.get(ticket_id)
    
    def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all currently active workflows.
        
        Returns:
            Dictionary of all active workflows
        """
        return self.active_workflows.copy()
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed workflows to prevent memory buildup.
        
        Args:
            max_age_hours: Maximum age in hours for completed workflows
            
        Returns:
            Number of workflows cleaned up
        """
        try:
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            # Find workflows to clean up
            workflows_to_remove = []
            for ticket_id, workflow in self.active_workflows.items():
                if workflow.get('status') in ['resolved', 'failed', 'escalated']:
                    updated_at = datetime.fromisoformat(workflow.get('updated_at', ''))
                    age_hours = (current_time - updated_at).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        workflows_to_remove.append(ticket_id)
            
            # Remove old workflows
            for ticket_id in workflows_to_remove:
                del self.active_workflows[ticket_id]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old workflows")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during workflow cleanup: {str(e)}")
            return 0
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Get current workflow performance metrics.
        
        Returns:
            Dictionary containing workflow metrics and health information
        """
        try:
            # Calculate success rate
            total_completed = (self.workflow_metrics['successful_workflows'] + 
                             self.workflow_metrics['failed_workflows'] + 
                             self.workflow_metrics['escalated_workflows'])
            
            success_rate = 0.0
            if total_completed > 0:
                success_rate = (self.workflow_metrics['successful_workflows'] / total_completed) * 100
            
            # Get circuit breaker status
            circuit_breaker_status = {}
            for name, cb in self.agent_circuit_breakers.items():
                circuit_breaker_status[name] = {
                    'state': cb.state,
                    'failure_count': cb.failure_count,
                    'last_failure_time': cb.last_failure_time
                }
            
            # Get active workflow count by status
            active_by_status = {}
            for workflow in self.active_workflows.values():
                status = workflow.get('status', 'unknown')
                active_by_status[status] = active_by_status.get(status, 0) + 1
            
            return {
                'performance_metrics': self.workflow_metrics.copy(),
                'success_rate_percent': round(success_rate, 2),
                'active_workflows_count': len(self.active_workflows),
                'active_workflows_by_status': active_by_status,
                'circuit_breaker_status': circuit_breaker_status,
                'system_health': self._assess_system_health()
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}")
            return {
                'error': str(e),
                'system_health': 'unknown'
            }
    
    def _assess_system_health(self) -> str:
        """
        Assess overall system health based on metrics and circuit breaker status.
        
        Returns:
            Health status: 'healthy', 'degraded', or 'unhealthy'
        """
        try:
            # Check circuit breaker status
            open_breakers = sum(1 for cb in self.agent_circuit_breakers.values() if cb.state == 'OPEN')
            
            # Check failure rate
            total_processed = self.workflow_metrics['total_processed']
            failed_workflows = self.workflow_metrics['failed_workflows']
            
            failure_rate = 0.0
            if total_processed > 0:
                failure_rate = (failed_workflows / total_processed) * 100
            
            # Determine health status
            if open_breakers > 0:
                return 'unhealthy'
            elif failure_rate > 20:  # More than 20% failure rate
                return 'degraded'
            elif failure_rate > 10:  # More than 10% failure rate
                return 'degraded'
            else:
                return 'healthy'
                
        except Exception as e:
            logger.error(f"Error assessing system health: {str(e)}")
            return 'unknown'