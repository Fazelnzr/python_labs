"""Сервіси потокового імпорту, валідації (strict/tolerant) та фільтрації за порогом успішності."""

from collections.abc import Collection, Iterable, Iterator
import logging
from pathlib import Path

from reliable_importer.exceptions import RecordValidationError
from reliable_importer.models import ImportStatistics, InvalidRecordDetail, StudentGrade
from reliable_importer.readers import get_importer
from reliable_importer.validators import parse_student_grade

logger = logging.getLogger(__name__)


def import_student_grades(
    path: Path,
    *,
    skip_invalid: bool,
    statistics: ImportStatistics,
    allowed_disciplines: Collection[str] | None = None,
    passing_grade: float = 60.0,
    input_format: str = "auto",
) -> Iterator[StudentGrade]:
    """Потоково імпортує записи оцінювання студентів, оновлюючи статистику та логуючи помилки."""
    importer = get_importer(path, fmt=input_format)

    for line_number, row in importer.read(path):
        statistics.total += 1
        try:
            record = parse_student_grade(
                row,
                line_number=line_number,
                allowed_disciplines=allowed_disciplines,
                passing_grade=passing_grade,
            )
        except RecordValidationError as error:
            statistics.invalid += 1
            statistics.errors.append(
                InvalidRecordDetail(
                    line_number=error.line_number,
                    field=error.field,
                    message=str(error),
                    raw_row=dict(row),
                )
            )
            logger.warning(
                "Invalid record at line %s (field=%s): %s",
                error.line_number,
                error.field,
                error,
            )
            if skip_invalid:
                continue
            raise

        statistics.valid += 1
        if record.passed:
            statistics.passed += 1
        else:
            statistics.failed_threshold += 1
        yield record


def filter_by_passing_grade(
    records: Iterable[StudentGrade],
    passing_grade: float,
) -> Iterator[StudentGrade]:
    """Потоково фільтрує записи студентів, які подолали поріг успішності (passing_grade)."""
    for record in records:
        if record.grade >= passing_grade:
            yield record
