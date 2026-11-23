# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №4

**Дисципліна:** «Професійний Python»  
**Тема:** Професійне ООП та система типів Python  
**Варіант:** №7 — Система оцінювання студентів (`grade_system`)  
**Виконав:** студент Назар Поцелуйко  

---

## 1. Мета роботи

Сформувати практичні навички побудови професійної об'єктно-орієнтованої моделі в Python із використанням класів, композиції (`composition`), наслідування (`inheritance`), абстрактних базових класів (`ABC`), структурних протоколів (`Protocol`), `dataclass`, контрольованих властивостей (`properties`), спеціальних `dunder`-методів, принципів **SOLID**, впровадження залежностей (`Dependency Injection`) та сучасної системи анотацій типів (`TypeVar`, `Generic`, `TypedDict`) із перевіркою кодової бази статичним аналізатором типів (`mypy`).

---

## 2. Індивідуальне завдання (Варіант №7)

**Постановка задачі (Варіант №7 — Система оцінювання студентів)**

Проєкт продовжує предметну область обліку та аналізу успішності студентів із Лабораторної роботи №3 (Варіант №7) і переводить її з потоково-функціональної організації у повноцінну типізовану об'єктно-орієнтовану архітектуру.

**Основні доменні об'єкти варіанта (Domain objects):**
- `Student` (базова сутність студента) та спеціалізовані підкласи `StateFundedStudent` (бюджетна форма навчання) і `ContractStudent` (контрактна форма навчання);
- `Discipline` (навчальна дисципліна з ідентифікатором, назвою та кількістю кредитів ECTS);
- `Grade` (незмінний об'єкт-значення оцінки у 100-бальній шкалі з конвертацією у шкалу ECTS `A`–`F` та рівень успішності `PerformanceLevel`);
- `AssessmentRecord` (запис про оцінювання студента з конкретної дисципліни та видом контролю);
- `GradeBook` (контейнерний клас журналу оцінок навчального потоку/групи).

**Необхідно реалізувати:**
1. Доменну модель із щонайменше 5 класів предметної області, `dataclass`, незмінного об'єкта-значення (`@dataclass(frozen=True, slots=True)`) та захищених `properties` із валідацією.
2. Додавання та оновлення оцінок студентів із навчальних дисциплін (`add_grade`, `record_grade`, `assign_grade`).
3. Обчислення середнього арифметичного (`average_score`), кредитно-зваженого (`weighted_average_score`), мінімального (`min_grade`) і максимального (`max_grade`) балів студента та загальної статистики групи (`calculate_group_statistics`).
4. Визначення рівня академічної успішності (`PerformanceLevel`: `Відмінно (A)`, `Добре (B/C)`, `Задовільно (D/E)`, `Незадовільно (FX/F)`), наявності академічної заборгованості (`has_academic_debt`), розміру стипендії бюджетника (`scholarship_amount`) та права контрактника на переведення на бюджет (`qualifies_for_budget_transfer`).
5. Сортування студентів за середнім або кредитно-зваженим рейтинговим балом (`sort_by_average`, `get_ranked_students`).
6. Пошук студентів із рейтинговим балом вище заданого порога (`find_above_threshold`, `find_students_above_threshold`).
7. Абстрактний базовий клас політики оцінювання `PerformanceEvaluationPolicy(ABC)` із конкретними реалізаціями `StandardAveragePolicy` та `CreditWeightedPolicy`.
8. Структурні інтерфейси (`Protocol`) для ідентифікації сутностей (`HasId`), серіалізації (`@runtime_checkable Serializable`), генерації звітів (`GradeReportFormatter`) та розсилки сповіщень (`NotificationSender`).
9. Перевизначення спеціальних `dunder`-методів (`__post_init__`, `__str__`, `__repr__`, `__len__`, `__iter__`, `__contains__`, `__getitem__`, `__lt__`, `__add__`).
10. Узагальнений репозиторій `InMemoryRepository(Generic[T])` із обмеженим параметром типу `T = TypeVar("T", bound=HasId)` та функцію масштабування балів із `constrained TypeVar` (`NumericScore = TypeVar("NumericScore", int, float)`).
11. Типізовані словники `TypedDict` (`StudentPayload`, `AssessmentPayload`) для прийому зовнішніх JSON-подібних даних та їх трансформації у доменні сутності (`student_from_payload`).
12. Сервісний шар `GradeBookService` із впровадженням залежностей (`Dependency Injection`) та дотриманням принципів **SOLID** (`SRP`, `OCP`, `LSP`, `ISP`, `DIP`).
13. Перевірку всієї кодової бази статичним аналізатором `mypy` у режимі `strict = true` та проведення обов'язкового експерименту з виявленням і виправленням помилок типізації.

---

## 3. Опис об'єктної моделі, архітектурних рішень та принципів SOLID

### 3.1. Розподіл класів за ролями в архітектурі

| Клас / Тип | Модуль | Стереотип ООП | Обґрунтування та відповідальність |
| :--- | :--- | :--- | :--- |
| `Grade` | `value_objects.py` | Immutable Value Object (`@dataclass(frozen=True, slots=True)`) | Представляє оцінку в діапазоні `0..100`. Рівність визначається значенням, об'єкт незмінний після створення, підтримує порівняння (`@total_ordering`, `__lt__`), додавання (`__add__`) та обчислення букви ECTS. |
| `PerformanceLevel` | `value_objects.py` | Enumeration (`str, Enum`) | Типобезпечне перерахування рівнів академічної успішності за національною шкалою та шкалою ECTS. |
| `Discipline` | `models.py` | Domain Entity (`@dataclass(slots=True)`) | Навчальна дисципліна з унікальним `id`, назвою та інкапсульованою кількістю кредитів `_credits`, доступ до якої контролюється через `@property credits`. |
| `AssessmentRecord` | `models.py` | Domain Entity (`@dataclass(slots=True)`) | Запис оцінювання, що поєднує композицією `Discipline` та `Grade`, зберігає вид контролю (`Екзамен`/`Залік`) і обчислює зважені бали (`weighted_points`). |
| `Student` | `models.py` | Base Domain Entity | Базовий клас студента, який інкапсулює список оцінок `_records: list[AssessmentRecord]`, надає незмінне представлення `records` (`tuple`), обчислює середній, зважений, мінімальний та максимальний бали. |
| `StateFundedStudent`, `ContractStudent` | `models.py` | Derived Domain Entities (`Inheritance`) | Спеціалізовані підкласи `Student`, що використовують `super().__init__()` і реалізують поліморфний метод `academic_status_note()`, розрахунок стипендії та умову переведення на бюджет. |
| `PerformanceEvaluationPolicy` | `models.py` | Abstract Base Class (`ABC`) | Визначає абстрактний контракт стратегії розрахунку рейтингу (`calculate_rating`) та рівня успішності (`determine_level`). Має підкласи `StandardAveragePolicy` і `CreditWeightedPolicy`. |
| `GradeBook` | `models.py` | Aggregate / Container (`@dataclass`) | Журнал оцінок, що агрегує студентів `_students: dict[int, Student]` та містить композицією стратегію `PerformanceEvaluationPolicy`. Реалізує контейнерні `dunder`-методи (`__len__`, `__iter__`, `__contains__`, `__getitem__`). |
| `HasId`, `Serializable`, `GradeReportFormatter`, `NotificationSender` | `protocols.py` | Structural Interfaces (`Protocol`) | Вузькоспеціалізовані структурні інтерфейси, які дозволяють підключати адаптери форматування звітів та сповіщень без явного наслідування. |
| `InMemoryRepository[T]` | `repositories.py` | Generic Infrastructure (`Generic[T]`) | Узагальнене типобезпечне сховище у пам'яті для будь-яких сутностей, що задовольняють протокол `HasId` (`Student`, `Discipline`). |
| `StudentPayload`, `AssessmentPayload` | `dto.py` | External Data Contracts (`TypedDict`) | Описують структуру зовнішніх словників (JSON/API payloads) із обов'язковими та необов'язковими (`NotRequired`) полями до їх перетворення у доменні об'єкти. |
| `GradeBookService` | `services.py` | Application Service (`Dependency Injection`) | Координує сценарії використання системи: імпорт даних, реєстрацію, виставлення оцінок зі сповіщенням, побудову рейтингових відомостей та відзначення відмінників. |

### 3.2. Діаграма класів (Class Diagram)

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
     ├── InMemoryRepository[Student]      (Generic[T], T bound to HasId)
     ├── InMemoryRepository[Discipline]   (Generic[T], T bound to HasId)
     ├── PerformanceEvaluationPolicy      (ABC)
     ├── GradeReportFormatter             (Protocol)
     └── NotificationSender               (Protocol)
```

### 3.3. Пояснення принципів SOLID у реалізованій моделі

1. **SRP (Single Responsibility Principle — Принцип єдиної відповідальності):**
   - `Grade` відповідає виключно за інваріант оцінки (`0..100`) та її переведення у шкалу ECTS;
   - `Student` відповідає за облік власних навчальних записів та індивідуальні показники успішності;
   - `GradeBook` відповідає за агрегацію групи, сортування та пошук за порогом;
   - `MarkdownReportFormatter` відповідає лише за текстове форматування таблиці відомості;
   - `ConsoleNotificationSender` відповідає лише за відправку сповіщень;
   - `GradeBookService` координує бізнес-сценарії (use cases), не змішуючи їх із деталями збереження чи форматування.
2. **OCP (Open/Closed Principle — Принцип відкритості/закритості):**
   - Класи `GradeBook` та `GradeBookService` закриті для модифікації, але відкриті для розширення: щоб змінити формулу розрахунку рейтингу (зі звичайного середнього `StandardAveragePolicy` на кредитно-зважений `CreditWeightedPolicy`) або формат звіту (з консольної таблиці на HTML/CSV), достатньо передати новий клас-реалізацію без редагування існуючого коду сервісу.
3. **LSP (Liskov Substitution Principle — Принцип підстановки Лісков):**
   - Підкласи `StateFundedStudent` та `ContractStudent` повністю дотримуються контракту базового класу `Student` і можуть передаватися у `InMemoryRepository[Student]`, `GradeBook` та `GradeReportFormatter` без порушення коректності програми.
4. **ISP (Interface Segregation Principle — Принцип розділення інтерфейсів):**
   - Замість одного перевантаженого інтерфейсу створено чотири окремі вузькі протоколи в `protocols.py`: `HasId` (лише поле `id: int`), `Serializable` (лише метод `to_dict()`), `GradeReportFormatter` (лише `format_report()`) та `NotificationSender` (лише `send()`).
5. **DIP (Dependency Inversion Principle — Принцип інверсії залежностей):**
   - Модуль верхнього рівня `GradeBookService` не залежить від конкретних класів `MarkdownReportFormatter` чи `ConsoleNotificationSender`. Він залежить від абстракцій (`PerformanceEvaluationPolicy`, `GradeReportFormatter`, `NotificationSender`), які передаються йому через конструктор (**Dependency Injection**).

---

## 4. Структура проєкту (`src-layout`)

```text
Lab_04/
│
├── report/
│   └── README.md
│
├── src/
│   └── grade_system/
│       ├── __init__.py
│       ├── value_objects.py
│       ├── dto.py
│       ├── models.py
│       ├── protocols.py
│       ├── repositories.py
│       ├── services.py
│       └── main.py
│
├── tests/
│   └── test_grade_system.py
│
├── .gitignore
├── README.md
└── pyproject.toml
```

---

## 5. Повні лістинги модулів та приклади ключових конструкцій

### 5.1. Файл `src/grade_system/value_objects.py` (Immutable Value Object, `@dataclass(frozen=True, slots=True)`, `@total_ordering`)

```python
"""Незмінні об'єкти-значення (Value Objects) предметної області оцінювання студентів."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import total_ordering


class PerformanceLevel(str, Enum):
    """Рівень академічної успішності за шкалою ECTS та національною шкалою."""

    EXCELLENT = "Відмінно (A)"
    GOOD = "Добре (B/C)"
    SATISFACTORY = "Задовільно (D/E)"
    UNSATISFACTORY = "Незадовільно (FX/F)"


@total_ordering
@dataclass(frozen=True, slots=True)
class Grade:
    """Незмінний об'єкт-значення (Value Object), що представляє оцінку у 100-бальній шкалі.

    Використовує frozen=True та slots=True, валідацію у __post_init__
    та підтримує порівняння і арифметичне додавання.
    """

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            raise ValueError(
                f"Оцінка повинна бути в діапазоні від 0 до 100, отримано: {self.value}"
            )

    @property
    def ects_letter(self) -> str:
        """Буквений еквівалент оцінки за шкалою ECTS."""
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

    @property
    def performance_level(self) -> PerformanceLevel:
        """Визначення рівня успішності для оцінки."""
        if self.value >= 90.0:
            return PerformanceLevel.EXCELLENT
        if self.value >= 74.0:
            return PerformanceLevel.GOOD
        if self.value >= 60.0:
            return PerformanceLevel.SATISFACTORY
        return PerformanceLevel.UNSATISFACTORY

    @property
    def is_passing(self) -> bool:
        """Чи є оцінка прохідною (>= 60 балів)."""
        return self.value >= 60.0

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value < other.value

    def __add__(self, other: Grade) -> float:
        """Повертає суму балів двох оцінок."""
        if not isinstance(other, Grade):
            return NotImplemented
        return self.value + other.value

    def __str__(self) -> str:
        return f"{self.value:.1f} ({self.ects_letter})"
```

### 5.2. Файл `src/grade_system/dto.py` (`TypedDict` та `NotRequired` для зовнішніх даних)

```python
"""Типізовані словники (TypedDict) та DTO для зовнішніх даних (payloads)."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class AssessmentPayload(TypedDict):
    """Зовнішній словник даних про оцінювання з дисципліни."""

    discipline_id: int
    discipline_name: str
    credits: int
    score: float
    assessment_type: NotRequired[str]


class StudentPayload(TypedDict):
    """Зовнішній JSON-подібний payload студента з переліком його оцінок."""

    id: int
    full_name: str
    group: str
    email: str
    funding_type: str  # "state" або "contract"
    contract_tuition_fee: NotRequired[float]
    assessments: list[AssessmentPayload]
```

### 5.3. Файл `src/grade_system/models.py` (Domain Entities, Encapsulation, Properties, Inheritance, Composition, `ABC`, Dunder-методи)

```python
"""Сутнісні класи предметної області (Domain Entities): Варіант 7 — Система оцінювання студентів."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

from grade_system.value_objects import Grade, PerformanceLevel


@dataclass(slots=True)
class Discipline:
    """Навчальна дисципліна."""

    id: int
    name: str
    _credits: int

    def __post_init__(self) -> None:
        self._validate_credits(self._credits)

    @staticmethod
    def _validate_credits(value: int) -> None:
        if value <= 0:
            raise ValueError(
                f"Кількість кредитів ECTS має бути додатною, отримано: {value}"
            )

    @property
    def credits(self) -> int:
        """Кількість кредитів ECTS із контрольованим доступом через property."""
        return self._credits

    @credits.setter
    def credits(self, value: int) -> None:
        self._validate_credits(value)
        self._credits = value

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "credits": self._credits,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self._credits} ECTS)"


@dataclass(slots=True)
class AssessmentRecord:
    """Запис про оцінювання студента з певної дисципліни."""

    discipline: Discipline
    _grade: Grade
    assessment_type: str = "Екзамен"

    @property
    def grade(self) -> Grade:
        """Оцінка запису (інкапсульована через property)."""
        return self._grade

    @grade.setter
    def grade(self, new_grade: Grade) -> None:
        self._grade = new_grade

    @property
    def weighted_points(self) -> float:
        """Кредитно-зважений бал: оцінка * кредити ECTS."""
        return self._grade.value * self.discipline.credits

    def to_dict(self) -> dict[str, object]:
        return {
            "discipline": self.discipline.name,
            "credits": self.discipline.credits,
            "score": self._grade.value,
            "ects": self._grade.ects_letter,
            "assessment_type": self.assessment_type,
        }

    def __str__(self) -> str:
        return (
            f"{self.discipline.name} [{self.assessment_type}]: {self._grade}"
        )


class Student:
    """Базова сутність студента (Domain Entity).

    Демонструє інкапсуляцію, properties, композицію (містить AssessmentRecord)
    та базовий клас для наслідування спеціалізованих форм навчання.
    """

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
    ) -> None:
        if student_id <= 0:
            raise ValueError("ID студента має бути додатним числом.")
        if not full_name.strip():
            raise ValueError("ПІБ студента не може бути порожнім.")
        self.id: int = student_id
        self._full_name: str = full_name.strip()
        self._group: str = group.strip()
        self.email: str = email.strip()
        self._records: list[AssessmentRecord] = []

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("ПІБ студента не може бути порожнім.")
        self._full_name = value.strip()

    @property
    def group(self) -> str:
        return self._group

    @group.setter
    def group(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Назва групи не може бути порожньою.")
        self._group = value.strip()

    @property
    def records(self) -> tuple[AssessmentRecord, ...]:
        """Повертає незмінний кортеж записів про оцінювання (захист інкапсуляції)."""
        return tuple(self._records)

    def add_grade(
        self,
        discipline: Discipline,
        grade: Grade,
        assessment_type: str = "Екзамен",
    ) -> AssessmentRecord:
        """Додає або оновлює оцінку студента з дисципліни."""
        for record in self._records:
            if record.discipline.id == discipline.id:
                record.grade = grade
                record.assessment_type = assessment_type
                return record
        new_record = AssessmentRecord(
            discipline=discipline,
            _grade=grade,
            assessment_type=assessment_type,
        )
        self._records.append(new_record)
        return new_record

    @property
    def average_score(self) -> float:
        """Середній арифметичний бал студента."""
        if not self._records:
            return 0.0
        total = sum(r.grade.value for r in self._records)
        return round(total / len(self._records), 2)

    @property
    def weighted_average_score(self) -> float:
        """Середньозважений бал за кредитами ECTS."""
        total_credits = sum(r.discipline.credits for r in self._records)
        if total_credits == 0:
            return 0.0
        weighted_sum = sum(r.weighted_points for r in self._records)
        return round(weighted_sum / total_credits, 2)

    @property
    def min_grade(self) -> Grade | None:
        """Мінімальна оцінка студента."""
        if not self._records:
            return None
        return min(r.grade for r in self._records)

    @property
    def max_grade(self) -> Grade | None:
        """Максимальна оцінка студента."""
        if not self._records:
            return None
        return max(r.grade for r in self._records)

    @property
    def has_academic_debt(self) -> bool:
        """Чи має студент академічну заборгованість (хоча б одну оцінку < 60)."""
        return any(not r.grade.is_passing for r in self._records)

    @property
    def performance_level(self) -> PerformanceLevel:
        """Узагальнений рівень успішності студента."""
        if not self._records or self.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        avg = self.average_score
        return Grade(avg).performance_level

    def academic_status_note(self) -> str:
        """Поліморфний метод опису статусу студента."""
        return f"Загальна форма навчання | Рівень: {self.performance_level.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "full_name": self._full_name,
            "group": self._group,
            "email": self.email,
            "average_score": self.average_score,
            "weighted_average_score": self.weighted_average_score,
            "performance_level": self.performance_level.value,
            "records_count": len(self._records),
        }

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[AssessmentRecord]:
        return iter(self._records)

    def __contains__(self, discipline_id: int) -> bool:
        return any(r.discipline.id == discipline_id for r in self._records)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"full_name={self._full_name!r}, group={self._group!r}, "
            f"avg={self.average_score:.2f})"
        )

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self._full_name} ({self._group}) — "
            f"Середній бал: {self.average_score:.2f}"
        )


class StateFundedStudent(Student):
    """Студент бюджетної форми навчання (наслідує Student із викликом super())."""

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
        base_scholarship: float = 2000.0,
    ) -> None:
        super().__init__(student_id, full_name, group, email)
        if base_scholarship < 0:
            raise ValueError("Розмір стипендії не може бути від'ємним.")
        self.base_scholarship: float = base_scholarship

    @property
    def scholarship_amount(self) -> float:
        """Розрахунок академічної стипендії залежно від успішності."""
        if not self._records or self.has_academic_debt:
            return 0.0
        if self.average_score >= 90.0:
            return round(self.base_scholarship * 1.455, 2)  # Підвищена стипендія
        if self.average_score >= 75.0:
            return self.base_scholarship
        return 0.0

    def academic_status_note(self) -> str:
        stipend = self.scholarship_amount
        stipend_info = (
            f"Стипендія: {stipend:.2f} UAH"
            if stipend > 0
            else "Без стипендії"
        )
        return (
            f"Бюджетна форма | {self.performance_level.value} | {stipend_info}"
        )


class ContractStudent(Student):
    """Студент контрактної форми навчання (наслідує Student із викликом super())."""

    def __init__(
        self,
        student_id: int,
        full_name: str,
        group: str,
        email: str,
        tuition_fee: float = 38000.0,
    ) -> None:
        super().__init__(student_id, full_name, group, email)
        if tuition_fee <= 0:
            raise ValueError("Вартість контракту має бути додатною.")
        self.tuition_fee: float = tuition_fee

    @property
    def qualifies_for_budget_transfer(self) -> bool:
        """Чи претендує контрактник на переведення на бюджет за відмінне навчання."""
        return (
            len(self._records) >= 3
            and not self.has_academic_debt
            and self.average_score >= 92.0
        )

    def academic_status_note(self) -> str:
        transfer = (
            "Рекомендовано до переведення на бюджет"
            if self.qualifies_for_budget_transfer
            else f"Контракт ({self.tuition_fee:.0f} UAH/рік)"
        )
        return f"Контрактна форма | {self.performance_level.value} | {transfer}"


class PerformanceEvaluationPolicy(ABC):
    """Абстрактний базовий клас (ABC) для політики оцінювання успішності."""

    @abstractmethod
    def calculate_rating(self, student: Student) -> float:
        """Обчислює підсумковий рейтинговий бал студента."""
        ...

    @abstractmethod
    def determine_level(self, student: Student) -> PerformanceLevel:
        """Визначає рівень академічної успішності за політикою."""
        ...


class StandardAveragePolicy(PerformanceEvaluationPolicy):
    """Стандартна політика оцінювання за середнім арифметичним балом."""

    def calculate_rating(self, student: Student) -> float:
        return student.average_score

    def determine_level(self, student: Student) -> PerformanceLevel:
        if len(student) == 0 or student.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        return Grade(self.calculate_rating(student)).performance_level


class CreditWeightedPolicy(PerformanceEvaluationPolicy):
    """Політика оцінювання з урахуванням вагових коефіцієнтів кредитів ECTS."""

    def calculate_rating(self, student: Student) -> float:
        return student.weighted_average_score

    def determine_level(self, student: Student) -> PerformanceLevel:
        if len(student) == 0 or student.has_academic_debt:
            return PerformanceLevel.UNSATISFACTORY
        return Grade(self.calculate_rating(student)).performance_level


@dataclass
class GradeBook:
    """Журнал оцінок (GradeBook) — контейнерний доменний клас.

    Використовує композицію для зберігання студентів та політики оцінювання.
    Реалізує dunder-методи: __len__, __iter__, __contains__, __getitem__, __repr__.
    """

    title: str
    policy: PerformanceEvaluationPolicy = field(
        default_factory=StandardAveragePolicy
    )
    _students: dict[int, Student] = field(default_factory=dict)

    def register_student(self, student: Student) -> None:
        """Реєструє студента в журналі."""
        self._students[student.id] = student

    def get_student(self, student_id: int) -> Student | None:
        """Повертає студента за його ID або None."""
        return self._students.get(student_id)

    def record_grade(
        self,
        student_id: int,
        discipline: Discipline,
        grade: Grade,
        assessment_type: str = "Екзамен",
    ) -> AssessmentRecord:
        """Додає оцінку студенту за його ID."""
        student = self._students.get(student_id)
        if student is None:
            raise KeyError(f"Студента з ID={student_id} не знайдено в журналі.")
        return student.add_grade(discipline, grade, assessment_type)

    def calculate_group_statistics(self) -> tuple[float, float, float]:
        """Повертає (середній, мінімальний, максимальний) бал серед усіх оцінок у журналі."""
        all_scores = [
            record.grade.value
            for student in self._students.values()
            for record in student.records
        ]
        if not all_scores:
            return (0.0, 0.0, 0.0)
        avg_score = round(sum(all_scores) / len(all_scores), 2)
        return (avg_score, min(all_scores), max(all_scores))

    def sort_by_average(self, descending: bool = True) -> list[Student]:
        """Сортує студентів за рейтинговим/середнім балом згідно з політикою."""
        return sorted(
            self._students.values(),
            key=lambda s: self.policy.calculate_rating(s),
            reverse=descending,
        )

    def find_above_threshold(self, threshold: float) -> list[Student]:
        """Пошук студентів із середнім балом вище заданого порога."""
        if not (0.0 <= threshold <= 100.0):
            raise ValueError("Поріг бала має бути в межах від 0 до 100.")
        return [
            s
            for s in self.sort_by_average(descending=True)
            if self.policy.calculate_rating(s) > threshold
        ]

    def __len__(self) -> int:
        return len(self._students)

    def __iter__(self) -> Iterator[Student]:
        return iter(self._students.values())

    def __contains__(self, student_id: int) -> bool:
        return student_id in self._students

    def __getitem__(self, student_id: int) -> Student:
        return self._students[student_id]
```

### 5.4. Файл `src/grade_system/protocols.py` (`Protocol` та `@runtime_checkable`)

```python
"""Структурні інтерфейси (Protocol) для зовнішніх залежностей та серіалізації."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from grade_system.models import Student


class HasId(Protocol):
    """Протокол для сутностей, які мають цілочисельний ідентифікатор id."""

    id: int


@runtime_checkable
class Serializable(Protocol):
    """Runtime-checkable протокол для об'єктів, що підтримують серіалізацію у словник."""

    def to_dict(self) -> dict[str, object]:
        ...


class GradeReportFormatter(Protocol):
    """Протокол генерації звітів успішності студентів (Reporting abstraction)."""

    def format_report(
        self,
        title: str,
        students: Sequence[Student],
    ) -> str:
        ...


class NotificationSender(Protocol):
    """Протокол надсилання сповіщень студентам (Notification abstraction)."""

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
    ) -> None:
        ...
```

### 5.5. Файл `src/grade_system/repositories.py` (`Generic[T]`, Bound `TypeVar` та Constrained `TypeVar`)

```python
"""Узагальнене сховище даних (Generic Repository) із використанням TypeVar та Generic[T]."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from grade_system.protocols import HasId

# Bound TypeVar: тип T повинен мати атрибут id: int (відповідати протоколу HasId)
T = TypeVar("T", bound=HasId)

# Constrained TypeVar: демонстрація обмеженого TypeVar для числових розрахунків
NumericScore = TypeVar("NumericScore", int, float)


def scale_score(value: NumericScore, factor: float) -> float:
    """Масштабує числове значення оцінки (демонстрація constrained TypeVar)."""
    return float(value) * factor


class InMemoryRepository(Generic[T]):
    """Типізований узагальнений репозиторій у пам'яті для будь-яких сутностей із HasId."""

    def __init__(self) -> None:
        self._items: dict[int, T] = {}

    def add(self, item: T) -> None:
        """Додає або оновлює сутність у репозиторії."""
        self._items[item.id] = item

    def get(self, item_id: int) -> T | None:
        """Отримує сутність за ID або повертає None."""
        return self._items.get(item_id)

    def all(self) -> list[T]:
        """Повертає список усіх збережених сутностей."""
        return list(self._items.values())

    def find_by(self, predicate: Callable[[T], bool]) -> list[T]:
        """Фільтрує сутності за предикатом."""
        return [item for item in self._items.values() if predicate(item)]

    def remove(self, item_id: int) -> bool:
        """Видаляє сутність за ID."""
        return self._items.pop(item_id, None) is not None

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._items
```

### 5.6. Файл `src/grade_system/services.py` (Application Service, Dependency Injection, Structural Adapters)

```python
"""Сервісний шар застосунку (Application Services) та адаптери інфраструктури."""

from __future__ import annotations

from collections.abc import Sequence

from grade_system.dto import StudentPayload
from grade_system.models import (
    ContractStudent,
    Discipline,
    GradeBook,
    PerformanceEvaluationPolicy,
    StateFundedStudent,
    Student,
)
from grade_system.protocols import GradeReportFormatter, NotificationSender
from grade_system.repositories import InMemoryRepository
from grade_system.value_objects import Grade, PerformanceLevel


class MarkdownReportFormatter:
    """Конкретна реалізація протоколу GradeReportFormatter (структурна типізація)."""

    def format_report(
        self,
        title: str,
        students: Sequence[Student],
    ) -> str:
        lines: list[str] = [
            f"=== ВІДОМІСТЬ УСПІШНОСТІ: {title} ===",
            f"{'№':<3} | {'ПІБ студента':<24} | {'Група':<7} | {'Сер. бал':<8} | {'Зваж.':<8} | {'Статус'}",
            "-" * 92,
        ]
        for idx, student in enumerate(students, start=1):
            lines.append(
                f"{idx:<3} | {student.full_name:<24} | {student.group:<7} | "
                f"{student.average_score:<8.2f} | {student.weighted_average_score:<8.2f} | "
                f"{student.academic_status_note()}"
            )
        return "\n".join(lines)


class ConsoleNotificationSender:
    """Конкретна реалізація протоколу NotificationSender для виводу в консоль."""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str, str]] = []

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
    ) -> None:
        self.sent_messages.append((recipient, subject, message))
        print(f"[СПОВІЩЕННЯ -> {recipient}] Тема: {subject} | {message}")


def student_from_payload(
    payload: StudentPayload,
    discipline_repo: InMemoryRepository[Discipline] | None = None,
) -> Student:
    """Перетворює зовнішній TypedDict (StudentPayload) у доменний об'єкт Student."""
    funding = payload["funding_type"].lower()
    student: Student
    if funding == "state":
        student = StateFundedStudent(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
        )
    elif funding == "contract":
        tuition = payload.get("contract_tuition_fee", 38000.0)
        student = ContractStudent(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
            tuition_fee=tuition,
        )
    else:
        student = Student(
            student_id=payload["id"],
            full_name=payload["full_name"],
            group=payload["group"],
            email=payload["email"],
        )

    for item in payload["assessments"]:
        discipline: Discipline | None = None
        if discipline_repo is not None:
            discipline = discipline_repo.get(item["discipline_id"])
        if discipline is None:
            discipline = Discipline(
                id=item["discipline_id"],
                name=item["discipline_name"],
                _credits=item["credits"],
            )
            if discipline_repo is not None:
                discipline_repo.add(discipline)

        assessment_type = item.get("assessment_type", "Екзамен")
        student.add_grade(
            discipline=discipline,
            grade=Grade(item["score"]),
            assessment_type=assessment_type,
        )

    return student


class GradeBookService:
    """Сервіс управління оцінюванням студентів (Application Service).

    Демонструє Dependency Injection та дотримання принципів SOLID (SRP, OCP, LSP, ISP, DIP).
    """

    def __init__(
        self,
        student_repo: InMemoryRepository[Student],
        discipline_repo: InMemoryRepository[Discipline],
        evaluation_policy: PerformanceEvaluationPolicy,
        report_formatter: GradeReportFormatter,
        notifier: NotificationSender,
        title: str = "Журнал успішності потоку",
    ) -> None:
        self._student_repo = student_repo
        self._discipline_repo = discipline_repo
        self._policy = evaluation_policy
        self._report_formatter = report_formatter
        self._notifier = notifier
        self._grade_book = GradeBook(title=title, policy=evaluation_policy)

    @property
    def grade_book(self) -> GradeBook:
        return self._grade_book

    def import_student_payload(self, payload: StudentPayload) -> Student:
        """Імпортує студента із зовнішнього TypedDict payload у репозиторій та журнал."""
        student = student_from_payload(payload, self._discipline_repo)
        self._student_repo.add(student)
        self._grade_book.register_student(student)
        return student

    def register_student(self, student: Student) -> None:
        """Реєструє студента в репозиторії та журналі."""
        self._student_repo.add(student)
        self._grade_book.register_student(student)

    def register_discipline(self, discipline: Discipline) -> None:
        """Реєструє навчальну дисципліну в репозиторії."""
        self._discipline_repo.add(discipline)

    def assign_grade(
        self,
        student_id: int,
        discipline_id: int,
        score: float,
        assessment_type: str = "Екзамен",
    ) -> Grade:
        """Виставляє оцінку студенту з дисципліни та надсилає сповіщення."""
        student = self._student_repo.get(student_id)
        if student is None:
            raise ValueError(f"Студента з ID {student_id} не знайдено.")
        discipline = self._discipline_repo.get(discipline_id)
        if discipline is None:
            raise ValueError(f"Дисципліну з ID {discipline_id} не знайдено.")

        grade = Grade(score)
        self._grade_book.record_grade(
            student_id=student.id,
            discipline=discipline,
            grade=grade,
            assessment_type=assessment_type,
        )

        self._notifier.send(
            recipient=student.email,
            subject=f"Нова оцінка з дисципліни «{discipline.name}»",
            message=(
                f"Виставлено {grade} ({assessment_type}). "
                f"Поточний середній бал: {student.average_score:.2f}."
            ),
        )
        return grade

    def get_student_summary(
        self, student_id: int
    ) -> dict[str, float | str | None]:
        """Обчислює середній, мінімальний, максимальний бал та рівень успішності студента."""
        student = self._student_repo.get(student_id)
        if student is None:
            raise ValueError(f"Студента з ID {student_id} не знайдено.")

        min_g = student.min_grade
        max_g = student.max_grade
        level: PerformanceLevel = self._policy.determine_level(student)

        return {
            "full_name": student.full_name,
            "average": student.average_score,
            "weighted_average": student.weighted_average_score,
            "rating": self._policy.calculate_rating(student),
            "min": min_g.value if min_g is not None else None,
            "max": max_g.value if max_g is not None else None,
            "performance_level": level.value,
        }

    def get_ranked_students(self, descending: bool = True) -> list[Student]:
        """Повертає відсортований за рейтингом список студентів."""
        return self._grade_book.sort_by_average(descending=descending)

    def find_students_above_threshold(self, threshold: float) -> list[Student]:
        """Повертає студентів, чий середній/рейтинговий бал перевищує заданий поріг."""
        return self._grade_book.find_above_threshold(threshold)

    def notify_honor_students(self, threshold: float = 90.0) -> list[Student]:
        """Сповіщає студентів-відмінників, які перевищили поріг успішності."""
        honors = self.find_students_above_threshold(threshold)
        for student in honors:
            self._notifier.send(
                recipient=student.email,
                subject="Відзнака за високу академічну успішність",
                message=(
                    f"Вітаємо, {student.full_name}! Ваш рейтинговий бал становить "
                    f"{self._policy.calculate_rating(student):.2f} (вище порога {threshold:.1f})."
                ),
            )
        return honors

    def generate_ranking_report(self) -> str:
        """Формує текстовий звіт рейтингу студентів через інжектований форматер."""
        ranked = self.get_ranked_students(descending=True)
        return self._report_formatter.format_report(
            title=self._grade_book.title,
            students=ranked,
        )
```

---

## 6. Результат роботи програми (`python -m grade_system.main`)

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

--- 5. Студенти з середнім балом вище порога 85.0 ---
  1. [101] Коваленко Анна Ігорівна (КН-21) — Середній бал: 94.50 | Бюджетна форма | Відмінно (A) | Стипендія: 2910.00 UAH
  2. [103] Шевченко Дарина Олександрівна (КН-22) — Середній бал: 93.00 | Контрактна форма | Відмінно (A) | Рекомендовано до переведення на бюджет

--- 6. Розсилка відзнак студентам із балом > 90.0 ---
[СПОВІЩЕННЯ -> anna.kovalenko@university.edu.ua] Тема: Відзнака за високу академічну успішність | Вітаємо, Коваленко Анна Ігорівна! Ваш рейтинговий бал становить 94.50 (вище порога 90.0).
[СПОВІЩЕННЯ -> daryna.shevchenko@university.edu.ua] Тема: Відзнака за високу академічну успішність | Вітаємо, Шевченко Дарина Олександрівна! Ваш рейтинговий бал становить 93.00 (вище порога 90.0).

--- 7. Порівняння з кредитно-зваженою політикою (CreditWeightedPolicy) ---
  Коваленко Анна Ігорівна: стандартний = 94.50, кредитно-зважений = 94.50
  Шевченко Дарина Олександрівна: стандартний = 93.00, кредитно-зважений = 93.06
```

---

## 7. Експериментальна частина та статична перевірка типів (`mypy`)

### 7.1. Обов'язковий експеримент із статичним аналізатором типів `mypy` (п. 71)

Налаштування `mypy` у `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_return_any = true
```

Для перевірки здатності статичного аналізатора виявляти помилки типізації до запуску програми було навмисно внесено три помилки:

| № | Навмисно внесений фрагмент коду | Повідомлення діагностики `mypy --strict` | Причина та виправлення |
| :-: | :--- | :--- | :--- |
| **1** | `student_id: int = "101"` | `error: Incompatible types in assignment (expression has type "str", variable has type "int") [assignment]` | Змінній із анотацією `int` присвоєно рядок `"101"`. Виправлено на ціле число `101`. |
| **2** | `def total_credits() -> int: return "18"` | `error: Incompatible return value type (got "str", expected "int") [return-value]` | Функція декларує повернення `int`, але повертає `str`. Виправлено на `return 18`. |
| **3** | `repo: InMemoryRepository[Student] = InMemoryRepository()`<br>`repo.add(Discipline(id=1, name="ООП", _credits=5))` | `error: Argument 1 to "add" of "InMemoryRepository" has incompatible type "Discipline"; expected "Student" [arg-type]` | У репозиторій, параметризований типом `Student` (`Generic[T]`), передано об'єкт `Discipline`. Виправлено передачею екземпляра `Student`. |

Результат запуску `python -m mypy src tests` та `pytest -v` після виправлення помилок:
```text
Success: no issues found in 9 source files
============================== 5 passed in 0.09s ==============================
```

### 7.2. Порівняння Варіанта A (жорстке створення залежностей) та Варіанта B (Dependency Injection) (п. 72)

| Критерій порівняння | Варіант A (`self.notifier = ConsoleNotificationSender()` всередині `__init__`) | Варіант B (Dependency Injection через конструктор `notifier: NotificationSender`) |
| :--- | :--- | :--- |
| **Зв'язність (Coupling)** | Висока: сервіс жорстко прив'язаний до конкретного класу консольного сповіщувача та стандартної політики оцінювання. | Низька: сервіс знає лише про абстрактний протокол `NotificationSender` та `ABC` `PerformanceEvaluationPolicy`. |
| **Тестованість (Testability)** | Складно тестувати ізольовано: кожен виклик у тестах друкує в консоль або звертається до реального зовнішнього сервісу. | Висока: у модульних тестах (`pytest`) легко передати mock/spy-об'єкт і перевірити `len(notifier.sent_messages) == 1`. |
| **Замінюваність та розширюваність** | Для переходу на Email чи Telegram-сповіщення потрібно змінювати код самого `GradeBookService` (порушення `OCP`). | Новий адаптер підключається при ініціалізації без жодної зміни в `GradeBookService`. |
| **Відповідність принципу DIP** | Порушує `DIP` (модуль вищого рівня залежить від модуля нижнього рівня). | Повністю відповідає `DIP` (обидва рівні залежать від абстракцій `Protocol` / `ABC`). |

### 7.3. Дослідження `Inheritance` vs `Composition` (п. 73)

- **Коли виправдане наслідування (`Inheritance`, відношення `is-a`):** для ієрархії `Student` $\to$ `StateFundedStudent`, `ContractStudent`. Бюджетник і контрактник дійсно *є студентами*, мають усі атрибути й методи базового студента та спеціалізують лише фінансово-академічний статус (`scholarship_amount`, `qualifies_for_budget_transfer`).
- **Коли композиція краща за наслідування (`Composition`, відношення `has-a`):** для `GradeBook` та `GradeBookService`. Якби `GradeBook` наслідував `StandardAveragePolicy` або `MarkdownReportFormatter`, виник би комбінаторний вибух класів (`WeightedMarkdownGradeBook`, `StandardHtmlGradeBook` тощо). Завдяки композиції `GradeBook` *містить* об'єкт `policy: PerformanceEvaluationPolicy`, а `GradeBookService` *містить* репозиторії, форматер і сповіщувач, що дозволяє комбінувати їх незалежно в runtime.

---

## 8. Відповіді на контрольні запитання

1. **Що таке class?** — Шаблон (креслення або користувацький тип даних), який визначає структуру атрибутів (даних) і поведінку (методів) для певної категорії об'єктів.
2. **Що таке object?** — Конкретна сутність у пам'яті під час виконання програми, яка має власний стан (значення атрибутів), ідентичність (`id()`) та поведінку, визначену її класом.
3. **Що таке instance?** — Конкретний екземпляр певного класу, створений викликом конструктора цього класу (наприклад, `anna = StateFundedStudent(...)`).
4. **Для чого `__init__()`?** — Спеціальний метод-ініціалізатор, який автоматично викликається після створення нового екземпляра об'єкта для встановлення його початкових атрибутів і перевірки інваріантів.
5. **Що таке instance attribute?** — Атрибут, який належить конкретному екземпляру об'єкта (зберігається в `self.__dict__` або `__slots__` цього екземпляра), і його зміна в одному об'єкті не впливає на інші.
6. **Що таке class attribute?** — Атрибут, оголошений безпосередньо в тілі класу, який є спільним для самого класу та всіх його екземплярів (наприклад, константи або значення за замовчуванням).
7. **Що таке encapsulation?** — Принцип ООП, за яким об'єкт приховує деталі своєї внутрішньої реалізації і сам контролює власний стан, дозволяючи змінювати його лише через перевірені публічні методи та `properties`.
8. **Для чого properties?** — Декоратор `@property` дозволяє звертатися до методів читання, запису (`@x.setter`) та обчислюваних полів через зручний синтаксис звичайного атрибута (`student.average_score`, `discipline.credits = 5`), зберігаючи при цьому валідацію.
9. **Чим property відрізняється від public field?** — Звичайне публічне поле записує будь-яке значення напряму в пам'ять без перевірок, тоді як `property` перехоплює читання/запис і виконує метод-геттер або сеттер із валідацією чи динамічним обчисленням.
10. **Що таке inheritance?** — Механізм створення нового спеціалізованого класу (підкласу) на основі існуючого базового класу з успадкуванням його атрибутів і методів та можливістю їх перевизначення або розширення.
11. **Що означає relation is-a?** — Логічне відношення «є різновидом», яке лежить в основі правильного наслідування (наприклад, `StateFundedStudent` *is a* `Student`).
12. **Що таке composition?** — Побудова складних об'єктів шляхом включення в них екземплярів інших незалежних класів як атрибутів і делегування їм частини роботи.
13. **Що означає relation has-a?** — Логічне відношення «має / містить у собі», характерне для композиції та агрегації (наприклад, `Student` *has* `AssessmentRecord`, `GradeBook` *has* `PerformanceEvaluationPolicy`).
14. **Коли composition краща за inheritance?** — Коли між класами немає природного відношення `is-a`, коли поведінку потрібно гнучко змінювати під час виконання програми (патерн Strategy) або коли потрібно уникнути жорсткої зв'язності та глибоких ієрархій класів.
15. **Для чого `super()`?** — Вбудована функція, яка повертає проксі-об'єкт для коректного делегування виклику методів (зокрема `__init__()`) батьківському класу згідно з порядком розв'язання методів (`MRO`).
16. **Що таке polymorphism?** — Здатність різних класів реалізовувати однаковий інтерфейс (методи з однаковою назвою та сигнатурою) по-різному, завдяки чому клієнтський код працює з ними однотипно (наприклад, виклик `student.academic_status_note()` для бюджетника і контрактника).
17. **Що таке duck typing?** — Концепція динамічної типізації Python («якщо щось ходить як качка і крякає як качка, то це качка»), за якою сумісність об'єкта визначається наявністю потрібних методів і атрибутів, а не його місцем в ієрархії наслідування.
18. **Що таке ABC?** — Абстрактний базовий клас (`abc.ABC`), який визначає спільний інтерфейс та обов'язкові абстрактні методи для своїх підкласів при номінальній типізації.
19. **Для чого `abstractmethod`?** — Декоратор `@abstractmethod` позначає метод абстрактного класу, який обов'язково має бути реалізований у кожному конкретному підкласі.
20. **Чи можна створити instance abstract class?** — Ні, якщо клас успадковує `ABC` і має хоча б один нереалізований `@abstractmethod`, спроба створити його екземпляр викличе `TypeError: Can't instantiate abstract class`.
21. **Що таке Protocol?** — Механізм із модуля `typing` (`typing.Protocol`), який дозволяє формалізувати структурну типізацію (static duck typing) для статичних аналізаторів типів (`mypy`, `Pyright`).
22. **Чим Protocol відрізняється від ABC?** — `ABC` використовує номінальну типізацію (клас мусить явно наслідувати `class Child(BaseABC)`), а `Protocol` використовує структурну типізацію (клас вважається сумісним автоматично, якщо має відповідні методи з правильними типами, навіть без явного наслідування).
23. **Що таке structural typing?** — Система типізації, в якій сумісність типів визначається виключно структурою об'єкта (наявністю потрібних атрибутів і сигнатур методів).
24. **Що таке nominal typing?** — Система типізації, в якій сумісність типів визначається явним оголошенням імені типу та явним наслідуванням у коді.
25. **Що таке dataclass?** — Декоратор `@dataclass` із модуля `dataclasses`, який автоматично генерує шаблонні методи класу на основі анотованих полів.
26. **Які methods генерує dataclass?** — За замовчуванням генерує `__init__()`, `__repr__()` та `__eq__()` (а за додаткових параметрів також методи порівняння `order=True` або хешування `__hash__()` при `frozen=True`).
27. **Для чого `default_factory`?** — Параметр `field(default_factory=list)` або `field(default_factory=dict)`, який викликає фабричну функцію окремо для кожного нового екземпляра, створюючи власну незалежну змінювану колекцію.
28. **Чому mutable default є проблемою?** — Якби всі екземпляри класу використовували один спільний змінюваний список або словник за замовчуванням, додавання елемента в одному об'єкті змінювало б дані в усіх інших об'єктах (тому `dataclass` прямо забороняє `items: list = []`).
29. **Для чого `__post_init__()`?** — Спеціальний метод `dataclass`, який автоматично викликається одразу після згенерованого `__init__()` і використовується для валідації полів або обчислення похідних атрибутів.
30. **Що означає `frozen=True`?** — Робить екземпляри `dataclass` незмінними (immutable): будь-яка спроба змінити атрибут після ініціалізації піднімає `FrozenInstanceError`, а сам об'єкт стає хешованим (`hashable`).
31. **Що означає `slots=True`?** — Вказує `dataclass` генерувати атрибут `__slots__` замість динамічного словника `__dict__`, що зменшує споживання оперативної пам'яті та прискорює доступ до атрибутів.
32. **Що таке dunder method?** — Спеціальний («магічний») метод Python із подвійним підкресленням на початку і в кінці (`double underscore`), через який користувацькі класи інтегруються у вбудовані оператори та функції мови (`len()`, `for`, `in`, `+`, `<`, `str()`).
33. **Для чого `__repr__()`?** — Повертає однозначне технічне рядкове представлення об'єкта для розробника та налагодження (бажано у вигляді валідного виразу створення об'єкта).
34. **Для чого `__str__()`?** — Повертає зручне людиночитабельне текстове представлення об'єкта для кінцевого користувача (викликається функціями `print()` та `str()`).
35. **Для чого `__len__()`?** — Дозволяє застосовувати до об'єкта-контейнера вбудовану функцію `len(obj)`, повертаючи цілу невід'ємну кількість елементів.
36. **Для чого `__iter__()`?** — Повертає ітератор по елементах контейнера, що дозволяє перебирати об'єкт у циклі `for`, comprehensions та передавати в `list()`, `tuple()`.
37. **Для чого `__contains__()`?** — Реалізує поведінку оператора перевірки входження `item in container`, повертаючи `True` або `False`.
38. **Для чого `__call__()`?** — Дозволяє викликати екземпляр класу як звичайну функцію за допомогою круглих дужок `obj(arg1, arg2)`.
39. **Що таке SOLID?** — Акронім п'яти фундаментальних принципів об'єктно-орієнтованого проєктування (Роберт Мартін), які роблять програмну архітектуру зрозумілою, гнучкою, слабкозв'язаною та придатною до тестування й розширення.
40. **Що означає SRP?** — *Single Responsibility Principle*: кожен клас або модуль повинен мати лише одну зону відповідальності і лише одну причину для зміни.
41. **Що означає OCP?** — *Open/Closed Principle*: програмні сутності мають бути відкритими для розширення новою поведінкою, але закритими для модифікації вже перевіреного вихідного коду.
42. **Що означає LSP?** — *Liskov Substitution Principle*: об'єкти підкласів повинні безпомилково замінювати об'єкти базового класу, не порушуючи очікуваної поведінки та інваріантів програми.
43. **Що означає ISP?** — *Interface Segregation Principle*: клієнти не повинні залежати від методів, які вони не використовують; великі інтерфейси слід розділяти на вузькі спеціалізовані контракти.
44. **Що означає DIP?** — *Dependency Inversion Principle*: модулі верхніх рівнів не повинні залежати від модулів нижніх рівнів; обидва повинні залежати від абстракцій (`ABC` або `Protocol`).
45. **Що таке dependency injection?** — Патерн проєктування, за яким зовнішні залежності об'єкта (репозиторії, шлюзи, сповіщувачі, стратегії) не створюються ним самим усередині, а передаються йому ззовні (найчастіше через параметри конструктора `__init__`).
46. **Чому DI покращує testability?** — Тому що під час модульного тестування замість реальних зовнішніх сервісів (БД, поштового сервера, платіжного шлюзу) у конструктор можна передати легкі фейкові або mock-реалізації.
47. **Що таке type hint?** — Синтаксична анотація типів змінних, атрибутів, параметрів і значень, що повертаються функціями (наприклад, `def get(self, item_id: int) -> T | None:`), яка документує контракт коду та перевіряється статичними аналізаторами.
48. **Чи перевіряє Python type hints автоматично в runtime?** — Ні, стандартний інтерпретатор CPython зберігає анотації в `__annotations__`, але не виконує автоматичної перевірки типів під час роботи програми.
49. **Що таке static type checker?** — Інструмент статичного аналізу коду (`mypy`, `Pyright`), який перевіряє узгодженість типів у всьому проєкті ще до запуску програми.
50. **Для чого mypy?** — Статичний аналізатор типів для Python, який виявляє помилки несумісності аргументів, некоректні типи повернення, звернення до неіснуючих атрибутів або небезпечну роботу з `None`.
51. **Для чого Pyright?** — Високошвидкісний статичний аналізатор типів від Microsoft (лежить в основі Pylance у VS Code), який виконує перевірку типів у реальному часі та в CI/CD.
52. **Що таке TypeVar?** — Конструкція з модуля `typing`, яка оголошує змінну типу для створення параметризованих (generic) функцій і класів зі збереженням зв'язку між вхідними та вихідними типами.
53. **Що таке Generic?** — Базовий клас `typing.Generic`, успадкування від якого дозволяє створювати узагальнені класи, параметризовані однією або кількома змінними типу `TypeVar`.
54. **Що означає `Generic[T]`?** — Означає, що клас є параметризованим типом за параметром `T` (наприклад, `InMemoryRepository[Student]` або `InMemoryRepository[Discipline]`).
55. **Що таке bound TypeVar?** — Змінна типу з верхньою межею `T = TypeVar("T", bound=HasId)`, яка дозволяє підставляти лише сам тип `HasId` або будь-який його підтип/структурно сумісний клас.
56. **Що таке constrained TypeVar?** — Змінна типу з переліком конкретних дозволених типів `NumericScore = TypeVar("NumericScore", int, float)`, яка може набувати лише одного з прямо перелічених типів.
57. **Що таке TypedDict?** — Конструкція з модуля `typing`, яка дозволяє описати словник (`dict`) із фіксованим набором рядкових ключів та строго визначеними типами значень для кожного ключа.
58. **Чим TypedDict відрізняється від dataclass?** — Екземпляр `TypedDict` у runtime залишається звичайним словником `dict` (доступ через `data["id"]`, без власних методів), тоді як `dataclass` створює повноцінний екземпляр класу з атрибутами (`obj.id`), методами, властивостями та валідацією у `__post_init__`.
59. **Коли доцільно використовувати TypedDict?** — Для типізації сирих JSON-відповідей від REST API, конфігураційних словників, результатів читання зовнішніх файлів або аргументів на межі інтеграції систем.
60. **Чому external payload і domain object краще розділяти?** — Зовнішній формат даних (API/JSON payload) може змінюватися незалежно від бізнес-логіки і не містить поведінки чи гарантій цілісності; перетворення `TypedDict` у валідований доменний об'єкт на вході системи захищає ядро програми від некоректних даних.

---

## 9. Висновок

У ході виконання лабораторної роботи №4 було спроєктовано та реалізовано типізовану об'єктно-орієнтовану модель системи оцінювання студентів (`grade_system`, Варіант №7). Предметну область декомпозовано на окремі модулі (`value_objects.py`, `dto.py`, `models.py`, `protocols.py`, `repositories.py`, `services.py`, `main.py`). У роботі практично застосовано доменні класи, `@dataclass`, незмінні об'єкти-значення (`@dataclass(frozen=True, slots=True)`), інкапсуляцію стану та контрольовані `properties`, обґрунтоване наслідування форм навчання (`Student` $\to$ `StateFundedStudent`, `ContractStudent`) із `super()`, композицію компонентів, абстрактні базові класи (`PerformanceEvaluationPolicy(ABC)`), структурні протоколи (`Protocol`, `@runtime_checkable`), спеціальні `dunder`-методи (`__post_init__`, `__str__`, `__repr__`, `__len__`, `__iter__`, `__contains__`, `__getitem__`, `__lt__`, `__add__`), принципи **SOLID** та **Dependency Injection**. Використання сучасної системи типів Python (`Generic[T]`, `bound` і `constrained TypeVar`, `TypedDict`) разом із перевіркою `mypy --strict` та модульними тестами `pytest` підтвердило повну типобезпечність та коректність розробленої архітектури.
