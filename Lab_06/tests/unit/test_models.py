"""Модульні тести доменних моделей Student, Discipline, Grade, AssessmentRecord та GradeBook."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from grading.exceptions import (
    DuplicateStudentError,
    EmptyGradeBookError,
    InvalidGradeError,
    StudentNotFoundError,
)
from grading.models import AssessmentRecord, Discipline, Grade, GradeBook, Student


@pytest.mark.unit
def test_create_domain_entities(sample_disciplines: dict[str, Discipline]) -> None:
    """Перевіряє нормальне створення Student, Discipline, Grade та AssessmentRecord (Arrange-Act-Assert)."""
    # Arrange
    discipline = sample_disciplines["python"]
    grade = Grade(91.5)

    # Act
    student = Student(student_id=101, name="  Бондар Ірина  ", group=" ПІ-21 ", email=" iryna@example.com ")
    record = student.add_assessment(discipline, grade)

    # Assert
    assert student.student_id == 101
    assert student.name == "Бондар Ірина"
    assert student.group == "ПІ-21"
    assert student.email == "iryna@example.com"
    assert isinstance(record, AssessmentRecord)
    assert record.student_id == 101
    assert record.discipline == discipline
    assert record.grade == Grade(91.5)
    assert record.weighted_points == pytest.approx(91.5 * 5)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_score", "expected_ects", "expected_passing"),
    [
        pytest.param(0.0, "F", False, id="min_boundary_0"),
        pytest.param(0.01, "F", False, id="just_above_min_0.01"),
        pytest.param(35.0, "FX", False, id="fx_boundary_35"),
        pytest.param(59.99, "FX", False, id="just_below_passing_59.99"),
        pytest.param(60.0, "E", True, id="passing_boundary_60"),
        pytest.param(64.0, "D", True, id="d_boundary_64"),
        pytest.param(74.0, "C", True, id="c_boundary_74"),
        pytest.param(82.0, "B", True, id="b_boundary_82"),
        pytest.param(90.0, "A", True, id="a_boundary_90"),
        pytest.param(99.99, "A", True, id="just_below_max_99.99"),
        pytest.param(100.0, "A", True, id="max_boundary_100"),
    ],
)
def test_grade_valid_boundaries_and_ects(
    raw_score: float,
    expected_ects: str,
    expected_passing: bool,
) -> None:
    """Параметризований boundary-тест валідних оцінок [0..100], шкали ECTS та порогу складання."""
    grade = Grade(raw_score)
    assert grade.value == pytest.approx(raw_score)
    assert grade.ects == expected_ects
    assert grade.is_passing(60.0) is expected_passing


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_score",
    [
        pytest.param(-0.01, id="below_min_-0.01"),
        pytest.param(-50.0, id="negative_-50"),
        pytest.param(100.01, id="above_max_100.01"),
        pytest.param(150.0, id="far_above_max_150"),
        pytest.param(float("nan"), id="nan_value"),
        pytest.param(float("inf"), id="positive_infinity"),
        pytest.param(float("-inf"), id="negative_infinity"),
        pytest.param(True, id="boolean_true_rejected"),
        pytest.param("90", id="string_type_rejected"),
    ],
)
def test_invalid_grade_raises_custom_exception(invalid_score: object) -> None:
    """Перевіряє, що некоректні оцінки та граничні значення поза [0, 100] викликають InvalidGradeError."""
    with pytest.raises(InvalidGradeError) as exc_info:
        Grade(invalid_score)  # type: ignore[arg-type]
    assert exc_info.value.value == invalid_score or str(invalid_score) in str(exc_info.value.value)


@pytest.mark.unit
def test_grade_ordering_and_comparison() -> None:
    """Перевіряє порівняння об'єктів Grade між собою та з іншими типами."""
    low = Grade(60.0)
    high = Grade(95.0)
    assert low < high
    assert high > low
    assert low <= Grade(60.0)
    assert low.__lt__("not-a-grade") is NotImplemented


@pytest.mark.unit
@pytest.mark.parametrize(
    ("code", "name", "credits", "expected_msg"),
    [
        ("", "Python", 4, "code cannot be empty"),
        ("   ", "Python", 4, "code cannot be empty"),
        ("CS101", "", 4, "name cannot be empty"),
        ("CS101", "Python", 0, "positive integer"),
        ("CS101", "Python", -3, "positive integer"),
        ("CS101", "Python", True, "positive integer"),
    ],
)
def test_discipline_validation_errors(
    code: str,
    name: str,
    credits: int,
    expected_msg: str,
) -> None:
    """Перевіряє валідацію полів Discipline (code, name, credits)."""
    with pytest.raises(ValueError, match=expected_msg):
        Discipline(code=code, name=name, credits=credits)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("student_id", "name", "group", "expected_msg"),
    [
        (0, "Анна", "ПІ-21", "positive integer"),
        (-5, "Анна", "ПІ-21", "positive integer"),
        (True, "Анна", "ПІ-21", "positive integer"),
        (1, "", "ПІ-21", "name cannot be empty"),
        (1, "   ", "ПІ-21", "name cannot be empty"),
        (1, "Анна", "", "group cannot be empty"),
    ],
)
def test_student_validation_errors(
    student_id: int,
    name: str,
    group: str,
    expected_msg: str,
) -> None:
    """Перевіряє валідацію обов'язкових полів Student при створенні."""
    with pytest.raises(ValueError, match=expected_msg):
        Student(student_id=student_id, name=name, group=group)


@pytest.mark.unit
def test_assessment_record_type_and_id_validation(sample_disciplines: dict[str, Discipline]) -> None:
    """Перевіряє захист AssessmentRecord від некоректного student_id, discipline або grade."""
    py = sample_disciplines["python"]
    with pytest.raises(ValueError, match="positive integer"):
        AssessmentRecord(student_id=0, discipline=py, grade=Grade(80.0))
    with pytest.raises(TypeError, match="Discipline"):
        AssessmentRecord(student_id=1, discipline="Python", grade=Grade(80.0))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Grade"):
        AssessmentRecord(student_id=1, discipline=py, grade=80.0)  # type: ignore[arg-type]


@pytest.mark.unit
def test_student_average_min_max_and_success_rate(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє обчислення середнього бала, середньозваженого бала, min/max оцінки та успішності студента."""
    # Оцінки Анни: Python (5 кр) = 95.0, Algo (4 кр) = 88.0, DB (3 кр) = 92.0
    assert anna_student.average_grade() == pytest.approx((95.0 + 88.0 + 92.0) / 3.0)
    expected_weighted = (95.0 * 5 + 88.0 * 4 + 92.0 * 3) / 12.0
    assert anna_student.weighted_average_grade() == pytest.approx(expected_weighted)
    assert anna_student.min_grade() == Grade(88.0)
    assert anna_student.max_grade() == Grade(95.0)
    assert anna_student.success_rate(60.0) == pytest.approx(100.0)
    assert anna_student.is_passing_all(60.0) is True

    # Оновлення існуючої оцінки з тієї ж дисципліни (повторна операція)
    anna_student.add_assessment(sample_disciplines["db"], 50.0)
    assert len(anna_student.records) == 3
    assert anna_student.min_grade() == Grade(50.0)
    assert anna_student.success_rate(60.0) == pytest.approx((2 / 3) * 100.0)
    assert anna_student.is_passing_all(60.0) is False


@pytest.mark.unit
def test_student_without_records_behavior(student_factory: Callable[..., Student]) -> None:
    """Перевіряє поведінку студента без оцінок (EmptyGradeBookError для агрегатів, 0.0 для success_rate)."""
    empty_student = student_factory(student_id=99, name="Новий Студент")
    assert empty_student.success_rate() == pytest.approx(0.0)
    assert empty_student.is_passing_all() is False

    with pytest.raises(EmptyGradeBookError):
        empty_student.average_grade()
    with pytest.raises(EmptyGradeBookError):
        empty_student.weighted_average_grade()
    with pytest.raises(EmptyGradeBookError):
        empty_student.min_grade()
    with pytest.raises(EmptyGradeBookError):
        empty_student.max_grade()


@pytest.mark.unit
def test_grade_book_sorting_and_filtering_above_threshold(
    populated_grade_book: GradeBook,
) -> None:
    """Перевіряє сортування студентів за середнім балом та пошук студентів вище заданого порогу."""
    # Сортування за спаданням: Анна (92.0) -> Олег (77.0) -> Тарас (54.0)
    descending = populated_grade_book.sort_students_by_average(descending=True)
    assert [s.student_id for s in descending] == [1, 2, 3]

    # Сортування за зростанням: Тарас (54.0) -> Олег (77.0) -> Анна (92.0)
    ascending = populated_grade_book.sort_students_by_average(descending=False)
    assert [s.student_id for s in ascending] == [3, 2, 1]

    # Студенти вище порогу 60.0 -> Анна (1) та Олег (2)
    above_60 = populated_grade_book.find_students_above_threshold(60.0)
    assert [s.student_id for s in above_60] == [1, 2]

    # Студенти вище порогу 85.0 -> лише Анна (1)
    above_85 = populated_grade_book.find_students_above_threshold(85.0)
    assert [s.student_id for s in above_85] == [1]

    # Студенти вище порогу 99.0 -> порожній список
    assert populated_grade_book.find_students_above_threshold(99.0) == []


@pytest.mark.unit
def test_grade_book_statistics_and_min_max(populated_grade_book: GradeBook) -> None:
    """Перевіряє розрахунок групової успішності, середнього бала та min/max оцінок у GradeBook."""
    assert len(populated_grade_book) == 3
    assert 1 in populated_grade_book
    assert 999 not in populated_grade_book
    assert len(list(populated_grade_book)) == 3
    assert len(populated_grade_book.students) == 3

    min_g, max_g = populated_grade_book.min_max_grades()
    assert min_g == Grade(49.0)
    assert max_g == Grade(95.0)
    assert populated_grade_book.class_average() == pytest.approx((92.0 + 77.0 + 54.0) / 3.0)

    stats = populated_grade_book.calculate_performance_stats(threshold=60.0)
    assert stats["total_students"] == 3
    assert stats["passed_students"] == 2
    assert stats["failed_students"] == 1
    assert stats["pass_rate"] == pytest.approx((2 / 3) * 100.0)
    assert stats["absolute_success_rate"] == pytest.approx((2 / 3) * 100.0)
    assert stats["quality_rate"] == pytest.approx((2 / 3) * 100.0)
    assert stats["average_score"] == pytest.approx(74.33333333333333)


@pytest.mark.unit
def test_empty_grade_book_and_duplicate_or_missing_student(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    """Перевіряє роботу з порожнім GradeBook, дублювання студента та звернення до неіснуючого студента."""
    empty_book = GradeBook()
    assert len(empty_book) == 0
    assert empty_book.sort_students_by_average() == []
    assert empty_book.find_students_above_threshold(60.0) == []

    with pytest.raises(EmptyGradeBookError):
        empty_book.class_average()
    with pytest.raises(EmptyGradeBookError):
        empty_book.min_max_grades()
    with pytest.raises(EmptyGradeBookError):
        empty_book.calculate_performance_stats()
    with pytest.raises(StudentNotFoundError):
        empty_book.get_student(404)

    empty_book.add_student(anna_student)
    with pytest.raises(DuplicateStudentError):
        empty_book.add_student(anna_student)

    record = empty_book.record_assessment(anna_student.student_id, sample_disciplines["python"], 98.0)
    assert record.grade == Grade(98.0)
