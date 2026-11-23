# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №6

**Тема:** Автоматизоване тестування Python-програм  
**Індивідуальний варіант:** Варіант 7 — Система оцінювання студентів (`Student`, `Discipline`, `Grade`, `AssessmentRecord`, `GradeBook`)  

---

## 1. Мета роботи

Сформувати практичні навички професійного автоматизованого тестування Python-програм із використанням фреймворку `pytest`, навчитися проєктувати `unit` та `integration tests`, створювати `fixtures` (включно з `yield`-teardown, `autouse`, `scope="module"`, параметризованими фікстурами та `fixture factory`), використовувати параметризацію (`@pytest.mark.parametrize` з `ids`), перевіряти числа з плаваючою комою через `pytest.approx`, перевіряти винятки через `pytest.raises` та `exc_info`, ізолювати файлову систему (`tmp_path`) і змінні середовища/функції (`monkeypatch`), застосовувати `Mock`, `create_autospec`, `return_value`, `side_effect`, `AsyncMock` та аналізувати `statement` і `branch coverage` за допомогою `pytest-cov`.

---

## 2. Короткий опис тестованого проєкту (Варіант 7)

Проєкт реалізує автоматизовану систему обліку та аналізу навчальних досягнень студентів закладу вищої освіти:
1. **Доменні сутності (`src/grading/models.py`):**
   - `Grade` — незмінний об'єкт-значення оцінки за 100-бальною шкалою (`0.0 <= value <= 100.0`), який обчислює букву ECTS (`A`, `B`, `C`, `D`, `E`, `FX`, `F`), перевіряє подолання порогу успішності (`is_passing`) та підтримує впорядкування (`@total_ordering`).
   - `Discipline` — навчальна дисципліна з кодом (`code`), назвою (`name`) та кількістю кредитів ECTS (`credits > 0`).
   - `AssessmentRecord` — запис про оцінку студента з конкретної дисципліни з розрахунком зважених балів (`weighted_points = grade.value * discipline.credits`).
   - `Student` — сутність студента зі списком оцінок, яка обчислює середній бал (`average_grade`), середньозважений бал (`weighted_average_grade`), мінімальну (`min_grade`) і максимальну (`max_grade`) оцінки, відсоток складених дисциплін (`success_rate`) та ознаку відсутності академічної заборгованості (`is_passing_all`).
   - `GradeBook` — журнал оцінок групи студентів, що підтримує реєстрацію студентів, виставлення оцінок, обчислення загального середнього бала (`class_average`), пошук мінімуму/максимуму (`min_max_grades`), сортування студентів за середнім балом (`sort_students_by_average`), фільтрацію студентів вище порогу (`find_students_above_threshold`) та розрахунок показників успішності (`calculate_performance_stats`).
2. **Конфігурація (`src/grading/config.py`):**
   - Клас `GradingConfig` та функції `load_config()`, `get_passing_threshold()`, `get_grading_mode()`, що підтримують завантаження з `YAML`/`JSON` та перевизначення через змінні середовища `GRADING_PASSING_THRESHOLD` і `GRADING_MODE`.
3. **Імпорт та експорт (`src/grading/importers.py`, `src/grading/exporters.py`):**
   - Валідація рядків CSV (`parse_csv_row`) та імпорт журналу (`import_assessments_from_csv`) із генерацією власного винятку `RecordValidationError(field, raw_value, line_number)` та збереженням ланцюжка винятків (`__cause__`).
   - Експорт звіту про успішність у JSON (`export_grade_report_json`) та транзакційний атомарний запис через тимчасовий `.tmp` файл (`export_grade_report_atomic`).
4. **Сервіси та сховища (`src/grading/services.py`, `src/grading/repositories.py`, `src/grading/protocols.py`):**
   - Структурні протоколи `GradeRepository`, `Notifier`, `AsyncGradeProvider`.
   - `InMemoryGradeRepository` (Fake) та `SQLiteGradeRepository` (реальна база даних SQLite з контекстним менеджером `__enter__`/`__exit__`).
   - `GradeBookService` (виставлення оцінок, інтеграція з репозиторієм і сповіщеннями, retry-логіка) та `AsyncGradeSyncService` (асинхронна синхронізація оцінок із зовнішнього API).

---

## 3. Структура Production Code та Test Suite

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

---

## 4. Матриця тестування (Test Matrix)

| Компонент / Функція | Normal Case | Minimum / Maximum Boundary | Empty / Missing Data | Invalid Input / Type | Dependency Failure / State Transition |
|---|---|---|---|---|---|
| `Grade` & `validate_grade_value` | `Grade(85.0)` -> ECTS `B`, `is_passing=True` | `0.0`, `0.01`, `35.0`, `59.99`, `60.0`, `64.0`, `74.0`, `82.0`, `90.0`, `99.99`, `100.0` | — | `-0.01`, `-50.0`, `100.01`, `150.0`, `NaN`, `±Inf`, `True`, `"90"` -> `InvalidGradeError` | Порівняння з не-`Grade` повертає `NotImplemented` |
| `Discipline` & `AssessmentRecord` | `Discipline("CS101", "Python", 5)`, `weighted_points = 457.5` | `credits = 1` | Порожній `code` або `name` -> `ValueError` | `credits <= 0`, `credits=True`, `student_id <= 0`, невірний тип `discipline`/`grade` | Незмінність (`frozen=True`) після створення |
| `Student` | Обчислення `average_grade`, `weighted_average_grade`, `min_grade`, `max_grade`, `success_rate` | Оцінки `0.0` та `100.0`, поріг `60.0` | Студент без оцінок -> `EmptyGradeBookError`, `success_rate() == 0.0` | Порожнє ім'я/група, `student_id <= 0` -> `ValueError` | Повторне додавання оцінки з тієї ж дисципліни оновлює існуючий запис |
| `GradeBook` | `sort_students_by_average`, `find_students_above_threshold`, `calculate_performance_stats` | Поріг `60.0`, `75.0`, `85.0`, `99.0` | Порожній `GradeBook` -> `EmptyGradeBookError` або `[]` | Неіснуючий ID -> `StudentNotFoundError` | Повторна реєстрація студента з тим самим ID -> `DuplicateStudentError` |
| `importers.py` (`parse_csv_row`, `import_assessments_from_csv`) | Імпорт коректного CSV із декількома студентами та дисциплінами | Оцінки `0.0` та `100.0`, кредити `1` | Відсутній файл, порожній CSV, відсутні колонки -> `DataImportError` | Пошкоджені поля (`student_id="abc"`, `grade="excellent"`, заборонена дисципліна) -> `RecordValidationError` + `__cause__` | — |
| `config.py` (`GradingConfig`, `load_config`) | Завантаження з `YAML`/`JSON`, змінні середовища `GRADING_PASSING_THRESHOLD`, `GRADING_MODE` | `passing_threshold == honors_threshold` | Відсутні змінні середовища -> значення за замовчуванням (`60.0`, `"standard"`) | `passing > honors`, невідомий `mode`, нечисловий поріг, битий YAML -> `ConfigurationError` | Перевизначення значень файлу конфігурації змінними середовища |
| `exporters.py` (`export_grade_report_json`, `export_grade_report_atomic`) | Експорт звіту зі статистикою та рейтингом у JSON | Порожній `GradeBook` -> `min_grade=None`, `total_students=0` | Автоматичне створення батьківських директорій | Помилка серіалізації -> `DataExportError` | При збої атомарного експорту старий файл зберігається, а `.tmp` видаляється |
| `GradeBookService` & `AsyncGradeSyncService` | Виставлення оцінки, збереження в репозиторії, відправка сповіщення | `max_retries=1`, `max_retries=3` | Студент без email -> сповіщення не шлеться | `max_retries=0` -> `ValueError`, оцінка `120.0` -> `InvalidGradeError` | Збій `Notifier.send` або `AsyncGradeProvider` (`side_effect`) -> виняток, відсутність побічних викликів |

---

## 5. Приклади реалізованих тестів та технік `pytest`

### 5.1. Фікстури (`conftest.py`): `autouse`, `scope="module"`, `fixture factory`, `yield`-teardown та параметризована фікстура

```python
@pytest.fixture(autouse=True)
def clean_grading_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Autouse-фікстура: гарантує ізоляцію змінних середовища перед кожним тестом."""
    monkeypatch.delenv("GRADING_PASSING_THRESHOLD", raising=False)
    monkeypatch.delenv("GRADING_MODE", raising=False)


@pytest.fixture
def sqlite_repository(tmp_path: Path) -> Iterator[SQLiteGradeRepository]:
    """Фікстура із teardown через yield: створює тимчасову SQLite БД і гарантовано закриває з'єднання."""
    db_file = tmp_path / "grades_test.sqlite3"
    repo = SQLiteGradeRepository(db_file)
    yield repo
    repo.close()


@pytest.fixture(params=[60.0, 75.0], ids=["standard_threshold_60", "high_threshold_75"])
def parameterized_config(request: pytest.FixtureRequest) -> GradingConfig:
    """Параметризована фікстура конфігурації з різними порогами успішності."""
    return GradingConfig(passing_threshold=float(request.param), honors_threshold=90.0)
```

### 5.2. Параметризований Boundary Test, `pytest.approx` та `pytest.raises` із перевіркою Custom Exception

```python
@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_score", "expected_ects", "expected_passing"),
    [
        pytest.param(0.0, "F", False, id="min_boundary_0"),
        pytest.param(0.01, "F", False, id="just_above_min_0.01"),
        pytest.param(59.99, "FX", False, id="just_below_passing_59.99"),
        pytest.param(60.0, "E", True, id="passing_boundary_60"),
        pytest.param(99.99, "A", True, id="just_below_max_99.99"),
        pytest.param(100.0, "A", True, id="max_boundary_100"),
    ],
)
def test_grade_valid_boundaries_and_ects(
    raw_score: float,
    expected_ects: str,
    expected_passing: bool,
) -> None:
    grade = Grade(raw_score)
    assert grade.value == pytest.approx(raw_score)
    assert grade.ects == expected_ects
    assert grade.is_passing(60.0) is expected_passing
```

Перевірка власного винятку `RecordValidationError` та ланцюжка винятків (`__cause__`):

```python
def test_exception_chaining_on_invalid_grade_parsing() -> None:
    row = {
        "student_id": "1",
        "name": "Коваленко Анна",
        "group": "ПІ-21",
        "discipline_code": "CS101",
        "discipline_name": "Python",
        "credits": "4",
        "grade": "not-a-float",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_csv_row(row, line_number=3)

    assert exc_info.value.field == "grade"
    assert exc_info.value.line_number == 3
    assert isinstance(exc_info.value.__cause__, ValueError)
```

### 5.3. Ізоляція файлової системи (`tmp_path`) та підміна оточення і функцій (`monkeypatch`)

```python
def test_monkeypatch_env_and_function_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    populated_grade_book: GradeBook,
) -> None:
    monkeypatch.setenv("GRADING_PASSING_THRESHOLD", "75.5")
    monkeypatch.setenv("GRADING_MODE", "weighted")
    assert get_passing_threshold() == pytest.approx(75.5)
    assert get_grading_mode() == "weighted"

    monkeypatch.setattr(exporters, "get_current_timestamp", lambda: "2026-11-21T12:00:00+00:00")
    monkeypatch.setattr(exporters, "generate_report_id", lambda: "REP-FIXED-001")

    output_file = tmp_path / "report.json"
    export_grade_report_json(populated_grade_book, output_file)

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["report_id"] == "REP-FIXED-001"
    assert saved["generated_at"] == "2026-11-21T12:00:00+00:00"
```

### 5.4. Використання `Mock`, `create_autospec`, `return_value`, `side_effect` та Interaction Assertions

```python
def test_assign_grade_success_with_mock_and_interaction_assertions(
    anna_student: Student,
    sample_disciplines: dict[str, Discipline],
) -> None:
    repository = Mock(spec=GradeRepository)
    repository.get_student.return_value = anna_student
    notifier = create_autospec(Notifier, instance=True)

    service = GradeBookService(repository=repository, notifier=notifier, passing_threshold=60.0)
    record = service.assign_grade(
        student_id=anna_student.student_id,
        discipline=sample_disciplines["python"],
        grade_value=96.0,
    )

    assert record.grade == Grade(96.0)
    repository.get_student.assert_called_once_with(anna_student.student_id)
    repository.save_assessment.assert_called_once_with(record)
    notifier.send.assert_called_once_with(
        "anna@example.com",
        "New grade in Програмування на Python",
        "Dear Коваленко Анна, your grade in Програмування на Python is 96.0 (A, PASSED).",
    )
```

Перевірка `side_effect` (список послідовних збоїв для перевірки retry-логіки):

```python
notifier.send.side_effect = [
    NotificationError("Temporary timeout 1"),
    NotificationError("Temporary timeout 2"),
    None,
]
record = service.assign_grade(
    student_id=anna_student.student_id,
    discipline=sample_disciplines["db"],
    grade_value=52.0,
    max_retries=3,
)
assert notifier.send.call_count == 3
```

### 5.5. Тестування асинхронної залежності через `AsyncMock`

```python
def test_async_grade_sync_service_with_async_mock(
    fake_repository: InMemoryGradeRepository,
) -> None:
    student = Student(student_id=10, name="Савченко Вікторія", group="ПІ-21", email="vika@example.com")
    fake_repository.save_student(student)

    provider = AsyncMock(spec=AsyncGradeProvider)
    provider.fetch_student_grades.return_value = [
        {"discipline_code": "CS101", "discipline_name": "Програмування на Python", "credits": 5, "grade": 94.0},
        {"discipline_code": "CS102", "discipline_name": "Бази даних", "credits": 4, "grade": 86.0},
    ]
    notifier = Mock(spec=Notifier)

    async_service = AsyncGradeSyncService(provider=provider, repository=fake_repository, notifier=notifier)
    records = asyncio.run(async_service.sync_student_grades(10))

    assert len(records) == 2
    assert student.average_grade() == pytest.approx(90.0)
    provider.fetch_student_grades.assert_awaited_once_with(10)
```

### 5.6. Інтеграційний тест повного конвеєра (`CSV Import -> Grade Calculation -> JSON Export`)

```python
@pytest.mark.integration
def test_full_csv_import_calculation_and_json_export_pipeline(
    tmp_path: Path,
    parameterized_config: GradingConfig,
) -> None:
    csv_path = tmp_path / "students_grades.csv"
    csv_path.write_text(
        "student_id,name,group,email,discipline_code,discipline_name,credits,grade\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS101,Програмування на Python,5,96.0\n"
        "1,Коваленко Анна,ПІ-21,anna@example.com,CS102,Бази даних,4,90.0\n"
        "2,Мельник Олег,ПІ-21,oleh@example.com,CS101,Програмування на Python,5,70.0\n"
        "2,Мельник Олег,ПІ-21,oleh@example.com,CS102,Бази даних,4,66.0\n"
        "3,Шевченко Тарас,ПІ-22,taras@example.com,CS101,Програмування на Python,5,52.0\n"
        "3,Шевченко Тарас,ПІ-22,taras@example.com,CS102,Бази даних,4,48.0\n",
        encoding="utf-8",
    )
    output_json = tmp_path / "out" / "grade_report.json"

    grade_book = import_assessments_from_csv(csv_path, config=parameterized_config)
    export_grade_report_json(grade_book, output_json, config=parameterized_config)

    assert output_json.exists()
    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert [s["student_id"] for s in report["students"]] == [1, 2, 3]
```

---

## 6. Результати обов'язкових експериментів (п. 84–90)

У файлі `tests/unit/test_experiments.py` виконано та задокументовано всі 7 експериментів:
1. **Експеримент 1–2 (Weak vs Strong tests & Coverage без assertions):** Продемонстровано, що виклик `anna_student.average_grade()` без перевірки результату забезпечує виконання рядків коду (statement coverage), але не здатний виявити логічну помилку у формулі. Додано сильні `assert` із `pytest.approx(91.66666666666667)` та перевіркою `min_grade`/`max_grade`. Висновок: *execution != verification*.
2. **Експеримент 3 (Branch coverage):** Для функції `classify_performance(grade)` перевірено всі 4 гілки розгалуження (`95.0 -> excellent`, `80.0 -> good`, `65.0 -> satisfactory`, `50.0 -> unsatisfactory`), що дало 100% покриття гілок умови.
3. **Експеримент 4 (Mock vs Fake):** Порівняно тестування `GradeBookService` із `Mock(spec=GradeRepository)` (перевірка виклику `save_assessment.assert_called_once()`) та з `InMemoryGradeRepository` (перевірка кінцевого стану збереженого студента та списку `saved_assessments`). Fake-репозиторій забезпечує кращу читабельність для перевірки стану, тоді як Mock зручний для перевірки протоколу взаємодії на межі системи.
4. **Експеримент 5 (Flaky vs Deterministic test):** Замість нестабільних перевірок реального системного часу `datetime.now()` та випадкового `uuid.uuid4()` використано `monkeypatch.setattr`, що зробило JSON-експорт повністю детермінованим.
5. **Експеримент 6 (`tmp_path` isolation):** Тест запису файлу запущено тричі поспіль через `@pytest.mark.parametrize("run_index", [1, 2, 3])`; перед кожним запуском `assert not marker_file.exists()` підтверджує, що `tmp_path` створює повністю ізольований каталог і не залишає сміття у репозиторії.
6. **Експеримент 7 (Failure path):** При імітації збою запису в БД (`repository.save_assessment.side_effect = RuntimeError("Database write failed")`) перевірено не лише підняття `RuntimeError`, а й те, що `notifier.send.assert_not_called()` — студент не отримує хибне повідомлення про незбережену оцінку.

---

## 7. Результат запуску Test Suite та аналіз Coverage

Команда запуску:
```powershell
pytest -v --cov=grading --cov-branch --cov-report=term-missing --cov-report=html
```

### Підсумок виконання тестів:
- **Зібрано та виконано:** `84 tests`
- **Успішно пройдено (PASSED):** `84`
- **Провалено (FAILED):** `0`

### Таблиця Statement та Branch Coverage:

```text
Name                          Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------
src\grading\__init__.py           9      0      0      0   100%
src\grading\config.py            69      0     20      2    98%   80->97, 92->97
src\grading\exceptions.py        20      0      0      0   100%
src\grading\exporters.py         49      3      4      1    92%   110-111, 131
src\grading\importers.py         31      1     10      0    98%   195
src\grading\main.py              35      0      4      1    97%   55->62
src\grading\models.py           186      0     62      0   100%
src\grading\protocols.py          6      0      0      0   100%
src\grading\repositories.py      77      1     16      3    96%   26, 31->exit, 84->exit, 167->165
src\grading\services.py          76      0     24      1    99%   108->exit
-------------------------------------------------------------------------
TOTAL                           558      5    140      8    98%
Required test coverage of 90.0% reached. Total coverage: 98.14%
```

### Аналіз HTML-звіту та залишкових неохоплених шляхів (Missing Paths):
- Модулі `models.py`, `exceptions.py`, `protocols.py`, `__init__.py` мають **100% statement і branch coverage**.
- Поодинокі неохоплені рядки (`exporters.py:110-111`, `importers.py:195`) відповідають захисним блокам `except OSError` при низькорівневій відмові файлової системи ОС під час запису/читання, а також гілці порожнього YAML-файлу (`loaded is None` у `config.py:92->97`). Щоб покрити їх за потреби, достатньо підмінити `Path.open` або `Path.write_text` через `monkeypatch.setattr` з `side_effect=OSError("Permission denied")`.

### Опис дефектів, виявлених під час розробки тестів:
1. **Проблема `bool` як підкласу `int` у Python:** Під час параметризованого тестування `Grade(True)` та `Student(student_id=True, ...)` стандартна перевірка `isinstance(val, int)` пропускала булеві значення `True`/`False` (оскільки `issubclass(bool, int) is True`). Завдяки unit-тестам з параметром `True` у функцію `validate_grade_value` та конструктори `Student`, `Discipline`, `AssessmentRecord` було додано явну перевірку `if isinstance(value, bool): raise ...`.
2. **Детермінованість сортування при однакових середніх балах:** Під час тестування `GradeBook.sort_students_by_average(descending=False)` та `descending=True` виявлено, що при однаковому середньому балі порядок студентів залежав від порядку додавання. Виправлено ключ сортування на `(s.average_grade(), -s.student_id if descending else s.student_id)`.

---

## 8. Відповіді на контрольні запитання

1. **Що таке automated test та які його основні переваги?**  
   Автоматизований тест — це програмний код, який автоматично виконує частину цільової програми з визначеними вхідними даними та перевіряє (`assert`), чи відповідає отриманий результат або поведінка очікуваній. Переваги: швидке виявлення дефектів, захист від регресій при рефакторингу, жива документація контрактів коду та можливість безперервної перевірки в CI/CD.
2. **Що таке regression?**  
   Регресія — це повторна поява помилки або порушення раніше працюючої функціональності після внесення змін, оптимізації чи додавання нового коду.
3. **Що таке unit test, integration test і чим вони відрізняються?**  
   *Unit test* перевіряє одну невелику одиницю поведінки (функцію, метод, клас) ізольовано від зовнішніх ресурсів та інших підсистем. *Integration test* перевіряє спільну роботу декількох реальних компонентів (наприклад, завантаження конфігурації + читання CSV + доменні розрахунки + запис у SQLite або JSON-файл).
4. **Що показує test pyramid і чому unit tests зазвичай більше?**  
   Піраміда тестування показує оптимальне співвідношення тестів: найбільша основа — швидкі й дешеві unit-тести, середній шар — інтеграційні тести, верхівка — невелика кількість повільних E2E-тестів. Unit-тестів більше, бо вони виконуються за мілісекунди, не потребують зовнішньої інфраструктури і точно локалізують місце поломки.
5. **Що таке pytest, як він знаходить тести і якими командами запускається?**  
   `pytest` — це найпопулярніший фреймворк тестування в Python. Він автоматично знаходить файли `test_*.py` або `*_test.py` та функції `test_*` (і класи `Test*`). Запускається командою `pytest`; ключі: `pytest -v` (детальний вивід імен тестів), `pytest -x` (зупинка після першого падіння), `pytest --tb=short` (короткий стек викликів).
6. **Що означає Arrange–Act–Assert та для чого використовується `assert`?**  
   Це трифазна структура тесту: *Arrange* (підготовка об'єктів і даних), *Act* (виклик тестованої дії), *Assert* (перевірка результату). Оператор `assert` перевіряє істинність умови; у разі хибності виникає `AssertionError` (assertion failure) з детальною інтроспекцією значень від `pytest`.
7. **Чому floats не завжди слід порівнювати через `==` і для чого `pytest.approx`?**  
   Через двійкове представлення чисел із плаваючою комою (IEEE 754) вираз `0.1 + 0.2` дає `0.30000000000000004`. `pytest.approx` виконує порівняння з допустимою відносною/абсолютною похибкою.
8. **Для чого `pytest.raises`, як перевірити message та отримати об'єкт винятку через `exc_info`?**  
   Контекстний менеджер `with pytest.raises(ExpectedException, match="regex") as exc_info:` перевіряє, що код всередині блоку піднімає очікуваний виняток із відповідним повідомленням (`match`). Саму інстанцію винятку та її атрибути (`exc_info.value.field`, `exc_info.value.__cause__`) отримують через `exc_info.value`.
9. **Що таке boundary testing і які межі тестують для діапазону `0–100`?**  
   Це тестування на межах області допустимих значень, де найчастіше трапляються помилки `<` замість `<=`. Для `0..100` тестують щонайменше: `-0.01`, `0`, `0.01`, `50`, `99.99`, `100`, `100.01`.
10. **Що таке parametrization, для чого `@pytest.mark.parametrize` та `ids`?**  
    Параметризація дозволяє запустити одну тестову функцію з багатьма наборами вхідних даних та очікуваних результатів без дублювання коду. Параметр `ids` (або `pytest.param(..., id="...")`) задає зрозумілі людиночитабельні назви тестових випадків у звіті.
11. **Що таке fixture, fixture setup/teardown, `yield`, scopes та `conftest.py`?**  
    Fixture — це функція з декоратором `@pytest.fixture`, яка готує тестове оточення або дані (*setup*) і передається у тест як аргумент за ім'ям. Код після оператора `yield` у фікстурі виконує гарантоване очищення ресурсів (*teardown*, наприклад `repo.close()`). Підтримувані scopes: `function` (за замовчуванням), `class`, `module`, `package`, `session`. Файл `tests/conftest.py` зберігає спільні фікстури, які `pytest` підключає автоматично без ручного `import`.
12. **Що таке `tmp_path` і `monkeypatch`?**  
    `tmp_path` — вбудована фікстура, що надає унікальну ізольовану тимчасову директорію (`pathlib.Path`) для кожного тесту, запобігаючи засміченню проєкту та конфліктам між тестами (*test isolation*). `monkeypatch` дозволяє безпечно підміняти змінні середовища (`setenv`, `delenv`), атрибути або функції модулів (`setattr`), автоматично відновлюючи початковий стан після завершення тесту.
13. **Що таке test double та чим відрізняються Dummy, Stub, Fake, Mock і Spy?**  
    *Test double* — підставний об'єкт, що замінює реальну залежність у тесті:
    - *Dummy* — об'єкт-заповнювач аргументу, який фактично не використовується;
    - *Stub* — повертає заздалегідь заготовлені відповіді (`return_value`);
    - *Fake* — має працюючу спрощену реалізацію (наприклад, `InMemoryGradeRepository` замість СУБД);
    - *Mock* — об'єкт з очікуваннями щодо того, як саме і з якими аргументами мають бути викликані його методи;
    - *Spy* — записує інформацію про виклики для подальшої перевірки, часто обгортаючи реальний об'єкт.
14. **Для чого `spec`, `return_value`, `side_effect` та методи перевірки викликів у `Mock`?**  
    `spec=ProtocolClass` (або `create_autospec`) обмежує інтерфейс мока методами реального класу, захищаючи від одруківок у назвах методів. `return_value` задає значення, яке повертає метод мока. `side_effect` дозволяє підняти виняток, викликати функцію або повертати послідовність різних значень при повторних викликах. Методи `assert_called_once()`, `assert_called_once_with(...)`, `assert_not_called()` перевіряють факт і аргументи взаємодії (*interaction testing*).
15. **Чим відрізняється state testing від interaction testing і чому потрібно `patch` там, де об'єкт використовується?**  
    *State testing* перевіряє кінцевий стан системи чи повернене значення після операції; *interaction testing* перевіряє, як об'єкт викликав зовнішні залежності (наприклад, відправку email через `Notifier`). Функція `patch` підміняє посилання на об'єкт у конкретному просторі імен, тому патчити треба в модулі, який імпортував і викликає функцію (*where it is looked up*), а не там, де вона була оголошена.
16. **Що таке `AsyncMock`, flaky test та over-mocking?**  
    `AsyncMock` — це мок для `async def` корутин, виклики якого перевіряють через `assert_awaited_once_with(...)`. *Flaky test* — нестабільний тест, який при незмінному коді іноді проходить, а іноді падає (через залежність від `random`, поточного часу, мережі чи порядку тестів). *Over-mocking* — антипатерн, коли в тесті замокано внутрішні деталі реалізації, через що тест перевіряє лише моки і ламається при будь-якому рефакторингу.
17. **Що таке statement coverage, branch coverage та чому 100% coverage не гарантує відсутності багів?**  
    *Statement coverage* вимірює частку виконаних рядків/інструкцій коду, а *branch coverage* (`--cov-branch`) перевіряє, чи були пройдені обидві гілки (`True` та `False`) кожної умовного оператора `if/else`. 100% покриття показує лише те, що код виконувався під час тестів, але без змістовних `assert` або при пропущених граничних значеннях код все одно може містити помилки.

---

## 9. Висновок

У ході виконання лабораторної роботи №6 для індивідуального варіанта 7 (Система оцінювання студентів) було розроблено архітектурно чистий Python-проєкт та створено комплексний автоматизований тестовий набір із **84 тестів** (`unit`, `integration` та дослідницьких тестів). У роботі практично застосовано фікстури різних рівнів (`autouse`, `scope="module"`, `yield`-teardown, параметризовані фікстури, `fixture factory`), параметризацію граничних значень оцінок `[0..100]`, перевірку `pytest.approx`, перехоплення власних винятків і ланцюжків `__cause__` через `pytest.raises`, ізоляцію файлових операцій через `tmp_path`, підміну конфігурації середовища та недетермінованих функцій через `monkeypatch`, а також тестування синхронних і асинхронних зовнішніх залежностей за допомогою `Mock`, `create_autospec` та `AsyncMock`. Досягнуто загального покриття коду з урахуванням гілок (**statement + branch coverage**) на рівні **98.14%**, що перевищує заданий поріг `90%` і гарантує надійний захист системи від регресій.
