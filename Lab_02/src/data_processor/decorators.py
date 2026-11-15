"""Decorators and operation history tracking using collections.deque."""

from collections import deque
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

# Bounded double-ended queue storing the history of the last 15 executed operations
OPERATION_HISTORY: deque[str] = deque(maxlen=15)


def record_operation(entry: str) -> None:
    """Append an operation entry to the bounded history deque."""
    OPERATION_HISTORY.append(entry)


def get_operation_history() -> list[str]:
    """Return a snapshot list of recorded operations from the deque."""
    return list(OPERATION_HISTORY)


def clear_operation_history() -> None:
    """Clear all entries from the operation history deque."""
    OPERATION_HISTORY.clear()


def measure_time(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that measures and prints function execution time."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - start
        message = f"{func.__name__}: {elapsed:.8f} s"
        record_operation(message)
        print(message)
        return result

    return wrapper


def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that logs function invocation and records it in history."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        record_operation(f"Called {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def repeat(count: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Parameterized decorator that executes the wrapped function `count` times."""
    if count <= 0:
        raise ValueError("Repeat count must be a positive integer.")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result: Any = None
            for _ in range(count):
                result = func(*args, **kwargs)
            record_operation(f"Repeated {func.__name__} x{count}")
            return result  # type: ignore[no-any-return]

        return wrapper

    return decorator

