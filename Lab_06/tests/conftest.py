"""Спільні фікстури (shared fixtures) для всіх модульних та інтеграційних тестів."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from grading.config import GradingConfig
from grading.models import Discipline, Grade, GradeBook, Student
from grading.repositories import InMemoryGradeRepository, SQLiteGradeRepository


@pytest.fixture(autouse=True)
def clean_grading_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Autouse-фікстура: гарантує ізоляцію змінних середовища перед кожним тестом."""
    monkeypatch.delenv("GRADING_PASSING_THRESHOLD", raising=False)
    monkeypatch.delenv("GRADING_MODE", raising=False)


@pytest.fixture(scope="module")
def sample_disciplines() -> dict[str, Discipline]:
    """Фікстура з області видимості module: набір навчальних дисциплін."""
    return {
        "python": Discipline(code="CS101", name="Програмування на Python", credits=5),
        "algo": Discipline(code="CS102", name="Алгоритми та структури даних", credits=4),
        "db": Discipline(code="CS103", name="Бази даних", credits=3),
    }


@pytest.fixture
def student_factory() -> Callable[..., Student]:
    """Fixture factory для гнучкого створення екземплярів Student у тестах."""
    counter = 0

    def _create_student(
        *,
        student_id: int | None = None,
        name: str = "Коваленко Анна",
        group: str = "ПІ-21",
        email: str = "anna@example.com",
        grades: list[tuple[Discipline, float]] | None = None,
    ) -> Student:
        nonlocal counter
        counter += 1
        actual_id = student_id if student_id is not None else counter
        student = Student(
            student_id=actual_id,
            name=name,
            group=group,
            email=email,
        )
        if grades:
            for discipline, score in grades:
                student.add_assessment(discipline, Grade(score))
        return student

    return _create_student


@pytest.fixture
def anna_student(sample_disciplines: dict[str, Discipline]) -> Student:
    """Фікстура студента з відмінними оцінками."""
    student = Student(
        student_id=1,
        name="Коваленко Анна",
        group="ПІ-21",
        email="anna@example.com",
    )
    student.add_assessment(sample_disciplines["python"], 95.0)
    student.add_assessment(sample_disciplines["algo"], 88.0)
    student.add_assessment(sample_disciplines["db"], 92.0)
    return student


@pytest.fixture
def populated_grade_book(
    sample_disciplines: dict[str, Discipline],
    student_factory: Callable[..., Student],
) -> GradeBook:
    """Фікстура заповненого журналу оцінок із трьома студентами різної успішності."""
    py = sample_disciplines["python"]
    algo = sample_disciplines["algo"]
    db = sample_disciplines["db"]

    anna = student_factory(
        student_id=1,
        name="Коваленко Анна",
        group="ПІ-21",
        email="anna@example.com",
        grades=[(py, 95.0), (algo, 90.0), (db, 91.0)],  # avg = 92.0
    )
    oleh = student_factory(
        student_id=2,
        name="Мельник Олег",
        group="ПІ-21",
        email="oleh@example.com",
        grades=[(py, 78.0), (algo, 72.0), (db, 81.0)],  # avg = 77.0
    )
    taras = student_factory(
        student_id=3,
        name="Шевченко Тарас",
        group="ПІ-22",
        email="taras@example.com",
        grades=[(py, 55.0), (algo, 49.0), (db, 58.0)],  # avg = 54.0
    )

    book = GradeBook()
    for student in (oleh, taras, anna):
        book.add_student(student)
    return book


@pytest.fixture
def fake_repository() -> InMemoryGradeRepository:
    """Фікстура in-memory (Fake) репозиторію."""
    return InMemoryGradeRepository()


@pytest.fixture
def sqlite_repository(tmp_path: Path) -> Iterator[SQLiteGradeRepository]:
    """Фікстура із teardown через yield: створює тимчасову SQLite БД і гарантовано закриває з'єднання."""
    db_file = tmp_path / "grades_test.sqlite3"
    repo = SQLiteGradeRepository(db_file)
    yield repo
    repo.close()


@pytest.fixture(params=[60.0, 75.0], ids=["standard_threshold_60", "high_threshold_75"])
def parameterized_config(request: pytest.FixtureRequest) -> GradingConfig:
    """Параметризована фікстура конфігурації з різними порогами успішності."""
    return GradingConfig(passing_threshold=float(request.param), honors_threshold=90.0)
