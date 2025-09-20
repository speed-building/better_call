from typing import Any, Dict, Optional


class BetterCallException(Exception):
    """Base exception for Better Call application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TwilioConfigurationError(BetterCallException):
    """Raised when Twilio configuration is missing or invalid."""
    pass


class OpenAIServiceError(BetterCallException):
    """Raised when OpenAI service encounters an error."""
    pass


class DatabaseError(BetterCallException):
    """Raised when database operations fail."""
    pass


class CallServiceError(BetterCallException):
    """Raised when call service operations fail."""
    pass
