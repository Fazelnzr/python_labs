"""Структурні інтерфейси (Protocol) для зовнішніх залежностей та серіалізації."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from grade_system.models import Student


class HasId(Protocol):
    """Протокол для сутностей, які мають цілочисельний ідентифікатор id."""

    id: int


@runtime_checkable
class Serializable(Protocol):
    """Runtime-checkable протокол для об'єктів, що підтримують серіалізацію у словник."""

    def to_dict(self) -> dict[str, object]:
        ...


class GradeReportFormatter(Protocol):
    """Протокол генерації звітів успішності студентів (Reporting abstraction)."""

    def format_report(
        self,
        title: str,
        students: Sequence[Student],
    ) -> str:
        ...


class NotificationSender(Protocol):
    """Протокол надсилання сповіщень студентам (Notification abstraction)."""

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
    ) -> None:
        ...
