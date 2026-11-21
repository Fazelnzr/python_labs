"""Валідація та парсинг записів системи оцінювання студентів (Варіант 7)."""

from collections.abc import Collection
import math
import re

from reliable_importer.exceptions import RecordValidationError
from reliable_importer.models import StudentGrade

NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ'’\- ]+$")


def parse_student_grade(
    row: dict[str, object],
    *,
    line_number: int,
    allowed_disciplines: Collection[str] | None = None,
    passing_grade: float = 60.0,
) -> StudentGrade:
    """Парсить і валідує запис оцінювання студента з використанням exception chaining."""
    # 1. Валідація student_id (EAFP + exception chaining)
    raw_id = row.get("student_id") if isinstance(row, dict) else None
    try:
        if raw_id is None or isinstance(raw_id, bool):
            raise ValueError("Missing or boolean student_id")
        student_id = int(str(raw_id).strip())
    except (KeyError, TypeError, ValueError) as error:
        raise RecordValidationError(
            "Invalid student ID: must be an integer",
            line_number=line_number,
            field="student_id",
            raw_value=raw_id,
        ) from error

    if student_id <= 0:
        raise RecordValidationError(
            "Student ID must be a positive integer (> 0)",
            line_number=line_number,
            field="student_id",
            raw_value=raw_id,
        )

    # 2. Валідація ПІБ (name)
    raw_name = row.get("name", "")
    name = str(raw_name if raw_name is not None else "").strip()
    if not name:
        raise RecordValidationError(
            "Student name is empty",
            line_number=line_number,
            field="name",
            raw_value=raw_name,
        )
    if len(name) < 2 or not NAME_PATTERN.match(name):
        raise RecordValidationError(
            "Student name contains invalid characters",
            line_number=line_number,
            field="name",
            raw_value=raw_name,
        )

    # 3. Валідація дисципліни (discipline)
    raw_discipline = row.get("discipline", "")
    discipline = str(raw_discipline if raw_discipline is not None else "").strip()
    if not discipline:
        raise RecordValidationError(
            "Discipline is empty",
            line_number=line_number,
            field="discipline",
            raw_value=raw_discipline,
        )
    if allowed_disciplines is not None and discipline not in allowed_disciplines:
        raise RecordValidationError(
            f"Discipline '{discipline}' is not in the allowed disciplines list",
            line_number=line_number,
            field="discipline",
            raw_value=raw_discipline,
        )

    # 4. Валідація оцінки (grade у межах 0–100) з exception chaining
    raw_grade = row.get("grade")
    try:
        if raw_grade is None or isinstance(raw_grade, bool):
            raise ValueError("Missing or boolean grade")
        grade = float(str(raw_grade).strip())
    except (KeyError, TypeError, ValueError) as error:
        raise RecordValidationError(
            "Grade must be a numeric value",
            line_number=line_number,
            field="grade",
            raw_value=raw_grade,
        ) from error

    if not math.isfinite(grade) or not 0.0 <= grade <= 100.0:
        raise RecordValidationError(
            "Grade must be between 0 and 100",
            line_number=line_number,
            field="grade",
            raw_value=raw_grade,
        )

    return StudentGrade(
        student_id=student_id,
        name=name,
        discipline=discipline,
        grade=round(grade, 2),
        passed=grade >= passing_grade,
    )
