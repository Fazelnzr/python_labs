"""Модуль потокового читання файлів та генерації тестових наборів даних."""

import csv
import random
from collections.abc import Iterable, Iterator
from itertools import chain, count
from pathlib import Path


def read_lines(path: Path) -> Iterator[str]:
    """Потокове читання рядків із файлу за допомогою yield from."""
    with path.open("r", encoding="utf-8") as file:
        yield from file


def read_multiple_files(paths: Iterable[Path]) -> Iterator[str]:
    """Об'єднання декількох файлів у єдиний потік рядків (пропускаючи повторні заголовки)."""
    iterator = iter(paths)
    try:
        first_path = next(iterator)
    except StopIteration:
        return

    first_stream = read_lines(first_path)

    def _skip_header(path: Path) -> Iterator[str]:
        lines = read_lines(path)
        next(lines, None)
        yield from lines

    rest_streams = (_skip_header(p) for p in iterator)
    yield from chain(first_stream, *rest_streams)


def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    """Очищення потоку рядків від пробільних символів та порожніх рядків."""
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            yield cleaned


def flatten_nested_records(items: Iterable[object]) -> Iterator[object]:
    """Рекурсивний генератор розгортання вкладених списків із використанням yield from."""
    for item in items:
        if isinstance(item, list):
            yield from flatten_nested_records(item)
        else:
            yield item


def infinite_grade_stream(seed: int = 42) -> Iterator[dict[str, str]]:
    """Нескінченний генератор потоків оцінок студентів (використовує itertools.count)."""
    rng = random.Random(seed)
    disciplines = (
        "Programming",
        "Algorithms",
        "Databases",
        "Mathematics",
        "Operating Systems",
        "Computer Networks",
    )
    first_names = ("Anna", "Oleh", "Iryna", "Andrii", "Maria", "Petro", "Dmytro", "Sofiia")
    last_names = ("Koval", "Melnyk", "Bondar", "Shevchenko", "Boyko", "Novak", "Tkachenko", "Kravchuk")

    for record_num in count(start=1):
        student_id = (record_num % 5000) + 1
        yield {
            "student_id": str(student_id),
            "name": f"{rng.choice(first_names)} {rng.choice(last_names)}",
            "discipline": rng.choice(disciplines),
            "grade": str(round(rng.uniform(50.0, 100.0), 2)),
        }


def generate_dataset(path: Path, count_records: int, seed: int = 42) -> None:
    """Генерація CSV-файлу з оцінками студентів (включно з невеликою часткою некоректних записів для перевірки валідації)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    disciplines = (
        "Programming",
        "Algorithms",
        "Databases",
        "Mathematics",
        "Operating Systems",
        "Computer Networks",
    )
    first_names = ("Anna", "Oleh", "Iryna", "Andrii", "Maria", "Petro", "Dmytro", "Sofiia")
    last_names = ("Koval", "Melnyk", "Bondar", "Shevchenko", "Boyko", "Novak", "Tkachenko", "Kravchuk")

    num_students = max(50, count_records // 5)
    student_names = {
        sid: f"{rng.choice(first_names)} {rng.choice(last_names)}"
        for sid in range(1, num_students + 1)
    }

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["student_id", "name", "discipline", "grade"])

        for idx in range(1, count_records + 1):
            # Кожен 250-й запис робимо некоректним для тестування streaming validation
            if idx % 250 == 0:
                writer.writerow([idx, "Invalid Grade Student", "Programming", "error_grade"])
            elif idx % 333 == 0:
                writer.writerow([idx, "Out of Range Student", "Algorithms", "115.5"])
            else:
                sid = rng.randint(1, num_students)
                writer.writerow(
                    [
                        sid,
                        student_names[sid],
                        rng.choice(disciplines),
                        round(rng.uniform(45.0, 100.0), 2),
                    ]
                )
