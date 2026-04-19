"""Logging middleware for FastAPI application."""
import logging
import time
import re
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Patterns for PII anonymization
PII_PATTERNS = [
    (re.compile(r'\b\d{10,}\b'), '[PHONE]'),  # Phone numbers
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),  # Email addresses
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '[CARD]'),  # Credit card numbers
    (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password": "[REDACTED]"'),  # Password fields
    (re.compile(r'"token"\s*:\s*"[^"]*"'), '"token": "[REDACTED]"'),  # Token fields
]


def anonymize_pii(text: str) -> str:
    """Anonymize personally identifiable information in text.
    
    Args:
        text: Text that may contain PII
        
    Returns:
        Text with PII replaced by placeholders
    """
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses with PII anonymization."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        # Generate request ID for tracking
        request_id = f"{int(time.time() * 1000)}"
        
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Anonymize path if it contains potential PII
        safe_path = anonymize_pii(path)
        
        # Log request
        logger.info(
            f"[{request_id}] {method} {safe_path} - Client: {client_host}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] {method} {safe_path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error with anonymized details
            error_msg = anonymize_pii(str(exc))
            logger.error(
                f"[{request_id}] {method} {safe_path} - "
                f"Error: {error_msg} - "
                f"Duration: {duration:.3f}s",
                exc_info=True
            )
            raise
