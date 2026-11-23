"""Структурні протоколи (Protocols) для зовнішніх залежностей системи оцінювання."""

from __future__ import annotations

from typing import Any, Protocol

from grading.models import AssessmentRecord, Student


class GradeRepository(Protocol):
    """Інтерфейс сховища студентів та їхніх оцінок."""

    def save_student(self, student: Student) -> None: ...

    def get_student(self, student_id: int) -> Student | None: ...

    def list_students(self) -> list[Student]: ...

    def save_assessment(self, record: AssessmentRecord) -> None: ...


class Notifier(Protocol):
    """Інтерфейс сервісу надсилання сповіщень студентам."""

    def send(self, recipient: str, subject: str, message: str) -> None: ...


class AsyncGradeProvider(Protocol):
    """Інтерфейс асинхронного зовнішнього постачальника оцінок (наприклад, REST API деканату/LMS)."""

    async def fetch_student_grades(self, student_id: int) -> list[dict[str, Any]]: ...
