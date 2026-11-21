# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №4

**Дисципліна:** «Професійний Python»  
**Тема:** Професійне ООП та система типів Python  
**Варіант:** №7 — Система оцінювання студентів (`grade_system`)  
**Виконав:** студент Назар Поцелуйко  

---

## 1. Мета роботи

Сформувати практичні навички побудови професійної об'єктно-орієнтованої моделі в Python із використанням класів, композиції, наслідування, абстрактних базових класів (`ABC`), протоколів (`Protocol`), `dataclass`, `properties`, `dunder`-методів, принципів **SOLID** та сучасної системи анотацій типів (`TypeVar`, `Generic`, `TypedDict`) із перевіркою статичним аналізатором типів (`mypy`).

---

## 2. Постановка задачі (Варіант 7 — Система оцінювання студентів)

**Обов'язкові доменні об'єкти варіанта:**
* `Student` (базовий клас студента) та його спеціалізовані підкласи `StateFundedStudent` (бюджетник) і `ContractStudent` (контрактник);
* `Discipline` (навчальна дисципліна з кількістю кредитів ECTS);
* `Grade` (незмінний об'єкт-значення оцінки у 100-бальній шкалі та ECTS);
* `AssessmentRecord` (запис про оцінювання студента з дисципліни);
* `GradeBook` (журнал оцінок потоку/групи).

**Необхідно реалізувати:**
1. Додавання та оновлення оцінок студентів із дисциплін.
2. Обчислення середнього, середньозваженого, мінімального і максимального бала.
3. Визначення рівня академічної успішності (`PerformanceLevel`).
4. Сортування студентів за середнім/рейтинговим балом.
5. Пошук студентів із середнім балом вище заданого порога.
6. Узагальнений репозиторій (`InMemoryRepository[T]` із `Generic[T]` та `TypeVar`).
7. Абстракції політики оцінювання (`PerformanceEvaluationPolicy` через `ABC`), звітності (`GradeReportFormatter` через `Protocol`) та сповіщень (`NotificationSender` через `Protocol`).
8. Сервісний шар (`GradeBookService`) із впровадженням залежностей (`Dependency Injection`) та імпортом зовнішніх даних через `TypedDict` (`StudentPayload`, `AssessmentPayload`).
9. Статичну перевірку типів через `mypy --strict` та аналіз навмисно внесених помилок типізації.

---

## 3. Опис предметної області та список Domain Entities

| Сутність / Клас | Модуль | Роль в архітектурі |
| :--- | :--- | :--- |
| `Grade` | `value_objects.py` | Immutable Value Object (`@dataclass(frozen=True, slots=True)`), оцінка `0..100`, буква ECTS, `__lt__`, `__add__` |
| `PerformanceLevel` | `value_objects.py` | Перелік (`Enum`) рівнів успішності (`Відмінно (A)`, `Добре (B/C)`, `Задовільно (D/E)`, `Незадовільно (FX/F)`) |
| `Discipline` | `models.py` | Domain Entity (`@dataclass(slots=True)`), навчальна дисципліна з `@property credits` |
| `AssessmentRecord` | `models.py` | Domain Entity (`@dataclass(slots=True)`), композиція `Discipline` + `Grade`, обчислення `weighted_points` |
| `Student` | `models.py` | Базова Domain Entity студента з інкапсульованим списком `_records`, властивостями статистики та dunder-методами |
| `StateFundedStudent` | `models.py` | Підклас `Student` для бюджетної форми навчання (розрахунок стипендії `scholarship_amount`) |
| `ContractStudent` | `models.py` | Підклас `Student` для контрактної форми навчання (перевірка умови переведення на бюджет) |
| `GradeBook` | `models.py` | Контейнерна Domain Entity журналу оцінок із композицією `PerformanceEvaluationPolicy` |
| `PerformanceEvaluationPolicy` | `models.py` | Абстрактний базовий клас (`ABC`) стратегії розрахунку рейтингу (`StandardAveragePolicy`, `CreditWeightedPolicy`) |
| `HasId`, `Serializable`, `GradeReportFormatter`, `NotificationSender` | `protocols.py` | Структурні інтерфейси (`Protocol`, `@runtime_checkable`) |
| `InMemoryRepository[T]` | `repositories.py` | Узагальнене сховище (`Generic[T]`, `TypeVar("T", bound=HasId)`) |
| `StudentPayload`, `AssessmentPayload` | `dto.py` | `TypedDict` для типізації зовнішніх JSON-подібних словників |
| `GradeBookService` | `services.py` | Application Service із Dependency Injection |

---

## 4. Діаграма класів (Class Diagram)

```text
                 PerformanceEvaluationPolicy (ABC)
                                ▲
                 ┌──────────────┴──────────────┐
                 │                             │
      StandardAveragePolicy          CreditWeightedPolicy

                         Student
                            ▲
             ┌──────────────┴──────────────┐
             │                             │
     StateFundedStudent             ContractStudent

  Discipline ◄──── AssessmentRecord ────► Grade (frozen Value Object)
                          ▲
                          │ (composition: _records)
                       Student
                          ▲
                          │ (aggregation: _students)
                      GradeBook ────────► PerformanceEvaluationPolicy (ABC)

  GradeBookService (Application Service)
     ├── InMemoryRepository[Student]      (Generic[T])
     ├── InMemoryRepository[Discipline]   (Generic[T])
     ├── PerformanceEvaluationPolicy      (ABC)
     ├── GradeReportFormatter             (Protocol)
     └── NotificationSender               (Protocol)
```

---

## 5. Реалізація вимог ООП та системи типів (із прикладами коду)

### 5.1. Immutable Value Object (`@dataclass(frozen=True, slots=True)`) та арифметичні/порівняльні dunder-методи
Файл `src/grade_system/value_objects.py`:
```python
@total_ordering
@dataclass(frozen=True, slots=True)
class Grade:
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            raise ValueError(
                f"Оцінка повинна бути в діапазоні від 0 до 100, отримано: {self.value}"
            )

    @property
    def ects_letter(self) -> str:
        if self.value >= 90.0:
            return "A"
        if self.value >= 82.0:
            return "B"
        if self.value >= 74.0:
            return "C"
        if self.value >= 64.0:
            return "D"
        if self.value >= 60.0:
            return "E"
        if self.value >= 35.0:
            return "FX"
        return "F"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value < other.value

    def __add__(self, other: Grade) -> float:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value + other.value
```

### 5.2. Інкапсуляція та Properties
У класі `Discipline` кількість кредитів ECTS захищена через `@property` та `@credits.setter`, а у класі `Student` внутрішній список `_records` не відкривається для прямої модифікації — властивість `records` повертає незмінний кортеж `tuple[AssessmentRecord, ...]`:
```python
@dataclass(slots=True)
class Discipline:
    id: int
    name: str
    _credits: int

    @property
    def credits(self) -> int:
        return self._credits

    @credits.setter
    def credits(self, value: int) -> None:
        self._validate_credits(value)
        self._credits = value
```

### 5.3. Наслідування (`Inheritance`) та `super()`
Підкласи `StateFundedStudent` і `ContractStudent` розширюють `Student` (відношення `is-a`), викликають `super().__init__()` та поліморфно перевизначають метод `academic_status_note()`:
```python
class StateFundedStudent(Student):
    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
        base_scholarship: float = 2000.0,
    ) -> None:
        super().__init__(student_id, full_name, group, email)
        self.base_scholarship = base_scholarship

    @property
    def scholarship_amount(self) -> float:
        if not self._records or self.has_academic_debt:
            return 0.0
        if self.average_score >= 90.0:
            return round(self.base_scholarship * 1.455, 2)
        if self.average_score >= 75.0:
            return self.base_scholarship
        return 0.0
```

### 5.4. Композиція (`Composition`), `ABC` та `Protocol`
* **Абстрактний базовий клас (`ABC`):** `PerformanceEvaluationPolicy` задає контракт для `StandardAveragePolicy` та `CreditWeightedPolicy`.
* **Структурні протоколи (`Protocol`):** `GradeReportFormatter`, `NotificationSender`, `HasId` та `@runtime_checkable Serializable` визначають поведінкові інтерфейси без жорсткого зв'язування класів-реалізацій (`MarkdownReportFormatter`, `ConsoleNotificationSender`).

### 5.5. Dunder-методи
Реалізовано 7 спеціальних методів Python:
* `__post_init__` — валідація `Grade` та `Discipline`;
* `__str__` і `__repr__` — форматований текстовий та налагоджувальний вивід;
* `__len__` — кількість оцінок у `Student` та кількість студентів у `GradeBook` / `InMemoryRepository`;
* `__iter__` — ітерація по записах студента або по студентах журналу;
* `__contains__` — перевірка `discipline_id in student` та `student_id in grade_book`;
* `__getitem__` — доступ до студента за ID `grade_book[101]`;
* `__lt__` та `__add__` — порівняння та додавання об'єктів `Grade`.

### 5.6. Generic Repository, `TypeVar` та `TypedDict`
* `T = TypeVar("T", bound=HasId)` та `class InMemoryRepository(Generic[T])` забезпечують типобезпечне зберігання як `Student`, так і `Discipline`.
* `NumericScore = TypeVar("NumericScore", int, float)` демонструє `constrained TypeVar` у функції `scale_score()`.
* `StudentPayload` та `AssessmentPayload` (`TypedDict`) відокремлюють сирі зовнішні словники від доменних об'єктів.

---

## 6. Застосування принципів SOLID та Dependency Injection (Експериментальна частина)

1. **Single Responsibility Principle (SRP):** кожен клас має одну чітку зону відповідальності (`Grade` — валідація оцінки та переведення в ECTS; `Student` — облік оцінок студента; `GradeBook` — ранжування та групова статистика; `MarkdownReportFormatter` — побудова звіту; `ConsoleNotificationSender` — відправка повідомлень; `GradeBookService` — координація сценаріїв).
2. **Open/Closed Principle (OCP):** система відкрита для розширення новими правилами рейтингу чи новими форматами звітів без зміни коду `GradeBookService`.
3. **Liskov Substitution Principle (LSP):** підкласи `StateFundedStudent` та `ContractStudent` коректно працюють у будь-якому місці, де очікується `Student`.
4. **Interface Segregation Principle (ISP):** інтерфейси розділені на атомарні протоколи `HasId`, `Serializable`, `GradeReportFormatter`, `NotificationSender`.
5. **Dependency Inversion Principle (DIP) та Dependency Injection:**
   * **Варіант А (жорстка залежність всередині сервісу):** якби `GradeBookService` сам створював `self._notifier = ConsoleNotificationSender()` у `__init__`, його неможливо було б протестувати без виводу в консоль або замінити на Email/Telegram-сповіщувач без редагування коду сервісу.
   * **Варіант Б (Dependency Injection, реалізований у роботі):** усі залежності (`student_repo`, `discipline_repo`, `evaluation_policy`, `report_formatter`, `notifier`) передаються ззовні через конструктор як абстракції (`ABC` / `Protocol`), що знижує зв'язність (`coupling`) і підвищує тестованість (`testability`).

---

## 7. Результат виконання програми та перевірки типів (`mypy`)

### 7.1. Вивід демонстраційного сценарію (`python -m grade_system.main`)
```text
============================================================================================
ЛАБОРАТОРНА РОБОТА №4 — ВАРІАНТ 7: СИСТЕМА ОЦІНЮВАННЯ СТУДЕНТІВ
============================================================================================

--- 1. Додавання нових оцінок та автоматичне сповіщення ---
[СПОВІЩЕННЯ -> anna.kovalenko@university.edu.ua] Тема: Нова оцінка з дисципліни «Дискретна математика» | Виставлено 98.0 (A) (Екзамен). Поточний середній бал: 94.50.
[СПОВІЩЕННЯ -> bohdan.melnyk@university.edu.ua] Тема: Нова оцінка з дисципліни «Дискретна математика» | Виставлено 89.0 (B) (Екзамен). Поточний середній бал: 84.75.
[СПОВІЩЕННЯ -> daryna.shevchenko@university.edu.ua] Тема: Нова оцінка з дисципліни «Дискретна математика» | Виставлено 91.0 (A) (Екзамен). Поточний середній бал: 93.00.

--- 2. Перевірка dunder-методів та контейнерної поведінки ---
Кількість студентів у журналі (len(grade_book)): 5
Чи є студент ID=101 у журналі (101 in grade_book): True
Кількість оцінок у Коваленко Анна Ігорівна (len(student)): 4
Чи складена дисципліна ID=4 у студента 101 (4 in student): True
Порівняння об'єктів Grade(98) > Grade(89): True
Сума двох оцінок Grade(98) + Grade(89): 187.0
Перевірка isinstance(anna, Serializable): True
Масштабування бала (constrained TypeVar): 99.75

--- 3. Статистика успішності за студентами ---
• Коваленко Анна Ігорівна: середній = 94.50, зважений = 94.50, мін = 91.0, макс = 98.0 | Успішність: Відмінно (A)
• Мельник Богдан Сергійович: середній = 84.75, зважений = 84.33, мін = 78.0, макс = 89.0 | Успішність: Добре (B/C)
• Шевченко Дарина Олександрівна: середній = 93.00, зважений = 93.06, мін = 91.0, макс = 95.0 | Успішність: Відмінно (A)
• Ткаченко Дмитро Васильович: середній = 67.00, зважений = 66.64, мін = 61.0, макс = 72.0 | Успішність: Задовільно (D/E)
• Бондаренко Ілля Петрович: середній = 60.00, зважений = 59.79, мін = 52.0, макс = 65.0 | Успішність: Незадовільно (FX/F)

Загальна статистика по журналу -> Середній бал: 81.67 | Мінімальний: 52.0 | Максимальний: 98.0

--- 4. Рейтингова відомість (сортування за спаданням середнього бала) ---
=== ВІДОМІСТЬ УСПІШНОСТІ: Осінній семестр 2026/2027 (Потік КН) ===
№   | ПІБ студента             | Група   | Сер. бал | Зваж.    | Статус
--------------------------------------------------------------------------------------------
1   | Коваленко Анна Ігорівна  | КН-21   | 94.50    | 94.50    | Бюджетна форма | Відмінно (A) | Стипендія: 2910.00 UAH
2   | Шевченко Дарина Олександрівна | КН-22   | 93.00    | 93.06    | Контрактна форма | Відмінно (A) | Рекомендовано до переведення на бюджет
3   | Мельник Богдан Сергійович | КН-21   | 84.75    | 84.33    | Бюджетна форма | Добре (B/C) | Стипендія: 2000.00 UAH
4   | Ткаченко Дмитро Васильович | КН-22   | 67.00    | 66.64    | Контрактна форма | Задовільно (D/E) | Контракт (38000 UAH/рік)
5   | Бондаренко Ілля Петрович | КН-21   | 60.00    | 59.79    | Бюджетна форма | Незадовільно (FX/F) | Без стипендії
```

### 7.2. Обов'язковий експеримент із `mypy` (виявлення та виправлення type errors)
Навмисно внесено 3 помилки типізації:
1. `student_id: int = "101"` → `error: Incompatible types in assignment (expression has type "str", variable has type "int") [assignment]`
2. `def total_credits() -> int: return "18"` → `error: Incompatible return value type (got "str", expected "int") [return-value]`
3. Додавання `Discipline` у `InMemoryRepository[Student]` → `error: Argument 1 to "add" of "InMemoryRepository" has incompatible type "Discipline"; expected "Student" [arg-type]`

Результат після виправлення (`python -m mypy src tests` з `strict = true`):
```text
Success: no issues found in 9 source files
```

---

## 8. Висновок

Під час виконання лабораторної роботи №4 за індивідуальним варіантом №7 розроблено професійну об'єктно-орієнтовану модель системи оцінювання студентів. У роботі поєднано доменні класи, `dataclass`, незмінні об'єкти-значення (`frozen=True, slots=True`), контроль стану через `properties`, ієрархію наслідування форм навчання (`Student` → `StateFundedStudent`, `ContractStudent`), композицію, абстрактні базові класи (`ABC`), структурні протоколи (`Protocol`), спеціальні `dunder`-методи, принципи **SOLID** та **Dependency Injection**. Статична типізація з `Generic[T]`, `TypeVar`, `TypedDict` та перевіркою `mypy --strict` дозволила гарантувати типобезпечність усіх компонентів системи.
