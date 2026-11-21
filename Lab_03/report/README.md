# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №3

**Дисципліна:** «Професійний Python»  
**Тема:** Ітератори, генератори та потокова обробка даних  
**Варіант:** №7 — Потокова обробка системи оцінювання студентів (`stream_processor`)  
**Виконав:** студент Назар Поцелуйко  

---

## 1. Мета роботи

Сформувати практичні навички роботи з ітераційною моделлю Python, ітераторами, генераторами, ключовими конструкціями `yield` та `yield from`, генераторними виразами (`generator expressions`), модулем `itertools`, принципом лінивих обчислень (`lazy evaluation`) та потоковою обробкою великих наборів даних (`streaming processing`) без повного завантаження проміжних колекцій в оперативну пам'ять.

---

## 2. Постановка задачі (Індивідуальний варіант №7)

**Тема варіанта:** Потокова обробка системи оцінювання студентів.  
**Формат вхідних даних (CSV):**

```text
student_id,name,discipline,grade
```

**Необхідно реалізувати:**
1. Потокове читання (`streaming reading`) та валідацію оцінок студентів (`streaming validation`) із пропуском та підрахунком некоректних записів.
2. Фільтрацію записів за дисципліною (`filter_by_discipline`) та діапазоном балів (`filter_by_grade_threshold`).
3. Потокове обчислення середньої оцінки (`streaming average grade`) для вибраних записів без матеріалізації списку.
4. Визначення мінімальної та максимальної оцінки (`streaming_min_max_grade`) за один прохід потоку.
5. Ліниве (`lazy`) визначення студентів із середнім балом вище заданого порогу (`lazy_students_above_average`).
6. Формування рейтингу студентів з обмеженням перших $N$ результатів через `itertools.islice` (`top_n_rating`).
7. Пакетну обробку записів (`batch processing` — `batched_records`) та потоковий експорт у файл.
8. Групування за дисципліною (`group_by_discipline`) або студентом (`group_by_student`) за допомогою `itertools.groupby`.
9. Власні класи `Iterable` (`GradeArchive`) та `Iterator` (`GradeRangeIterator`), рекурсивний генератор із `yield from`, нескінченний потік із `itertools.count` + `islice`, аналіз послідовних оцінок через `itertools.pairwise` та `itertools.accumulate`, а також експериментальне дослідження **Eager vs Lazy** на вибірках у **10 000**, **100 000** та **500 000** записів.

---

## 3. Опис вхідного набору даних та структури проєкту

### 3.1. Опис вхідного датасету (`data/input.csv`)

Файл `data/input.csv` містить **100 000 записів** оцінювання студентів за 6 дисциплінами (`Programming`, `Algorithms`, `Databases`, `Mathematics`, `Operating Systems`, `Computer Networks`). Для перевірки надійності етапу потокової валідації генератор тестових даних спеціально вставляє некоректні рядки (текстові значення `"error_grade"` замість числа та оцінки поза межами `[0; 100]`, наприклад `115.5`). Із 100 000 рядків **99 301** є валідними, а **699** автоматично відсіюються на етапі валідації.

### 3.2. Структура проєкту

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

---

## 4. Теоретичні основи та ключові конструкції у проєкті

### 4.1. Різниця між `Iterable` та `Iterator` і власний клас-ітератор

- **Iterable (ітерований об'єкт)** — об'єкт, з якого можна отримати ітератор за допомогою `iter(obj)`. Він реалізує метод `__iter__()`, який щоразу повертає новий екземпляр ітератора. При цьому `iter(iterable) is iterable` повертає `False`.
- **Iterator (ітератор)** — об'єкт, що зберігає поточний стан обходу, реалізує метод `__next__()` для повернення чергового елемента (або підняття винятку `StopIteration` після вичерпання) та метод `__iter__()`, який повертає `self` (`iter(iterator) is iterator == True`). Ітератор є *one-shot* об'єктом.

У файлі `src/stream_processor/models.py` реалізовано розділення контейнера `GradeArchive` (`Iterable`) та ітератора `GradeRangeIterator` (`Iterator`):

```python
class GradeRangeIterator:
    """Власний клас-ітератор (Iterator), який ітерує по записах оцінок у заданому діапазоні балів."""

    def __init__(
        self,
        records: list[GradeRecord],
        min_grade: float = 0.0,
        max_grade: float = 100.0,
    ) -> None:
        self._records = records
        self._min_grade = min_grade
        self._max_grade = max_grade
        self._index = 0

    def __iter__(self) -> "GradeRangeIterator":
        return self

    def __next__(self) -> GradeRecord:
        while self._index < len(self._records):
            record = self._records[self._index]
            self._index += 1
            if self._min_grade <= record.grade <= self._max_grade:
                return record
        raise StopIteration


class GradeArchive:
    """Окремий клас-контейнер (Iterable), що повертає новий незалежний GradeRangeIterator при кожному iter()."""

    def __init__(
        self,
        records: list[GradeRecord],
        min_grade: float = 0.0,
        max_grade: float = 100.0,
    ) -> None:
        self.records = records
        self.min_grade = min_grade
        self.max_grade = max_grade

    def __iter__(self) -> GradeRangeIterator:
        return GradeRangeIterator(self.records, self.min_grade, self.max_grade)
```

### 4.2. Генераторні функції, `yield`, `yield from` та `generator expressions`

У проєкті реалізовано понад 10 генераторних функцій із `yield` та `yield from`:
1. **Потокове читання рядків із файлу (`yield from`)** та **рекурсивний генератор розгортання списків**:
```python
def read_lines(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as file:
        yield from file

def flatten_nested_records(items: Iterable[object]) -> Iterator[object]:
    for item in items:
        if isinstance(item, list):
            yield from flatten_nested_records(item)
        else:
            yield item
```
2. **Генераторні вирази (`generator expressions`)**:
   - обчислення загальної суми балів без створення проміжного списку: `total_points = sum(r.grade for r in build_pipeline(main_csv))`;
   - ліниве формування статистики студентів із середнім балом вище порогу у функції `lazy_students_above_average`.

### 4.3. Використані засоби модуля `itertools`

1. **`itertools.islice`** — обмеження нескінченного потоку `infinite_grade_stream()`, отримання перших $N$ студентів у рейтингу `top_n_rating()` та формування пакетів фіксованого розміру в `batched_records()`.
2. **`itertools.groupby`** — групування відсортованих записів за дисципліною (`group_by_discipline`) та за ID студента (`group_by_student`).
3. **`itertools.pairwise`** — аналіз різниць між сусідніми оцінками у потоці (`analyze_grade_trends`).
4. **`itertools.accumulate`** — обчислення накопичувальної суми балів (`analyze_grade_trends`).
5. **`itertools.chain`** — об'єднання потоків рядків із декількох CSV-файлів у `read_multiple_files()`.
6. **`itertools.count`** — генерація нескінченної послідовності номерів записів у `infinite_grade_stream()`.

---

## 5. Схема та реалізація потокового конвеєра (Lazy Pipeline)

### 5.1. Архітектурна схема конвеєра

```text
Input CSV File (100 000+ records)
    ↓
read_lines(path)                  [Streaming Reader: yield from file]
    ↓
clean_lines(lines)                [Cleaning Stage: strip() & skip empty]
    ↓
parse_csv_rows(cleaned)           [Parser Stage: csv.DictReader + yield from]
    ↓
validate_grades(rows)             [Validation Stage: int/float checks, 0 <= grade <= 100]
    ↓
normalize_records(valid)          [Transformation Stage: .title(), round(grade, 2)]
    ↓
filter_by_discipline(normalized)  [Filtering Stage 1: discipline match]
    ↓
filter_by_grade_threshold(...)    [Filtering Stage 2: min_grade <= grade <= max_grade]
    ↓
Batching / Aggregation / Rating   [Sink Stage: avg, min/max, top-N, groupby, CSV export]
```

### 5.2. Код основних етапів конвеєра

#### Модуль читання та очищення (`src/stream_processor/readers.py`)
```python
def read_lines(path: Path) -> Iterator[str]:
    """Потокове читання рядків із файлу за допомогою yield from."""
    with path.open("r", encoding="utf-8") as file:
        yield from file

def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    """Очищення потоку рядків від пробільних символів та порожніх рядків."""
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            yield cleaned
```

#### Модуль парсингу та потокової валідації (`src/stream_processor/parsers.py`)
```python
def parse_csv_rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """Парсинг CSV-рядків у словники через csv.DictReader та yield from."""
    reader = csv.DictReader(lines)
    yield from reader

def validate_grades(
    rows: Iterable[dict[str, str]],
    stats_out: dict[str, int] | None = None,
) -> Iterator[GradeRecord]:
    """Потокова валідація оцінок студентів (діапазон [0, 100], непорожні поля, додатний ID)."""
    for row in rows:
        try:
            student_id = int(row["student_id"])
            name = row["name"].strip()
            discipline = row["discipline"].strip()
            grade = float(row["grade"])
        except (ValueError, TypeError, KeyError):
            if stats_out is not None:
                stats_out["invalid"] = stats_out.get("invalid", 0) + 1
            continue

        if student_id <= 0 or not name or not discipline or not (0.0 <= grade <= 100.0):
            if stats_out is not None:
                stats_out["invalid"] = stats_out.get("invalid", 0) + 1
            continue

        if stats_out is not None:
            stats_out["valid"] = stats_out.get("valid", 0) + 1

        yield GradeRecord(
            student_id=student_id,
            name=name,
            discipline=discipline,
            grade=grade,
        )
```

#### Модуль фільтрації, трансформації та пакетної обробки (`src/stream_processor/filters.py`)
```python
def filter_by_discipline(
    records: Iterable[GradeRecord],
    discipline: str | None = None,
) -> Iterator[GradeRecord]:
    if not discipline:
        yield from records
        return
    target = discipline.strip().lower()
    for record in records:
        if record.discipline.lower() == target:
            yield record

def normalize_records(records: Iterable[GradeRecord]) -> Iterator[GradeRecord]:
    for record in records:
        yield GradeRecord(
            student_id=record.student_id,
            name=record.name.strip().title(),
            discipline=record.discipline.strip().title(),
            grade=round(record.grade, 2),
        )

def batched_records(
    records: Iterable[GradeRecord],
    batch_size: int,
) -> Iterator[list[GradeRecord]]:
    iterator = iter(records)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            return
        yield batch
```

#### Модуль аналітики та агрегації (`src/stream_processor/analytics.py`)
```python
def streaming_average_grade(records: Iterable[GradeRecord]) -> float:
    total = 0.0
    count = 0
    for record in records:
        total += record.grade
        count += 1
    return total / count if count > 0 else 0.0

def streaming_min_max_grade(
    records: Iterable[GradeRecord],
) -> tuple[GradeRecord | None, GradeRecord | None]:
    min_record: GradeRecord | None = None
    max_record: GradeRecord | None = None
    for record in records:
        if min_record is None or record.grade < min_record.grade:
            min_record = record
        if max_record is None or record.grade > max_record.grade:
            max_record = record
    return min_record, max_record

def lazy_students_above_average(
    records: Iterable[GradeRecord],
    threshold: float,
) -> Iterator[StudentStats]:
    totals: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)
    names: dict[int, str] = {}
    for record in records:
        sid = record.student_id
        totals[sid] += record.grade
        counts[sid] += 1
        names[sid] = record.name

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
```

#### Збірка конвеєра (`src/stream_processor/pipeline.py`)
```python
def build_pipeline(
    path: Path,
    discipline: str | None = None,
    min_grade: float = 0.0,
    max_grade: float = 100.0,
    validation_stats: dict[str, int] | None = None,
) -> Iterator[GradeRecord]:
    lines = read_lines(path)
    cleaned = clean_lines(lines)
    rows = parse_csv_rows(cleaned)
    valid = validate_grades(rows, stats_out=validation_stats)
    normalized = normalize_records(valid)
    by_discipline = filter_by_discipline(normalized, discipline)
    filtered = filter_by_grade_threshold(by_discipline, min_grade, max_grade)
    return filtered
```

---

## 6. Експериментальна частина: порівняння Eager та Lazy обробки

### 6.1. Таблиця результатів експерименту (10 000, 100 000 та 500 000 записів)

Вимірювання виконано за допомогою `time.perf_counter()` та `tracemalloc.get_traced_memory()` на реальних CSV-файлах:

| Records | Eager time (s) | Lazy time (s) | Eager peak memory (KB) | Lazy peak memory (KB) | Eager TTFR (ms) | Lazy TTFR (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **10 000** | 0.2306 | 0.2372 | 7 127.93 (~7.0 МБ) | **52.61 (~0.05 МБ)** | 34.230 | **0.557** |
| **100 000** | 2.2990 | 2.1992 | 71 830.00 (~70.1 МБ) | **52.82 (~0.05 МБ)** | 388.624 | **0.383** |
| **500 000** | 10.6976 | 10.0076 | 359 758.45 (~351.3 МБ) | **52.85 (~0.05 МБ)** | 1 770.714 | **0.467** |

### 6.2. Дослідження Early Termination (пошук першого запису з оцінкою `>= 99.0` у 100 000 записах)

| Показник | Eager підхід (повна матеріалізація списку) | Lazy підхід (`find_first_record` на генераторі) | Виграш Lazy |
| :--- | :---: | :---: | :---: |
| **Час пошуку** | 1 998.379 мс | **0.464 мс** | **у 4 307 разів швидше** |
| **Пікова пам'ять** | 62 126.98 КБ | **36.46 КБ** | **у 1 704 рази менше пам'яті** |

### 6.3. Аналіз результатів експерименту

1. **Пікове споживання пам'яті (`Peak Memory`):**
   - У жадібному (`Eager`) підході споживання пам'яті зростає **лінійно $O(N)$** разом із розміром файлу: від `7.1 МБ` для 10 000 записів до `359.8 МБ` для 500 000 записів, оскільки створюються великі проміжні списки рядків, словників та об'єктів `GradeRecord`.
   - У лінивому (`Lazy`) потоковому конвеєрі пікове споживання пам'яті є **константним $O(1)$** і становить лише **`~52.8 КБ`** незалежно від того, обробляється 10 000 чи 500 000 записів (у 6 800 разів менше на 500 000 записах).
2. **Загальний час повного проходу (`Total Elapsed Time`):**
   - При повному проході всього датасету загальний час виконання `Eager` і `Lazy` є близьким (`2.30 с` проти `2.20 с` на 100 000 записах; `10.70 с` проти `10.01 с` на 500 000 записах). Це підтверджує важливе правило: **генератор не обов'язково радикально швидший при повному обході всього набору**, адже кількість операцій парсингу й валідації однакова, проте на великих обсягах `Lazy` трохи виграє завдяки відсутності витрат на алокацію та перевиділення гігантських списків і роботу збирача сміття.
3. **Час до першого результату (`Time to First Result — TTFR`) та `Early Termination`:**
   - У `Lazy` конвеєрі перший відфільтрований елемент доступний вже через **`0.38–0.55 мс`** незалежно від розміру файлу, тоді як `Eager` змушений спочатку прочитати й обробити весь файл (`1 770.7 мс` для 500 000 записів).
4. **Переваги та недоліки Lazy Evaluation:**
   - *Переваги:* мінімальне споживання RAM $O(1)$, миттєвий час отримання першого результату, підтримка дострокового завершення (`early termination`), можливість роботи з нескінченними потоками.
   - *Недоліки:* ітератори є одноразовими (`one-shot`), не підтримують індексацію `stream[i]` та `len()`, утримують файловий дескриптор відкритим до завершення або закриття генератора, а винятки виникають відкладено під час споживання.

---

## 7. Відповіді на контрольні запитання

1. **Що таке iterable?** — Об'єкт, здатний повертати свої елементи по одному, який реалізує метод `__iter__()` (або `__getitem__()`), з якого функція `iter()` може отримати `iterator`.
2. **Що таке iterator?** — Об'єкт потокового обходу з внутрішнім станом, який реалізує методи `__iter__()` (повертає `self`) та `__next__()` (повертає наступний елемент або піднімає `StopIteration`).
3. **Чим iterable відрізняється від iterator?** — `Iterable` є контейнером або джерелом даних, по якому можна ітеруватися багато разів, а `Iterator` представляє конкретний одноразовий стан обходу.
4. **Для чого використовується `iter()`?** — Для отримання об'єкта-ітератора з `iterable` шляхом виклику його методу `__iter__()`.
5. **Для чого використовується `next()`?** — Для отримання чергового елемента з ітератора шляхом виклику його методу `__next__()` (із можливістю вказати значення за замовчуванням при `StopIteration`).
6. **Що робить `__iter__()`?** — В `Iterable` створює і повертає новий об'єкт-ітератор; в `Iterator` повертає сам об'єкт `self`.
7. **Що робить `__next__()`?** — Повертає наступний елемент послідовності, просуває внутрішній стан ітератора вперед, а якщо елементи закінчилися — генерує виняток `StopIteration`.
8. **Що таке `StopIteration`?** — Вбудований сигнальний виняток Python, який повідомляє цикл `for` або іншого споживача ітератора про завершення послідовності.
9. **Як цикл `for` використовує iterator protocol?** — Спочатку викликає `iterator = iter(iterable)`, а потім у нескінченному циклі викликає `next(iterator)`, перехоплюючи `StopIteration` для штатного виходу з циклу.
10. **Чому iterator часто називають one-shot object?** — Тому що після досягнення кінця послідовності і підняття `StopIteration` його внутрішній стан не скидається, і всі наступні виклики `next()` знову піднімають `StopIteration`.
11. **Чому `iter(iterator) is iterator`?** — Щоб ітератор можна було напряму передавати у цикл `for` та функції, які очікують `iterable` (вони викликають `iter()` і отримують той самий ітератор).
12. **Чи можна повторно використати exhausted generator?** — Ні, вичерпаний генератор повертатиме порожній результат (`list(gen) == []`). Для повторного проходу потрібно викликати генераторну функцію заново.
13. **Що таке generator function?** — Функція, яка містить одне або більше ключових слів `yield` і при виклику повертає об'єкт-генератор (`generator iterator`).
14. **Яку роль виконує `yield`?** — Видає поточне значення споживачу і призупиняє виконання функції зі збереженням її локального стану до наступного виклику `next()`.
15. **Чим `yield` відрізняється від `return`?** — `return` остаточно завершує виконання функції (у генераторі викликає `StopIteration`), тоді як `yield` лише тимчасово призупиняє функцію з можливістю продовження з того самого місця.
16. **Коли фактично починає виконуватися generator function?** — Лише при першому виклику `next()` на створеному об'єкті-генераторі, а не в момент виклику самої функції.
17. **Що зберігає generator між викликами `next()`?** — Стек виклику фрейму (`frame`), значення всіх локальних змінних та вказівник поточної інструкції байткоду (`instruction pointer`).
18. **Що таке generator expression?** — Компактний синтаксис у круглих дужках `(expr for x in iterable if cond)`, який створює об'єкт-генератор без попереднього формування списку.
19. **Чим generator expression відрізняється від list comprehension?** — `List comprehension` `[...]` одразу обчислює всі елементи і зберігає їх у списку в пам'яті (`eager`), а `generator expression` `(...)` обчислює елементи по одному за запитом (`lazy`).
20. **Що таке lazy evaluation?** — Стратегія обчислень, за якої значення обчислюються лише в той момент, коли вони реально потрібні споживачу.
21. **Що таке eager evaluation?** — Стратегія обчислень, за якої вся колекція результатів обчислюється та матеріалізується в пам'яті одразу при виклику операції.
22. **Які переваги lazy evaluation?** — Постійне низьке споживання оперативної пам'яті $O(1)$, малий час до отримання першого результату, ефективна підтримка дострокової зупинки (`early termination`) та можливість роботи з нескінченними послідовностями.
23. **Які недоліки lazy evaluation?** — Одноразовість проходу (`one-shot`), неможливість прямого індексування та визначення довжини через `len()`, складніше налагодження через відкладене виникнення винятків та необхідність контролювати час життя відкритих ресурсів.
24. **Що таке streaming?** — Потокова обробка даних невеликими порціями (по одному рядку або пакету) без завантаження всього набору даних у RAM.
25. **Чому streaming важливий для великих files?** — Він дозволяє обробляти файли розміром у десятки гігабайтів на машині з обмеженим обсягом оперативної пам'яті, уникаючи `MemoryError`.
26. **Чому `read()` може бути проблемою для multi-GB file?** — Виклик `file.read()` завантажує весь вміст файлу в один рядок у RAM, що призводить до вичерпання пам'яті та аварійного завершення програми або активного свопінгу ОС.
27. **Чому file object є iterable?** — Текстовий файловий об'єкт у Python реалізує методи `__iter__()` та `__next__()`, читаючи файл буферизовано рядок за рядком.
28. **Для чого використовується `yield from`?** — Для делегування генерації елементів іншому вкладеному ітератору або генератору без написання явного циклу `for item in subiterable: yield item`.
29. **Що таке `itertools`?** — Модуль стандартної бібліотеки Python, що містить швидкі, реалізовані мовою C компонувальні блоки-ітератори для побудови потокових конвеєрів.
30. **Для чого `itertools.count()`?** — Створює нескінченний ітератор арифметичної прогресії чисел `start, start + step, start + 2*step, ...`.
31. **Чому `count()` потрібно обмежувати?** — Оскільки він нескінченний, спроба матеріалізувати його без умови виходу або `islice` призведе до нескінченного циклу та вичерпання пам'яті.
32. **Для чого `islice()`?** — Для отримання зрізу (перших $N$ або діапазону `start:stop:step`) з будь-якого ітератора без матеріалізації попередніх чи наступних елементів.
33. **Для чого `chain()`?** — Для послідовного об'єднання декількох `iterables` в один неперервний лінивий потік без створення спільного списку.
34. **Як працює `takewhile()`?** — Повертає елементи з ітератора доти, доки предикат повертає `True`; як тільки умова вперше стає `False`, ітерація негайно припиняється.
35. **Як працює `dropwhile()`?** — Пропускає початкові елементи ітератора, доки предикат повертає `True`, а після першого `False` видає всі решту елементів без перевірки умови.
36. **Для чого `accumulate()`?** — Повертає ітератор накопичувальних сум (або результатів іншої бінарної функції, наприклад `max`, `mul`) префіксів послідовності.
37. **Для чого `pairwise()`?** — Повертає послідовні перекривні пари сусідніх елементів `(s0, s1), (s1, s2), (s2, s3), ...`, що зручно для аналізу трендів і різниць.
38. **Як працює `groupby()`?** — Групує **сусідні** послідовні елементи ітератора, які мають однакове значення ключової функції `key`, повертаючи пари `(key, group_iterator)`.
39. **Чому перед `groupby()` часто потрібне sorting?** — Тому що `groupby()` об'єднує лише підряд розташовані елементи з однаковим ключем; якщо однакові ключі розкидані по потоку, без попереднього сортування утвориться кілька окремих груп для одного ключа.
40. **Що робить `product()`?** — Обчислює декартовий добуток вхідних ітерованих об'єктів (еквівалент вкладених циклів `for`).
41. **Чим `combinations()` відрізняється від `permutations()`?** — У `combinations()` порядок елементів у вибірці не має значення (комбінації без повторень), а у `permutations()` порядок має значення (розміщення/перестановки).
42. **Чому combinatorial iterators можуть бути небезпечними навіть при lazy execution?** — Кількість комбінацій або перестановок зростає факторіально чи експоненційно ($n!$), тому повний перебір навіть без витрат пам'яті може тривати неприйнятно довго.
43. **Що таке batching?** — Розбиття потоку окремих записів на невеликі пакети фіксованого розміру (наприклад, по `1 000` записів) для групової обробки.
44. **Які переваги batching?** — Дозволяє виконувати bulk-вставки в БД, пакетні мережеві запити до API або буферизований запис у файл, зберігаючи при цьому контрольоване споживання пам'яті (у RAM лише один поточний батч).
45. **Що таке lazy pipeline?** — Ланцюжок генераторів, де вихід одного генератора є входом для наступного, і кожен елемент проходить усі стадії обробки поштучно за запитом фінального споживача.
46. **Які stages може містити pipeline?** — Source (читання джерела), Cleaning (очищення), Parsing (парсинг), Validation (валідація), Filtering (фільтрація), Transformation (нормалізація/мапінг), Batching/Aggregation (Sink).
47. **Що є source у streaming pipeline?** — Початкове джерело даних, яке створює потік (наприклад, генератор читання файлу `read_lines(path)`, мережевий сокет або курсор БД).
48. **Що є transformation?** — Проміжний етап конвеєра, який приймає потік елементів, змінює їхню форму чи значення (наприклад, нормалізує регістр тексту або округлює оцінку) і видає трансформовані елементи через `yield`.
49. **Що є sink?** — Кінцевий споживач конвеєра, який ініціює рух даних по pipeline (наприклад, агрегація `sum()`, `streaming_average_grade()`, збереження у файл або виведення на екран).
50. **Чи гарантує generator менший total execution time?** — Ні. При повному проході всього набору даних сумарний час виконання може бути близьким до `eager` (або інколи трохи більшим через накладні витрати на перемикання контексту генераторів).
51. **Яка основна memory advantage generator?** — У пам'яті одночасно зберігається лише один поточний елемент (або один батч), тому пікове споживання пам'яті $O(1)$ не залежить від загального розміру датасету.
52. **Що таке time to first result?** — Час від моменту запуску обробки до отримання першого готового елемента на виході конвеєра.
53. **Чому lazy pipeline добре підтримує early termination?** — Як тільки знайдено потрібний елемент (або набрано $N$ елементів через `islice`), споживач припиняє викликати `next()`, і решта файлу навіть не читається і не парситься.
54. **Чому exception у generator може виникати із затримкою?** — Тіло генератора не виконується при його створенні; помилка (наприклад, `ValueError` на 50-му рядку) виникне лише тоді, коли споживач дійде до цього елемента викликами `next()`.
55. **Чому `list(generator)` може бути проблемою?** — Виклик `list()` примусово матеріалізує всі елементи генератора в оперативній пам'яті, повністю нівелюючи перевагу лінивої обробки для великих даних.
56. **Що трапиться при `list(count())`?** — Програма зависне у нескінченному циклі виділення пам'яті під список, доки не завершиться аварійно з `MemoryError`.
57. **Як generator може впливати на lifecycle file resource?** — Якщо генератор відкриває файл через `with open(...)` і споживач припиняє читання достроково, блок `with` залишається незавершеним, доки об'єкт генератора не буде закритий методом `.close()` або знищений збирачем сміття.
58. **Як тестувати невеликий generator?** — Перетворити його вихід на список через `list(gen)` на малому тестовому наборі або перевіряти послідовні значення через `next(gen)` та `assertRaises(StopIteration)`.
59. **Як тестувати infinite generator?** — Обмежити кількість елементів за допомогою `list(itertools.islice(infinite_gen, k))` і перевірити отриманий скінченний зріз.
60. **Коли краще використовувати `list`, а коли `generator`?** — `list` варто використовувати для невеликих колекцій, коли потрібні багаторазовий обхід, індексація `items[i]`, сортування на місці або відома довжина `len()`; `generator` — для великих файлів, потокових конвеєрів, нескінченних послідовностей та задач із можливістю дострокової зупинки.

---

## 8. Висновок

У ході виконання лабораторної роботи №3 було розроблено потоковий конвеєр обробки даних системи оцінювання студентів (Варіант №7) на основі ітераційної моделі Python та принципу `lazy evaluation`. Реалізовано власні класи `Iterable` (`GradeArchive`) та `Iterator` (`GradeRangeIterator`), генераторні функції з `yield` та `yield from`, генераторні вирази, засоби модуля `itertools` (`islice`, `groupby`, `pairwise`, `accumulate`, `chain`, `count`), пакетну обробку (`batching`) і потокову агрегацію на наборі зі 100 000 записів. Експериментальне порівняння `Eager` та `Lazy` підходів на вибірках у 10 000, 100 000 та 500 000 записів довело, що лінивий конвеєр зберігає константне пікове споживання пам'яті (`~52.8 КБ` проти `359.8 МБ` у жадібного підходу на 500 000 записах) і скорочує час отримання першого результату та пошуку з достроковим завершенням у тисячі разів.
