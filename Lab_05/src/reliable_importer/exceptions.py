"""Ієрархія власних винятків (custom exceptions) для модуля імпорту та експорту."""


class ApplicationError(Exception):
    """Базовий виняток застосунку."""


class ConfigurationError(ApplicationError):
    """Помилка завантаження або валідації конфігурації."""


class DataError(ApplicationError):
    """Базовий виняток для помилок обробки даних."""


class DataImportError(DataError):
    """Помилка під час читання вхідного файлу або парсингу формату."""


class DataValidationError(DataError):
    """Базовий виняток валідації даних."""


class RecordValidationError(DataValidationError):
    """Помилка валідації конкретного запису з додатковим контекстом."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
        raw_value: object = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field
        self.raw_value = raw_value


class DataExportError(DataError):
    """Помилка під час серіалізації або запису вихідного файлу."""
