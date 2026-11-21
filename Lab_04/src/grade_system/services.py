"""Сервісний шар застосунку (Application Services) та адаптери інфраструктури."""

from __future__ import annotations

from collections.abc import Sequence

from grade_system.dto import StudentPayload
from grade_system.models import (
    ContractStudent,
    Discipline,
    GradeBook,
    PerformanceEvaluationPolicy,
    StateFundedStudent,
    Student,
)
from grade_system.protocols import GradeReportFormatter, NotificationSender
from grade_system.repositories import InMemoryRepository
from grade_system.value_objects import Grade, PerformanceLevel


class MarkdownReportFormatter:
    """Конкретна реалізація протоколу GradeReportFormatter (структурна типізація)."""

    def format_report(
        self,
        title: str,
        students: Sequence[Student],
    ) -> str:
        lines: list[str] = [
            f"=== ВІДОМІСТЬ УСПІШНОСТІ: {title} ===",
            f"{'№':<3} | {'ПІБ студента':<24} | {'Група':<7} | {'Сер. бал':<8} | {'Зваж.':<8} | {'Статус'}",
            "-" * 92,
        ]
        for idx, student in enumerate(students, start=1):
            lines.append(
                f"{idx:<3} | {student.full_name:<24} | {student.group:<7} | "
                f"{student.average_score:<8.2f} | {student.weighted_average_score:<8.2f} | "
                f"{student.academic_status_note()}"
            )
        return "\n".join(lines)


class ConsoleNotificationSender:
    """Конкретна реалізація протоколу NotificationSender для виводу в консоль."""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str, str]] = []

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
    ) -> None:
        self.sent_messages.append((recipient, subject, message))
        print(f"[СПОВІЩЕННЯ -> {recipient}] Тема: {subject} | {message}")


def student_from_payload(
    payload: StudentPayload,
    discipline_repo: InMemoryRepository[Discipline] | None = None,
) -> Student:
    """Перетворює зовнішній TypedDict (StudentPayload) у доменний об'єкт Student."""
    funding = payload["funding_type"].lower()
    student: Student
    if funding == "state":
        student = StateFundedStudent(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
        )
    elif funding == "contract":
        tuition = payload.get("contract_tuition_fee", 38000.0)
        student = ContractStudent(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
            tuition_fee=tuition,
        )
    else:
        student = Student(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
        )

    for item in payload["assessments"]:
        discipline: Discipline | None = None
        if discipline_repo is not None:
            discipline = discipline_repo.get(item["discipline_id"])
        if discipline is None:
            discipline = Discipline(
                id=item["discipline_id"],
                name=item["discipline_name"],
                _credits=item["credits"],
            )
            if discipline_repo is not None:
                discipline_repo.add(discipline)

        assessment_type = item.get("assessment_type", "Екзамен")
        student.add_grade(
            discipline=discipline,
            grade=Grade(item["score"]),
            assessment_type=assessment_type,
        )

    return student


class GradeBookService:
    """Сервіс управління оцінюванням студентів (Application Service).

    Демонструє Dependency Injection та дотримання принципів SOLID (SRP, OCP, LSP, ISP, DIP).
    """

    def __init__(
        self,
        student_repo: InMemoryRepository[Student],
        discipline_repo: InMemoryRepository[Discipline],
        evaluation_policy: PerformanceEvaluationPolicy,
        report_formatter: GradeReportFormatter,
        notifier: NotificationSender,
        title: str = "Журнал успішності потоку",
    ) -> None:
        self._student_repo = student_repo
        self._discipline_repo = discipline_repo
        self._policy = evaluation_policy
        self._report_formatter = report_formatter
        self._notifier = notifier
        self._grade_book = GradeBook(title=title, policy=evaluation_policy)

    @property
    def grade_book(self) -> GradeBook:
        return self._grade_book

    def import_student_payload(self, payload: StudentPayload) -> Student:
        """Імпортує студента із зовнішнього TypedDict payload у репозиторій та журнал."""
        student = student_from_payload(payload, self._discipline_repo)
        self._student_repo.add(student)
        self._grade_book.register_student(student)
        return student

    def register_student(self, student: Student) -> None:
        """Реєструє студента в репозиторії та журналі."""
        self._student_repo.add(student)
        self._grade_book.register_student(student)

    def register_discipline(self, discipline: Discipline) -> None:
        """Реєструє навчальну дисципліну в репозиторії."""
        self._discipline_repo.add(discipline)

    def assign_grade(
        self,
        student_id: int,
        discipline_id: int,
        score: float,
        assessment_type: str = "Екзамен",
    ) -> Grade:
        """Виставляє оцінку студенту з дисципліни та надсилає сповіщення."""
        student = self._student_repo.get(student_id)
        if student is None:
            raise ValueError(f"Студента з ID {student_id} не знайдено.")
        discipline = self._discipline_repo.get(discipline_id)
        if discipline is None:
            raise ValueError(f"Дисципліну з ID {discipline_id} не знайдено.")

        grade = Grade(score)
        self._grade_book.record_grade(
            student_id=student.id,
            discipline=discipline,
            grade=grade,
            assessment_type=assessment_type,
        )

        self._notifier.send(
            recipient=student.email,
            subject=f"Нова оцінка з дисципліни «{discipline.name}»",
            message=(
                f"Виставлено {grade} ({assessment_type}). "
                f"Поточний середній бал: {student.average_score:.2f}."
            ),
        )
        return grade

    def get_student_summary(
        self, student_id: int
    ) -> dict[str, float | str | None]:
        """Обчислює середній, мінімальний, максимальний бал та рівень успішності студента."""
        student = self._student_repo.get(student_id)
        if student is None:
            raise ValueError(f"Студента з ID {student_id} не знайдено.")

        min_g = student.min_grade
        max_g = student.max_grade
        level: PerformanceLevel = self._policy.determine_level(student)

        return {
            "full_name": student.full_name,
            "average": student.average_score,
            "weighted_average": student.weighted_average_score,
            "rating": self._policy.calculate_rating(student),
            "min": min_g.value if min_g is not None else None,
            "max": max_g.value if max_g is not None else None,
            "performance_level": level.value,
        }

    def get_ranked_students(self, descending: bool = True) -> list[Student]:
        """Повертає відсортований за рейтингом список студентів."""
        return self._grade_book.sort_by_average(descending=descending)

    def find_students_above_threshold(self, threshold: float) -> list[Student]:
        """Повертає студентів, чий середній/рейтинговий бал перевищує заданий поріг."""
        return self._grade_book.find_above_threshold(threshold)

    def notify_honor_students(self, threshold: float = 90.0) -> list[Student]:
        """Сповіщає студентів-відмінників, які перевищили поріг успішності."""
        honors = self.find_students_above_threshold(threshold)
        for student in honors:
            self._notifier.send(
                recipient=student.email,
                subject="Відзнака за високу академічну успішність",
                message=(
                    f"Вітаємо, {student.full_name}! Ваш рейтинговий бал становить "
                    f"{self._policy.calculate_rating(student):.2f} (вище порога {threshold:.1f})."
                ),
            )
        return honors

    def generate_ranking_report(self) -> str:
        """Формує текстовий звіт рейтингу студентів через інжектований форматер."""
        ranked = self.get_ranked_students(descending=True)
        return self._report_formatter.format_report(
            title=self._grade_book.title,
            students=ranked,
        )
