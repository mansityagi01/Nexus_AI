"""
Master Agent for intelligent ticket triage and classification.

This agent analyzes incoming IT support tickets and classifies them as either
'Phishing/Security' or 'General Inquiry' to route them to appropriate specialist agents.
"""

import os
import logging
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from strands_agents import Agent

from backend.utils.error_handling import (
    AgentError, APIError, RetryableError, CircuitBreaker, 
    retry_with_backoff, handle_error
)

# Configure logging
logger = logging.getLogger("nexusai.agents.master")

class MasterAgent(Agent):
    """
    Master Agent responsible for ticket triage and classification.
    
    Uses Google Gemini AI to analyze ticket subjects and classify them
    for routing to appropriate specialist agents.
    """
    
    def __init__(self):
        """Initialize the Master Agent with Gemini model integration."""
        super().__init__(name="Master Agent")
        
        # Configure Gemini API with error handling
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found. Agent will use fallback classification.")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini API configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {str(e)}")
                self.model = None
        
        # Circuit breaker for Gemini API calls
        self.gemini_circuit_breaker = CircuitBreaker(
            service_name="gemini_api",
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception=(APIError, RetryableError, Exception)
        )
        
        # System prompt for ticket classification
        self.system_prompt = """
You are a Master Agent responsible for triaging IT support tickets. Your job is to analyze ticket subjects and classify them into one of two categories:

1. "Phishing/Security" - For tickets related to:
   - Suspicious emails or phishing attempts
   - Security threats or malware
   - Unauthorized access or breaches
   - Suspicious links or attachments
   - Social engineering attempts
   - Any cybersecurity-related incidents

2. "General Inquiry" - For all other tickets including:
   - Technical support requests
   - Software issues
   - Hardware problems
   - Account access issues (non-security related)
   - General IT questions
   - System maintenance requests

Analyze the ticket subject and respond with ONLY one of these two classifications: "Phishing/Security" or "General Inquiry"

Do not provide explanations or additional text - just the classification.
"""
    
    @retry_with_backoff(max_retries=2, base_delay=1.0, retryable_exceptions=(RetryableError, ConnectionError))
    async def classify_ticket(self, ticket_subject: str) -> str:
        """
        Classify a ticket based on its subject line with comprehensive error handling.
        
        Args:
            ticket_subject: The subject line of the ticket to classify
            
        Returns:
            Classification as either 'Phishing/Security' or 'General Inquiry'
        """
        try:
            if not self.model:
                logger.info("No Gemini model available, using fallback classification")
                return self._fallback_classification(ticket_subject)
            
            # Use circuit breaker for Gemini API calls
            return await self._classify_with_gemini(ticket_subject)
                
        except Exception as e:
            error_context = {
                "agent": self.name,
                "ticket_subject": ticket_subject,
                "operation": "classify_ticket"
            }
            
            # Handle different types of errors
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                logger.warning(f"API quota/rate limit exceeded: {str(e)}")
                handle_error(APIError("gemini", f"Rate limit exceeded: {str(e)}"), error_context)
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                logger.warning(f"Network error during classification: {str(e)}")
                handle_error(RetryableError(f"Network error: {str(e)}"), error_context)
            else:
                logger.error(f"Unexpected error during ticket classification: {str(e)}")
                handle_error(AgentError(self.name, f"Classification failed: {str(e)}"), error_context)
            
            # Always fall back to rule-based classification
            return self._fallback_classification(ticket_subject)
    
    @CircuitBreaker(service_name="gemini_classification", failure_threshold=3, recovery_timeout=30.0)
    async def _classify_with_gemini(self, ticket_subject: str) -> str:
        """
        Perform classification using Gemini API with circuit breaker protection.
        
        Args:
            ticket_subject: The subject line to classify
            
        Returns:
            Classification result
        """
        try:
            # Prepare the prompt with the ticket subject
            prompt = f"{self.system_prompt}\n\nTicket Subject: {ticket_subject}"
            
            # Generate classification using Gemini
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise APIError("gemini", "Empty response from Gemini API")
            
            classification = response.text.strip()
            
            # Validate the classification response
            valid_classifications = ["Phishing/Security", "General Inquiry"]
            if classification in valid_classifications:
                logger.info(f"Classified ticket '{ticket_subject}' as '{classification}'")
                return classification
            else:
                logger.warning(f"Invalid classification response: {classification}. Using fallback.")
                raise APIError("gemini", f"Invalid classification response: {classification}")
                
        except Exception as e:
            # Convert to appropriate error type for circuit breaker
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise RetryableError(f"Gemini API rate limit: {str(e)}", retry_after=5.0)
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise RetryableError(f"Gemini API network error: {str(e)}", retry_after=2.0)
            else:
                raise APIError("gemini", f"Gemini API error: {str(e)}")
    
    def _fallback_classification(self, ticket_subject: str) -> str:
        """
        Fallback classification logic when AI model is unavailable.
        
        Args:
            ticket_subject: The subject line to classify
            
        Returns:
            Classification based on keyword matching
        """
        # Convert to lowercase for case-insensitive matching
        subject_lower = ticket_subject.lower()
        
        # Security-related keywords
        security_keywords = [
            'phishing', 'suspicious', 'malware', 'virus', 'hack', 'breach',
            'security', 'threat', 'spam', 'scam', 'fraud', 'unauthorized',
            'malicious', 'attack', 'compromise', 'infected', 'trojan',
            'ransomware', 'suspicious email', 'fake email', 'spoofed'
        ]
        
        # Check if any security keywords are present
        for keyword in security_keywords:
            if keyword in subject_lower:
                logger.info(f"Fallback classification: '{ticket_subject}' contains security keyword '{keyword}'")
                return "Phishing/Security"
        
        # Default to General Inquiry
        logger.info(f"Fallback classification: '{ticket_subject}' classified as General Inquiry")
        return "General Inquiry"
    
    async def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket by classifying it and preparing routing information with comprehensive error handling.
        
        Args:
            ticket_data: Dictionary containing ticket information
            
        Returns:
            Updated ticket data with classification and routing information
        """
        ticket_subject = ticket_data.get('subject', '')
        ticket_id = ticket_data.get('id', 'Unknown')
        
        try:
            logger.info(f"Processing ticket {ticket_id}: {ticket_subject}")
            
            # Validate input data
            if not ticket_subject.strip():
                raise AgentError(self.name, "Empty ticket subject provided", "INVALID_INPUT")
            
            # Classify the ticket with error handling
            classification = await self.classify_ticket(ticket_subject)
            
            # Update ticket data with classification
            ticket_data['classification'] = classification
            ticket_data['status'] = 'classified'
            ticket_data['processed_by'] = self.name
            ticket_data['processing_timestamp'] = time.time()
            
            # Add routing information based on classification
            if classification == "Phishing/Security":
                ticket_data['assigned_agent'] = 'PhishGuard Agent'
                ticket_data['priority'] = 'high'
                ticket_data['escalation_level'] = 'security'
            else:
                ticket_data['assigned_agent'] = 'General Support Agent'
                ticket_data['priority'] = 'normal'
                ticket_data['escalation_level'] = 'standard'
            
            logger.info(f"Ticket {ticket_id} successfully classified as '{classification}' "
                       f"and assigned to '{ticket_data['assigned_agent']}'")
            
            return ticket_data
            
        except AgentError:
            # Re-raise agent errors as they're already properly formatted
            raise
        except Exception as e:
            # Handle unexpected errors with graceful degradation
            error_context = {
                "agent": self.name,
                "ticket_id": ticket_id,
                "ticket_subject": ticket_subject,
                "operation": "process_ticket"
            }
            
            logger.error(f"Unexpected error processing ticket {ticket_id}: {str(e)}")
            handle_error(AgentError(self.name, f"Ticket processing failed: {str(e)}"), error_context)
            
            # Ensure we always return a valid classification for system stability
            ticket_data.update({
                'classification': 'General Inquiry',
                'assigned_agent': 'General Support Agent',
                'status': 'classified',
                'priority': 'normal',
                'escalation_level': 'standard',
                'processed_by': self.name,
                'processing_timestamp': time.time(),
                'processing_error': str(e),
                'fallback_used': True
            })
            
            logger.info(f"Ticket {ticket_id} processed with fallback classification due to error")
            return ticket_data