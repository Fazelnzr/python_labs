"""Реалізації сховищ даних (Fake/In-Memory та SQLite репозиторії)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType

from grading.models import AssessmentRecord, Discipline, Grade, Student


class InMemoryGradeRepository:
    """In-memory (Fake) репозиторій для швидких тестів стану без моків."""

    def __init__(self) -> None:
        self._students: dict[int, Student] = {}
        self._assessments: list[AssessmentRecord] = []

    def save_student(self, student: Student) -> None:
        self._students[student.student_id] = student

    def get_student(self, student_id: int) -> Student | None:
        return self._students.get(student_id)

    def list_students(self) -> list[Student]:
        return list(self._students.values())

    def save_assessment(self, record: AssessmentRecord) -> None:
        self._assessments.append(record)
        student = self._students.get(record.student_id)
        if student is not None:
            student.add_assessment(record.discipline, record.grade)

    @property
    def saved_assessments(self) -> tuple[AssessmentRecord, ...]:
        return tuple(self._assessments)


class SQLiteGradeRepository:
    """Репозиторій оцінок на базі SQLite із підтримкою протоколу контекстного менеджера."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._db_path = str(db_path)
        self._connection: sqlite3.Connection | None = sqlite3.connect(self._db_path)
        self._create_schema()

    def _ensure_open(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("Database connection is closed")
        return self._connection

    def _create_schema(self) -> None:
        conn = self._ensure_open()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    student_id INTEGER NOT NULL,
                    discipline_code TEXT NOT NULL,
                    discipline_name TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    grade_value REAL NOT NULL,
                    PRIMARY KEY (student_id, discipline_code),
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                )
                """
            )

    @property
    def is_open(self) -> bool:
        return self._connection is not None

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> SQLiteGradeRepository:
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def save_student(self, student: Student) -> None:
        conn = self._ensure_open()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO students (student_id, name, group_name, email)
                VALUES (?, ?, ?, ?)
                """,
                (student.student_id, student.name, student.group, student.email),
            )
        for record in student.records:
            self.save_assessment(record)

    def save_assessment(self, record: AssessmentRecord) -> None:
        conn = self._ensure_open()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO assessments (
                    student_id, discipline_code, discipline_name, credits, grade_value
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.student_id,
                    record.discipline.code,
                    record.discipline.name,
                    record.discipline.credits,
                    record.grade.value,
                ),
            )

    def get_student(self, student_id: int) -> Student | None:
        conn = self._ensure_open()
        cursor = conn.execute(
            "SELECT student_id, name, group_name, email FROM students WHERE student_id = ?",
            (student_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        student = Student(
            student_id=int(row[0]),
            name=str(row[1]),
            group=str(row[2]),
            email=str(row[3]),
        )
        records_cursor = conn.execute(
            """
            SELECT discipline_code, discipline_name, credits, grade_value
            FROM assessments
            WHERE student_id = ?
            ORDER BY discipline_code
            """,
            (student_id,),
        )
        for code, name, credits, grade_val in records_cursor.fetchall():
            discipline = Discipline(code=str(code), name=str(name), credits=int(credits))
            student.add_assessment(discipline, Grade(float(grade_val)))
        return student

    def list_students(self) -> list[Student]:
        conn = self._ensure_open()
        cursor = conn.execute("SELECT student_id FROM students ORDER BY student_id")
        students: list[Student] = []
        for (student_id,) in cursor.fetchall():
            student = self.get_student(int(student_id))
            if student is not None:
                students.append(student)
        return students
