"""
Comprehensive error handling and logging utilities for NexusAI.

Provides centralized error handling, retry mechanisms, and logging
configuration for robust system operation.
"""

import asyncio
import functools
import logging
import sys
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime
import json


class NexusAIError(Exception):
    """Base exception class for NexusAI system errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "NEXUS_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class AgentError(NexusAIError):
    """Exception for agent-related errors."""
    
    def __init__(self, agent_name: str, message: str, error_code: str = "AGENT_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.agent_name = agent_name


class ToolError(NexusAIError):
    """Exception for tool execution errors."""
    
    def __init__(self, tool_name: str, message: str, error_code: str = "TOOL_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.tool_name = tool_name


class WorkflowError(NexusAIError):
    """Exception for workflow processing errors."""
    
    def __init__(self, workflow_id: str, message: str, error_code: str = "WORKFLOW_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.workflow_id = workflow_id


class MCPError(NexusAIError):
    """Exception for MCP-related errors."""
    
    def __init__(self, message: str, error_code: str = "MCP_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


class APIError(NexusAIError):
    """Exception for external API errors."""
    
    def __init__(self, api_name: str, message: str, error_code: str = "API_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.api_name = api_name


class RetryableError(NexusAIError):
    """Exception for errors that should be retried."""
    
    def __init__(self, message: str, retry_after: float = 1.0, max_retries: int = 3, 
                 error_code: str = "RETRYABLE_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.retry_after = retry_after
        self.max_retries = max_retries


class CircuitBreakerError(NexusAIError):
    """Exception for circuit breaker activation."""
    
    def __init__(self, service_name: str, message: str = None, error_code: str = "CIRCUIT_BREAKER_OPEN"):
        message = message or f"Circuit breaker is open for service: {service_name}"
        super().__init__(message, error_code)
        self.service_name = service_name


class ErrorHandler:
    """Centralized error handling and logging system."""
    
    def __init__(self, logger_name: str = "nexusai"):
        self.logger = logging.getLogger(logger_name)
        self.error_counts = {}
        self.circuit_breakers = {}
        
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and response generation.
        
        Args:
            error: The exception to handle
            context: Additional context information
            
        Returns:
            Error response dictionary
        """
        context = context or {}
        
        # Extract error information
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        
        # Add specific error details for NexusAI errors
        if isinstance(error, NexusAIError):
            error_info.update({
                "error_code": error.error_code,
                "details": error.details
            })
            
            # Add specific fields for different error types
            if isinstance(error, AgentError):
                error_info["agent_name"] = error.agent_name
            elif isinstance(error, ToolError):
                error_info["tool_name"] = error.tool_name
            elif isinstance(error, WorkflowError):
                error_info["workflow_id"] = error.workflow_id
            elif isinstance(error, APIError):
                error_info["api_name"] = error.api_name
        
        # Add stack trace for debugging
        error_info["traceback"] = traceback.format_exc()
        
        # Log the error
        self._log_error(error, error_info)
        
        # Update error counts for monitoring
        self._update_error_counts(error_info["type"])
        
        return error_info
    
    def _log_error(self, error: Exception, error_info: Dict[str, Any]):
        """Log error with appropriate level and formatting."""
        
        # Determine log level based on error type
        if isinstance(error, (RetryableError, CircuitBreakerError)):
            log_level = logging.WARNING
        elif isinstance(error, (AgentError, ToolError, WorkflowError)):
            log_level = logging.ERROR
        else:
            log_level = logging.CRITICAL
        
        # Format log message
        log_message = f"{error_info['type']}: {error_info['message']}"
        if error_info.get("context"):
            log_message += f" | Context: {json.dumps(error_info['context'])}"
        
        # Log with appropriate level
        self.logger.log(log_level, log_message, extra={"error_info": error_info})
    
    def _update_error_counts(self, error_type: str):
        """Update error counts for monitoring and circuit breaker logic."""
        current_time = time.time()
        
        if error_type not in self.error_counts:
            self.error_counts[error_type] = []
        
        # Add current error timestamp
        self.error_counts[error_type].append(current_time)
        
        # Clean up old entries (keep last hour)
        cutoff_time = current_time - 3600  # 1 hour
        self.error_counts[error_type] = [
            timestamp for timestamp in self.error_counts[error_type] 
            if timestamp > cutoff_time
        ]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics."""
        current_time = time.time()
        stats = {}
        
        for error_type, timestamps in self.error_counts.items():
            # Count errors in different time windows
            last_hour = sum(1 for t in timestamps if t > current_time - 3600)
            last_15_min = sum(1 for t in timestamps if t > current_time - 900)
            last_5_min = sum(1 for t in timestamps if t > current_time - 300)
            
            stats[error_type] = {
                "last_hour": last_hour,
                "last_15_min": last_15_min,
                "last_5_min": last_5_min,
                "total_tracked": len(timestamps)
            }
        
        return stats


class CircuitBreaker:
    """Circuit breaker implementation for service protection."""
    
    def __init__(self, service_name: str, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0, expected_exception: Type[Exception] = Exception):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        self.logger = logging.getLogger(f"circuit_breaker.{service_name}")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker logic."""
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._call_async(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self._call_sync(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _call_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerError(self.service_name)
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _call_sync(self, func: Callable, *args, **kwargs):
        """Execute sync function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerError(self.service_name)
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.logger.info(f"Circuit breaker for {self.service_name} reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker for {self.service_name} opened after {self.failure_count} failures")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      max_delay: float = 60.0, backoff_factor: float = 2.0,
                      retryable_exceptions: tuple = (RetryableError, ConnectionError, TimeoutError)):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        retryable_exceptions: Tuple of exceptions that should trigger retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed
                        logger = logging.getLogger(func.__module__)
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Calculate next delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                                 f"retrying in {actual_delay:.1f}s: {str(e)}")
                    
                    await asyncio.sleep(actual_delay)
                    delay *= backoff_factor
                except Exception as e:
                    # Non-retryable exception
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"Function {func.__name__} failed with non-retryable error: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed
                        logger = logging.getLogger(func.__module__)
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Calculate next delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                                 f"retrying in {actual_delay:.1f}s: {str(e)}")
                    
                    time.sleep(actual_delay)
                    delay *= backoff_factor
                except Exception as e:
                    # Non-retryable exception
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"Function {func.__name__} failed with non-retryable error: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def configure_logging(log_level: str = "INFO", log_format: str = None, 
                     log_file: str = None, enable_json_logging: bool = False) -> logging.Logger:
    """
    Configure comprehensive logging for the NexusAI system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Optional file path for log output
        enable_json_logging: Enable structured JSON logging
        
    Returns:
        Configured logger instance
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Default format
    if log_format is None:
        if enable_json_logging:
            log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        else:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers_config = {
        "nexusai": log_level,
        "nexusai.agents": log_level,
        "nexusai.workflow": log_level,
        "nexusai.tools": log_level,
        "nexusai.web": log_level,
        "werkzeug": "WARNING",  # Reduce Flask noise
        "socketio": "WARNING",   # Reduce SocketIO noise
        "engineio": "WARNING"    # Reduce EngineIO noise
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Log configuration
    main_logger = logging.getLogger("nexusai")
    main_logger.info(f"Logging configured - Level: {log_level}, JSON: {enable_json_logging}")
    if log_file:
        main_logger.info(f"Log file: {log_file}")
    
    return main_logger


def graceful_shutdown_handler(shutdown_callback: Callable = None):
    """
    Decorator for graceful shutdown handling.
    
    Args:
        shutdown_callback: Optional callback function to execute during shutdown
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except KeyboardInterrupt:
                logger = logging.getLogger(func.__module__)
                logger.info("Shutdown signal received, initiating graceful shutdown...")
                
                if shutdown_callback:
                    try:
                        if asyncio.iscoroutinefunction(shutdown_callback):
                            await shutdown_callback()
                        else:
                            shutdown_callback()
                    except Exception as e:
                        logger.error(f"Error during shutdown callback: {str(e)}")
                
                logger.info("Graceful shutdown completed")
                raise
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                logger = logging.getLogger(func.__module__)
                logger.info("Shutdown signal received, initiating graceful shutdown...")
                
                if shutdown_callback:
                    try:
                        shutdown_callback()
                    except Exception as e:
                        logger.error(f"Error during shutdown callback: {str(e)}")
                
                logger.info("Graceful shutdown completed")
                raise
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function for global error handling."""
    return global_error_handler.handle_error(error, context)