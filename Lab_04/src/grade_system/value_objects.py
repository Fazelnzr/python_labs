"""Незмінні об'єкти-значення (Value Objects) предметної області оцінювання студентів."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import total_ordering


class PerformanceLevel(str, Enum):
    """Рівень академічної успішності за шкалою ECTS та національною шкалою."""

    EXCELLENT = "Відмінно (A)"
    GOOD = "Добре (B/C)"
    SATISFACTORY = "Задовільно (D/E)"
    UNSATISFACTORY = "Незадовільно (FX/F)"


@total_ordering
@dataclass(frozen=True, slots=True)
class Grade:
    """Незмінний об'єкт-значення (Value Object), що представляє оцінку у 100-бальній шкалі.

    Використовує frozen=True та slots=True, валідацію у __post_init__
    та підтримує порівняння і арифметичне додавання.
    """

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            raise ValueError(
                f"Оцінка повинна бути в діапазоні від 0 до 100, отримано: {self.value}"
            )

    @property
    def ects_letter(self) -> str:
        """Буквений еквівалент оцінки за шкалою ECTS."""
        if self.value >= 90.0:
            return "A"
        if self.value >= 82.0:
            return "B"
        if self.value >= 74.0:
            return "C"
        if self.value >= 64.0:
            return "D"
        if self.value >= 60.0:
            return "E"
        if self.value >= 35.0:
            return "FX"
        return "F"

    @property
    def performance_level(self) -> PerformanceLevel:
        """Визначення рівня успішності для оцінки."""
        if self.value >= 90.0:
            return PerformanceLevel.EXCELLENT
        if self.value >= 74.0:
            return PerformanceLevel.GOOD
        if self.value >= 60.0:
            return PerformanceLevel.SATISFACTORY
        return PerformanceLevel.UNSATISFACTORY

    @property
    def is_passing(self) -> bool:
        """Чи є оцінка прохідною (>= 60 балів)."""
        return self.value >= 60.0

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value < other.value

    def __add__(self, other: Grade) -> float:
        """Повертає суму балів двох оцінок."""
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value + other.value

    def __str__(self) -> str:
        return f"{self.value:.1f} ({self.ects_letter})"
