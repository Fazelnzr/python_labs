"""Модуль потокової аналітики, агрегації, рейтингів та групування (Варіант 7)."""

from collections import defaultdict
from collections.abc import Iterable, Iterator
from itertools import accumulate, groupby, islice, pairwise
from stream_processor.models import GradeRecord, StudentStats


def streaming_average_grade(records: Iterable[GradeRecord]) -> float:
    """Потокове обчислення середньої оцінки без створення списку всіх записів."""
    total = 0.0
    count = 0
    for record in records:
        total += record.grade
        count += 1
    return total / count if count > 0 else 0.0


def streaming_min_max_grade(
    records: Iterable[GradeRecord],
) -> tuple[GradeRecord | None, GradeRecord | None]:
    """Визначення мінімальної та максимальної оцінки за один прохід потоку."""
    min_record: GradeRecord | None = None
    max_record: GradeRecord | None = None

    for record in records:
        if min_record is None or record.grade < min_record.grade:
            min_record = record
        if max_record is None or record.grade > max_record.grade:
            max_record = record

    return min_record, max_record


def calculate_stream_summary(records: Iterable[GradeRecord]) -> dict[str, object]:
    """Комплексна потокова агрегація: кількість, середній бал, мінімум та максимум."""
    count = 0
    total = 0.0
    min_grade: float | None = None
    max_grade: float | None = None
    by_discipline: dict[str, int] = defaultdict(int)

    for record in records:
        grade = record.grade
        count += 1
        total += grade
        by_discipline[record.discipline] += 1
        if min_grade is None or grade < min_grade:
            min_grade = grade
        if max_grade is None or grade > max_grade:
            max_grade = grade

    return {
        "count": count,
        "average": total / count if count else 0.0,
        "minimum": min_grade,
        "maximum": max_grade,
        "disciplines": dict(by_discipline),
    }


def lazy_students_above_average(
    records: Iterable[GradeRecord],
    threshold: float,
) -> Iterator[StudentStats]:
    """
    Lazy визначення студентів із середнім балом вище заданого порогу.
    Агрегує суму та кількість оцінок для кожного студента, після чого ліниво генерує StudentStats.
    """
    totals: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)
    names: dict[int, str] = {}

    for record in records:
        sid = record.student_id
        totals[sid] += record.grade
        counts[sid] += 1
        names[sid] = record.name

    # Generator expression для підрахунку середніх балів і лінивої видачі тих, хто перевищує поріг
    student_averages = (
        StudentStats(
            student_id=sid,
            name=names[sid],
            average_grade=round(totals[sid] / counts[sid], 2),
            disciplines_count=counts[sid],
        )
        for sid in totals
        if (totals[sid] / counts[sid]) > threshold
    )
    yield from student_averages


def top_n_rating(
    records: Iterable[GradeRecord],
    n: int = 10,
    min_threshold: float = 0.0,
) -> list[StudentStats]:
    """
    Формування рейтингу студентів за середнім балом з обмеженням перших N результатів через itertools.islice.
    """
    qualified_stream = lazy_students_above_average(records, threshold=min_threshold)
    sorted_students = sorted(
        qualified_stream,
        key=lambda s: (s.average_grade, s.disciplines_count),
        reverse=True,
    )
    return list(islice(sorted_students, n))


def group_by_discipline(
    records: Iterable[GradeRecord],
) -> dict[str, dict[str, float | int]]:
    """
    Групування записів за дисципліною за допомогою itertools.groupby після попереднього сортування.
    """
    sorted_records = sorted(records, key=lambda r: r.discipline)
    result: dict[str, dict[str, float | int]] = {}

    for discipline, group_iter in groupby(sorted_records, key=lambda r: r.discipline):
        # Використовуємо generator expression для оцінок у групі
        grades = [item.grade for item in group_iter]
        result[discipline] = {
            "count": len(grades),
            "average": round(sum(grades) / len(grades), 2) if grades else 0.0,
            "min": min(grades) if grades else 0.0,
            "max": max(grades) if grades else 0.0,
        }
    return result


def group_by_student(
    records: Iterable[GradeRecord],
) -> Iterator[tuple[int, str, list[GradeRecord]]]:
    """
    Ліниве групування оцінок за студентом через itertools.groupby після сортування за student_id.
    """
    sorted_records = sorted(records, key=lambda r: r.student_id)
    for student_id, group_iter in groupby(sorted_records, key=lambda r: r.student_id):
        items = list(group_iter)
        name = items[0].name if items else "Unknown"
        yield student_id, name, items


def analyze_grade_trends(
    records: Iterable[GradeRecord],
    limit: int = 10,
) -> dict[str, list[float]]:
    """
    Демонстрація itertools.pairwise та itertools.accumulate на потоці оцінок:
    - pairwise обчислює різниці між послідовними оцінками;
    - accumulate обчислює накопичувальну суму балів.
    """
    limited_grades = list(islice((r.grade for r in records), limit))
    differences = [
        round(curr - prev, 2)
        for prev, curr in pairwise(limited_grades)
    ]
    cumulative = [round(val, 2) for val in accumulate(limited_grades)]
    return {
        "grades": limited_grades,
        "pairwise_diffs": differences,
        "cumulative_sum": cumulative,
    }
