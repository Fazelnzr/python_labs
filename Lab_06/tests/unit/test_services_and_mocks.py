"""Модульні тести сервісного шару з використанням Mock, autospec, return_value, side_effect та AsyncMock."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from grading.exceptions import (
    InvalidGradeError,
    NotificationError,
    StudentNotFoundError,
)
from grading.models import Discipline, Grade, Student
from grading.protocols import AsyncGradeProvider, GradeRepository, Notifier
from grading.repositories import InMemoryGradeRepository, SQLiteGradeRepository
from grading.services import AsyncGradeSyncService, GradeBookService, classify_performance


@pytest.mark.unit
def test_assign_grade_success_with_mock_and_interaction_assertions(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє успішне виставлення оцінки через Mock із spec, return_value та assert_called_once_with."""
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = anna_student
    notifier = create_autospec(Notifier, instance=True)

    service = GradeBookService(repository=repository, notifier=notifier, passing_threshold=60.0)
    discipline = sample_disciplines["python"]

    record = service.assign_grade(
        student_id=anna_student.student_id,
        discipline=discipline,
        grade_value=96.0,
    )

    assert record.grade == Grade(96.0)
    assert service.passing_threshold == pytest.approx(60.0)
    repository.get_student.assert_called_once_with(anna_student.student_id)
    repository.save_assessment.assert_called_once_with(record)
    notifier.send.assert_called_once_with(
        "anna@example.com",
        "New grade in Програмування на Python",
        "Dear Коваленко Анна, your grade in Програмування на Python is 96.0 (A, PASSED).",
    )


@pytest.mark.unit
def test_assign_grade_notifier_failure_via_side_effect(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє failure path зовнішнього сервісу сповіщень через side_effect."""
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = anna_student
    notifier = Mock(spec=Notifier)
    notifier.send.side_effect = NotificationError("SMTP gateway unavailable")

    service = GradeBookService(repository=repository, notifier=notifier)

    with pytest.raises(NotificationError, match="SMTP gateway unavailable"):
        service.assign_grade(
            student_id=anna_student.student_id,
            discipline=sample_disciplines["algo"],
            grade_value=85.0,
        )

    repository.save_assessment.assert_called_once()
    notifier.send.assert_called_once()


@pytest.mark.unit
def test_assign_grade_retry_logic_with_side_effect_sequence(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє retry-логіку сервісу сповіщень за допомогою списку side_effect (2 збої -> успіх)."""
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = anna_student
    notifier = Mock(spec=Notifier)
    notifier.send.side_effect = [
        NotificationError("Temporary timeout 1"),
        NotificationError("Temporary timeout 2"),
        None,
    ]

    service = GradeBookService(repository=repository, notifier=notifier)
    record = service.assign_grade(
        student_id=anna_student.student_id,
        discipline=sample_disciplines["db"],
        grade_value=52.0,
        max_retries=3,
    )

    assert record.grade == Grade(52.0)
    assert notifier.send.call_count == 3


@pytest.mark.unit
def test_assign_grade_invalid_input_or_missing_student_prevents_interactions(
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє, що при невалідній оцінці або відсутності студента зайві виклики не виконуються."""
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = None
    notifier = Mock(spec=Notifier)
    service = GradeBookService(repository=repository, notifier=notifier)

    # Некоректний max_retries
    with pytest.raises(ValueError, match="max_retries"):
        service.assign_grade(1, sample_disciplines["python"], 80.0, max_retries=0)

    # Некоректна оцінка -> навіть get_student не повинен викликатися
    with pytest.raises(InvalidGradeError):
        service.assign_grade(1, sample_disciplines["python"], 120.0)
    repository.get_student.assert_not_called()
    repository.save_assessment.assert_not_called()
    notifier.send.assert_not_called()

    # Студента не знайдено -> save_assessment та notifier.send не викликаються
    with pytest.raises(StudentNotFoundError):
        service.assign_grade(404, sample_disciplines["python"], 85.0)
    repository.get_student.assert_called_once_with(404)
    repository.save_assessment.assert_not_called()
    notifier.send.assert_not_called()


@pytest.mark.unit
def test_evaluate_student_summary_and_performance_classification(
    anna_student: Student,
    fake_repository: InMemoryGradeRepository,
) -> None:
    """Перевіряє роботу GradeBookService із Fake-репозиторієм та всі гілки classify_performance."""
    service = GradeBookService(repository=fake_repository, passing_threshold=60.0)
    service.register_student(anna_student)

    summary = service.evaluate_student_summary(anna_student.student_id)
    assert summary["student_id"] == 1
    assert summary["performance_level"] == "excellent"
    assert summary["is_passing_all"] is True
    assert summary["average_grade"] == pytest.approx(91.66666666666667)

    with pytest.raises(StudentNotFoundError):
        service.evaluate_student_summary(999)

    assert classify_performance(95.0) == "excellent"
    assert classify_performance(80.0) == "good"
    assert classify_performance(65.0) == "satisfactory"
    assert classify_performance(40.0) == "unsatisfactory"


@pytest.mark.unit
def test_async_grade_sync_service_with_async_mock(
    fake_repository: InMemoryGradeRepository,
) -> None:
    """Перевіряє асинхронну синхронізацію оцінок через AsyncMock (return_value та assert_awaited_once_with)."""
    import asyncio

    student = Student(student_id=10, name="Савченко Вікторія", group="ПІ-21", email="vika@example.com")
    fake_repository.save_student(student)

    provider = AsyncMock(spec=AsyncGradeProvider)
    provider.fetch_student_grades.return_value = [
        {"discipline_code": "CS101", "discipline_name": "Програмування на Python", "credits": 5, "grade": 94.0},
        {"discipline_code": "CS102", "discipline_name": "Бази даних", "credits": 4, "grade": 86.0},
    ]
    notifier = Mock(spec=Notifier)

    async_service = AsyncGradeSyncService(
        provider=provider,
        repository=fake_repository,
        notifier=notifier,
    )
    records = asyncio.run(async_service.sync_student_grades(10))

    assert len(records) == 2
    assert student.average_grade() == pytest.approx(90.0)
    provider.fetch_student_grades.assert_awaited_once_with(10)
    notifier.send.assert_called_once_with(
        "vika@example.com",
        "Grades synchronized",
        "Synchronized 2 grade(s). Current average: 90.00",
    )


@pytest.mark.unit
def test_async_grade_sync_service_failure_and_missing_student(
    fake_repository: InMemoryGradeRepository,
) -> None:
    """Перевіряє обробку помилки мережі в AsyncMock (side_effect) та випадок відсутності студента."""
    import asyncio

    provider = AsyncMock(spec=AsyncGradeProvider)
    provider.fetch_student_grades.side_effect = ConnectionError("LMS API timeout")
    notifier = Mock(spec=Notifier)
    async_service = AsyncGradeSyncService(provider=provider, repository=fake_repository, notifier=notifier)

    # Якщо студента немає в репозиторії — провайдер навіть не викликається
    with pytest.raises(StudentNotFoundError):
        asyncio.run(async_service.sync_student_grades(404))
    provider.fetch_student_grades.assert_not_awaited()

    # Якщо студент є, але провайдер кидає ConnectionError — помилка прокидається, сповіщення не шлеться
    student = Student(student_id=11, name="Кравчук Дмитро", group="ПІ-22", email="dmytro@example.com")
    fake_repository.save_student(student)

    with pytest.raises(ConnectionError, match="LMS API timeout"):
        asyncio.run(async_service.sync_student_grades(11))

    provider.fetch_student_grades.assert_awaited_once_with(11)
    notifier.send.assert_not_called()


@pytest.mark.unit
def test_sqlite_repository_context_manager_cleanup_on_exception() -> None:
    """Перевіряє гарантоване закриття з'єднання SQLiteGradeRepository при виході з with навіть під час винятку."""
    repo = SQLiteGradeRepository(":memory:")
    with pytest.raises(RuntimeError, match="Simulated crash inside with"):
        with repo:
            assert repo.is_open is True
            raise RuntimeError("Simulated crash inside with")

    assert repo.is_open is False
    with pytest.raises(RuntimeError, match="Database connection is closed"):
        repo.list_students()
