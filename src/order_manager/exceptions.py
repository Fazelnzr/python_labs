"""Custom exceptions for the order management domain."""


class OrderError(Exception):
    """Base exception for all order-related domain errors."""


class OrderValidationError(OrderError):
    """Raised when order attributes fail business validation rules."""


class OrderNotFoundError(OrderError):
    """Raised when an order with the specified ID does not exist."""


class DuplicateOrderError(OrderError):
    """Raised when attempting to add an order with an existing ID."""
