"""Модульні тести імпорту CSV, експорту JSON, атомарного запису та конфігурації."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grading import exporters
from grading.config import (
    DEFAULT_GRADING_MODE,
    DEFAULT_PASSING_THRESHOLD,
    GradingConfig,
    get_grading_mode,
    get_passing_threshold,
    load_config,
)
from grading.exceptions import (
    ConfigurationError,
    DataExportError,
    DataImportError,
    RecordValidationError,
)
from grading.exporters import export_grade_report_atomic, export_grade_report_json
from grading.importers import import_assessments_from_csv, parse_csv_row
from grading.models import GradeBook


@pytest.mark.unit
def test_csv_import_valid_file_with_tmp_path(tmp_path: Path) -> None:
    """Перевіряє імпорт коректного CSV-файлу з оцінками через ізольовану фікстуру tmp_path."""
    csv_file = tmp_path / "grades.csv"
    csv_file.write_text(
        "student_id,name,group,email,discipline_code,discipline_name,credits,grade\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS101,Програмування на Python,5,95.5\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS102,Бази даних,4,88.5\n"
        "2,Мельник Олег,ПІ-21,oleh@example.com,CS101,Програмування на Python,5,76.0\n",
        encoding="utf-8",
    )

    book = import_assessments_from_csv(csv_file)

    assert len(book) == 2
    anna = book.get_student(1)
    assert anna.name == "Коваленко Анна"
    assert len(anna.records) == 2
    assert anna.average_grade() == pytest.approx(92.0)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("row_overrides", "expected_field"),
    [
        pytest.param({"student_id": ""}, "student_id", id="missing_student_id"),
        pytest.param({"student_id": "abc"}, "student_id", id="non_numeric_student_id"),
        pytest.param({"student_id": "-5"}, "student_id", id="negative_student_id"),
        pytest.param({"name": "   "}, "name", id="empty_name"),
        pytest.param({"group": ""}, "group", id="empty_group"),
        pytest.param({"discipline_code": ""}, "discipline_code", id="empty_discipline_code"),
        pytest.param({"discipline_name": ""}, "discipline_name", id="empty_discipline_name"),
        pytest.param({"discipline_name": "Астрологія"}, "discipline_name", id="disallowed_discipline"),
        pytest.param({"credits": "two"}, "credits", id="non_numeric_credits"),
        pytest.param({"credits": "0"}, "credits", id="zero_credits"),
        pytest.param({"grade": ""}, "grade", id="empty_grade"),
        pytest.param({"grade": "excellent"}, "grade", id="non_numeric_grade"),
        pytest.param({"grade": "105.5"}, "grade", id="out_of_range_grade"),
    ],
)
def test_parse_csv_row_malformed_records_and_exception_chaining(
    row_overrides: dict[str, str],
    expected_field: str,
) -> None:
    """Перевіряє генерацію RecordValidationError з атрибутами field/line_number для всіх типів пошкоджених записів."""
    base_row = {
        "student_id": "1",
        "name": "Коваленко Анна",
        "group": "ПІ-21",
        "email": "anna@example.com",
        "discipline_code": "CS101",
        "discipline_name": "Програмування на Python",
        "credits": "5",
        "grade": "90.0",
    }
    base_row.update(row_overrides)

    with pytest.raises(RecordValidationError) as exc_info:
        parse_csv_row(
            base_row,
            line_number=7,
            allowed_disciplines=("Програмування на Python", "Бази даних"),
        )

    assert exc_info.value.field == expected_field
    assert exc_info.value.line_number == 7


@pytest.mark.unit
def test_exception_chaining_on_invalid_grade_parsing() -> None:
    """Перевіряє збереження першопричини (__cause__) при розборі некоректної оцінки."""
    row = {
        "student_id": "1",
        "name": "Коваленко Анна",
        "group": "ПІ-21",
        "discipline_code": "CS101",
        "discipline_name": "Python",
        "credits": "4",
        "grade": "not-a-float",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_csv_row(row, line_number=3)

    assert exc_info.value.field == "grade"
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.unit
def test_csv_import_missing_file_or_missing_columns(tmp_path: Path) -> None:
    """Перевіряє помилки імпорту при відсутньому файлі, порожньому файлі або відсутності колонок."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(DataImportError, match="not found"):
        import_assessments_from_csv(missing_path)

    empty_path = tmp_path / "empty.csv"
    empty_path.write_text("", encoding="utf-8")
    with pytest.raises(DataImportError, match="empty or missing header"):
        import_assessments_from_csv(empty_path)

    bad_header_path = tmp_path / "bad_header.csv"
    bad_header_path.write_text("student_id,name\n1,Anna\n", encoding="utf-8")
    with pytest.raises(DataImportError, match="missing required columns"):
        import_assessments_from_csv(bad_header_path)


@pytest.mark.unit
def test_monkeypatch_env_and_function_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    populated_grade_book: GradeBook,
) -> None:
    """Перевіряє підміну змінних середовища та функцій часу/UUID через monkeypatch."""
    # За замовчуванням змінні очищені autouse-фікстурою
    assert get_passing_threshold() == pytest.approx(DEFAULT_PASSING_THRESHOLD)
    assert get_grading_mode() == DEFAULT_GRADING_MODE

    # Встановлюємо змінні середовища через monkeypatch
    monkeypatch.setenv("GRADING_PASSING_THRESHOLD", "75.5")
    monkeypatch.setenv("GRADING_MODE", "weighted")
    assert get_passing_threshold() == pytest.approx(75.5)
    assert get_grading_mode() == "weighted"

    # Некоректні значення змінних середовища
    monkeypatch.setenv("GRADING_PASSING_THRESHOLD", "invalid")
    with pytest.raises(ConfigurationError, match="GRADING_PASSING_THRESHOLD"):
        get_passing_threshold()

    monkeypatch.setenv("GRADING_MODE", "unknown_mode")
    with pytest.raises(ConfigurationError, match="GRADING_MODE"):
        get_grading_mode()

    # Підміна функцій get_current_timestamp та generate_report_id для детермінованого експорту
    monkeypatch.delenv("GRADING_PASSING_THRESHOLD", raising=False)
    monkeypatch.delenv("GRADING_MODE", raising=False)
    monkeypatch.setattr(exporters, "get_current_timestamp", lambda: "2026-11-21T12:00:00+00:00")
    monkeypatch.setattr(exporters, "generate_report_id", lambda: "REP-FIXED-001")

    output_file = tmp_path / "report.json"
    export_grade_report_json(populated_grade_book, output_file)

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["report_id"] == "REP-FIXED-001"
    assert saved["generated_at"] == "2026-11-21T12:00:00+00:00"
    assert saved["statistics"]["total_students"] == 3


@pytest.mark.unit
def test_config_validation_and_file_loading(tmp_path: Path) -> None:
    """Перевіряє валідацію GradingConfig та завантаження з YAML і JSON файлів."""
    with pytest.raises(ConfigurationError, match="passing_threshold cannot be greater"):
        GradingConfig(passing_threshold=95.0, honors_threshold=90.0)

    with pytest.raises(ConfigurationError, match="Invalid grading mode"):
        GradingConfig(mode="custom")

    with pytest.raises(ConfigurationError, match="between 0 and 100"):
        GradingConfig(passing_threshold=120.0)

    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        "passing_threshold: 65.0\n"
        "honors_threshold: 92.0\n"
        "mode: weighted\n"
        "allowed_disciplines:\n"
        "  - Програмування на Python\n"
        "  - Бази даних\n",
        encoding="utf-8",
    )
    cfg = load_config(yaml_path)
    assert cfg.passing_threshold == pytest.approx(65.0)
    assert cfg.honors_threshold == pytest.approx(92.0)
    assert cfg.mode == "weighted"
    assert cfg.allowed_disciplines == ("Програмування на Python", "Бази даних")

    json_path = tmp_path / "config.json"
    json_path.write_text(
        json.dumps({"passing_threshold": 70.0, "honors_threshold": 90.0, "mode": "standard"}),
        encoding="utf-8",
    )
    json_cfg = load_config(json_path)
    assert json_cfg.passing_threshold == pytest.approx(70.0)

    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "missing.yaml")

    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("[: invalid yaml", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Failed to parse"):
        load_config(bad_yaml)

    list_yaml = tmp_path / "list.yaml"
    list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="mapping/object"):
        load_config(list_yaml)

    bad_disc_yaml = tmp_path / "bad_disc.yaml"
    bad_disc_yaml.write_text("allowed_disciplines: 123\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="allowed_disciplines must be a list"):
        load_config(bad_disc_yaml)


@pytest.mark.unit
def test_atomic_export_preserves_old_file_on_failure(
    tmp_path: Path,
    populated_grade_book: GradeBook,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Перевіряє атомарний експорт: при збої старий файл залишається неушкодженим, а .tmp видаляється."""
    output_path = tmp_path / "atomic_report.json"
    output_path.write_text("old valid data", encoding="utf-8")

    # Спочатку перевіряємо нормальний експорт порожнього журналу
    empty_path = tmp_path / "empty_report.json"
    empty_payload = export_grade_report_atomic(GradeBook(), empty_path)
    assert empty_payload["statistics"]["total_students"] == 0
    assert empty_payload["min_grade"] is None

    # Тепер імітуємо збій під час серіалізації в export_grade_report_atomic
    def broken_dumps(*args: object, **kwargs: object) -> str:
        raise ValueError("Disk serialization error")

    monkeypatch.setattr(exporters.json, "dumps", broken_dumps)

    with pytest.raises(DataExportError, match="Atomic export failed"):
        export_grade_report_atomic(populated_grade_book, output_path)

    assert output_path.read_text(encoding="utf-8") == "old valid data"
    temp_file = output_path.with_suffix(".json.tmp")
    assert not temp_file.exists()
