"""
exceptions.py
Custom exception hierarchy for the Contact Manager application.
Using specific exceptions (instead of generic Exception) makes error
handling more precise and the code easier to debug/maintain.
"""


class ContactManagerError(Exception):
    """Base exception for all application-specific errors."""
    pass


class ValidationError(ContactManagerError):
    """Raised when user input fails validation rules."""
    pass


class RecordNotFoundError(ContactManagerError):
    """Raised when a requested record does not exist in the database."""
    pass


class DatabaseConnectionError(ContactManagerError):
    """Raised when the application fails to connect to / initialize the database."""
    pass


class DuplicateRecordError(ContactManagerError):
    """Raised when attempting to create a record that violates uniqueness rules."""
    pass
