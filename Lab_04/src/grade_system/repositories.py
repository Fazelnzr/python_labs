"""Узагальнене сховище даних (Generic Repository) із використанням TypeVar та Generic[T]."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from grade_system.protocols import HasId

# Bound TypeVar: тип T повинен мати атрибут id: int (відповідати протоколу HasId)
T = TypeVar("T", bound=HasId)

# Constrained TypeVar: демонстрація обмеженого TypeVar для числових розрахунків
NumericScore = TypeVar("NumericScore", int, float)


def scale_score(value: NumericScore, factor: float) -> float:
    """Масштабує числове значення оцінки (демонстрація constrained TypeVar)."""
    return float(value) * factor


class InMemoryRepository(Generic[T]):
    """Типізований узагальнений репозиторій у пам'яті для будь-яких сутностей із HasId."""

    def __init__(self) -> None:
        self._items: dict[int, T] = {}

    def add(self, item: T) -> None:
        """Додає або оновлює сутність у репозиторії."""
        self._items[item.id] = item

    def get(self, item_id: int) -> T | None:
        """Отримує сутність за ID або повертає None."""
        return self._items.get(item_id)

    def all(self) -> list[T]:
        """Повертає список усіх збережених сутностей."""
        return list(self._items.values())

    def find_by(self, predicate: Callable[[T], bool]) -> list[T]:
        """Фільтрує сутності за предикатом."""
        return [item for item in self._items.values() if predicate(item)]

    def remove(self, item_id: int) -> bool:
        """Видаляє сутність за ID."""
        return self._items.pop(item_id, None) is not None

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._items
