"""Сервісний шар системи оцінювання студентів (синхронні та асинхронні сервіси)."""

from __future__ import annotations

from grading.exceptions import InvalidGradeError, StudentNotFoundError
from grading.models import AssessmentRecord, Discipline, Grade, Student, validate_grade_value
from grading.protocols import AsyncGradeProvider, GradeRepository, Notifier


def classify_performance(grade: float) -> str:
    """Класифікує рівень успішності за числовим балом (використовується також для аналізу branch coverage)."""
    validated = validate_grade_value(grade)
    if validated >= 90.0:
        return "excellent"
    if validated >= 75.0:
        return "good"
    if validated >= 60.0:
        return "satisfactory"
    return "unsatisfactory"


class GradeBookService:
    """Прикладний сервіс керування оцінками студентів зі сповіщеннями та репозиторієм."""

    def __init__(
        self,
        repository: GradeRepository,
        notifier: Notifier | None = None,
        *,
        passing_threshold: float = 60.0,
    ) -> None:
        self._repository = repository
        self._notifier = notifier
        self._passing_threshold = validate_grade_value(passing_threshold)

    @property
    def passing_threshold(self) -> float:
        return self._passing_threshold

    def register_student(self, student: Student) -> Student:
        """Зберігає студента у репозиторії."""
        self._repository.save_student(student)
        return student

    def assign_grade(
        self,
        student_id: int,
        discipline: Discipline,
        grade_value: float | int | Grade,
        *,
        notify: bool = True,
        max_retries: int = 1,
    ) -> AssessmentRecord:
        """Виставляє оцінку студенту, зберігає її в репозиторії та надсилає сповіщення.

        Якщо студента немає в репозиторії — піднімає StudentNotFoundError.
        Якщо оцінка некоректна — піднімає InvalidGradeError (репозиторій і сповіщення не викликаються).
        Підтримує retry-логіку для тимчасових збоїв сповіщень (max_retries >= 1).
        """
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")

        grade_obj = (
            grade_value
            if isinstance(grade_value, Grade)
            else Grade(validate_grade_value(grade_value))
        )

        student = self._repository.get_student(student_id)
        if student is None:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")

        record = student.add_assessment(discipline, grade_obj)
        self._repository.save_assessment(record)

        if notify and self._notifier is not None and student.email:
            status = "PASSED" if grade_obj.is_passing(self._passing_threshold) else "FAILED"
            subject = f"New grade in {discipline.name}"
            message = (
                f"Dear {student.name}, your grade in {discipline.name} is "
                f"{grade_obj.value:.1f} ({grade_obj.ects}, {status})."
            )
            self._send_with_retry(
                recipient=student.email,
                subject=subject,
                message=message,
                max_retries=max_retries,
            )

        return record

    def _send_with_retry(
        self,
        *,
        recipient: str,
        subject: str,
        message: str,
        max_retries: int,
    ) -> None:
        assert self._notifier is not None
        last_error: Exception | None = None
        for _ in range(max_retries):
            try:
                self._notifier.send(recipient, subject, message)
                return
            except Exception as error:
                last_error = error
        if last_error is not None:
            raise last_error

    def evaluate_student_summary(self, student_id: int) -> dict[str, float | int | str | bool]:
        """Формує підсумкову картку успішності студента з репозиторію."""
        student = self._repository.get_student(student_id)
        if student is None:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")

        avg = student.average_grade()
        return {
            "student_id": student.student_id,
            "name": student.name,
            "group": student.group,
            "average_grade": avg,
            "weighted_average_grade": student.weighted_average_grade(),
            "min_grade": student.min_grade().value,
            "max_grade": student.max_grade().value,
            "success_rate": student.success_rate(self._passing_threshold),
            "performance_level": classify_performance(avg),
            "is_passing_all": student.is_passing_all(self._passing_threshold),
        }


class AsyncGradeSyncService:
    """Асинхронний сервіс синхронізації оцінок студентів із зовнішнім провайдером (LMS/API деканату)."""

    def __init__(
        self,
        provider: AsyncGradeProvider,
        repository: GradeRepository,
        notifier: Notifier | None = None,
    ) -> None:
        self._provider = provider
        self._repository = repository
        self._notifier = notifier

    async def sync_student_grades(self, student_id: int) -> list[AssessmentRecord]:
        """Асинхронно завантажує оцінки студента з провайдера, валідує та зберігає їх у репозиторії."""
        student = self._repository.get_student(student_id)
        if student is None:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")

        external_items = await self._provider.fetch_student_grades(student_id)
        synced_records: list[AssessmentRecord] = []

        for item in external_items:
            discipline = Discipline(
                code=str(item["discipline_code"]),
                name=str(item["discipline_name"]),
                credits=int(item.get("credits", 4)),
            )
            grade = Grade(float(item["grade"]))
            record = student.add_assessment(discipline, grade)
            self._repository.save_assessment(record)
            synced_records.append(record)

        if self._notifier is not None and student.email and synced_records:
            self._notifier.send(
                student.email,
                "Grades synchronized",
                f"Synchronized {len(synced_records)} grade(s). Current average: {student.average_grade():.2f}",
            )

        return synced_records
