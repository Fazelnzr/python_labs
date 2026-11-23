"""Власна ієрархія винятків системи оцінювання студентів."""

from __future__ import annotations

from typing import Any


class GradingSystemError(Exception):
    """Базовий виняток для всіх помилок системи оцінювання."""


class InvalidGradeError(GradingSystemError, ValueError):
    """Виняток при спробі створити або обробити оцінку поза межами [0, 100]."""

    def __init__(self, message: str, value: Any = None) -> None:
        super().__init__(message)
        self.value = value


class RecordValidationError(GradingSystemError):
    """Виняток при некоректному форматі або значенні поля під час імпорту запису."""

    def __init__(
        self,
        message: str,
        *,
        field: str,
        raw_value: Any = None,
        line_number: int | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.raw_value = raw_value
        self.line_number = line_number


class EmptyGradeBookError(GradingSystemError):
    """Виняток при спробі виконати агрегуючі розрахунки над порожнім журналом або списком оцінок."""


class StudentNotFoundError(GradingSystemError, KeyError):
    """Виняток, коли студента із заданим ID не знайдено."""


class DuplicateStudentError(GradingSystemError, ValueError):
    """Виняток при повторній реєстрації студента з тим самим ID."""


class ConfigurationError(GradingSystemError):
    """Виняток при некоректних параметрах конфігурації."""


class DataImportError(GradingSystemError):
    """Виняток при помилці читання вхідного файлу."""


class DataExportError(GradingSystemError):
    """Виняток при помилці експорту звіту."""


class NotificationError(GradingSystemError):
    """Виняток при збої зовнішнього сервісу сповіщень."""
