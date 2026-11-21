"""Модульні тести для Лабораторної роботи №5 (Варіант 7: Система оцінювання студентів)."""

import json
from pathlib import Path
import pytest

from reliable_importer.config import load_config
from reliable_importer.exceptions import (
    ConfigurationError,
    DataExportError,
    DataImportError,
    RecordValidationError,
)
from reliable_importer.exporters import (
    export_grades_json,
    export_invalid_records_csv,
    export_summary_report,
    get_exporter,
)
from reliable_importer.main import main, run_pipeline
from reliable_importer.models import ImportStatistics, StudentGrade
from reliable_importer.readers import get_importer
from reliable_importer.services import filter_by_passing_grade, import_student_grades
from reliable_importer.utils import AtomicFileWriter, logged_operation
from reliable_importer.validators import parse_student_grade

ALLOWED_DISCIPLINES = (
    "Програмування на Python",
    "Алгоритми та структури даних",
    "Бази даних",
)


def test_parse_valid_student_grade() -> None:
    row = {
        "student_id": "101",
        "name": "Коваленко Анна Сергіївна",
        "discipline": "Програмування на Python",
        "grade": "95.5",
    }
    record = parse_student_grade(
        row,
        line_number=2,
        allowed_disciplines=ALLOWED_DISCIPLINES,
        passing_grade=60.0,
    )
    assert record.student_id == 101
    assert record.name == "Коваленко Анна Сергіївна"
    assert record.discipline == "Програмування на Python"
    assert record.grade == 95.5
    assert record.passed is True


def test_parse_invalid_grade_exception_chaining() -> None:
    row = {
        "student_id": "101",
        "name": "Коваленко Анна",
        "discipline": "Програмування на Python",
        "grade": "not_a_number",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_student_grade(row, line_number=7, allowed_disciplines=ALLOWED_DISCIPLINES)

    err = exc_info.value
    assert err.line_number == 7
    assert err.field == "grade"
    assert isinstance(err.__cause__, ValueError)


@pytest.mark.parametrize(
    ("override", "expected_field"),
    [
        ({"student_id": "abc"}, "student_id"),
        ({"student_id": "-5"}, "student_id"),
        ({"name": "   "}, "name"),
        ({"name": "12345"}, "name"),
        ({"discipline": ""}, "discipline"),
        ({"discipline": "Невідомий предмет"}, "discipline"),
        ({"grade": "105"}, "grade"),
        ({"grade": "-1"}, "grade"),
    ],
)
def test_validation_rules(override: dict[str, str], expected_field: str) -> None:
    base = {
        "student_id": "10",
        "name": "Мельник Олег",
        "discipline": "Бази даних",
        "grade": "80.0",
    }
    base.update(override)
    with pytest.raises(RecordValidationError) as exc_info:
        parse_student_grade(base, line_number=3, allowed_disciplines=ALLOWED_DISCIPLINES)
    assert exc_info.value.field == expected_field


def test_strict_vs_tolerant_modes(tmp_path: Path) -> None:
    csv_file = tmp_path / "grades.csv"
    csv_file.write_text(
        "student_id,name,discipline,grade\n"
        "1,Коваленко Анна,Бази даних,90\n"
        "2,,Бази даних,80\n"
        "3,Мельник Олег,Бази даних,50\n",
        encoding="utf-8",
    )

    # Strict mode stops on line 3
    strict_stats = ImportStatistics()
    with pytest.raises(RecordValidationError) as exc_info:
        list(
            import_student_grades(
                csv_file,
                skip_invalid=False,
                statistics=strict_stats,
                allowed_disciplines=ALLOWED_DISCIPLINES,
                passing_grade=60.0,
            )
        )
    assert exc_info.value.line_number == 3
    assert strict_stats.total == 2
    assert strict_stats.valid == 1
    assert strict_stats.invalid == 1

    # Tolerant mode skips invalid and continues
    tol_stats = ImportStatistics()
    records = list(
        import_student_grades(
            csv_file,
            skip_invalid=True,
            statistics=tol_stats,
            allowed_disciplines=ALLOWED_DISCIPLINES,
            passing_grade=60.0,
        )
    )
    assert len(records) == 2
    assert tol_stats.total == 3
    assert tol_stats.valid == 2
    assert tol_stats.invalid == 1
    assert tol_stats.passed == 1
    assert tol_stats.failed_threshold == 1

    passed_only = list(filter_by_passing_grade(records, 60.0))
    assert len(passed_only) == 1
    assert passed_only[0].student_id == 1


def test_atomic_export_preserves_existing_file_on_error(tmp_path: Path) -> None:
    out_file = tmp_path / "result.json"
    initial = [StudentGrade(1, "Коваленко Анна", "Бази даних", 92.0, True)]
    export_grades_json(initial, out_file)
    before = out_file.read_text(encoding="utf-8")

    def broken_stream():
        yield StudentGrade(2, "Мельник Олег", "Бази даних", 81.0, True)
        raise OSError("Simulated write error")

    with pytest.raises(DataExportError):
        export_grades_json(broken_stream(), out_file)

    assert out_file.read_text(encoding="utf-8") == before
    assert not out_file.with_suffix(".json.tmp").exists()


def test_multi_format_importers_and_exporters(tmp_path: Path) -> None:
    records = [
        StudentGrade(1, "Коваленко Анна", "Бази даних", 95.0, True),
        StudentGrade(2, "Мельник Олег", "Програмування на Python", 84.5, True),
    ]
    for ext in ("json", "jsonl", "csv", "yaml"):
        file_path = tmp_path / f"data.{ext}"
        exporter = get_exporter(file_path)
        count = exporter.export(records, file_path)
        assert count == 2

        importer = get_importer(file_path)
        loaded_rows = list(importer.read(file_path))
        assert len(loaded_rows) == 2
        parsed = [
            parse_student_grade(row, line_number=ln, allowed_disciplines=ALLOWED_DISCIPLINES)
            for ln, row in loaded_rows
        ]
        assert parsed == records


def test_config_validation_and_full_pipeline(tmp_path: Path) -> None:
    csv_path = tmp_path / "grades.csv"
    csv_path.write_text(
        "student_id,name,discipline,grade\n"
        "101,Коваленко Анна,Бази даних,88.0\n"
        "102,Мельник Олег,Невідома,75.0\n"
        "103,Бондар Ірина,Бази даних,55.0\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "out" / "grades.json"
    err_csv = tmp_path / "out" / "errors.csv"
    summary_json = tmp_path / "out" / "summary.json"
    log_path = tmp_path / "logs" / "app.log"
    err_log_path = tmp_path / "logs" / "errors.log"

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        f"""
input:
  path: {csv_path.as_posix()}
output:
  path: {out_path.as_posix()}
  error_csv_path: {err_csv.as_posix()}
  summary_report_path: {summary_json.as_posix()}
processing:
  passing_grade: 60
  skip_invalid: true
  allowed_disciplines:
    - "Бази даних"
logging:
  level: INFO
  path: {log_path.as_posix()}
  error_log_path: {err_log_path.as_posix()}
""",
        encoding="utf-8",
    )

    stats = run_pipeline(cfg_path)
    assert stats.total == 3
    assert stats.valid == 2
    assert stats.invalid == 1
    assert stats.exported == 1

    exported_data = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(exported_data) == 1
    assert exported_data[0]["student_id"] == 101
    assert err_csv.exists()
    assert summary_json.exists()
    assert err_log_path.exists()


def test_main_exits_with_code_1_on_configuration_error(tmp_path: Path) -> None:
    missing_cfg = tmp_path / "nonexistent.yaml"
    with pytest.raises(SystemExit) as exc_info:
        main(["--config", str(missing_cfg)])
    assert exc_info.value.code == 1
