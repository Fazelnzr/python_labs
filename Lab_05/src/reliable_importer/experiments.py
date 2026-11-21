"""Автоматизоване виконання всіх 5 експериментів Лабораторної роботи №5 (Варіант 7)."""

import csv
import gc
from pathlib import Path
import tempfile
from time import perf_counter
import traceback
import tracemalloc

from reliable_importer.config import load_config
from reliable_importer.exceptions import (
    ConfigurationError,
    DataExportError,
    RecordValidationError,
)
from reliable_importer.exporters import export_grades_json
from reliable_importer.models import ImportStatistics, StudentGrade
from reliable_importer.services import filter_by_passing_grade, import_student_grades
from reliable_importer.validators import parse_student_grade

ALLOWED_DISCIPLINES = (
    "Програмування на Python",
    "Алгоритми та структури даних",
    "Бази даних",
    "Комп'ютерні мережі",
    "Дискретна математика",
    "Операційні системи",
)


def experiment_1_strict_vs_tolerant() -> dict[str, dict[str, object]]:
    """Експеримент 1: Порівняння Strict mode (skip_invalid=False) та Tolerant mode (skip_invalid=True)
    на наборі з 1000 валідних і 10 невалідних записів.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        csv_path = tmp / "exp1_input.csv"
        out_strict = tmp / "strict.json"
        out_tolerant = tmp / "tolerant.json"

        invalid_positions = {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
        total_rows = 1010

        with csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["student_id", "name", "discipline", "grade"])
            valid_idx = 1
            for row_idx in range(1, total_rows + 1):
                if row_idx in invalid_positions:
                    writer.writerow([f"bad_{row_idx}", "", "Невідома дисципліна", "150"])
                else:
                    disc = ALLOWED_DISCIPLINES[valid_idx % len(ALLOWED_DISCIPLINES)]
                    grade = 65.0 + (valid_idx % 35)
                    writer.writerow([valid_idx, f"Студент Тестовий", disc, f"{grade:.1f}"])
                    valid_idx += 1

        # 1. Strict mode
        strict_stats = ImportStatistics()
        strict_status = "Успішне завершення (0)"
        strict_exported = 0
        try:
            stream = import_student_grades(
                csv_path,
                skip_invalid=False,
                statistics=strict_stats,
                allowed_disciplines=ALLOWED_DISCIPLINES,
                passing_grade=60.0,
            )
            filtered = filter_by_passing_grade(stream, 60.0)
            strict_exported = export_grades_json(filtered, out_strict)
        except RecordValidationError as exc:
            strict_status = (
                f"Аварійна зупинка на рядку {exc.line_number} "
                f"(RecordValidationError → SystemExit(1))"
            )

        # 2. Tolerant mode
        tolerant_stats = ImportStatistics()
        tolerant_status = "Успішне завершення (0)"
        stream = import_student_grades(
            csv_path,
            skip_invalid=True,
            statistics=tolerant_stats,
            allowed_disciplines=ALLOWED_DISCIPLINES,
            passing_grade=60.0,
        )
        filtered = filter_by_passing_grade(stream, 60.0)
        tolerant_exported = export_grades_json(filtered, out_tolerant)

        return {
            "strict": {
                "processed": strict_stats.total,
                "valid": strict_stats.valid,
                "invalid": strict_stats.invalid,
                "exported": strict_exported,
                "output_exists": out_strict.exists(),
                "status": strict_status,
            },
            "tolerant": {
                "processed": tolerant_stats.total,
                "valid": tolerant_stats.valid,
                "invalid": tolerant_stats.invalid,
                "exported": tolerant_exported,
                "output_exists": out_tolerant.exists(),
                "status": tolerant_status,
            },
        }


def eager_import(path: Path) -> list[dict[str, str]]:
    """Жадібне (eager) завантаження всього CSV-файлу в пам'ять у список."""
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def streaming_import(path: Path):
    """Потокове (streaming) читання CSV-файлу через генератор."""
    with path.open("r", encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def experiment_2_streaming_vs_eager() -> list[dict[str, object]]:
    """Експеримент 2: Вимірювання часу та пікового використання RAM (tracemalloc)
    для 10 000, 100 000 та 500 000 записів у режимах Eager vs Streaming.
    """
    sizes = [10_000, 100_000, 500_000]
    results: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for n in sizes:
            csv_path = tmp / f"dataset_{n}.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as file:
                file.write("student_id,name,discipline,grade\n")
                chunk = []
                for i in range(1, n + 1):
                    chunk.append(
                        f"{i},Коваленко Анна Сергіївна,Програмування на Python,{60 + (i % 40)}\n"
                    )
                    if len(chunk) >= 10_000:
                        file.writelines(chunk)
                        chunk.clear()
                if chunk:
                    file.writelines(chunk)

            # Eager benchmark
            gc.collect()
            tracemalloc.start()
            t0 = perf_counter()
            rows = eager_import(csv_path)
            total_grade_eager = 0.0
            for r in rows:
                total_grade_eager += float(r["grade"])
            eager_time = perf_counter() - t0
            _, eager_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            del rows
            gc.collect()

            # Streaming benchmark
            tracemalloc.start()
            t0 = perf_counter()
            total_grade_stream = 0.0
            for r in streaming_import(csv_path):
                total_grade_stream += float(r["grade"])
            stream_time = perf_counter() - t0
            _, stream_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            gc.collect()

            assert abs(total_grade_eager - total_grade_stream) < 1e-6
            results.append(
                {
                    "records": n,
                    "eager_time_s": round(eager_time, 4),
                    "streaming_time_s": round(stream_time, 4),
                    "eager_peak_kb": round(eager_peak / 1024, 2),
                    " eager_peak_mb": round(eager_peak / (1024 * 1024), 2),
                    "streaming_peak_kb": round(stream_peak / 1024, 2),
                    "ram_ratio": round(eager_peak / max(stream_peak, 1), 1),
                }
            )
            csv_path.unlink(missing_ok=True)

    return results


def experiment_3_exception_chaining() -> str:
    """Експеримент 3: Демонстрація явного ланцюжка винятків (ValueError -> RecordValidationError)."""
    bad_row = {
        "student_id": "101",
        "name": "Коваленко Анна",
        "discipline": "Програмування на Python",
        "grade": "wrong",
    }
    try:
        parse_student_grade(
            bad_row,
            line_number=2,
            allowed_disciplines=ALLOWED_DISCIPLINES,
        )
    except RecordValidationError as exc:
        tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return tb_text
    return ""


def experiment_4_atomic_output() -> dict[str, object]:
    """Експеримент 4: Перевірка атомарності запису при аварійному винятку посеред експорту."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "grades.json"
        initial_record = StudentGrade(
            student_id=101,
            name="Коваленко Анна Сергіївна",
            discipline="Програмування на Python",
            grade=95.5,
            passed=True,
        )
        export_grades_json([initial_record], out_path)
        original_content = out_path.read_text(encoding="utf-8")

        def failing_generator():
            yield StudentGrade(
                student_id=202,
                name="Мельник Олег Ігорович",
                discipline="Бази даних",
                grade=88.0,
                passed=True,
            )
            raise OSError("Simulated disk write failure mid-stream")

        caught_error = None
        try:
            export_grades_json(failing_generator(), out_path)
        except DataExportError as exc:
            caught_error = f"{type(exc).__name__}: {exc} (cause: {type(exc.__cause__).__name__})"

        after_content = out_path.read_text(encoding="utf-8")
        tmp_file = out_path.with_suffix(out_path.suffix + ".tmp")

        return {
            "caught_exception": caught_error,
            "previous_output_intact": original_content == after_content,
            "tmp_file_exists": tmp_file.exists(),
        }


def experiment_5_configuration_errors() -> list[dict[str, str]]:
    """Експеримент 5: Перевірка fail-fast реакції на 6 сценаріїв помилок конфігурації."""
    cases: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        valid_input = tmp / "input.csv"
        valid_input.write_text("student_id,name,discipline,grade\n1,А Б,Бази даних,90\n", encoding="utf-8")

        # 1. Відсутній config.yaml
        try:
            load_config(tmp / "missing_config.yaml")
        except ConfigurationError as exc:
            cases.append({"case": "Відсутній config.yaml", "result": f"ConfigurationError: {exc}"})

        # 2. Неправильний синтаксис YAML
        bad_yaml = tmp / "bad_syntax.yaml"
        bad_yaml.write_text("input: [unclosed\n", encoding="utf-8")
        try:
            load_config(bad_yaml)
        except ConfigurationError as exc:
            cases.append({"case": "Неправильний синтаксис YAML", "result": f"ConfigurationError: {exc}"})

        # 3. Відсутній обов'язковий ключ input
        no_input_key = tmp / "no_input.yaml"
        no_input_key.write_text(
            "output:\n  path: out.json\nprocessing:\n  passing_grade: 60\n  skip_invalid: true\n"
            "  allowed_disciplines: ['Бази даних']\nlogging:\n  level: INFO\n  path: app.log\n",
            encoding="utf-8",
        )
        try:
            load_config(no_input_key)
        except ConfigurationError as exc:
            cases.append({"case": "Відсутній ключ input", "result": f"ConfigurationError: {exc}"})

        # 4. passing_grade = 150 (поза межами 0..100)
        bad_grade = tmp / "bad_grade.yaml"
        bad_grade.write_text(
            f"input:\n  path: {valid_input.as_posix()}\noutput:\n  path: out.json\n"
            "processing:\n  passing_grade: 150\n  skip_invalid: true\n"
            "  allowed_disciplines: ['Бази даних']\nlogging:\n  level: INFO\n  path: app.log\n",
            encoding="utf-8",
        )
        try:
            load_config(bad_grade)
        except ConfigurationError as exc:
            cases.append({"case": "passing_grade = 150", "result": f"ConfigurationError: {exc}"})

        # 5. Вхідний файл відсутній
        missing_input = tmp / "missing_input.yaml"
        missing_input.write_text(
            f"input:\n  path: {(tmp / 'no_such_file.csv').as_posix()}\noutput:\n  path: out.json\n"
            "processing:\n  passing_grade: 60\n  skip_invalid: true\n"
            "  allowed_disciplines: ['Бази даних']\nlogging:\n  level: INFO\n  path: app.log\n",
            encoding="utf-8",
        )
        try:
            load_config(missing_input)
        except ConfigurationError as exc:
            cases.append({"case": "Відсутній вхідний файл", "result": f"ConfigurationError: {exc}"})

        # 6. Output directory не існує (автоматично створюється під час експорту)
        non_existent_out_dir = tmp / "nested" / "deep" / "output" / "result.json"
        cfg_file = tmp / "valid_cfg.yaml"
        cfg_file.write_text(
            f"input:\n  path: {valid_input.as_posix()}\n"
            f"output:\n  path: {non_existent_out_dir.as_posix()}\n"
            "processing:\n  passing_grade: 60\n  skip_invalid: true\n"
            "  allowed_disciplines: ['Бази даних']\nlogging:\n  level: INFO\n"
            f"  path: {(tmp / 'logs' / 'app.log').as_posix()}\n",
            encoding="utf-8",
        )
        cfg = load_config(cfg_file)
        export_grades_json(
            [StudentGrade(1, "Коваленко Анна", "Бази даних", 90.0, True)],
            cfg.output_path,
        )
        cases.append(
            {
                "case": "Output directory не існує",
                "result": f"Директорію створено автоматично (mkdir parents=True), файл існує: {cfg.output_path.exists()}",
            }
        )

    return cases


def main() -> None:
    print("=== ЕКСПЕРИМЕНТ 1: Strict vs Tolerant (1000 valid + 10 invalid) ===")
    exp1 = experiment_1_strict_vs_tolerant()
    for mode, data in exp1.items():
        print(f"  {mode.upper()}: {data}")

    print("\n=== ЕКСПЕРИМЕНТ 2: Streaming vs Eager (10k, 100k, 500k records) ===")
    exp2 = experiment_2_streaming_vs_eager()
    for row in exp2:
        print(f"  {row}")

    print("\n=== ЕКСПЕРИМЕНТ 3: Exception Chaining ===")
    exp3 = experiment_3_exception_chaining()
    print(exp3)

    print("\n=== ЕКСПЕРИМЕНТ 4: Atomic Output ===")
    exp4 = experiment_4_atomic_output()
    print(f"  {exp4}")

    print("\n=== ЕКСПЕРИМЕНТ 5: Configuration Errors ===")
    exp5 = experiment_5_configuration_errors()
    for c in exp5:
        print(f"  - {c['case']} -> {c['result']}")


if __name__ == "__main__":
    main()
