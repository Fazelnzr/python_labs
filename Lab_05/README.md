# Лабораторна робота №5. Обробка помилок, файли та серіалізація

## Варіант 7 — Імпорт та експорт системи оцінювання студентів

**Поля запису:** `student_id`, `name`, `discipline`, `grade`

### Реалізовані вимоги та додаткові можливості
- **Потоковий імпорт (Streaming I/O)** через генератори та єдиний протокол `Importer` для форматів **CSV, JSON, JSON Lines (`.jsonl`), YAML** (+ прозора підтримка `.gz`).
- **Сувора валідація даних (`validators.py`)**:
  - `student_id` — додатне ціле число (`> 0`);
  - `name` — непорожнє ПІБ (літери, апостроф, дефіс, пробіли);
  - `discipline` — перевірка належності до дозволеного переліку дисциплін із `config.yaml`;
  - `grade` — скінченне дійсне число у діапазоні `0..100`, перевірка порогу успішності (`passing_grade`).
- **Власна ієрархія винятків (`exceptions.py`)** та **явний ланцюжок винятків (`raise ... from error`)**.
- **Два режими надійності (`skip_invalid`)**:
  - **Tolerant mode (`skip_invalid: true`)** — логування некоректних записів у основний лог, окремий `logs/errors.log`, збереження деталей у `output/invalid_records.csv` та `output/summary_report.json` і продовження обробки;
  - **Strict mode (`skip_invalid: false`)** — негайна контрольована зупинка на першому некоректному записі без залишення пошкодженого вихідного файлу.
- **Власні контекстні менеджери (`utils.py`)**:
  - `@contextmanager def logged_operation(...)` — вимірювання часу виконання та логування старту/завершення/помилки;
  - `class AtomicFileWriter` (`__enter__` / `__exit__`) — транзакційний атомарний запис через тимчасовий файл `.tmp` із резервним копіюванням `.bak` та гарантованим очищенням `.tmp` у разі помилки.
- **Гнучка конфігурація (`config.yaml` + `config.py`)** з fail-fast валідацією на старті та підтримкою перевизначення через змінні середовища (`IMPORTER_INPUT_PATH`, `IMPORTER_OUTPUT_PATH`, `IMPORTER_PASSING_GRADE`, `IMPORTER_SKIP_INVALID`, `IMPORTER_LOG_LEVEL`).

## Структура проєкту

```text
Lab_5/
├── pyproject.toml
├── config.yaml
├── README.md
├── REPORT.md
├── data/
│   └── grades.csv
├── output/
│   ├── grades.json
│   ├── invalid_records.csv
│   └── summary_report.json
├── logs/
│   ├── application.log
│   └── errors.log
├── src/
│   └── reliable_importer/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── exporters.py
│       ├── experiments.py
│       ├── logging_config.py
│       ├── main.py
│       ├── models.py
│       ├── readers.py
│       ├── services.py
│       ├── utils.py
│       └── validators.py
└── tests/
    └── test_importer.py
```

## Запуск

```powershell
$env:PYTHONPATH = "src"
python -m reliable_importer.main
python -m reliable_importer.experiments
python -m pytest -v
```
