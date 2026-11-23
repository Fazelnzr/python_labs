"""Модуль імпорту оцінок студентів із CSV-файлів."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping

from grading.config import GradingConfig
from grading.exceptions import DataImportError, InvalidGradeError, RecordValidationError
from grading.models import Discipline, Grade, GradeBook, Student

REQUIRED_CSV_COLUMNS: frozenset[str] = frozenset(
    {
        "student_id",
        "name",
        "group",
        "discipline_code",
        "discipline_name",
        "credits",
        "grade",
    }
)


def parse_csv_row(
    row: Mapping[str, str | None],
    *,
    line_number: int = 1,
    allowed_disciplines: tuple[str, ...] = (),
) -> tuple[Student, Discipline, Grade]:
    """Валідує та розбирає один рядок CSV у кортеж (Student, Discipline, Grade).

    У разі помилки валідації піднімає RecordValidationError із атрибутами
    field, raw_value, line_number та збереженим ланцюжком винятків (__cause__).
    """
    raw_id = (row.get("student_id") or "").strip()
    if not raw_id:
        raise RecordValidationError(
            "Missing student_id",
            field="student_id",
            raw_value=raw_id,
            line_number=line_number,
        )
    try:
        student_id = int(raw_id)
    except ValueError as error:
        raise RecordValidationError(
            f"Invalid integer for student_id: {raw_id!r}",
            field="student_id",
            raw_value=raw_id,
            line_number=line_number,
        ) from error

    if student_id <= 0:
        raise RecordValidationError(
            f"student_id must be positive, got {student_id}",
            field="student_id",
            raw_value=raw_id,
            line_number=line_number,
        )

    name = (row.get("name") or "").strip()
    if not name:
        raise RecordValidationError(
            "Student name cannot be empty",
            field="name",
            raw_value=row.get("name"),
            line_number=line_number,
        )

    group = (row.get("group") or "").strip()
    if not group:
        raise RecordValidationError(
            "Student group cannot be empty",
            field="group",
            raw_value=row.get("group"),
            line_number=line_number,
        )

    email = (row.get("email") or "").strip()

    discipline_code = (row.get("discipline_code") or "").strip()
    if not discipline_code:
        raise RecordValidationError(
            "Discipline code cannot be empty",
            field="discipline_code",
            raw_value=row.get("discipline_code"),
            line_number=line_number,
        )

    discipline_name = (row.get("discipline_name") or "").strip()
    if not discipline_name:
        raise RecordValidationError(
            "Discipline name cannot be empty",
            field="discipline_name",
            raw_value=row.get("discipline_name"),
            line_number=line_number,
        )

    if allowed_disciplines and discipline_name not in allowed_disciplines:
        raise RecordValidationError(
            f"Discipline {discipline_name!r} is not in allowed disciplines",
            field="discipline_name",
            raw_value=discipline_name,
            line_number=line_number,
        )

    raw_credits = (row.get("credits") or "").strip()
    try:
        credits_val = int(raw_credits)
    except ValueError as error:
        raise RecordValidationError(
            f"Invalid integer for credits: {raw_credits!r}",
            field="credits",
            raw_value=raw_credits,
            line_number=line_number,
        ) from error

    if credits_val <= 0:
        raise RecordValidationError(
            f"Credits must be positive, got {credits_val}",
            field="credits",
            raw_value=raw_credits,
            line_number=line_number,
        )

    raw_grade = (row.get("grade") or "").strip()
    if not raw_grade:
        raise RecordValidationError(
            "Missing grade value",
            field="grade",
            raw_value=raw_grade,
            line_number=line_number,
        )
    try:
        numeric_grade = float(raw_grade)
        grade_obj = Grade(numeric_grade)
    except (ValueError, InvalidGradeError) as error:
        raise RecordValidationError(
            f"Invalid grade value: {raw_grade!r}",
            field="grade",
            raw_value=raw_grade,
            line_number=line_number,
        ) from error

    student = Student(
        student_id=student_id,
        name=name,
        group=group,
        email=email,
    )
    discipline = Discipline(
        code=discipline_code,
        name=discipline_name,
        credits=credits_val,
    )
    return student, discipline, grade_obj


def import_assessments_from_csv(
    path: Path,
    *,
    config: GradingConfig | None = None,
) -> GradeBook:
    """Читає CSV-файл з оцінками та формує заповнений екземпляр GradeBook."""
    if not path.exists():
        raise DataImportError(f"CSV file not found: {path}")

    allowed = config.allowed_disciplines if config is not None else ()
    grade_book = GradeBook()

    try:
        with path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise DataImportError(f"CSV file is empty or missing header: {path}")

            header_set = {col.strip() for col in reader.fieldnames if col}
            missing_cols = REQUIRED_CSV_COLUMNS - header_set
            if missing_cols:
                sorted_missing = ", ".join(sorted(missing_cols))
                raise DataImportError(f"CSV file missing required columns: {sorted_missing}")

            for line_number, row in enumerate(reader, start=2):
                student, discipline, grade = parse_csv_row(
                    row,
                    line_number=line_number,
                    allowed_disciplines=allowed,
                )
                if student.student_id not in grade_book:
                    grade_book.add_student(student)
                grade_book.record_assessment(student.student_id, discipline, grade)
    except OSError as error:
        raise DataImportError(f"Failed to read CSV file {path}: {error}") from error

    return grade_book
