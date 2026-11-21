"""Головний модуль демонстрації роботи потокового конвеєра (Варіант 7)."""

from itertools import islice
from pathlib import Path

from stream_processor.analytics import (
    analyze_grade_trends,
    calculate_stream_summary,
    group_by_discipline,
    lazy_students_above_average,
    streaming_average_grade,
    streaming_min_max_grade,
    top_n_rating,
)
from stream_processor.filters import batched_records
from stream_processor.models import GradeArchive
from stream_processor.parsers import validate_grades
from stream_processor.pipeline import (
    build_pipeline,
    compare_early_termination,
    export_pipeline_to_csv,
    run_benchmark_for_file,
)
from stream_processor.readers import (
    flatten_nested_records,
    generate_dataset,
    infinite_grade_stream,
)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data"
    main_csv = data_dir / "input.csv"

    print("=" * 72)
    print("ЛАБОРАТОРНА РОБОТА №3 | ВАРІАНТ 7: СИСТЕМА ОЦІНЮВАННЯ СТУДЕНТІВ")
    print("=" * 72)

    # 1. Створення основного датасету на 100 000 записів
    if not main_csv.exists():
        print(f"\n[1] Генерація тестового набору даних (100 000 записів): {main_csv} ...")
        generate_dataset(main_csv, count_records=100_000)
    else:
        print(f"\n[1] Використовується наявний набір даних: {main_csv}")

    # 2. Демонстрація власного Iterable та Iterator класу (GradeArchive / GradeRangeIterator)
    sample_records = list(islice(build_pipeline(main_csv), 10))
    archive = GradeArchive(sample_records, min_grade=85.0, max_grade=100.0)
    print("\n[2] Демонстрація власного Iterable (GradeArchive) та Iterator (GradeRangeIterator):")
    print(f"    Перший прохід (оцінки >= 85 із перших 10): {[round(r.grade, 1) for r in archive]}")
    print(f"    Повторний прохід по тому ж Iterable:       {[round(r.grade, 1) for r in archive]}")

    # 3. Демонстрація потокової валідації та фільтрації за дисципліною
    val_stats: dict[str, int] = {}
    discipline_name = "Programming"
    prog_pipeline = build_pipeline(
        main_csv,
        discipline=discipline_name,
        min_grade=0.0,
        validation_stats=val_stats,
    )
    avg_prog = streaming_average_grade(prog_pipeline)
    print(f"\n[3] Потокова валідація всього файлу (100 000 рядків) та фільтрація за '{discipline_name}':")
    print(f"    Валідних записів: {val_stats.get('valid', 0)} | Відсіяно невалідних: {val_stats.get('invalid', 0)}")
    print(f"    Потоковий середній бал з дисципліни '{discipline_name}': {avg_prog:.2f}")

    # 4. Визначення мінімальної та максимальної оцінки у потоці
    min_rec, max_rec = streaming_min_max_grade(build_pipeline(main_csv, discipline=discipline_name))
    print("\n[4] Мінімальна та максимальна оцінка з дисципліни 'Programming':")
    print(f"    Мінімальна: {min_rec}")
    print(f"    Максимальна: {max_rec}")

    # 5. Загальна потокова статистика та generator expression
    summary = calculate_stream_summary(build_pipeline(main_csv))
    total_points = sum(r.grade for r in build_pipeline(main_csv))
    print("\n[5] Загальна потокова агрегація по всіх дисциплінах:")
    print(f"    Кількість валідних оцінок: {summary['count']}")
    print(f"    Загальна сума балів (через generator expression): {total_points:,.2f}")
    print(f"    Середній бал: {summary['average']:.2f} (Min: {summary['minimum']}, Max: {summary['maximum']})")

    # 6. Lazy визначення студентів із середнім балом вище заданого (наприклад > 80.0)
    high_achievers = lazy_students_above_average(build_pipeline(main_csv), threshold=80.0)
    first_5_achievers = list(islice(high_achievers, 5))
    print("\n[6] Перші 5 студентів із середнім балом > 80.0 (lazy evaluation + islice):")
    for st in first_5_achievers:
        print(f"    ID {st.student_id:<5} | {st.name:<20} | Середній бал: {st.average_grade:<6.2f} | Оцінок: {st.disciplines_count}")

    # 7. Формування рейтингу ТОП-10 студентів
    top_10 = top_n_rating(build_pipeline(main_csv), n=10, min_threshold=75.0)
    print("\n[7] Рейтинг ТОП-10 студентів за середнім балом:")
    for rank, st in enumerate(top_10, start=1):
        print(f"    #{rank:<2} | ID {st.student_id:<5} | {st.name:<20} | Бал: {st.average_grade:<6.2f} ({st.disciplines_count} дисц.)")

    # 8. Групування за дисципліною через itertools.groupby
    grouped_disc = group_by_discipline(build_pipeline(main_csv))
    print("\n[8] Групування за дисциплінами (itertools.groupby):")
    for disc, info in grouped_disc.items():
        print(f"    {disc:<18} -> Записів: {info['count']:<6} | Середній: {info['average']:<6.2f} | Min: {info['min']} | Max: {info['max']}")

    # 9. Batch processing та потоковий експорт
    batches_count = 0
    total_in_batches = 0
    for batch in batched_records(build_pipeline(main_csv, min_grade=90.0), batch_size=2500):
        batches_count += 1
        total_in_batches += len(batch)
    export_path = data_dir / "excellent_grades_export.csv"
    exported_count = export_pipeline_to_csv(
        build_pipeline(main_csv, min_grade=95.0),
        export_path,
        batch_size=1000,
    )
    print("\n[9] Пакетна обробка (Batch processing) та потоковий експорт:")
    print(f"    Оцінок >= 90.0 оброблено пакетами по 2500: {batches_count} пакетів ({total_in_batches} записів)")
    print(f"    Експортовано оцінок >= 95.0 у {export_path.name}: {exported_count} записів")

    # 10. Додаткові засоби itertools (pairwise, accumulate, нескінченний генератор + islice, рекурсивний yield from)
    trends = analyze_grade_trends(build_pipeline(main_csv, discipline="Algorithms"), limit=6)
    inf_sample = list(islice(validate_grades(infinite_grade_stream()), 3))
    flattened = list(flatten_nested_records([100, [95, [88, 92]], 76]))
    print("\n[10] Додаткові можливості (pairwise, accumulate, infinite stream, recursive yield from):")
    print(f"    Оцінки (6 шт.):           {trends['grades']}")
    print(f"    Різниці (pairwise):       {trends['pairwise_diffs']}")
    print(f"    Накопичення (accumulate): {trends['cumulative_sum']}")
    print(f"    Нескінченний потік (3):   {[(r.name, r.grade) for r in inf_sample]}")
    print(f"    Рекурсивний flatten:      {flattened}")

    # 11. Дослідження Early Termination
    early_res = compare_early_termination(main_csv)
    print("\n[11] Дослідження Early Termination (пошук першої оцінки >= 99.0 у 100 000 записах):")
    print(f"    Знайдено:   {early_res['found_record']}")
    print(f"    Eager час:  {early_res['eager_time_ms']} мс | Eager пікова пам'ять: {early_res['eager_peak_kb']} КБ")
    print(f"    Lazy час:   {early_res['lazy_time_ms']} мс | Lazy пікова пам'ять:  {early_res['lazy_peak_kb']} КБ")

    # 12. Експериментальне порівняння Eager vs Lazy для 10 000, 100 000 та 500 000 записів
    print("\n[12] Експериментальне порівняння Eager vs Lazy (10 000 / 100 000 / 500 000 записів):")
    sizes = (10_000, 100_000, 500_000)
    header = (
        f"{'Records':>10} | {'Eager time (s)':>14} | {'Lazy time (s)':>13} | "
        f"{'Eager mem (KB)':>14} | {'Lazy mem (KB)':>13} | {'Eager TTFR (ms)':>15} | {'Lazy TTFR (ms)':>14}"
    )
    print("    " + "-" * len(header))
    print("    " + header)
    print("    " + "-" * len(header))

    for size in sizes:
        bench_file = main_csv if size == 100_000 else data_dir / f"dataset_{size}.csv"
        if not bench_file.exists():
            generate_dataset(bench_file, count_records=size)
        metrics = run_benchmark_for_file(bench_file)
        print(
            f"    {size:>10,d} | {metrics['eager_time_s']:>14.4f} | {metrics['lazy_time_s']:>13.4f} | "
            f"{metrics['eager_peak_kb']:>14.2f} | {metrics['lazy_peak_kb']:>13.2f} | "
            f"{metrics['eager_ttfr_ms']:>15.3f} | {metrics['lazy_ttfr_ms']:>14.3f}"
        )
        # Видаляємо тимчасові файли 10k і 500k, залишаючи основний input.csv на 100 000 записів
        if bench_file != main_csv and bench_file.exists():
            bench_file.unlink()

    print("    " + "-" * len(header))


if __name__ == "__main__":
    main()
