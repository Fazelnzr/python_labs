"""Модульні тести для Лабораторної роботи №4 (Варіант 7 — Система оцінювання студентів)."""

from __future__ import annotations

import pytest

from grade_system.dto import StudentPayload
from grade_system.models import (
    ContractStudent,
    CreditWeightedPolicy,
    Discipline,
    GradeBook,
    StandardAveragePolicy,
    StateFundedStudent,
    Student,
)
from grade_system.protocols import Serializable
from grade_system.repositories import InMemoryRepository, scale_score
from grade_system.services import (
    ConsoleNotificationSender,
    GradeBookService,
    MarkdownReportFormatter,
)
from grade_system.value_objects import Grade, PerformanceLevel


def test_grade_value_object() -> None:
    g1 = Grade(95.0)
    g2 = Grade(82.0)

    assert g1.ects_letter == "A"
    assert g2.ects_letter == "B"
    assert g1.performance_level == PerformanceLevel.EXCELLENT
    assert g1 > g2
    assert (g1 + g2) == 177.0
    assert g1.is_passing is True

    with pytest.raises(ValueError):
        Grade(105.0)
    with pytest.raises(ValueError):
        Grade(-5.0)


def test_discipline_and_student_encapsulation() -> None:
    d = Discipline(id=1, name="ООП", _credits=5)
    assert d.credits == 5
    d.credits = 6
    assert d.credits == 6
    with pytest.raises(ValueError):
        d.credits = 0

    s = StateFundedStudent(
        student_id=1,
        full_name="Коваленко Анна",
        group="КН-21",
        email="anna@example.com",
    )
    s.add_grade(d, Grade(92.0))
    assert len(s) == 1
    assert 1 in s
    assert s.average_score == 92.0
    assert s.scholarship_amount > 2000.0
    assert isinstance(s, Serializable)


def test_contract_student_inheritance() -> None:
    c = ContractStudent(
        student_id=2,
        full_name="Шевченко Дарина",
        group="КН-22",
        email="daryna@example.com",
        tuition_fee=40000.0,
    )
    for i, score in enumerate([95.0, 93.0, 94.0], start=1):
        c.add_grade(Discipline(id=i, name=f"Дисц {i}", _credits=4), Grade(score))
    assert c.qualifies_for_budget_transfer is True


def test_grade_book_and_service() -> None:
    student_repo = InMemoryRepository[Student]()
    discipline_repo = InMemoryRepository[Discipline]()
    notifier = ConsoleNotificationSender()
    service = GradeBookService(
        student_repo=student_repo,
        discipline_repo=discipline_repo,
        evaluation_policy=StandardAveragePolicy(),
        report_formatter=MarkdownReportFormatter(),
        notifier=notifier,
    )

    payload: StudentPayload = {
        "id": 10,
        "full_name": "Тестовий Студент",
        "group": "КН-21",
        "email": "test@example.com",
        "funding_type": "state",
        "assessments": [
            {
                "discipline_id": 1,
                "discipline_name": "ООП",
                "credits": 5,
                "score": 90.0,
            },
            {
                "discipline_id": 2,
                "discipline_name": "БД",
                "credits": 4,
                "score": 80.0,
            },
        ],
    }
    student = service.import_student_payload(payload)
    assert student.id in service.grade_book
    assert len(service.grade_book) == 1

    service.assign_grade(student_id=10, discipline_id=2, score=94.0)
    assert len(notifier.sent_messages) == 1

    summary = service.get_student_summary(10)
    assert summary["average"] == 92.0
    assert summary["min"] == 90.0
    assert summary["max"] == 94.0

    above_90 = service.find_students_above_threshold(90.0)
    assert len(above_90) == 1
    assert scale_score(90, 1.0) == 90.0
    assert CreditWeightedPolicy().calculate_rating(student) > 90.0


def test_grade_book_container_dunders() -> None:
    gb = GradeBook(title="Тест")
    st = Student(1, "Іваненко Іван", "КН-21", "ivan@example.com")
    gb.register_student(st)
    assert len(gb) == 1
    assert 1 in gb
    assert gb[1] is st
    assert list(gb) == [st]
