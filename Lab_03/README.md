# Stream Grade Processor (Variant 7)

Лабораторна робота №3 з дисципліни **«Професійний Python»** — **«Ітератори, генератори та потокова обробка даних»** (Варіант №7: *Потокова обробка системи оцінювання студентів*).

## Опис проєкту

Модуль потокової обробки великих наборів даних (`100 000+` записів оцінок студентів), побудований за принципом **lazy evaluation** без повної матеріалізації проміжних колекцій в оперативній пам'яті.

Реалізовано:
- власні класи протоколу ітерації `Iterable` (`GradeArchive`) та `Iterator` (`GradeRangeIterator`) з методами `__iter__()` і `__next__()`;
- потокове читання та очищення CSV-файлів (`read_lines`, `clean_lines`, `read_multiple_files`) із використанням `yield` та `yield from`;
- потокову валідацію оцінок (`validate_grades`) з підрахунком валідних і відсіяних некоректних записів;
- фільтрацію за дисципліною та порогом балів (`filter_by_discipline`, `filter_by_grade_threshold`);
- потокову трансформацію та нормалізацію записів (`normalize_records`);
- потокове обчислення середнього бала (`streaming_average_grade`), мінімуму та максимуму (`streaming_min_max_grade`);
- ліниве визначення студентів із середнім балом вище заданого порогу (`lazy_students_above_average`) із використанням `generator expression`;
- формування рейтингу ТОП-$N$ студентів (`top_n_rating`) з обмеженням через `itertools.islice`;
- групування за дисципліною (`group_by_discipline`) та студентом (`group_by_student`) за допомогою `itertools.groupby`;
- пакетну обробку (`batched_records`) та потоковий експорт у CSV (`export_pipeline_to_csv`);
- додаткові засоби `itertools` (`count`, `islice`, `chain`, `groupby`, `pairwise`, `accumulate`), рекурсивний генератор `flatten_nested_records` та експериментальне порівняння **Eager vs Lazy** на вибірках у `10 000`, `100 000` та `500 000` записів за часом, піковою пам'яттю (`tracemalloc`) та `time-to-first-result`.

## Вимоги

- Python 3.10+

## Встановлення та запуск

Встановлення пакета в режимі редагування:

```bash
python -m pip install -e .
```

Запуск демонстраційного конвеєра та бенчмарку:

```bash
PYTHONPATH=src python -m stream_processor.main
```

Запуск модульних тестів:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Структура проєкту

```text
Lab_03/
├── data/
│   └── input.csv
├── report/
│   ├── README.md
│   └── Lab_03_Report.docx
├── src/
│   └── stream_processor/
│       ├── __init__.py
│       ├── models.py
│       ├── readers.py
│       ├── parsers.py
│       ├── filters.py
│       ├── analytics.py
│       ├── pipeline.py
│       └── main.py
├── tests/
│   └── test_pipeline.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Автор

- **Студент:** Назар Поцелуйко
- **Варіант:** №7
