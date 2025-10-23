"""
MCP Client for agent tool access.

Provides a client interface for agents to access MCP tools with proper
error handling, logging, and UI update integration.
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional, Union
import os
import sys

from backend.utils.error_handling import (
    MCPError, ToolError, RetryableError, CircuitBreaker,
    retry_with_backoff, handle_error
)

# Configure logging
logger = logging.getLogger("nexusai.tools.mcp_client")

class MCPClient:
    """
    MCP Client for connecting to and invoking tools from MCP servers.
    
    Provides a high-level interface for agents to access security tools
    with proper error handling, retry logic, and logging integration.
    """
    
    def __init__(self, server_command: Optional[List[str]] = None, socketio_client=None):
        """
        Initialize the MCP client with comprehensive error handling.
        
        Args:
            server_command: Command to start the MCP server (if not already running)
            socketio_client: SocketIO client for UI updates
        """
        self.server_command = server_command or [
            sys.executable, "-m", "backend.tools.security_mcp_server"
        ]
        self.socketio_client = socketio_client
        self.server_process = None
        self.is_connected = False
        self.available_tools = []
        
        # Connection settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.connection_timeout = 10.0
        
        # Error tracking
        self.connection_failures = 0
        self.last_connection_attempt = None
        self.tool_call_failures = {}
        
        # Circuit breaker for MCP operations
        self.mcp_circuit_breaker = CircuitBreaker(
            service_name="mcp_server",
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=(MCPError, ToolError, ConnectionError)
        )
        
        logger.info("MCP Client initialized with error handling")
    
    @retry_with_backoff(max_retries=3, base_delay=2.0, retryable_exceptions=(RetryableError, ConnectionError))
    async def connect(self) -> bool:
        """
        Connect to the MCP server with comprehensive error handling.
        
        Returns:
            True if connection successful, False otherwise
        """
        self.last_connection_attempt = time.time()
        
        try:
            logger.info("Connecting to MCP server...")
            
            # For this implementation, we'll simulate the connection
            # In a real implementation, this would establish the MCP protocol connection
            await self._simulate_connection()
            
            self.is_connected = True
            self.connection_failures = 0  # Reset failure count on success
            logger.info("Successfully connected to MCP server")
            return True
            
        except Exception as e:
            self.connection_failures += 1
            error_context = {
                "service": "mcp_server",
                "attempt": self.connection_failures,
                "last_attempt": self.last_connection_attempt
            }
            
            logger.error(f"Failed to connect to MCP server (attempt {self.connection_failures}): {str(e)}")
            handle_error(MCPError(f"Connection failed: {str(e)}"), error_context)
            
            self.is_connected = False
            
            # If too many failures, raise a more serious error
            if self.connection_failures >= self.max_retries:
                raise MCPError(f"MCP server connection failed after {self.connection_failures} attempts")
            
            return False
    
    async def _simulate_connection(self):
        """
        Simulate MCP server connection for demonstration purposes.
        
        In a real implementation, this would:
        1. Start the MCP server process if needed
        2. Establish stdio communication
        3. Perform MCP handshake
        4. List available tools
        """
        # Simulate connection delay
        await asyncio.sleep(0.5)
        
        # Simulate tool discovery
        self.available_tools = [
            {
                "name": "log_action_for_ui",
                "description": "Log an action message for display in the UI dashboard"
            },
            {
                "name": "analyze_email_for_iocs",
                "description": "Analyze an email for Indicators of Compromise (IOCs)"
            },
            {
                "name": "block_malicious_url",
                "description": "Block a malicious URL at the network level"
            },
            {
                "name": "search_and_destroy_email",
                "description": "Search for and remove malicious emails from all user inboxes"
            }
        ]
        
        logger.info(f"Discovered {len(self.available_tools)} available tools")
    
    async def disconnect(self):
        """Disconnect from the MCP server and cleanup resources."""
        try:
            if self.server_process:
                self.server_process.terminate()
                await asyncio.sleep(1.0)
                if self.server_process.poll() is None:
                    self.server_process.kill()
                self.server_process = None
            
            self.is_connected = False
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Error during MCP server disconnect: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        
        Returns:
            List of available tool definitions
        """
        if not self.is_connected:
            await self.connect()
        
        return self.available_tools.copy()
    
    @retry_with_backoff(max_retries=2, base_delay=1.0, retryable_exceptions=(RetryableError, ConnectionError))
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server with comprehensive error handling and logging.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        
        try:
            # Ensure we're connected with circuit breaker protection
            if not self.is_connected:
                connection_success = await self.mcp_circuit_breaker(self.connect)()
                if not connection_success:
                    raise MCPError("Failed to establish MCP server connection")
            
            # Validate tool exists
            tool_names = [tool["name"] for tool in self.available_tools]
            if tool_name not in tool_names:
                raise ToolError(tool_name, f"Tool not available. Available tools: {tool_names}")
            
            # Track tool call attempts
            if tool_name not in self.tool_call_failures:
                self.tool_call_failures[tool_name] = 0
            
            # Log tool invocation
            logger.info(f"Calling MCP tool: {tool_name} with arguments: {arguments}")
            
            # Emit UI update for tool call
            await self._emit_tool_call_update(tool_name, arguments, "started")
            
            # Execute the tool with circuit breaker protection
            result = await self.mcp_circuit_breaker(self._execute_tool_simulation)(tool_name, arguments)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Reset failure count on success
            self.tool_call_failures[tool_name] = 0
            
            # Log successful execution
            logger.info(f"Tool {tool_name} executed successfully in {execution_time:.2f}s")
            
            # Emit UI update for completion
            await self._emit_tool_call_update(tool_name, arguments, "completed", result, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Track failure
            if tool_name in self.tool_call_failures:
                self.tool_call_failures[tool_name] += 1
            
            error_context = {
                "tool_name": tool_name,
                "arguments": arguments,
                "execution_time": execution_time,
                "failure_count": self.tool_call_failures.get(tool_name, 0)
            }
            
            logger.error(f"Tool {tool_name} failed after {execution_time:.2f}s: {str(e)}")
            handle_error(ToolError(tool_name, f"Tool execution failed: {str(e)}"), error_context)
            
            # Emit UI update for failure
            await self._emit_tool_call_update(tool_name, arguments, "failed", {"error": str(e)}, execution_time)
            
            # Handle tool execution failures with retry logic
            return await self._handle_tool_failure(tool_name, arguments, str(e))
    
    async def _execute_tool_simulation(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate tool execution for demonstration purposes.
        
        In a real implementation, this would send the tool call via MCP protocol.
        """
        # Simulate realistic execution time
        await asyncio.sleep(0.5 + (len(str(arguments)) * 0.01))
        
        if tool_name == "log_action_for_ui":
            return await self._simulate_log_action(arguments)
        elif tool_name == "analyze_email_for_iocs":
            return await self._simulate_ioc_analysis(arguments)
        elif tool_name == "block_malicious_url":
            return await self._simulate_url_blocking(arguments)
        elif tool_name == "search_and_destroy_email":
            return await self._simulate_email_removal(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _simulate_log_action(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the log_action_for_ui tool."""
        message = arguments.get("message", "")
        agent = arguments.get("agent", "Unknown Agent")
        status = arguments.get("status", "working")
        
        return {
            "content": [{
                "type": "text",
                "text": f"Successfully logged action for UI: {message}"
            }],
            "success": True,
            "tool": "log_action_for_ui"
        }
    
    async def _simulate_ioc_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the analyze_email_for_iocs tool."""
        email_subject = arguments.get("email_subject", "")
        
        # Simulate IOC detection based on subject content
        suspicious_keywords = ["urgent", "verify", "click", "suspended", "payment"]
        found_iocs = []
        
        subject_lower = email_subject.lower()
        if any(keyword in subject_lower for keyword in suspicious_keywords):
            found_iocs = [
                "http://malicious-phishing-site.com/login",
                "suspicious-sender@fake-domain.com"
            ]
        
        result_text = f"""IOC Analysis Complete:
- Email Subject: {email_subject}
- IOCs Found: {len(found_iocs)}
- Threat Level: {'HIGH' if found_iocs else 'LOW'}

Detected Indicators:
{chr(10).join(f'  • {ioc}' for ioc in found_iocs) if found_iocs else '  • No malicious indicators detected'}"""
        
        return {
            "content": [{
                "type": "text",
                "text": result_text
            }],
            "success": True,
            "tool": "analyze_email_for_iocs",
            "iocs_found": len(found_iocs),
            "indicators": found_iocs
        }
    
    async def _simulate_url_blocking(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the block_malicious_url tool."""
        url = arguments.get("url", "")
        reason = arguments.get("reason", "Malicious content detected")
        
        block_id = f"BLK-{int(time.time() * 1000) % 1000000}"
        
        result_text = f"""URL Blocking Complete:
- URL: {url}
- Block ID: {block_id}
- Method: Firewall rule
- Reason: {reason}
- Status: BLOCKED

The malicious URL has been successfully blocked across all network access points."""
        
        return {
            "content": [{
                "type": "text",
                "text": result_text
            }],
            "success": True,
            "tool": "block_malicious_url",
            "block_id": block_id,
            "url": url
        }
    
    async def _simulate_email_removal(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the search_and_destroy_email tool."""
        search_criteria = arguments.get("search_criteria", "")
        search_type = arguments.get("search_type", "subject")
        
        # Simulate realistic numbers
        import random
        total_mailboxes = random.randint(150, 300)
        emails_found = random.randint(5, 25)
        
        result_text = f"""Email Search and Destroy Complete:
- Search Criteria: {search_criteria}
- Search Type: {search_type}
- Mailboxes Scanned: {total_mailboxes}
- Malicious Emails Found: {emails_found}
- Emails Successfully Removed: {emails_found}

All identified malicious emails have been quarantined and removed from user inboxes."""
        
        return {
            "content": [{
                "type": "text",
                "text": result_text
            }],
            "success": True,
            "tool": "search_and_destroy_email",
            "emails_found": emails_found,
            "emails_removed": emails_found
        }
    
    async def _emit_tool_call_update(self, tool_name: str, arguments: Dict[str, Any], 
                                   status: str, result: Optional[Dict[str, Any]] = None,
                                   execution_time: Optional[float] = None):
        """
        Emit UI update for tool call progress.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
            status: Call status (started, completed, failed)
            result: Tool execution result (if completed)
            execution_time: Execution time in seconds
        """
        try:
            if self.socketio_client:
                update_data = {
                    'type': 'tool_call',
                    'tool_name': tool_name,
                    'arguments': arguments,
                    'status': status,
                    'timestamp': time.time()
                }
                
                if result:
                    update_data['result'] = result
                if execution_time:
                    update_data['execution_time'] = execution_time
                
                self.socketio_client.emit('tool_call_update', update_data)
                logger.debug(f"Emitted tool call update: {tool_name} - {status}")
            
        except Exception as e:
            logger.error(f"Error emitting tool call update: {str(e)}")
    
    async def _handle_tool_failure(self, tool_name: str, arguments: Dict[str, Any], 
                                 error_message: str) -> Dict[str, Any]:
        """
        Handle tool execution failures with retry logic.
        
        Args:
            tool_name: Name of the failed tool
            arguments: Tool arguments
            error_message: Error message from the failure
            
        Returns:
            Error result or retry result
        """
        # For critical tools, we might want to retry
        critical_tools = ["block_malicious_url", "search_and_destroy_email"]
        
        if tool_name in critical_tools:
            logger.warning(f"Critical tool {tool_name} failed, implementing fallback")
            
            # Return a fallback result indicating manual intervention needed
            return {
                "content": [{
                    "type": "text",
                    "text": f"Tool {tool_name} failed: {error_message}. Manual intervention required."
                }],
                "success": False,
                "tool": tool_name,
                "error": error_message,
                "requires_manual_intervention": True
            }
        else:
            # For non-critical tools, return the error
            return {
                "content": [{
                    "type": "text",
                    "text": f"Tool execution failed: {error_message}"
                }],
                "success": False,
                "tool": tool_name,
                "error": error_message
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the MCP connection.
        
        Returns:
            Health status information
        """
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "message": "Not connected to MCP server"
                }
            
            # Test with a simple tool call
            test_result = await self.call_tool("log_action_for_ui", {
                "message": "Health check test",
                "agent": "MCP Client",
                "status": "testing"
            })
            
            return {
                "status": "healthy",
                "message": "MCP connection is working properly",
                "available_tools": len(self.available_tools),
                "test_result": test_result.get("success", False)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "error": str(e)
            }
    
    def __del__(self):
        """Cleanup on object destruction."""
        if self.server_process:
            try:
                self.server_process.terminate()
            except:
                pass