"""Модуль конструювання потокового конвеєра (lazy pipeline) та порівняння Eager і Lazy підходів."""

import csv
import time
import tracemalloc
from collections.abc import Iterable, Iterator
from itertools import islice
from pathlib import Path

from stream_processor.filters import (
    batched_records,
    filter_by_discipline,
    filter_by_grade_threshold,
    find_first_record,
    normalize_records,
)
from stream_processor.models import GradeRecord
from stream_processor.parsers import parse_csv_rows, validate_grades
from stream_processor.readers import clean_lines, read_lines


def build_pipeline(
    path: Path,
    discipline: str | None = None,
    min_grade: float = 0.0,
    max_grade: float = 100.0,
    validation_stats: dict[str, int] | None = None,
) -> Iterator[GradeRecord]:
    """
    Побудова багатоступеневого лінивого конвеєра (lazy pipeline):
    Input CSV -> read_lines -> clean_lines -> parse_csv_rows -> validate_grades
    -> normalize_records -> filter_by_discipline -> filter_by_grade_threshold.
    """
    lines = read_lines(path)
    cleaned = clean_lines(lines)
    rows = parse_csv_rows(cleaned)
    valid = validate_grades(rows, stats_out=validation_stats)
    normalized = normalize_records(valid)
    by_discipline = filter_by_discipline(normalized, discipline)
    filtered = filter_by_grade_threshold(by_discipline, min_grade, max_grade)
    return filtered


def export_pipeline_to_csv(
    records: Iterable[GradeRecord],
    output_path: Path,
    batch_size: int = 1000,
) -> int:
    """Потоковий експорт відфільтрованих записів у новий CSV-файл пакетами (batches)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["student_id", "name", "discipline", "grade"])
        for batch in batched_records(records, batch_size):
            for rec in batch:
                writer.writerow([rec.student_id, rec.name, rec.discipline, rec.grade])
                written += 1
    return written


def eager_process_dataset(
    path: Path,
    discipline: str | None = None,
    min_grade: float = 0.0,
) -> dict[str, float | int]:
    """
    Жадібна (Eager) обробка набору даних:
    Матеріалізує всі рядки, словники, валідні записи та відфільтровані списки у пам'яті.
    """
    with path.open("r", encoding="utf-8", newline="") as file:
        all_lines = [line.strip() for line in file if line.strip()]

    all_rows = list(csv.DictReader(all_lines))

    valid_records: list[GradeRecord] = []
    for row in all_rows:
        try:
            sid = int(row["student_id"])
            name = row["name"].strip().title()
            disc = row["discipline"].strip().title()
            grade = round(float(row["grade"]), 2)
        except (ValueError, TypeError, KeyError):
            continue
        if sid > 0 and name and disc and 0.0 <= grade <= 100.0:
            valid_records.append(GradeRecord(sid, name, disc, grade))

    if discipline:
        target = discipline.strip().lower()
        filtered_records = [
            r for r in valid_records if r.discipline.lower() == target and r.grade >= min_grade
        ]
    else:
        filtered_records = [r for r in valid_records if r.grade >= min_grade]

    grades_list = [r.grade for r in filtered_records]
    count = len(grades_list)
    avg = sum(grades_list) / count if count else 0.0
    return {
        "count": count,
        "average": round(avg, 2),
        "min": min(grades_list) if count else 0.0,
        "max": max(grades_list) if count else 0.0,
    }


def lazy_process_dataset(
    path: Path,
    discipline: str | None = None,
    min_grade: float = 0.0,
) -> dict[str, float | int]:
    """
    Лінива (Lazy) потокова обробка набору даних:
    Жоден проміжний етап не матеріалізує весь список у пам'яті.
    """
    pipeline = build_pipeline(path, discipline=discipline, min_grade=min_grade)
    count = 0
    total = 0.0
    min_val: float | None = None
    max_val: float | None = None

    for record in pipeline:
        grade = record.grade
        count += 1
        total += grade
        if min_val is None or grade < min_val:
            min_val = grade
        if max_val is None or grade > max_val:
            max_val = grade

    return {
        "count": count,
        "average": round(total / count, 2) if count else 0.0,
        "min": min_val if min_val is not None else 0.0,
        "max": max_val if max_val is not None else 0.0,
    }


def run_benchmark_for_file(path: Path) -> dict[str, float | int]:
    """Вимірює час виконання, пікове споживання пам'яті та time-to-first-result для Eager і Lazy підходів."""
    # 1. Вимірювання Eager
    tracemalloc.start()
    t0 = time.perf_counter()
    eager_res = eager_process_dataset(path, min_grade=60.0)
    eager_time = time.perf_counter() - t0
    _, eager_peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 2. Вимірювання Lazy
    tracemalloc.start()
    t0 = time.perf_counter()
    lazy_res = lazy_process_dataset(path, min_grade=60.0)
    lazy_time = time.perf_counter() - t0
    _, lazy_peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 3. Вимірювання Time to First Result (отримання першого валідного запису з оцінкою >= 95)
    t0 = time.perf_counter()
    eager_all = eager_process_dataset_list(path, min_grade=95.0)
    _ = eager_all[0] if eager_all else None
    eager_ttfr = time.perf_counter() - t0

    t0 = time.perf_counter()
    lazy_pipe = build_pipeline(path, min_grade=95.0)
    _ = next(islice(lazy_pipe, 1), None)
    lazy_ttfr = time.perf_counter() - t0

    assert eager_res["count"] == lazy_res["count"], "Розбіжність результатів Eager та Lazy!"

    return {
        "valid_count": int(lazy_res["count"]),
        "eager_time_s": round(eager_time, 4),
        "lazy_time_s": round(lazy_time, 4),
        "eager_peak_kb": round(eager_peak_mem / 1024, 2),
        "lazy_peak_kb": round(lazy_peak_mem / 1024, 2),
        "eager_ttfr_ms": round(eager_ttfr * 1000, 3),
        "lazy_ttfr_ms": round(lazy_ttfr * 1000, 3),
    }


def eager_process_dataset_list(path: Path, min_grade: float = 95.0) -> list[GradeRecord]:
    """Допоміжна функція для вимірювання Eager early termination / time-to-first-result."""
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    result: list[GradeRecord] = []
    for row in rows:
        try:
            sid = int(row["student_id"])
            name = row["name"].strip().title()
            disc = row["discipline"].strip().title()
            grade = float(row["grade"])
        except (ValueError, TypeError, KeyError):
            continue
        if sid > 0 and name and disc and min_grade <= grade <= 100.0:
            result.append(GradeRecord(sid, name, disc, grade))
    return result


def compare_early_termination(path: Path) -> dict[str, float | str]:
    """Порівняння пошуку першого запису з оцінкою >= 99.0 у великому файлі (Lazy vs Eager)."""
    predicate = lambda r: r.grade >= 99.0

    tracemalloc.start()
    t0 = time.perf_counter()
    all_records = eager_process_dataset_list(path, min_grade=0.0)
    filtered_all = [r for r in all_records if predicate(r)]
    eager_found = filtered_all[0] if filtered_all else None
    eager_time_ms = (time.perf_counter() - t0) * 1000
    _, eager_mem_kb = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    t0 = time.perf_counter()
    pipeline = build_pipeline(path)
    lazy_found = find_first_record(pipeline, predicate)
    lazy_time_ms = (time.perf_counter() - t0) * 1000
    _, lazy_mem_kb = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "found_record": str(lazy_found or eager_found),
        "eager_time_ms": round(eager_time_ms, 3),
        "lazy_time_ms": round(lazy_time_ms, 3),
        "eager_peak_kb": round(eager_mem_kb / 1024, 2),
        "lazy_peak_kb": round(lazy_mem_kb / 1024, 2),
    }
