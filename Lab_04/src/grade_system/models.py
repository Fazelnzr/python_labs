"""Сутнісні класи предметної області (Domain Entities): Варіант 7 — Система оцінювання студентів."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

from grade_system.value_objects import Grade, PerformanceLevel


@dataclass(slots=True)
class Discipline:
    """Навчальна дисципліна."""

    id: int
    name: str
    _credits: int

    def __post_init__(self) -> None:
        self._validate_credits(self._credits)

    @staticmethod
    def _validate_credits(value: int) -> None:
        if value <= 0:
            raise ValueError(
                f"Кількість кредитів ECTS має бути додатною, отримано: {value}"
            )

    @property
    def credits(self) -> int:
        """Кількість кредитів ECTS із контрольованим доступом через property."""
        return self._credits

    @credits.setter
    def credits(self, value: int) -> None:
        self._validate_credits(value)
        self._credits = value

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "credits": self._credits,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self._credits} ECTS)"


@dataclass(slots=True)
class AssessmentRecord:
    """Запис про оцінювання студента з певної дисципліни."""

    discipline: Discipline
    _grade: Grade
    assessment_type: str = "Екзамен"

    @property
    def grade(self) -> Grade:
        """Оцінка запису (інкапсульована через property)."""
        return self._grade

    @grade.setter
    def grade(self, new_grade: Grade) -> None:
        self._grade = new_grade

    @property
    def weighted_points(self) -> float:
        """Кредитно-зважений бал: оцінка * кредити ECTS."""
        return self._grade.value * self.discipline.credits

    def to_dict(self) -> dict[str, object]:
        return {
            "discipline": self.discipline.name,
            "credits": self.discipline.credits,
            "score": self._grade.value,
            "ects": self._grade.ects_letter,
            "assessment_type": self.assessment_type,
        }

    def __str__(self) -> str:
        return (
            f"{self.discipline.name} [{self.assessment_type}]: {self._grade}"
        )


class Student:
    """Базова сутність студента (Domain Entity).

    Демонструє інкапсуляцію, properties, композицію (містить AssessmentRecord)
    та базовий клас для наслідування спеціалізованих форм навчання.
    """

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
    ) -> None:
        if student_id <= 0:
            raise ValueError("ID студента має бути додатним числом.")
        if not full_name.strip():
            raise ValueError("ПІБ студента не може бути порожнім.")
        self.id: int = student_id
        self._full_name: str = full_name.strip()
        self._group: str = group.strip()
        self.email: str = email.strip()
        self._records: list[AssessmentRecord] = []

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("ПІБ студента не може бути порожнім.")
        self._full_name = value.strip()

    @property
    def group(self) -> str:
        return self._group

    @group.setter
    def group(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Назва групи не може бути порожньою.")
        self._group = value.strip()

    @property
    def records(self) -> tuple[AssessmentRecord, ...]:
        """Повертає незмінний кортеж записів про оцінювання (захист інкапсуляції)."""
        return tuple(self._records)

    def add_grade(
        self,
        discipline: Discipline,
        grade: Grade,
        assessment_type: str = "Екзамен",
    ) -> AssessmentRecord:
        """Додає або оновлює оцінку студента з дисципліни."""
        for record in self._records:
            if record.discipline.id == discipline.id:
                record.grade = grade
                record.assessment_type = assessment_type
                return record
        new_record = AssessmentRecord(
            discipline=discipline,
            _grade=grade,
            assessment_type=assessment_type,
        )
        self._records.append(new_record)
        return new_record

    @property
    def average_score(self) -> float:
        """Середній арифметичний бал студента."""
        if not self._records:
            return 0.0
        total = sum(r.grade.value for r in self._records)
        return round(total / len(self._records), 2)

    @property
    def weighted_average_score(self) -> float:
        """Середньозважений бал за кредитами ECTS."""
        total_credits = sum(r.discipline.credits for r in self._records)
        if total_credits == 0:
            return 0.0
        weighted_sum = sum(r.weighted_points for r in self._records)
        return round(weighted_sum / total_credits, 2)

    @property
    def min_grade(self) -> Grade | None:
        """Мінімальна оцінка студента."""
        if not self._records:
            return None
        return min(r.grade for r in self._records)

    @property
    def max_grade(self) -> Grade | None:
        """Максимальна оцінка студента."""
        if not self._records:
            return None
        return max(r.grade for r in self._records)

    @property
    def has_academic_debt(self) -> bool:
        """Чи має студент академічну заборгованість (хоча б одну оцінку < 60)."""
        return any(not r.grade.is_passing for r in self._records)

    @property
    def performance_level(self) -> PerformanceLevel:
        """Узагальнений рівень успішності студента."""
        if not self._records or self.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        avg = self.average_score
        return Grade(avg).performance_level

    def academic_status_note(self) -> str:
        """Поліморфний метод опису статусу студента."""
        return f"Загальна форма навчання | Рівень: {self.performance_level.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "full_name": self._full_name,
            "group": self._group,
            "email": self.email,
            "average_score": self.average_score,
            "weighted_average_score": self.weighted_average_score,
            "performance_level": self.performance_level.value,
            "records_count": len(self._records),
        }

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[AssessmentRecord]:
        return iter(self._records)

    def __contains__(self, discipline_id: int) -> bool:
        return any(r.discipline.id == discipline_id for r in self._records)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"full_name={self._full_name!r}, group={self._group!r}, "
            f"avg={self.average_score:.2f})"
        )

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self._full_name} ({self._group}) — "
            f"Середній бал: {self.average_score:.2f}"
        )


class StateFundedStudent(Student):
    """Студент бюджетної форми навчання (наслідує Student із викликом super())."""

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
        base_scholarship: float = 2000.0,
    ) -> None:
        super().__init__(student_id, full_name, group, email)
        if base_scholarship < 0:
            raise ValueError("Розмір стипендії не може бути від'ємним.")
        self.base_scholarship: float = base_scholarship

    @property
    def scholarship_amount(self) -> float:
        """Розрахунок академічної стипендії залежно від успішності."""
        if not self._records or self.has_academic_debt:
            return 0.0
        if self.average_score >= 90.0:
            return round(self.base_scholarship * 1.455, 2)  # Підвищена стипендія
        if self.average_score >= 75.0:
            return self.base_scholarship
        return 0.0

    def academic_status_note(self) -> str:
        stipend = self.scholarship_amount
        stipend_info = (
            f"Стипендія: {stipend:.2f} UAH"
            if stipend > 0
            else "Без стипендії"
        )
        return (
            f"Бюджетна форма | {self.performance_level.value} | {stipend_info}"
        )


class ContractStudent(Student):
    """Студент контрактної форми навчання (наслідує Student із викликом super())."""

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
        tuition_fee: float = 38000.0,
    ) -> None:
        super().__init__(student_id, full_name, group, email)
        if tuition_fee <= 0:
            raise ValueError("Вартість контракту має бути додатною.")
        self.tuition_fee: float = tuition_fee

    @property
    def qualifies_for_budget_transfer(self) -> bool:
        """Чи претендує контрактник на переведення на бюджет за відмінне навчання."""
        return (
            len(self._records) >= 3
            and not self.has_academic_debt
            and self.average_score >= 92.0
        )

    def academic_status_note(self) -> str:
        transfer = (
            "Рекомендовано до переведення на бюджет"
            if self.qualifies_for_budget_transfer
            else f"Контракт ({self.tuition_fee:.0f} UAH/рік)"
        )
        return f"Контрактна форма | {self.performance_level.value} | {transfer}"


class PerformanceEvaluationPolicy(ABC):
    """Абстрактний базовий клас (ABC) для політики оцінювання успішності."""

    @abstractmethod
    def calculate_rating(self, student: Student) -> float:
        """Обчислює підсумковий рейтинговий бал студента."""
        ...

    @abstractmethod
    def determine_level(self, student: Student) -> PerformanceLevel:
        """Визначає рівень академічної успішності за політикою."""
        ...


class StandardAveragePolicy(PerformanceEvaluationPolicy):
    """Стандартна політика оцінювання за середнім арифметичним балом."""

    def calculate_rating(self, student: Student) -> float:
        return student.average_score

    def determine_level(self, student: Student) -> PerformanceLevel:
        if len(student) == 0 or student.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        return Grade(self.calculate_rating(student)).performance_level


class CreditWeightedPolicy(PerformanceEvaluationPolicy):
    """Політика оцінювання з урахуванням вагових коефіцієнтів кредитів ECTS."""

    def calculate_rating(self, student: Student) -> float:
        return student.weighted_average_score

    def determine_level(self, student: Student) -> PerformanceLevel:
        if len(student) == 0 or student.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        return Grade(self.calculate_rating(student)).performance_level


@dataclass
class GradeBook:
    """Журнал оцінок (GradeBook) — контейнерний доменний клас.

    Використовує композицію для зберігання студентів та політики оцінювання.
    Реалізує dunder-методи: __len__, __iter__, __contains__, __getitem__, __repr__.
    """

    title: str
    policy: PerformanceEvaluationPolicy = field(
        default_factory=StandardAveragePolicy
    )
    _students: dict[int, Student] = field(default_factory=dict)

    def register_student(self, student: Student) -> None:
        """Реєструє студента в журналі."""
        self._students[student.id] = student

    def get_student(self, student_id: int) -> Student | None:
        """Повертає студента за його ID або None."""
        return self._students.get(student_id)

    def record_grade(
        self,
        student_id: int,
        discipline: Discipline,
        grade: Grade,
        assessment_type: str = "Екзамен",
    ) -> AssessmentRecord:
        """Додає оцінку студенту за його ID."""
        student = self._students.get(student_id)
        if student is None:
            raise KeyError(f"Студента з ID={student_id} не знайдено в журналі.")
        return student.add_grade(discipline, grade, assessment_type)

    def calculate_group_statistics(self) -> tuple[float, float, float]:
        """Повертає (середній, мінімальний, максимальний) бал серед усіх оцінок у журналі."""
        all_scores = [
            record.grade.value
            for student in self._students.values()
            for record in student.records
        ]
        if not all_scores:
            return (0.0, 0.0, 0.0)
        avg_score = round(sum(all_scores) / len(all_scores), 2)
        return (avg_score, min(all_scores), max(all_scores))

    def sort_by_average(self, descending: bool = True) -> list[Student]:
        """Сортує студентів за рейтинговим/середнім балом згідно з політикою."""
        return sorted(
            self._students.values(),
            key=lambda s: self.policy.calculate_rating(s),
            reverse=descending,
        )

    def find_above_threshold(self, threshold: float) -> list[Student]:
        """Пошук студентів із середнім балом вище заданого порога."""
        if not (0.0 <= threshold <= 100.0):
            raise ValueError("Поріг бала має бути в межах від 0 до 100.")
        return [
            s
            for s in self.sort_by_average(descending=True)
            if self.policy.calculate_rating(s) > threshold
        ]

    def __len__(self) -> int:
        return len(self._students)

    def __iter__(self) -> Iterator[Student]:
        return iter(self._students.values())

    def __contains__(self, student_id: int) -> bool:
        return student_id in self._students

    def __getitem__(self, student_id: int) -> Student:
        return self._students[student_id]
