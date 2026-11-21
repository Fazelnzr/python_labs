"""Модуль фільтрації, трансформації та пакетної обробки (batching) потоку оцінок."""

from collections.abc import Callable, Iterable, Iterator
from itertools import islice
from stream_processor.models import GradeRecord


def filter_by_discipline(
    records: Iterable[GradeRecord],
    discipline: str | None = None,
) -> Iterator[GradeRecord]:
    """Потокова фільтрація записів за назвою дисципліни (без урахування регістру)."""
    if not discipline:
        yield from records
        return

    target = discipline.strip().lower()
    for record in records:
        if record.discipline.lower() == target:
            yield record


def filter_by_grade_threshold(
    records: Iterable[GradeRecord],
    min_grade: float = 0.0,
    max_grade: float = 100.0,
) -> Iterator[GradeRecord]:
    """Потокова фільтрація записів за діапазоном оцінки."""
    for record in records:
        if min_grade <= record.grade <= max_grade:
            yield record


def normalize_records(records: Iterable[GradeRecord]) -> Iterator[GradeRecord]:
    """Потокова трансформація (нормалізація ПІБ студента, назви дисципліни та округлення оцінки)."""
    for record in records:
        yield GradeRecord(
            student_id=record.student_id,
            name=record.name.strip().title(),
            discipline=record.discipline.strip().title(),
            grade=round(record.grade, 2),
        )


def batched_records(
    records: Iterable[GradeRecord],
    batch_size: int,
) -> Iterator[list[GradeRecord]]:
    """Пакетна обробка (batch processing) записів за допомогою itertools.islice."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    iterator = iter(records)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            return
        yield batch


def find_first_record(
    records: Iterable[GradeRecord],
    predicate: Callable[[GradeRecord], bool],
) -> GradeRecord | None:
    """Лінивий пошук першого запису за предикатом (демонстрація early termination)."""
    for record in records:
        if predicate(record):
            return record
    return None
