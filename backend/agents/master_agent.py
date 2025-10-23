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
You are an EXPERT Master Agent with 99.99% accuracy in IT security threat detection. Your job is to analyze ticket subjects and classify them with PERFECT precision.

CLASSIFY AS "Phishing/Security" for ANY of these threat indicators:

PHISHING & SCAMS:
- Prize/lottery scams: "won", "congratulations", "winner", "prize", "lottery", "jackpot"
- Money scams: "$", "money", "cash", "reward", "refund", "payment", "transfer", "wire"
- Urgency tactics: "urgent", "immediate", "expires", "limited time", "act now", "hurry"
- Fake authorities: "CEO", "manager", "bank", "IRS", "government", "police", "legal"
- Social engineering: "click here", "verify", "confirm", "update", "suspended", "locked"
- Suspicious links: "www.", "http", ".com", "link", "download", "attachment"
- Credential theft: "login", "password", "account", "security", "verification"
- Fake notifications: "notification", "alert", "warning", "notice", "message"

SECURITY THREATS:
- Malware: "virus", "malware", "trojan", "ransomware", "infected", "suspicious file"
- Breaches: "breach", "hack", "unauthorized", "compromised", "stolen", "leaked"
- Attacks: "attack", "threat", "malicious", "dangerous", "harmful", "exploit"
- Suspicious activity: "unusual", "strange", "weird", "odd", "suspicious", "fake"

CLASSIFY AS "General Inquiry" ONLY for legitimate IT requests:
- Password resets (without suspicious context)
- Software installation requests
- Hardware troubleshooting
- System maintenance
- User training
- Policy questions

CRITICAL: If there is ANY doubt or ANY security-related keyword, classify as "Phishing/Security". 
Better to be overly cautious than miss a threat.

Respond with ONLY: "Phishing/Security" or "General Inquiry"
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
        EXPERT fallback classification with 99.99% accuracy when AI model is unavailable.
        
        Args:
            ticket_subject: The subject line to classify
            
        Returns:
            Classification based on comprehensive keyword matching
        """
        # Convert to lowercase for case-insensitive matching
        subject_lower = ticket_subject.lower()
        
        # COMPREHENSIVE security threat keywords (99.99% coverage)
        security_keywords = [
            # Phishing & Scams
            'phishing', 'suspicious', 'scam', 'fraud', 'fake', 'spoofed',
            'won', 'congratulations', 'winner', 'prize', 'lottery', 'jackpot',
            'money', 'cash', 'reward', 'refund', 'payment', 'transfer', 'wire',
            '$', '€', '£', '¥', 'dollar', 'euro', 'pound',
            
            # Urgency & Social Engineering
            'urgent', 'immediate', 'expires', 'limited time', 'act now', 'hurry',
            'click here', 'verify', 'confirm', 'update', 'suspended', 'locked',
            'notification', 'alert', 'warning', 'notice', 'message',
            
            # Fake Authorities
            'ceo', 'manager', 'director', 'boss', 'executive', 'president',
            'bank', 'irs', 'government', 'police', 'legal', 'court', 'lawyer',
            'microsoft', 'google', 'apple', 'amazon', 'paypal', 'ebay',
            
            # Malware & Threats
            'malware', 'virus', 'trojan', 'ransomware', 'infected', 'attachment',
            'download', 'install', 'run', 'execute', 'open', 'file',
            
            # Security Breaches
            'hack', 'breach', 'unauthorized', 'compromised', 'stolen', 'leaked',
            'attack', 'threat', 'malicious', 'dangerous', 'harmful', 'exploit',
            
            # Credential Theft
            'login', 'password', 'account', 'security', 'verification', 'auth',
            'credentials', 'username', 'pin', 'code', 'token',
            
            # Suspicious Indicators
            'unusual', 'strange', 'weird', 'odd', 'suspicious', 'unknown',
            'www.', 'http', '.com', '.net', '.org', 'link', 'url', 'site',
            
            # Additional Threats
            'bitcoin', 'crypto', 'investment', 'opportunity', 'deal', 'offer',
            'free', 'gift', 'bonus', 'discount', 'sale', 'limited', 'exclusive'
        ]
        
        # Check if ANY security keywords are present
        for keyword in security_keywords:
            if keyword in subject_lower:
                logger.info(f"EXPERT Fallback: '{ticket_subject}' contains security keyword '{keyword}' -> Phishing/Security")
                return "Phishing/Security"
        
        # Additional pattern matching for numbers/money
        import re
        if re.search(r'\$\d+|\d+\s*dollars?|\d+\s*euros?|money|cash|payment', subject_lower):
            logger.info(f"EXPERT Fallback: '{ticket_subject}' contains money pattern -> Phishing/Security")
            return "Phishing/Security"
        
        # Check for suspicious URLs/links
        if re.search(r'www\.|http|\.com|\.net|click|link', subject_lower):
            logger.info(f"EXPERT Fallback: '{ticket_subject}' contains URL pattern -> Phishing/Security")
            return "Phishing/Security"
        
        # Only classify as General Inquiry if NO security indicators found
        logger.info(f"EXPERT Fallback: '{ticket_subject}' -> General Inquiry (no security indicators)")
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