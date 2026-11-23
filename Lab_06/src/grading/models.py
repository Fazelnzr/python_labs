"""Доменні моделі системи оцінювання студентів (Варіант 7).

Містить класи:
- Grade (оцінка з валідацією діапазону [0, 100], ECTS та рівнем успішності)
- Discipline (навчальна дисципліна з кредитами ECTS)
- AssessmentRecord (запис про оцінювання студента з дисципліни)
- Student (студент зі списком оцінок, обчисленням середнього, min/max та успішності)
- GradeBook (журнал оцінок групи студентів із сортуванням, пошуком вище порогу та статистикою)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Iterator

from grading.exceptions import (
    DuplicateStudentError,
    EmptyGradeBookError,
    InvalidGradeError,
    StudentNotFoundError,
)


def validate_grade_value(value: float | int) -> float:
    """Перевіряє, чи є оцінка коректним скінченним числом у діапазоні [0.0, 100.0]."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidGradeError("Grade must be a numeric value", value=value)
    numeric = float(value)
    if not math.isfinite(numeric):
        raise InvalidGradeError("Grade must be a finite number", value=value)
    if numeric < 0.0 or numeric > 100.0:
        raise InvalidGradeError(
            f"Grade must be between 0 and 100, got {numeric}",
            value=numeric,
        )
    return numeric


@total_ordering
@dataclass(frozen=True, slots=True)
class Grade:
    """Незмінний об'єкт-значення оцінки за 100-бальною шкалою."""

    value: float

    def __post_init__(self) -> None:
        validated = validate_grade_value(self.value)
        object.__setattr__(self, "value", validated)

    @property
    def ects(self) -> str:
        """Буквена оцінка за шкалою ECTS."""
        if self.value >= 90.0:
            return "A"
        if self.value >= 82.0:
            return "B"
        if self.value >= 74.0:
            return "C"
        if self.value >= 64.0:
            return "D"
        if self.value >= 60.0:
            return "E"
        if self.value >= 35.0:
            return "FX"
        return "F"

    def is_passing(self, threshold: float = 60.0) -> bool:
        """Перевіряє, чи складено дисципліну відносно порогу успішності."""
        validated_threshold = validate_grade_value(threshold)
        return self.value >= validated_threshold

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value < other.value


@dataclass(frozen=True, slots=True)
class Discipline:
    """Навчальна дисципліна."""

    code: str
    name: str
    credits: int = 4

    def __post_init__(self) -> None:
        clean_code = self.code.strip() if isinstance(self.code, str) else ""
        clean_name = self.name.strip() if isinstance(self.name, str) else ""
        if not clean_code:
            raise ValueError("Discipline code cannot be empty")
        if not clean_name:
            raise ValueError("Discipline name cannot be empty")
        if isinstance(self.credits, bool) or not isinstance(self.credits, int) or self.credits <= 0:
            raise ValueError("Discipline credits must be a positive integer")
        object.__setattr__(self, "code", clean_code)
        object.__setattr__(self, "name", clean_name)


@dataclass(frozen=True, slots=True)
class AssessmentRecord:
    """Запис про оцінювання студента з конкретної дисципліни."""

    student_id: int
    discipline: Discipline
    grade: Grade

    def __post_init__(self) -> None:
        if isinstance(self.student_id, bool) or not isinstance(self.student_id, int) or self.student_id <= 0:
            raise ValueError("Student ID must be a positive integer")
        if not isinstance(self.discipline, Discipline):
            raise TypeError("discipline must be an instance of Discipline")
        if not isinstance(self.grade, Grade):
            raise TypeError("grade must be an instance of Grade")

    @property
    def weighted_points(self) -> float:
        """Оцінка, зважена на кількість кредитів ECTS дисципліни."""
        return self.grade.value * self.discipline.credits


@dataclass(slots=True)
class Student:
    """Доменна сутність студента зі списком оцінок."""

    student_id: int
    name: str
    group: str
    email: str = ""
    _records: list[AssessmentRecord] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.student_id, bool) or not isinstance(self.student_id, int) or self.student_id <= 0:
            raise ValueError("Student ID must be a positive integer")
        clean_name = self.name.strip() if isinstance(self.name, str) else ""
        clean_group = self.group.strip() if isinstance(self.group, str) else ""
        if not clean_name:
            raise ValueError("Student name cannot be empty")
        if not clean_group:
            raise ValueError("Student group cannot be empty")
        self.name = clean_name
        self.group = clean_group
        self.email = self.email.strip()

    @property
    def records(self) -> tuple[AssessmentRecord, ...]:
        """Повертає незмінний кортеж записів про оцінювання студента."""
        return tuple(self._records)

    def add_assessment(self, discipline: Discipline, grade: Grade | float | int) -> AssessmentRecord:
        """Додає або оновлює оцінку студента з дисципліни."""
        grade_obj = grade if isinstance(grade, Grade) else Grade(float(grade))
        record = AssessmentRecord(
            student_id=self.student_id,
            discipline=discipline,
            grade=grade_obj,
        )
        for idx, existing in enumerate(self._records):
            if existing.discipline.code == discipline.code:
                self._records[idx] = record
                return record
        self._records.append(record)
        return record

    def average_grade(self) -> float:
        """Обчислює середній арифметичний бал студента."""
        if not self._records:
            raise EmptyGradeBookError(f"Student {self.student_id} has no grade records")
        return sum(r.grade.value for r in self._records) / len(self._records)

    def weighted_average_grade(self) -> float:
        """Обчислює середньозважений бал студента за кредитами ECTS."""
        if not self._records:
            raise EmptyGradeBookError(f"Student {self.student_id} has no grade records")
        total_credits = sum(r.discipline.credits for r in self._records)
        return sum(r.weighted_points for r in self._records) / total_credits

    def min_grade(self) -> Grade:
        """Визначає мінімальну оцінку студента."""
        if not self._records:
            raise EmptyGradeBookError(f"Student {self.student_id} has no grade records")
        return min(r.grade for r in self._records)

    def max_grade(self) -> Grade:
        """Визначає максимальну оцінку студента."""
        if not self._records:
            raise EmptyGradeBookError(f"Student {self.student_id} has no grade records")
        return max(r.grade for r in self._records)

    def success_rate(self, threshold: float = 60.0) -> float:
        """Розраховує відсоток складених дисциплін студента (0.0 .. 100.0)."""
        validated_threshold = validate_grade_value(threshold)
        if not self._records:
            return 0.0
        passed_count = sum(1 for r in self._records if r.grade.is_passing(validated_threshold))
        return (passed_count / len(self._records)) * 100.0

    def is_passing_all(self, threshold: float = 60.0) -> bool:
        """Перевіряє, чи склав студент усі свої дисципліни не нижче порогу."""
        validated_threshold = validate_grade_value(threshold)
        if not self._records:
            return False
        return all(r.grade.is_passing(validated_threshold) for r in self._records)


@dataclass
class GradeBook:
    """Журнал оцінювання групи студентів."""

    _students: dict[int, Student] = field(default_factory=dict)

    def add_student(self, student: Student) -> None:
        """Реєструє нового студента в журналі."""
        if student.student_id in self._students:
            raise DuplicateStudentError(f"Student with ID {student.student_id} already exists")
        self._students[student.student_id] = student

    def get_student(self, student_id: int) -> Student:
        """Повертає студента за його ID або піднімає StudentNotFoundError."""
        try:
            return self._students[student_id]
        except KeyError as error:
            raise StudentNotFoundError(f"Student with ID {student_id} not found") from error

    def record_assessment(
        self,
        student_id: int,
        discipline: Discipline,
        grade: Grade | float | int,
    ) -> AssessmentRecord:
        """Виставляє оцінку зареєстрованому студенту з дисципліни."""
        student = self.get_student(student_id)
        return student.add_assessment(discipline, grade)

    @property
    def students(self) -> list[Student]:
        """Повертає список усіх зареєстрованих студентів."""
        return list(self._students.values())

    def __len__(self) -> int:
        return len(self._students)

    def __contains__(self, student_id: int) -> bool:
        return student_id in self._students

    def __iter__(self) -> Iterator[Student]:
        return iter(self._students.values())

    def all_grades(self) -> list[Grade]:
        """Збирає всі оцінки всіх студентів у журналі."""
        return [record.grade for student in self._students.values() for record in student.records]

    def class_average(self) -> float:
        """Обчислює загальний середній бал по всіх оцінках у журналі."""
        grades = self.all_grades()
        if not grades:
            raise EmptyGradeBookError("GradeBook contains no grades")
        return sum(g.value for g in grades) / len(grades)

    def min_max_grades(self) -> tuple[Grade, Grade]:
        """Повертає кортеж (мінімальна оцінка, максимальна оцінка) по всьому журналу."""
        grades = self.all_grades()
        if not grades:
            raise EmptyGradeBookError("GradeBook contains no grades")
        return min(grades), max(grades)

    def sort_students_by_average(self, *, descending: bool = True) -> list[Student]:
        """Сортує студентів, які мають оцінки, за їхнім середнім балом."""
        graded_students = [s for s in self._students.values() if s.records]
        return sorted(
            graded_students,
            key=lambda s: (s.average_grade(), -s.student_id if descending else s.student_id),
            reverse=descending,
        )

    def find_students_above_threshold(self, threshold: float = 60.0) -> list[Student]:
        """Повертає студентів, середній бал яких >= threshold, відсортованих за спаданням середнього бала."""
        validated_threshold = validate_grade_value(threshold)
        matching = [
            s
            for s in self._students.values()
            if s.records and s.average_grade() >= validated_threshold
        ]
        return sorted(matching, key=lambda s: (s.average_grade(), -s.student_id), reverse=True)

    def calculate_performance_stats(self, threshold: float = 60.0) -> dict[str, float | int]:
        """Розраховує показники успішності студентів у журналі.

        Повертає словник із полями:
        - total_students: загальна кількість студентів із оцінками
        - passed_students: кількість студентів із середнім балом >= threshold
        - failed_students: кількість студентів із середнім балом < threshold
        - pass_rate: частка успішних студентів у відсотках (0..100)
        - absolute_success_rate: частка студентів без жодної заборгованості (< threshold) у %
        - quality_rate: якісна успішність (частка студентів із середнім балом >= 75.0) у %
        - average_score: середній бал по групі
        """
        validated_threshold = validate_grade_value(threshold)
        graded_students = [s for s in self._students.values() if s.records]
        if not graded_students:
            raise EmptyGradeBookError("Cannot calculate performance statistics for an empty GradeBook")

        total = len(graded_students)
        passed = sum(1 for s in graded_students if s.average_grade() >= validated_threshold)
        failed = total - passed
        no_debt = sum(1 for s in graded_students if s.is_passing_all(validated_threshold))
        quality = sum(1 for s in graded_students if s.average_grade() >= 75.0)
        avg_score = sum(s.average_grade() for s in graded_students) / total

        return {
            "total_students": total,
            "passed_students": passed,
            "failed_students": failed,
            "pass_rate": (passed / total) * 100.0,
            "absolute_success_rate": (no_debt / total) * 100.0,
            "quality_rate": (quality / total) * 100.0,
            "average_score": avg_score,
        }
