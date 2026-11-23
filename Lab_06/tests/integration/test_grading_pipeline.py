"""Інтеграційні тести повного циклу: Конфігурація -> CSV Імпорт -> Розрахунок оцінок -> SQLite -> JSON Експорт."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from grading.config import GradingConfig, load_config
from grading.exporters import export_grade_report_atomic, export_grade_report_json
from grading.importers import import_assessments_from_csv
from grading.models import Discipline, Grade, Student
from grading.protocols import AsyncGradeProvider
from grading.repositories import SQLiteGradeRepository
from grading.services import AsyncGradeSyncService, GradeBookService


@pytest.mark.integration
def test_full_csv_import_calculation_and_json_export_pipeline(
    tmp_path: Path,
    parameterized_config: GradingConfig,
) -> None:
    """Інтеграційний тест 1: CSV import -> GradeBook calculation -> JSON export з параметризованою конфігурацією."""
    csv_path = tmp_path / "students_grades.csv"
    csv_path.write_text(
        "student_id,name,group,email,discipline_code,discipline_name,credits,grade\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS101,Програмування на Python,5,96.0\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS102,Бази даних,4,90.0\n"
        "2,Мельник Олег,ПІ-21,oleh@example.com,CS101,Програмування на Python,5,70.0\n"
        "2,Мельник Олег,ПІ-21,oleh@example.com,CS102,Бази даних,4,66.0\n"
        "3,Шевченко Тарас,ПІ-22,taras@example.com,CS101,Програмування на Python,5,52.0\n"
        "3,Шевченко Тарас,ПІ-22,taras@example.com,CS102,Бази даних,4,48.0\n",
        encoding="utf-8",
    )
    output_json = tmp_path / "out" / "grade_report.json"

    # Act: імпорт CSV та експорт звіту
    grade_book = import_assessments_from_csv(csv_path, config=parameterized_config)
    export_grade_report_json(grade_book, output_json, config=parameterized_config)

    # Assert: перевірка згенерованого JSON-файлу
    assert output_json.exists()
    report = json.loads(output_json.read_text(encoding="utf-8"))

    assert report["passing_threshold"] == pytest.approx(parameterized_config.passing_threshold)
    assert report["min_grade"] == pytest.approx(48.0)
    assert report["max_grade"] == pytest.approx(96.0)
    assert [s["student_id"] for s in report["students"]] == [1, 2, 3]

    if parameterized_config.passing_threshold == 60.0:
        # Середні бали: Анна=93.0, Олег=68.0, Тарас=50.0 -> при порозі 60.0 проходять [1, 2]
        assert report["students_above_threshold_ids"] == [1, 2]
        assert report["statistics"]["passed_students"] == 2
    else:
        # При порозі 75.0 проходить лише Анна [1]
        assert report["students_above_threshold_ids"] == [1]
        assert report["statistics"]["passed_students"] == 1


@pytest.mark.integration
def test_yaml_config_and_env_override_integration_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Інтеграційний тест 2: YAML конфігурація + перевизначення через змінні середовища + імпорт + атомарний експорт."""
    config_file = tmp_path / "grading_config.yaml"
    config_file.write_text(
        "passing_threshold: 60.0\n"
        "honors_threshold: 90.0\n"
        "mode: standard\n"
        "allowed_disciplines:\n"
        "  - Програмування на Python\n"
        "  - Алгоритми та структури даних\n",
        encoding="utf-8",
    )

    # Перевизначаємо поріг успішності та режим через змінні середовища
    monkeypatch.setenv("GRADING_PASSING_THRESHOLD", "80.0")
    monkeypatch.setenv("GRADING_MODE", "weighted")

    config = load_config(config_file)
    assert config.passing_threshold == pytest.approx(80.0)
    assert config.mode == "weighted"

    csv_file = tmp_path / "input.csv"
    csv_file.write_text(
        "student_id,name,group,email,discipline_code,discipline_name,credits,grade\n"
        "10,Бондар Ірина,ПІ-21,iryna@example.com,CS101,Програмування на Python,5,85.0\n"
        "20,Литвин Андрій,ПІ-21,andrii@example.com,CS102,Алгоритми та структури даних,4,75.0\n",
        encoding="utf-8",
    )

    book = import_assessments_from_csv(csv_file, config=config)
    report_path = tmp_path / "atomic_summary.json"
    payload = export_grade_report_atomic(book, report_path, config=config)

    assert report_path.exists()
    assert payload["mode"] == "weighted"
    assert payload["students_above_threshold_ids"] == [10]


@pytest.mark.integration
def test_sqlite_repository_and_service_persistence_integration(
    sqlite_repository: SQLiteGradeRepository,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Інтеграційний тест 3: взаємодія GradeBookService із реальною базою даних SQLite у tmp_path."""
    service = GradeBookService(repository=sqlite_repository, passing_threshold=60.0)
    student = Student(student_id=7, name="Поліщук Богдан", group="ПІ-21", email="bohdan@example.com")
    student.add_assessment(sample_disciplines["db"], Grade(81.0))

    service.register_student(student)
    service.assign_grade(7, sample_disciplines["python"], 93.0, notify=False)
    service.assign_grade(7, sample_disciplines["algo"], 87.0, notify=False)

    all_students = sqlite_repository.list_students()
    assert len(all_students) == 1
    assert sqlite_repository.get_student(999) is None

    summary = service.evaluate_student_summary(7)
    assert summary["name"] == "Поліщук Богдан"
    assert summary["average_grade"] == pytest.approx((81.0 + 93.0 + 87.0) / 3.0)
    assert summary["min_grade"] == pytest.approx(81.0)
    assert summary["max_grade"] == pytest.approx(93.0)
    assert summary["performance_level"] == "good"


@pytest.mark.integration
def test_async_sync_to_sqlite_and_export_integration(
    sqlite_repository: SQLiteGradeRepository,
    tmp_path: Path,
) -> None:
    """Інтеграційний тест 4: AsyncGradeSyncService -> SQLiteGradeRepository -> GradeBook -> JSON Export."""
    import asyncio

    student = Student(student_id=42, name="Гнатюк Софія", group="ПІ-22", email="sofiia@example.com")
    sqlite_repository.save_student(student)

    provider = AsyncMock(spec=AsyncGradeProvider)
    provider.fetch_student_grades.return_value = [
        {"discipline_code": "CS101", "discipline_name": "Програмування на Python", "credits": 5, "grade": 98.0},
        {"discipline_code": "CS102", "discipline_name": "Алгоритми та структури даних", "credits": 4, "grade": 92.0},
    ]

    sync_service = AsyncGradeSyncService(provider=provider, repository=sqlite_repository)
    asyncio.run(sync_service.sync_student_grades(42))

    persisted_student = sqlite_repository.get_student(42)
    assert persisted_student is not None
    assert persisted_student.average_grade() == pytest.approx(95.0)

    from grading.models import GradeBook

    book = GradeBook()
    for s in sqlite_repository.list_students():
        book.add_student(s)

    output_file = tmp_path / "async_synced_report.json"
    report = export_grade_report_json(book, output_file)
    assert report["students"][0]["student_id"] == 42
    assert report["students"][0]["honors"] is True


@pytest.mark.integration
def test_run_demo_pipeline_end_to_end(tmp_path: Path) -> None:
    """Інтеграційний тест 5: перевірка демонстраційного пайплайна run_demo_pipeline (config -> data -> output + logs)."""
    from grading.main import run_demo_pipeline

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "passing_threshold: 60.0\n"
        "honors_threshold: 90.0\n"
        "mode: standard\n"
        "allowed_disciplines:\n"
        "  - Програмування на Python\n",
        encoding="utf-8",
    )
    csv_path = tmp_path / "grades.csv"
    csv_path.write_text(
        "student_id,name,group,email,discipline_code,discipline_name,credits,grade\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS101,Програмування на Python,5,95.0\n"
        "2,Шевченко Тарас,ПІ-22,taras@example.com,CS101,Програмування на Python,5,50.0\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "output" / "grade_report.json"
    log_dir = tmp_path / "logs"

    report = run_demo_pipeline(
        config_path=cfg_path,
        input_csv=csv_path,
        output_json=out_path,
        log_dir=log_dir,
    )

    assert out_path.exists()
    assert (log_dir / "application.log").exists()
    assert (log_dir / "errors.log").exists()
    assert "below threshold" in (log_dir / "errors.log").read_text(encoding="utf-8")
    assert report["statistics"] == {
        "total_students": 2,
        "passed_students": 1,
        "failed_students": 1,
        "pass_rate": 50.0,
        "absolute_success_rate": 50.0,
        "quality_rate": 50.0,
        "average_score": 72.5,
    }

