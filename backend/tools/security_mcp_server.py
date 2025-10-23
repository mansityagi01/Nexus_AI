"""
MCP Security Tools Server

Provides security tools to agents via Model Context Protocol.
Implements simulated security tools for demonstration purposes.
"""

import asyncio
import json
import logging
import random
import time
import argparse
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("security-tools")

# Simulated data for realistic responses
SAMPLE_IOCS = [
    "http://malicious-phishing-site.com/login",
    "http://evil-domain.net/steal-credentials",
    "attachment_malware.exe",
    "192.168.1.100",
    "suspicious-sender@fake-domain.com"
]

SAMPLE_EMAIL_SUBJECTS = [
    "Urgent: Verify your account immediately",
    "Your package delivery failed - click here",
    "Security alert: Suspicious login detected",
    "Invoice payment required - download attachment",
    "Your account will be suspended"
]


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available security tools."""
    return [
        Tool(
            name="log_action_for_ui",
            description="Log an action message for display in the UI dashboard",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to log for UI display"
                    },
                    "agent": {
                        "type": "string",
                        "description": "The name of the agent performing the action"
                    },
                    "status": {
                        "type": "string",
                        "description": "The current status of the workflow"
                    }
                },
                "required": ["message", "agent"]
            }
        ),
        Tool(
            name="analyze_email_for_iocs",
            description="Analyze an email for Indicators of Compromise (IOCs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_subject": {
                        "type": "string",
                        "description": "The subject line of the email to analyze"
                    },
                    "email_content": {
                        "type": "string",
                        "description": "The content of the email to analyze (optional)"
                    }
                },
                "required": ["email_subject"]
            }
        ),
        Tool(
            name="block_malicious_url",
            description="Block a malicious URL at the network level",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The malicious URL to block"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="search_and_remove_emails",
            description="Search for and remove malicious emails from all inboxes",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_criteria": {
                        "type": "string",
                        "description": "Criteria to search for malicious emails"
                    }
                },
                "required": ["search_criteria"]
            }
        ),
        Tool(
            name="document_incident",
            description="Document the security incident and resolution",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_summary": {
                        "type": "string",
                        "description": "Summary of the security incident"
                    },
                    "actions_taken": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of actions taken to resolve the incident"
                    }
                },
                "required": ["incident_summary", "actions_taken"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool execution requests."""
    
    # Add realistic delay for demonstration
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    if name == "log_action_for_ui":
        message = arguments.get("message", "")
        agent = arguments.get("agent", "Unknown Agent")
        status = arguments.get("status", "in_progress")
        
        logger.info(f"UI Log - {agent}: {message}")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Logged: {message}",
                        "agent": agent,
                        "status": status,
                        "timestamp": time.time()
                    })
                )
            ]
        )
    
    elif name == "analyze_email_for_iocs":
        email_subject = arguments.get("email_subject", "")
        
        # Simulate IOC analysis
        iocs_found = random.sample(SAMPLE_IOCS, random.randint(2, 4))
        
        result = {
            "success": True,
            "email_subject": email_subject,
            "iocs_found": iocs_found,
            "threat_level": "high" if "suspicious" in email_subject.lower() else "medium",
            "analysis_time": f"{random.uniform(1.2, 3.5):.1f} seconds"
        }
        
        logger.info(f"IOC Analysis completed for: {email_subject}")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result)
                )
            ]
        )
    
    elif name == "block_malicious_url":
        url = arguments.get("url", "")
        
        result = {
            "success": True,
            "blocked_url": url,
            "block_method": "DNS blacklist + Firewall rule",
            "affected_users": random.randint(15, 150),
            "block_time": f"{random.uniform(0.8, 2.1):.1f} seconds"
        }
        
        logger.info(f"Blocked malicious URL: {url}")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result)
                )
            ]
        )
    
    elif name == "search_and_remove_emails":
        search_criteria = arguments.get("search_criteria", "")
        
        emails_found = random.randint(8, 25)
        
        result = {
            "success": True,
            "search_criteria": search_criteria,
            "emails_found": emails_found,
            "emails_removed": emails_found,
            "inboxes_scanned": random.randint(50, 200),
            "scan_time": f"{random.uniform(2.5, 5.8):.1f} seconds"
        }
        
        logger.info(f"Email removal completed: {emails_found} emails removed")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result)
                )
            ]
        )
    
    elif name == "document_incident":
        incident_summary = arguments.get("incident_summary", "")
        actions_taken = arguments.get("actions_taken", [])
        
        incident_id = f"INC-{random.randint(10000, 99999)}"
        
        result = {
            "success": True,
            "incident_id": incident_id,
            "incident_summary": incident_summary,
            "actions_taken": actions_taken,
            "documentation_complete": True,
            "compliance_status": "SOC 2 compliant",
            "created_timestamp": time.time()
        }
        
        logger.info(f"Incident documented with ID: {incident_id}")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result)
                )
            ]
        )
    
    else:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    })
                )
            ]
        )


async def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="NexusAI Security Tools MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    logger.info(f"Starting MCP Security Tools Server on {args.host}:{args.port}")
    
    # For now, we'll use stdio server as MCP typically uses stdio
    # In a real implementation, you might want to use HTTP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="security-tools",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP server shutdown requested")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        sys.exit(1)
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The malicious URL to block"
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for blocking this URL"
                    }
                },
                "required": ["url", "reason"]
            }
        ),
        Tool(
            name="search_and_destroy_email",
            description="Search for and remove malicious emails from all user inboxes",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_criteria": {
                        "type": "string",
                        "description": "The criteria to search for (subject, sender, etc.)"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["subject", "sender", "attachment", "url"],
                        "description": "The type of search to perform"
                    }
                },
                "required": ["search_criteria", "search_type"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls from agents."""
    
    # Add realistic response time simulation
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    try:
        if name == "log_action_for_ui":
            return await _log_action_for_ui(arguments)
        elif name == "analyze_email_for_iocs":
            return await _analyze_email_for_iocs(arguments)
        elif name == "block_malicious_url":
            return await _block_malicious_url(arguments)
        elif name == "search_and_destroy_email":
            return await _search_and_destroy_email(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )
            ]
        )


async def _log_action_for_ui(arguments: Dict[str, Any]) -> CallToolResult:
    """Log an action message for UI display."""
    message = arguments.get("message", "")
    agent = arguments.get("agent", "Unknown Agent")
    status = arguments.get("status", "working")
    
    # Simulate logging to UI system
    log_entry = {
        "timestamp": time.time(),
        "agent": agent,
        "message": message,
        "status": status
    }
    
    logger.info(f"UI Log: {agent} - {message}")
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Successfully logged action for UI: {message}"
            )
        ]
    )


async def _analyze_email_for_iocs(arguments: Dict[str, Any]) -> CallToolResult:
    """Analyze an email for Indicators of Compromise."""
    email_subject = arguments.get("email_subject", "")
    email_content = arguments.get("email_content", "")
    
    # Simulate IOC analysis with realistic results
    found_iocs = []
    
    # Check for suspicious keywords and patterns
    suspicious_keywords = ["urgent", "verify", "click here", "suspended", "payment", "invoice"]
    phishing_indicators = ["login", "credentials", "account", "security alert"]
    
    subject_lower = email_subject.lower()
    
    # Simulate finding IOCs based on content
    if any(keyword in subject_lower for keyword in suspicious_keywords):
        # Add some sample malicious URLs
        found_iocs.extend(random.sample(SAMPLE_IOCS[:2], random.randint(1, 2)))
    
    if any(indicator in subject_lower for indicator in phishing_indicators):
        # Add suspicious sender
        found_iocs.append(SAMPLE_IOCS[4])  # suspicious sender
        
    # Add random IP if content suggests network activity
    if "click" in subject_lower or "download" in subject_lower:
        found_iocs.append(SAMPLE_IOCS[3])  # suspicious IP
    
    # Simulate attachment analysis
    if "attachment" in subject_lower or "download" in subject_lower:
        found_iocs.append(SAMPLE_IOCS[2])  # malicious attachment
    
    analysis_result = {
        "email_subject": email_subject,
        "iocs_found": len(found_iocs),
        "indicators": found_iocs,
        "threat_level": "HIGH" if len(found_iocs) > 2 else "MEDIUM" if found_iocs else "LOW",
        "analysis_time": f"{random.uniform(1.2, 3.5):.1f}s"
    }
    
    result_text = f"""IOC Analysis Complete:
- Email Subject: {email_subject}
- IOCs Found: {len(found_iocs)}
- Threat Level: {analysis_result['threat_level']}
- Analysis Time: {analysis_result['analysis_time']}

Detected Indicators:
{chr(10).join(f'  • {ioc}' for ioc in found_iocs) if found_iocs else '  • No malicious indicators detected'}"""
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=result_text
            )
        ]
    )


async def _block_malicious_url(arguments: Dict[str, Any]) -> CallToolResult:
    """Block a malicious URL at the network level."""
    url = arguments.get("url", "")
    reason = arguments.get("reason", "Malicious content detected")
    
    # Simulate network blocking operation
    blocking_methods = [
        "DNS blackhole",
        "Firewall rule",
        "Proxy filter",
        "Web gateway block"
    ]
    
    method = random.choice(blocking_methods)
    block_id = f"BLK-{random.randint(100000, 999999)}"
    
    # Simulate processing time
    processing_time = random.uniform(0.8, 2.2)
    
    result_text = f"""URL Blocking Complete:
- URL: {url}
- Block ID: {block_id}
- Method: {method}
- Reason: {reason}
- Processing Time: {processing_time:.1f}s
- Status: BLOCKED

The malicious URL has been successfully blocked across all network access points."""
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=result_text
            )
        ]
    )


async def _search_and_destroy_email(arguments: Dict[str, Any]) -> CallToolResult:
    """Search for and remove malicious emails from all user inboxes."""
    search_criteria = arguments.get("search_criteria", "")
    search_type = arguments.get("search_type", "subject")
    
    # Simulate email search and removal
    total_mailboxes = random.randint(150, 300)
    emails_found = random.randint(5, 25)
    emails_removed = emails_found  # Assume all found emails are successfully removed
    
    # Simulate processing time based on scope
    processing_time = random.uniform(3.0, 8.0)
    
    # Generate some sample affected users
    sample_users = [
        f"user{random.randint(1, 999)}@company.com" 
        for _ in range(min(5, emails_found))
    ]
    
    result_text = f"""Email Search and Destroy Complete:
- Search Criteria: {search_criteria}
- Search Type: {search_type}
- Mailboxes Scanned: {total_mailboxes}
- Malicious Emails Found: {emails_found}
- Emails Successfully Removed: {emails_removed}
- Processing Time: {processing_time:.1f}s

Sample Affected Users:
{chr(10).join(f'  • {user}' for user in sample_users)}

All identified malicious emails have been quarantined and removed from user inboxes."""
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=result_text
            )
        ]
    )


def run_mcp_server(host: str = "localhost", port: int = 8000):
    """
    Run the MCP server with proper host/port binding and configuration.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
    """
    import os
    import sys
    
    # Validate environment variables
    required_env_vars = []  # Add any required env vars here
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Configure server settings from environment
    server_host = os.getenv("MCP_SERVER_HOST", host)
    server_port = int(os.getenv("MCP_SERVER_PORT", port))
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    logger.info(f"Starting Security Tools MCP Server on {server_host}:{server_port}")
    logger.info(f"Log level: {log_level}")
    
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Security Tools MCP Server...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="security-tools",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    )
                )
            )
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise


def validate_configuration():
    """
    Validate server configuration and environment variables.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    import os
    
    # Check for optional configuration
    config_items = {
        "MCP_SERVER_HOST": os.getenv("MCP_SERVER_HOST", "localhost"),
        "MCP_SERVER_PORT": os.getenv("MCP_SERVER_PORT", "8000"),
        "MCP_LOG_LEVEL": os.getenv("MCP_LOG_LEVEL", "INFO")
    }
    
    logger.info("MCP Server Configuration:")
    for key, value in config_items.items():
        logger.info(f"  {key}: {value}")
    
    # Validate port is numeric
    try:
        port = int(config_items["MCP_SERVER_PORT"])
        if not (1 <= port <= 65535):
            logger.error(f"Invalid port number: {port}. Must be between 1 and 65535.")
            return False
    except ValueError:
        logger.error(f"Invalid port number: {config_items['MCP_SERVER_PORT']}. Must be numeric.")
        return False
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config_items["MCP_LOG_LEVEL"].upper() not in valid_log_levels:
        logger.error(f"Invalid log level: {config_items['MCP_LOG_LEVEL']}. Must be one of: {', '.join(valid_log_levels)}")
        return False
    
    return True


if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Security Tools MCP Server")
    parser.add_argument(
        "--host", 
        default="localhost", 
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set environment variables from command line args
    import os
    os.environ["MCP_SERVER_HOST"] = args.host
    os.environ["MCP_SERVER_PORT"] = str(args.port)
    os.environ["MCP_LOG_LEVEL"] = args.log_level
    
    # Validate configuration before starting
    if not validate_configuration():
        sys.exit(1)
    
    # Run the server
    run_mcp_server(args.host, args.port)