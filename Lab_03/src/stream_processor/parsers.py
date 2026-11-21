"""Модуль парсингу та потокової валідації записів оцінок студентів."""

import csv
from collections.abc import Iterable, Iterator
from stream_processor.models import GradeRecord


def parse_csv_rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """Парсинг CSV-рядків у словники через csv.DictReader та yield from."""
    reader = csv.DictReader(lines)
    yield from reader


def validate_grades(
    rows: Iterable[dict[str, str]],
    stats_out: dict[str, int] | None = None,
) -> Iterator[GradeRecord]:
    """
    Потокова валідація оцінок студентів (streaming validation).
    Перевіряє коректність ID, імені, назви дисципліни та діапазон оцінки [0, 100].
    Опціонально підраховує кількість valid та invalid записів.
    """
    for row in rows:
        try:
            student_id = int(row["student_id"])
            name = row["name"].strip()
            discipline = row["discipline"].strip()
            grade = float(row["grade"])
        except (ValueError, TypeError, KeyError):
            if stats_out is not None:
                stats_out["invalid"] = stats_out.get("invalid", 0) + 1
            continue

        if student_id <= 0 or not name or not discipline or not (0.0 <= grade <= 100.0):
            if stats_out is not None:
                stats_out["invalid"] = stats_out.get("invalid", 0) + 1
            continue

        if stats_out is not None:
            stats_out["valid"] = stats_out.get("valid", 0) + 1

        yield GradeRecord(
            student_id=student_id,
            name=name,
            discipline=discipline,
            grade=grade,
        )
