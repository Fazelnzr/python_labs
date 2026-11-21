"""Моделі предметної області та конфігурації."""

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StudentGrade:
    """Запис оцінки студента з дисципліни (Варіант 7)."""

    student_id: int
    name: str
    discipline: str
    grade: float
    passed: bool = True

    def to_dict(self) -> dict[str, object]:
        """Перетворює domain-об'єкт на словник для серіалізації."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InvalidRecordDetail:
    """Інформація про некоректний запис для журналу помилок та звіту."""

    line_number: int | None
    field: str | None
    message: str
    raw_row: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ImportStatistics:
    """Статистика обробки записів."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    passed: int = 0
    failed_threshold: int = 0
    exported: int = 0
    errors: list[InvalidRecordDetail] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "passed": self.passed,
            "failed_threshold": self.failed_threshold,
            "exported": self.exported,
            "error_count": len(self.errors),
        }


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Налаштування правил валідації та фільтрації."""

    passing_grade: float
    skip_invalid: bool
    allowed_disciplines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Налаштування системи логування."""

    level: str
    path: Path
    error_log_path: Path | None = None
    max_bytes: int = 1048576
    backup_count: int = 3


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Головна конфігурація застосунку."""

    input_path: Path
    output_path: Path
    processing: ProcessingConfig
    logging: LoggingConfig
    input_format: str = "auto"
    output_format: str = "auto"
    error_csv_path: Path | None = None
    summary_report_path: Path | None = None
    backup_existing: bool = True
