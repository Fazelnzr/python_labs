# Лабораторна робота №6. Автоматизоване тестування Python-програм

## Варіант 7 — Система оцінювання студентів (`Student`, `Discipline`, `Grade`, `AssessmentRecord`, `GradeBook`)

### Реалізовані вимоги та можливості
- **Доменна модель (`models.py`)**:
  - `Grade` — незмінний об'єкт-значення оцінки (`0 <= grade <= 100`), автоматичне визначення букви ECTS (`A`–`F`) та перевірка порогу складання (`is_passing`);
  - `Discipline` — навчальна дисципліна з кодом, назвою та кредитами ECTS;
  - `AssessmentRecord` — запис про оцінювання студента з обчисленням зважених балів (`weighted_points`);
  - `Student` — студент зі списком оцінок, розрахунком середнього бала (`average_grade`), середньозваженого бала (`weighted_average_grade`), `min_grade`, `max_grade`, відсотка успішності (`success_rate`) та перевіркою відсутності заборгованостей (`is_passing_all`);
  - `GradeBook` — журнал оцінок групи з обчисленням загальної статистики (`calculate_performance_stats`), `min_max_grades`, сортуванням за середнім балом (`sort_students_by_average`) та пошуком студентів вище заданого порогу (`find_students_above_threshold`).
- **Імпорт, експорт та конфігурація (`importers.py`, `exporters.py`, `config.py`)**:
  - Імпорт оцінок із CSV (`import_assessments_from_csv`, `parse_csv_row`) із детальною перевіркою кожного поля та власним винятком `RecordValidationError(field, raw_value, line_number)` зі збереженням першопричини (`raise ... from error`);
  - Експорт звіту у JSON (`export_grade_report_json`) та транзакційний атомарний експорт через `.tmp` файл (`export_grade_report_atomic`);
  - Конфігурація порогів успішності (`passing_threshold`, `honors_threshold`, `mode`, `allowed_disciplines`) через `config.yaml`, JSON або змінні середовища (`GRADING_PASSING_THRESHOLD`, `GRADING_MODE`).
- **Сервісний шар та зовнішні залежності (`services.py`, `protocols.py`, `repositories.py`)**:
  - `GradeBookService` — виставлення оцінок із підтримкою `GradeRepository`, `Notifier` та retry-логіки при тимчасових збоях сповіщень;
  - `AsyncGradeSyncService` — асинхронна синхронізація оцінок із зовнішнім провайдером (`AsyncGradeProvider`);
  - `InMemoryGradeRepository` (Fake) та `SQLiteGradeRepository` (реальна SQLite БД із протоколом контекстного менеджера `__enter__`/`__exit__`).
- **Повноцінний Test Suite (`pytest`, `pytest-cov`)**:
  - **84 тести** (unit, integration та експериментальні тести з розділів 84–90 методичних вказівок);
  - Фікстури різного scope (`function`, `module`), `autouse`-фікстура ізоляції середовища, параметризована фікстура, fixture factory (`student_factory`) та фікстура з `yield`-teardown (`sqlite_repository`);
  - Використання `pytest.approx`, `pytest.raises`, `@pytest.mark.parametrize` з `ids`, `tmp_path`, `monkeypatch`, `Mock(spec=...)`, `create_autospec`, `return_value`, `side_effect`, `AsyncMock`;
  - Загальне покриття коду (**statement + branch coverage**): **98.14%** (при встановленому порозі `fail_under = 90`).

## Структура проєкту

```text
Lab_06/
├── pyproject.toml
├── config.yaml
├── README.md
├── REPORT.md
├── data/
│   └── grades.csv
├── output/
│   └── grade_report.json
├── logs/
│   ├── application.log
│   └── errors.log
├── src/
│   └── grading/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── exporters.py
│       ├── importers.py
│       ├── main.py
│       ├── models.py
│       ├── protocols.py
│       ├── repositories.py
│       └── services.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_models.py
    │   ├── test_io_and_config.py
    │   ├── test_services_and_mocks.py
    │   └── test_experiments.py
    └── integration/
        └── test_grading_pipeline.py
```

## Запуск

```powershell
# Запуск демонстраційного конвеєра
$env:PYTHONPATH = "src"
python -m grading.main

# Запуск усього тестового набору зі звітом про покриття (statement + branch)
pytest -v --cov=grading --cov-branch --cov-report=term-missing --cov-report=html

# Запуск лише unit або лише integration тестів за маркерами
pytest -m unit
pytest -m integration
```
