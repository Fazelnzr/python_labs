"""Модуль експорту результатів оцінювання студентів у формат JSON (включно з атомарним записом)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grading.config import GradingConfig
from grading.exceptions import DataExportError
from grading.models import GradeBook


def get_current_timestamp() -> str:
    """Повертає поточну UTC дату-час у форматі ISO-8601 (зручно для підміни через monkeypatch)."""
    return datetime.now(timezone.utc).isoformat()


def generate_report_id() -> str:
    """Генерує унікальний ідентифікатор звіту (зручно для підміни через monkeypatch)."""
    return str(uuid.uuid4())


def build_grade_report_payload(
    grade_book: GradeBook,
    *,
    config: GradingConfig | None = None,
) -> dict[str, Any]:
    """Формує словник звіту з журналу оцінок для подальшої JSON-серіалізації."""
    active_config = config or GradingConfig()
    threshold = active_config.passing_threshold

    ranked_students = grade_book.sort_students_by_average(descending=True)
    above_threshold = grade_book.find_students_above_threshold(threshold)

    if ranked_students:
        stats = grade_book.calculate_performance_stats(threshold)
        min_g, max_g = grade_book.min_max_grades()
        min_val: float | None = min_g.value
        max_val: float | None = max_g.value
    else:
        stats = {
            "total_students": 0,
            "passed_students": 0,
            "failed_students": 0,
            "pass_rate": 0.0,
            "absolute_success_rate": 0.0,
            "quality_rate": 0.0,
            "average_score": 0.0,
        }
        min_val = None
        max_val = None

    students_payload = [
        {
            "student_id": s.student_id,
            "name": s.name,
            "group": s.group,
            "average_grade": round(s.average_grade(), 2),
            "weighted_average_grade": round(s.weighted_average_grade(), 2),
            "min_grade": s.min_grade().value,
            "max_grade": s.max_grade().value,
            "success_rate": round(s.success_rate(threshold), 2),
            "passed": s.average_grade() >= threshold,
            "honors": s.average_grade() >= active_config.honors_threshold,
            "records": [
                {
                    "discipline_code": r.discipline.code,
                    "discipline_name": r.discipline.name,
                    "credits": r.discipline.credits,
                    "grade": r.grade.value,
                    "ects": r.grade.ects,
                }
                for r in s.records
            ],
        }
        for s in ranked_students
    ]

    return {
        "report_id": generate_report_id(),
        "generated_at": get_current_timestamp(),
        "passing_threshold": threshold,
        "honors_threshold": active_config.honors_threshold,
        "mode": active_config.mode,
        "statistics": stats,
        "min_grade": min_val,
        "max_grade": max_val,
        "students_above_threshold_ids": [s.student_id for s in above_threshold],
        "students": students_payload,
    }


def export_grade_report_json(
    grade_book: GradeBook,
    output_path: Path,
    *,
    config: GradingConfig | None = None,
) -> dict[str, Any]:
    """Експортує звіт по журналу оцінок у JSON-файл та повертає сформований словник."""
    payload = build_grade_report_payload(grade_book, config=config)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError) as error:
        raise DataExportError(f"Failed to export JSON report to {output_path}: {error}") from error
    return payload


def export_grade_report_atomic(
    grade_book: GradeBook,
    output_path: Path,
    *,
    config: GradingConfig | None = None,
) -> dict[str, Any]:
    """Атомарно експортує JSON-звіт через тимчасовий файл .tmp із гарантованим очищенням при збої."""
    payload = build_grade_report_payload(grade_book, config=config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(output_path)
    except Exception as error:
        if temp_path.exists():
            temp_path.unlink()
        raise DataExportError(f"Atomic export failed for {output_path}: {error}") from error
    return payload
