class MelodiaError(Exception):
    """Base exception for the app"""
    pass


class ValidationError(MelodiaError):
    """Data validation errors"""
    pass


class NotFoundError(MelodiaError):
    """Errors when a resource is not found"""
    pass


class DatabaseError(MelodiaError):
    """Database-related errors"""
    pass


class AuthenticationError(MelodiaError):
    """Authentication-related errors"""
    pass
