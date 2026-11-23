"""Обов'язкові експерименти з розділів 84–90 методичних вказівок.

Експеримент 1: Weak vs strong tests (execution != verification)
Експеримент 2: Coverage без змістовних assertions
Експеримент 3: Branch coverage (classify_performance)
Експеримент 4: Mock vs Fake repository
Експеримент 5: Flaky vs Deterministic test (monkeypatch)
Експеримент 6: tmp_path isolation
Експеримент 7: Failure path та відсутність небажаних викликів
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from grading import exporters
from grading.exceptions import NotificationError
from grading.models import Discipline, Grade, Student
from grading.protocols import GradeRepository, Notifier
from grading.repositories import InMemoryGradeRepository
from grading.services import GradeBookService, classify_performance


@pytest.mark.experiment
def test_experiment_1_and_2_weak_vs_strong_assertions(anna_student: Student) -> None:
    """Експерименти 1 та 2: порівняння слабкого виклику (лише покриття) і сильного тесту зі змістовними assertions."""
    # Слабкий виклик лише виконує код (даючи coverage), але нічого не перевіряє:
    _ = anna_student.average_grade()

    # Сильний тест перевіряє точний математичний результат та інваріанти стану:
    avg = anna_student.average_grade()
    assert avg == pytest.approx(91.66666666666667)
    assert anna_student.min_grade() == Grade(88.0)
    assert anna_student.max_grade() == Grade(95.0)
    assert anna_student.is_passing_all(60.0) is True


@pytest.mark.experiment
@pytest.mark.parametrize(
    ("score", "expected_label"),
    [
        (95.0, "excellent"),
        (80.0, "good"),
        (65.0, "satisfactory"),
        (50.0, "unsatisfactory"),
    ],
)
def test_experiment_3_full_branch_coverage(score: float, expected_label: str) -> None:
    """Експеримент 3: перевірка всіх гілок розгалуження функції classify_performance."""
    assert classify_performance(score) == expected_label


@pytest.mark.experiment
def test_experiment_4_mock_vs_fake_repository(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Експеримент 4: порівняння тестування взаємодії через Mock та тестування стану через Fake."""
    discipline = sample_disciplines["python"]

    # 1. Тестування через Mock (Interaction testing)
    mock_repo = Mock(spec=GradeRepository)
    mock_repo.get_student.return_value = anna_student
    service_with_mock = GradeBookService(repository=mock_repo)
    service_with_mock.assign_grade(anna_student.student_id, discipline, 99.0, notify=False)
    mock_repo.save_assessment.assert_called_once()

    # 2. Тестування через Fake (State testing)
    fake_repo = InMemoryGradeRepository()
    fake_repo.save_student(anna_student)
    service_with_fake = GradeBookService(repository=fake_repo)
    service_with_fake.assign_grade(anna_student.student_id, discipline, 100.0, notify=False)

    stored_student = fake_repo.get_student(anna_student.student_id)
    assert stored_student is not None
    assert stored_student.max_grade() == Grade(100.0)
    assert len(fake_repo.saved_assessments) == 1


@pytest.mark.experiment
def test_experiment_5_deterministic_time_and_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Експеримент 5: усунення недетермінованості часу та UUID через monkeypatch."""
    monkeypatch.setattr(exporters, "get_current_timestamp", lambda: "2026-11-21T00:00:00+00:00")
    monkeypatch.setattr(exporters, "generate_report_id", lambda: "00000000-0000-0000-0000-000000000001")

    assert exporters.get_current_timestamp() == "2026-11-21T00:00:00+00:00"
    assert exporters.generate_report_id() == "00000000-0000-0000-0000-000000000001"


@pytest.mark.experiment
@pytest.mark.parametrize("run_index", [1, 2, 3])
def test_experiment_6_tmp_path_isolation(tmp_path: Path, run_index: int) -> None:
    """Експеримент 6: перевірка повної ізоляції tmp_path між повторними запусками того самого тесту."""
    marker_file = tmp_path / "isolated_output.txt"
    assert not marker_file.exists()
    marker_file.write_text(f"run={run_index}", encoding="utf-8")
    assert marker_file.read_text(encoding="utf-8") == f"run={run_index}"


@pytest.mark.experiment
def test_experiment_7_failure_path_prevents_downstream_calls(
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Експеримент 7: перевірка того, що при збої репозиторію сповіщення студенту НЕ надсилається."""
    student = Student(student_id=5, name="Мороз Максим", group="ПІ-21", email="max@example.com")
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = student
    repository.save_assessment.side_effect = RuntimeError("Database write failed")
    notifier = Mock(spec=Notifier)

    service = GradeBookService(repository=repository, notifier=notifier)

    with pytest.raises(RuntimeError, match="Database write failed"):
        service.assign_grade(5, sample_disciplines["python"], 85.0)

    notifier.send.assert_not_called()
