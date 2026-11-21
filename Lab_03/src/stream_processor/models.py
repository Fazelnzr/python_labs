"""Моделі даних та власні класи Iterable/Iterator для варіанту 7."""

from collections.abc import Iterator
from typing import NamedTuple


class GradeRecord(NamedTuple):
    """Запис оцінки студента з певної дисципліни."""

    student_id: int
    name: str
    discipline: str
    grade: float


class StudentStats(NamedTuple):
    """Агрегована статистика успішності студента."""

    student_id: int
    name: str
    average_grade: float
    disciplines_count: int


class GradeRangeIterator:
    """Власний клас-ітератор (Iterator), який ітерує по записах оцінок у заданому діапазоні балів."""

    def __init__(
        self,
        records: list[GradeRecord],
        min_grade: float = 0.0,
        max_grade: float = 100.0,
    ) -> None:
        self._records = records
        self._min_grade = min_grade
        self._max_grade = max_grade
        self._index = 0

    def __iter__(self) -> "GradeRangeIterator":
        return self

    def __next__(self) -> GradeRecord:
        while self._index < len(self._records):
            record = self._records[self._index]
            self._index += 1
            if self._min_grade <= record.grade <= self._max_grade:
                return record
        raise StopIteration


class GradeArchive:
    """Окремий клас-контейнер (Iterable), що повертає новий незалежний GradeRangeIterator при кожному iter()."""

    def __init__(
        self,
        records: list[GradeRecord],
        min_grade: float = 0.0,
        max_grade: float = 100.0,
    ) -> None:
        self.records = records
        self.min_grade = min_grade
        self.max_grade = max_grade

    def __iter__(self) -> GradeRangeIterator:
        return GradeRangeIterator(
            self.records,
            self.min_grade,
            self.max_grade,
        )
