class EntityNotFoundError(Exception):
    """Raised when a requested entity cannot be found."""


class AccessDeniedError(Exception):
    """Raised when access to a resource is denied."""


class ExternalServiceError(Exception):
    """Raised when an external service fails unexpectedly."""
