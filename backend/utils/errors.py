"""
Custom exception classes for the platform.
"""


class PlatformError(Exception):
    """Base exception for all platform errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AgentError(PlatformError):
    """Raised when an agent encounters an error during execution."""
    pass


class CommunicationError(PlatformError):
    """Raised when inter-agent communication fails."""
    pass


class LLMError(PlatformError):
    """Raised when LLM provider encounters an error."""
    pass


class ConfigurationError(PlatformError):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(PlatformError):
    """Raised when database operations fail."""
    pass


class ValidationError(PlatformError):
    """Raised when data validation fails."""
    pass
