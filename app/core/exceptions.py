"""
Custom exceptions for the BuildWise application
"""


class BuildWiseException(Exception):
    """Base exception for BuildWise application"""
    pass


class NotFoundException(BuildWiseException):
    """Exception raised when a resource is not found"""
    pass


class ForbiddenException(BuildWiseException):
    """Exception raised when access is forbidden"""
    pass


class ConflictException(BuildWiseException):
    """Exception raised when there's a conflict with existing data"""
    pass


class ValidationException(BuildWiseException):
    """Exception raised when validation fails"""
    pass


class AuthenticationException(BuildWiseException):
    """Exception raised when authentication fails"""
    pass