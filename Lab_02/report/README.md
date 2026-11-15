# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №2

**Дисципліна:** «Професійний Python»  
**Тема:** Структури даних та функціональна декомпозиція  
**Варіант:** №7 — Аналіз системи замовлень інтернет-магазину (`data_processor`, узгоджено з Лабораторною роботою №1)  
**Виконав:** студент Назар Поцелуйко  

---

## 1. Мета роботи

Сформувати практичні навички професійного використання базових (`list`, `tuple`, `set`, `dict`) та розширених (`collections.Counter`, `collections.defaultdict`, `collections.deque`) структур даних Python, навчитися обирати структуру відповідно до задачі, застосовувати `list/set/dict comprehensions` і генераторні вирази (`generator expressions`), оцінювати часову складність основних операцій у нотації Big-O, проводити експериментальний бенчмаркінг та декомпозувати програму на невеликі функції з чітко визначеною відповідальністю із використанням позиційних та іменованих аргументів, `*args`, `**kwargs`, `lambda`, замикань (`closures`) і декораторів (`decorators`).

---

## 2. Індивідуальне завдання (Варіант №7)

### Постановка задачі (Варіант №7 — Аналіз системи замовлень інтернет-магазину)

Проєкт є логічним продовженням наскрізної предметної області з Лабораторної роботи №1 (**Варіант №7 — Система управління замовленнями інтернет-магазину**).

**Вхідні структуровані дані кожного замовлення (`OrderRecord`):**
- унікальний номер замовлення (`id: str`, наприклад, `"ORD-1001"`);
- ім'я та прізвище клієнта (`customer: str`);
- назва товару (`item: str`);
- категорія товару (`category: str`: `"Peripherals"`, `"Monitors"`, `"Laptops"`, `"Audio"`, `"Accessories"`);
- кількість одиниць (`quantity: int`);
- ціна за одиницю (`unit_price: float`);
- підсумкова сума замовлення з урахуванням знижки 10% для замовлень від 10 000 грн (`amount: float`);
- статус замовлення (`status: str`: `"new"`, `"paid"`, `"shipped"`, `"cancelled"`).

**Необхідно реалізувати:**
1. Зберігання та обробку даних із використанням `list`, `tuple`, `set`, `dict` та спеціалізованих колекцій модуля `collections` (`Counter`, `defaultdict`, `deque`).
2. `list comprehension`, `set comprehension`, `dict comprehension` та `generator expressions`.
3. Пошук замовлення за номером: лінійний пошук у списку `find_order_linear` ($O(n)$) та швидкий пошук за індексом-словником `find_order_by_index` ($O(1)$).
4. Побудову `dict-index` за номером замовлення (`create_order_index`).
5. Групування замовлень за статусом (`group_orders_by_status`), за категорією (`group_orders_by_category`) та вкладене групування `category -> status -> list[order]` (`group_orders_nested`) через `defaultdict`.
6. Статистику кількості замовлень за статусами і категоріями через `Counter` (`count_orders_by_status`, `count_orders_by_category`).
7. Агрегацію даних: загальна виручка активних замовлень (`calculate_total_revenue`), середній чек (`calculate_average_order`), найдорожче замовлення (`find_most_expensive_order`), межі вартості замовлень у вигляді кортежу `(min_amount, max_amount)` (`get_amount_bounds`).
8. Фільтрацію замовлень за статусом, мінімальною сумою та універсальну функцію вищого порядку `filter_items(items, predicate)`.
9. Сортування замовлень за сумою (`sort_orders_by_amount`) та універсальне сортування `sort_items(items, key_func, reverse)` із використанням `lambda`.
10. Функції зі змінною кількістю позиційних (`*args` — `calculate_average_values`, `run_pipeline`) та іменованих (`**kwargs` — `create_record`) аргументів.
11. Замикання (`closures`): `create_min_amount_filter(minimum_amount)` та `create_category_filter(allowed_categories, active_only)`.
12. Декоратори (`decorators`): вимірювання часу виконання `@measure_time`, логування в історію операцій `@log_call` та параметризований декоратор `@repeat(count)`.
13. Збереження історії останніх операцій у двосторонній черзі обмеженої довжини `collections.deque(maxlen=15)`.
14. Конвеєрну обробку даних (`run_pipeline`), експорт зведеного аналітичного звіту у JSON (`build_summary_report`, `export_summary_to_json`) та експериментальний бенчмарк швидкодії пошуку `list` ($O(n)$) проти `dict`/`set` ($O(1)$) на вибірках у **1 000**, **10 000** та **100 000** записів.

---

## 3. Опис структур даних та обґрунтування їх вибору

### 3.1. Чому обрано `list`, `tuple`, `set`, `dict`

| Структура | Де використано у проєкті | Обґрунтування вибору |
| :--- | :--- | :--- |
| **`list`** | Основний набір замовлень `orders: list[OrderRecord]`, результати фільтрації, сортування та конвеєра (`run_pipeline`). | Зберігає впорядковану послідовність записів, підтримує ітерацію за $O(n)$, сортування Timsort за $O(n \log n)$ та додавання у кінець за $O(1)$ амортизовано. |
| **`tuple`** | Константи `VALID_STATUSES`, `PRODUCT_CATEGORIES`, правило знижки `DISCOUNT_RULE = (10000.0, 0.10)`, координати складу `WAREHOUSE_COORDINATES = (49.8397, 24.0297)`, повернення пари `(min_amount, max_amount)` у `get_amount_bounds()`. | Незмінювана (`immutable`) структура фіксованої структури, яка захищає доменні константи від випадкової модифікації та дозволяє зручне розпакування (`min_amt, max_amt = get_amount_bounds(orders)`). |
| **`set`** | Унікальні статуси (`get_unique_statuses`), категорії (`get_unique_categories`), клієнти (`get_unique_customers`), сегментація клієнтів (`analyze_customer_segments`). | Автоматично усуває дублікати, забезпечує перевірку належності елемента `x in s` у середньому за $O(1)$ та підтримує теоретико-множинні операції об'єднання (`\|`), перетину (`&`), різниці (`-`) та симетричної різниці (`^`). |
| **`dict`** | Представлення кожного замовлення `OrderRecord`, пошуковий індекс `order_index` (`id -> order`), результати групування та зведений звіт `build_summary_report()`. | Хеш-таблиця забезпечує доступ та пошук за ключем `index.get(order_id)` у середньому за $O(1)$ замість повільного лінійного перебору $O(n)$. |

### 3.2. Використання спеціалізованих структур модуля `collections`

1. **`collections.Counter`** — використано у функціях `count_orders_by_status(orders)` та `count_orders_by_category(orders)` для підрахунку частоти появ кожного статусу та категорії в один прохід $O(n)$.
2. **`collections.defaultdict`** — використано у `group_orders_by_status(orders)`, `group_orders_by_category(orders)` та у вкладеному групуванні `group_orders_nested(orders)` (`defaultdict(lambda: defaultdict(list))`), що усуває потребу вручну перевіряти наявність ключа перед додаванням елемента у список групи.
3. **`collections.deque`** — використано для журналу останніх операцій `OPERATION_HISTORY: deque[str] = deque(maxlen=15)` у модулі `decorators.py`. Завдяки параметру `maxlen=15` додавання нового запису в кінець і автоматичне витіснення найстарішого запису з початку виконуються за $O(1)$.

---

## 4. Структура проєкту (`src-layout`)

```text
Lab_02/
│
├── report/
│   ├── README.md
│   └── Lab_02_Report.docx
│
├── src/
│   └── data_processor/
│       ├── __init__.py
│       ├── data.py
│       ├── decorators.py
│       ├── processors.py
│       ├── analytics.py
│       └── main.py
│
├── tests/
│   └── test_data_processor.py
│
├── .gitignore
├── README.md
└── pyproject.toml
```

---

## 5. Повні лістинги модулів та приклади ключових конструкцій

### 5.1. Файл `src/data_processor/data.py`

```python
"""Structured order dataset and configuration constants (Variant 7)."""

from typing import Any, TypeAlias

OrderRecord: TypeAlias = dict[str, Any]

# Immutable tuples representing fixed domain constants and discount rules
VALID_STATUSES: tuple[str, ...] = ("new", "paid", "shipped", "cancelled")
PRODUCT_CATEGORIES: tuple[str, ...] = (
    "Peripherals",
    "Monitors",
    "Laptops",
    "Audio",
    "Accessories",
)
DISCOUNT_RULE: tuple[float, float] = (10000.0, 0.10)  # (threshold_uah, discount_rate)
WAREHOUSE_COORDINATES: tuple[float, float] = (49.8397, 24.0297)  # Lviv hub (lat, lon)

# Initial structured dataset of online store orders (aligned with Lab 01 Variant 7)
orders: list[OrderRecord] = [
    {
        "id": "ORD-1001",
        "customer": "Anna Koval",
        "item": "Mechanical Keyboard Keychron K8",
        "category": "Peripherals",
        "quantity": 2,
        "unit_price": 4200.00,
        "amount": 8400.00,
        "status": "paid",
    },
    {
        "id": "ORD-1002",
        "customer": "Oleh Melnyk",
        "item": "Monitor Dell UltraSharp 27",
        "category": "Monitors",
        "quantity": 1,
        "unit_price": 16500.00,
        "amount": 14850.00,
        "status": "shipped",
    },
    {
        "id": "ORD-1003",
        "customer": "Iryna Bondar",
        "item": "Wireless Mouse Logitech MX Master 3S",
        "category": "Peripherals",
        "quantity": 3,
        "unit_price": 4500.00,
        "amount": 12150.00,
        "status": "new",
    },
    {
        "id": "ORD-1004",
        "customer": "Andrii Shevchenko",
        "item": "USB-C Docking Station",
        "category": "Accessories",
        "quantity": 1,
        "unit_price": 3800.00,
        "amount": 3800.00,
        "status": "paid",
    },
    {
        "id": "ORD-1005",
        "customer": "Natalia Boyko",
        "item": "Noise-Cancelling Headphones Sony",
        "category": "Audio",
        "quantity": 1,
        "unit_price": 11200.00,
        "amount": 10080.00,
        "status": "cancelled",
    },
    {
        "id": "ORD-1006",
        "customer": "Anna Koval",
        "item": "Laptop Stand Aluminum",
        "category": "Accessories",
        "quantity": 2,
        "unit_price": 1950.00,
        "amount": 3900.00,
        "status": "shipped",
    },
    {
        "id": "ORD-1007",
        "customer": "Dmytro Tkachenko",
        "item": "Laptop ThinkPad X1 Carbon",
        "category": "Laptops",
        "quantity": 1,
        "unit_price": 62000.00,
        "amount": 55800.00,
        "status": "paid",
    },
    {
        "id": "ORD-1008",
        "customer": "Oleh Melnyk",
        "item": "Studio Microphone RODE NT-USB",
        "category": "Audio",
        "quantity": 1,
        "unit_price": 7600.00,
        "amount": 7600.00,
        "status": "new",
    },
]


def generate_synthetic_orders(count: int) -> list[OrderRecord]:
    """Generate a large synthetic dataset of orders for complexity benchmarking."""
    customers = (
        "Anna Koval",
        "Oleh Melnyk",
        "Iryna Bondar",
        "Andrii Shevchenko",
        "Natalia Boyko",
        "Dmytro Tkachenko",
    )
    threshold, discount_rate = DISCOUNT_RULE

    return [
        {
            "id": f"ORD-{i:06d}",
            "customer": customers[i % len(customers)],
            "item": f"Product Item #{i % 200}",
            "category": PRODUCT_CATEGORIES[i % len(PRODUCT_CATEGORIES)],
            "quantity": (i % 5) + 1,
            "unit_price": float(((i % 40) + 1) * 500),
            "amount": round(
                (((i % 5) + 1) * float(((i % 40) + 1) * 500))
                * (
                    (1.0 - discount_rate)
                    if (((i % 5) + 1) * float(((i % 40) + 1) * 500)) >= threshold
                    else 1.0
                ),
                2,
            ),
            "status": VALID_STATUSES[i % len(VALID_STATUSES)],
        }
        for i in range(1, count + 1)
    ]
```

### 5.2. Файл `src/data_processor/decorators.py` (Пояснення Decorators та `deque`)

Декоратор — це функція вищого порядку, яка приймає функцію `func` і повертає нову функцію-обгортку `wrapper`, розширюючи поведінку без зміни основного коду. Використання `@wraps(func)` із модуля `functools` зберігає метадані оригінальної функції (`__name__`, `__doc__`, анотації типів). У модулі реалізовано:
- `@measure_time` — вимірює час виконання через `perf_counter()`, записує результат у `OPERATION_HISTORY` (`deque`) та виводить у консоль;
- `@log_call` — фіксує факт виклику функції в історії операцій;
- `@repeat(count)` — параметризований декоратор (фабрика декораторів, що використовує три рівні вкладеності, `closure`, `*args` та `**kwargs`).

```python
"""Decorators and operation history tracking using collections.deque."""

from collections import deque
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

# Bounded double-ended queue storing the history of the last 15 executed operations
OPERATION_HISTORY: deque[str] = deque(maxlen=15)


def record_operation(entry: str) -> None:
    """Append an operation entry to the bounded history deque."""
    OPERATION_HISTORY.append(entry)


def get_operation_history() -> list[str]:
    """Return a snapshot list of recorded operations from the deque."""
    return list(OPERATION_HISTORY)


def clear_operation_history() -> None:
    """Clear all entries from the operation history deque."""
    OPERATION_HISTORY.clear()


def measure_time(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that measures and prints function execution time."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - start
        message = f"{func.__name__}: {elapsed:.8f} s"
        record_operation(message)
        print(message)
        return result

    return wrapper


def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that logs function invocation and records it in history."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        record_operation(f"Called {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def repeat(count: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Parameterized decorator that executes the wrapped function `count` times."""
    if count <= 0:
        raise ValueError("Repeat count must be a positive integer.")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result: Any = None
            for _ in range(count):
                result = func(*args, **kwargs)
            record_operation(f"Repeated {func.__name__} x{count}")
            return result  # type: ignore[no-any-return]

        return wrapper

    return decorator
```

### 5.3. Файл `src/data_processor/processors.py` (Comprehensions, `Counter`, `defaultdict`)

У цьому модулі реалізовано всі три види comprehensions:
- **Set comprehension:** `{str(order["category"]) for order in orders}` у `get_unique_categories`;
- **Dict comprehension:** `{str(order["id"]).upper(): order for order in orders}` у `create_order_index`;
- **List comprehension:** `[item for item in items if predicate(item)]` у `filter_items`, `filter_by_status`, `filter_by_min_amount`.

```python
"""Collection processing functions: indexing, searching, filtering, grouping, and sets."""

from collections import Counter, defaultdict
from collections.abc import Callable

from data_processor.data import OrderRecord
from data_processor.decorators import log_call


@log_call
def get_unique_statuses(orders: list[OrderRecord]) -> set[str]:
    """Return a set of unique order statuses using a set comprehension."""
    return {str(order["status"]) for order in orders}


@log_call
def get_unique_categories(orders: list[OrderRecord]) -> set[str]:
    """Return a set of unique product categories using a set comprehension."""
    return {str(order["category"]) for order in orders}


@log_call
def get_unique_customers(orders: list[OrderRecord]) -> set[str]:
    """Return a set of unique customer names using a set comprehension."""
    return {str(order["customer"]) for order in orders}


def analyze_customer_segments(orders: list[OrderRecord]) -> dict[str, set[str]]:
    """Demonstrate set operations (union, intersection, difference, symmetric diff)."""
    paid_customers = {
        str(order["customer"])
        for order in orders
        if order["status"] == "paid"
    }
    shipped_customers = {
        str(order["customer"])
        for order in orders
        if order["status"] == "shipped"
    }
    return {
        "paid_or_shipped_union": paid_customers | shipped_customers,
        "both_paid_and_shipped_intersection": paid_customers & shipped_customers,
        "paid_only_difference": paid_customers - shipped_customers,
        "exclusive_status_symmetric_diff": paid_customers ^ shipped_customers,
    }


@log_call
def create_order_index(orders: list[OrderRecord]) -> dict[str, OrderRecord]:
    """Build a dict index mapping order_id -> order using a dict comprehension."""
    return {str(order["id"]).upper(): order for order in orders}


def find_order_linear(
    orders: list[OrderRecord],
    order_id: str,
) -> OrderRecord | None:
    """Find an order by ID using linear scan in a list — O(n) time complexity."""
    target = order_id.strip().upper()
    for order in orders:
        if str(order["id"]).upper() == target:
            return order
    return None


def find_order_by_index(
    order_index: dict[str, OrderRecord],
    order_id: str,
) -> OrderRecord | None:
    """Find an order by ID using a pre-built dict index — O(1) average complexity."""
    return order_index.get(order_id.strip().upper())


@log_call
def filter_by_status(
    orders: list[OrderRecord],
    status: str,
) -> list[OrderRecord]:
    """Filter orders matching the given status using a list comprehension."""
    normalized = status.strip().lower()
    return [
        order
        for order in orders
        if str(order["status"]).lower() == normalized
    ]


@log_call
def filter_by_min_amount(
    orders: list[OrderRecord],
    min_amount: float,
) -> list[OrderRecord]:
    """Filter orders with amount >= min_amount using a list comprehension."""
    return [
        order
        for order in orders
        if float(order["amount"]) >= min_amount
    ]


@log_call
def filter_items(
    items: list[OrderRecord],
    predicate: Callable[[OrderRecord], bool],
) -> list[OrderRecord]:
    """Universal higher-order filtering function accepting any predicate."""
    return [item for item in items if predicate(item)]


@log_call
def group_orders_by_status(
    orders: list[OrderRecord],
) -> dict[str, list[OrderRecord]]:
    """Group orders by status using collections.defaultdict(list)."""
    result: defaultdict[str, list[OrderRecord]] = defaultdict(list)
    for order in orders:
        result[str(order["status"])].append(order)
    return dict(result)


@log_call
def group_orders_by_category(
    orders: list[OrderRecord],
) -> dict[str, list[OrderRecord]]:
    """Group orders by product category using collections.defaultdict(list)."""
    result: defaultdict[str, list[OrderRecord]] = defaultdict(list)
    for order in orders:
        result[str(order["category"])].append(order)
    return dict(result)


@log_call
def group_orders_nested(
    orders: list[OrderRecord],
) -> dict[str, dict[str, list[OrderRecord]]]:
    """Perform nested grouping of orders: category -> status -> list of orders."""
    nested: defaultdict[str, defaultdict[str, list[OrderRecord]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for order in orders:
        category = str(order["category"])
        status = str(order["status"])
        nested[category][status].append(order)
    return {cat: dict(status_map) for cat, status_map in nested.items()}


@log_call
def count_orders_by_status(orders: list[OrderRecord]) -> Counter[str]:
    """Count occurrences of each order status using collections.Counter."""
    return Counter(str(order["status"]) for order in orders)


@log_call
def count_orders_by_category(orders: list[OrderRecord]) -> Counter[str]:
    """Count occurrences of each product category using collections.Counter."""
    return Counter(str(order["category"]) for order in orders)
```

### 5.4. Файл `src/data_processor/analytics.py` (`*args`, `**kwargs`, `lambda`, Closure, Pipeline, Benchmark)

**Пояснення Closure у проєкті:**
Функція `create_min_amount_filter(minimum_amount: float)` створює та повертає вкладену функцію `predicate(order: OrderRecord) -> bool`. Навіть після завершення виконання `create_min_amount_filter(10000.0)` внутрішня функція `predicate` зберігає у своєму замиканні (`__closure__`) посилання на нелокальну змінну `minimum_amount = 10000.0`. Це дозволяє передавати налаштований предикат в універсальну функцію вищого порядку `filter_items(dataset, is_high_value)`.

```python
"""Analytics, aggregations, closures, *args/**kwargs, pipelines, and benchmarking."""

from collections.abc import Callable
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from data_processor.data import (
    DISCOUNT_RULE,
    OrderRecord,
    generate_synthetic_orders,
)
from data_processor.decorators import log_call, measure_time, repeat
from data_processor.processors import (
    count_orders_by_category,
    count_orders_by_status,
    create_order_index,
    find_order_by_index,
    find_order_linear,
    get_unique_categories,
    get_unique_customers,
)


def _get_relevant_orders(
    orders: list[OrderRecord],
    active_only: bool = True,
) -> list[OrderRecord]:
    """Return non-cancelled orders when active_only is True, otherwise all orders."""
    if not active_only:
        return orders
    return [order for order in orders if order["status"] != "cancelled"]


@measure_time
def calculate_total_revenue(
    orders: list[OrderRecord],
    active_only: bool = True,
) -> float:
    """Calculate total order revenue using a generator expression."""
    relevant = _get_relevant_orders(orders, active_only=active_only)
    return round(sum(float(order["amount"]) for order in relevant), 2)


@measure_time
def calculate_average_order(
    orders: list[OrderRecord],
    active_only: bool = True,
) -> float:
    """Calculate average order amount using a generator expression."""
    relevant = _get_relevant_orders(orders, active_only=active_only)
    if not relevant:
        return 0.0
    total = sum(float(order["amount"]) for order in relevant)
    return round(total / len(relevant), 2)


def find_most_expensive_order(
    orders: list[OrderRecord],
    active_only: bool = True,
) -> OrderRecord | None:
    """Find the order with the largest amount using max() and a lambda key."""
    relevant = _get_relevant_orders(orders, active_only=active_only)
    if not relevant:
        return None
    return max(relevant, key=lambda order: float(order["amount"]))


def get_amount_bounds(
    orders: list[OrderRecord],
    active_only: bool = True,
) -> tuple[float, float]:
    """Return a tuple (min_amount, max_amount) across orders."""
    relevant = _get_relevant_orders(orders, active_only=active_only)
    if not relevant:
        return (0.0, 0.0)
    lowest = min(relevant, key=lambda order: float(order["amount"]))
    highest = max(relevant, key=lambda order: float(order["amount"]))
    return (float(lowest["amount"]), float(highest["amount"]))


@log_call
def sort_orders_by_amount(
    orders: list[OrderRecord],
    reverse: bool = True,
) -> list[OrderRecord]:
    """Sort orders by amount using sorted() and a lambda function."""
    return sorted(
        orders,
        key=lambda order: float(order["amount"]),
        reverse=reverse,
    )


@log_call
def sort_items(
    items: list[OrderRecord],
    key_func: Callable[[OrderRecord], Any],
    reverse: bool = True,
) -> list[OrderRecord]:
    """Universal higher-order sorting function accepting any key function."""
    return sorted(items, key=key_func, reverse=reverse)


def calculate_average_values(*values: float) -> float:
    """Calculate arithmetic mean of an arbitrary number of positional arguments (*args)."""
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def create_record(**fields: Any) -> OrderRecord:
    """Create a structured dictionary record from arbitrary keyword arguments (**kwargs)."""
    record: OrderRecord = dict(fields)
    if (
        "amount" not in record
        and "quantity" in record
        and "unit_price" in record
    ):
        raw_total = float(record["quantity"]) * float(record["unit_price"])
        threshold, discount_rate = DISCOUNT_RULE
        multiplier = (1.0 - discount_rate) if raw_total >= threshold else 1.0
        record["amount"] = round(raw_total * multiplier, 2)
    return record


def create_min_amount_filter(
    minimum_amount: float,
) -> Callable[[OrderRecord], bool]:
    """Closure that captures `minimum_amount` and returns a filter predicate."""

    def predicate(order: OrderRecord) -> bool:
        return float(order["amount"]) >= minimum_amount

    return predicate


def create_category_filter(
    allowed_categories: set[str],
    active_only: bool = True,
) -> Callable[[OrderRecord], bool]:
    """Closure that captures a set of categories and active flag for fast O(1) filtering."""
    normalized = {cat.strip().lower() for cat in allowed_categories}

    def predicate(order: OrderRecord) -> bool:
        if active_only and order["status"] == "cancelled":
            return False
        return str(order["category"]).lower() in normalized

    return predicate


@log_call
def run_pipeline(
    items: list[OrderRecord],
    *steps: Callable[[list[OrderRecord]], list[OrderRecord]],
) -> list[OrderRecord]:
    """Execute a sequential data transformation pipeline over `items` using *args."""
    current = list(items)
    for step in steps:
        current = step(current)
    return current


@repeat(2)
def verify_pipeline_integrity(items: list[OrderRecord]) -> int:
    """Demonstrate the parameterized @repeat decorator by verifying record count."""
    return len(items)


def build_summary_report(orders: list[OrderRecord]) -> dict[str, Any]:
    """Build a structured analytical summary dictionary suitable for JSON export."""
    min_amount, max_amount = get_amount_bounds(orders, active_only=True)
    best_order = find_most_expensive_order(orders, active_only=True)
    return {
        "total_orders": len(orders),
        "unique_customers_count": len(get_unique_customers(orders)),
        "unique_categories": sorted(get_unique_categories(orders)),
        "total_active_revenue": calculate_total_revenue(orders, active_only=True),
        "average_active_order": calculate_average_order(orders, active_only=True),
        "min_active_amount": min_amount,
        "max_active_amount": max_amount,
        "most_expensive_order_id": best_order["id"] if best_order else None,
        "orders_by_status": dict(count_orders_by_status(orders)),
        "orders_by_category": dict(count_orders_by_category(orders)),
    }


def export_summary_to_json(
    orders: list[OrderRecord],
    output_path: str | Path,
) -> Path:
    """Export the analytical summary report to a formatted JSON file."""
    destination = Path(output_path)
    summary = build_summary_report(orders)
    destination.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination


def run_search_benchmark(
    sizes: tuple[int, ...] = (1_000, 10_000, 100_000),
    lookups: int = 500,
) -> list[dict[str, float | int]]:
    """Compare O(n) list search vs O(1) dict/set lookup across dataset sizes."""
    results: list[dict[str, float | int]] = []

    for size in sizes:
        dataset = generate_synthetic_orders(size)
        target_id = f"ORD-{size:06d}"

        idx_start = perf_counter()
        index = create_order_index(dataset)
        index_build_sec = perf_counter() - idx_start

        list_start = perf_counter()
        for _ in range(lookups):
            find_order_linear(dataset, target_id)
        list_search_sec = perf_counter() - list_start

        dict_start = perf_counter()
        for _ in range(lookups):
            find_order_by_index(index, target_id)
        dict_search_sec = perf_counter() - dict_start

        id_list = [str(item["id"]) for item in dataset]
        id_set = set(id_list)

        set_start = perf_counter()
        for _ in range(lookups):
            _ = target_id in id_set
        set_lookup_sec = perf_counter() - set_start

        speedup = (
            round(list_search_sec / dict_search_sec, 1)
            if dict_search_sec > 0
            else 0.0
        )

        results.append(
            {
                "records": size,
                "lookups": lookups,
                "list_search_s": round(list_search_sec, 6),
                "dict_search_s": round(dict_search_sec, 6),
                "set_lookup_s": round(set_lookup_sec, 6),
                "index_build_s": round(index_build_sec, 6),
                "speedup_x": speedup,
            }
        )

    return results
```

---

## 6. Результат роботи програми (`python -m data_processor.main --demo`)

```text
=== Order Data Processor (Variant 7) - Laboratory Work No. 2 ===
Warehouse hub coordinates (tuple): (49.8397, 24.0297) | Allowed statuses (tuple): ('new', 'paid', 'shipped', 'cancelled') | Discount rule: 10% from 10000 UAH

1. All Structured Orders (list[dict])
----------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                 Category       Qty  Amount (UAH) Status    
----------------------------------------------------------------------------------------------------------------
ORD-1001   Anna Koval           Mechanical Keyboard Keychron K8      Peripherals      2       8400.00 paid      
ORD-1002   Oleh Melnyk          Monitor Dell UltraSharp 27           Monitors         1      14850.00 shipped   
ORD-1003   Iryna Bondar         Wireless Mouse Logitech MX Master 3S Peripherals      3      12150.00 new       
ORD-1004   Andrii Shevchenko    USB-C Docking Station                Accessories      1       3800.00 paid      
ORD-1005   Natalia Boyko        Noise-Cancelling Headphones Sony     Audio            1      10080.00 cancelled 
ORD-1006   Anna Koval           Laptop Stand Aluminum                Accessories      2       3900.00 shipped   
ORD-1007   Dmytro Tkachenko     Laptop ThinkPad X1 Carbon            Laptops          1      55800.00 paid      
ORD-1008   Oleh Melnyk          Studio Microphone RODE NT-USB        Audio            1       7600.00 new       
----------------------------------------------------------------------------------------------------------------

2. Unique Sets & Set Operations:
   Unique categories (set): ['Accessories', 'Audio', 'Laptops', 'Monitors', 'Peripherals']
   Unique statuses (set):   ['cancelled', 'new', 'paid', 'shipped']
   Unique customers (set):  ['Andrii Shevchenko', 'Anna Koval', 'Dmytro Tkachenko', 'Iryna Bondar', 'Natalia Boyko', 'Oleh Melnyk']
   Paid OR Shipped (union):         ['Andrii Shevchenko', 'Anna Koval', 'Dmytro Tkachenko', 'Oleh Melnyk']
   Paid AND Shipped (intersection): ['Anna Koval']

3. Aggregations & Decorator Timing (@measure_time):
calculate_total_revenue: 0.00001180 s
calculate_average_order: 0.00000450 s
   Total active revenue:  106500.00 UAH
   Average active check:  15214.29 UAH
   Active amount bounds:  min=3800.00 UAH, max=55800.00 UAH
   Most expensive order:  ORD-1007 | Dmytro Tkachenko | Laptop ThinkPad X1 Carbon | 55800.00 UAH

4. Orders Sorted by Amount Descending (lambda)
----------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                 Category       Qty  Amount (UAH) Status    
----------------------------------------------------------------------------------------------------------------
ORD-1007   Dmytro Tkachenko     Laptop ThinkPad X1 Carbon            Laptops          1      55800.00 paid      
ORD-1002   Oleh Melnyk          Monitor Dell UltraSharp 27           Monitors         1      14850.00 shipped   
ORD-1003   Iryna Bondar         Wireless Mouse Logitech MX Master 3S Peripherals      3      12150.00 new       
ORD-1005   Natalia Boyko        Noise-Cancelling Headphones Sony     Audio            1      10080.00 cancelled 
ORD-1001   Anna Koval           Mechanical Keyboard Keychron K8      Peripherals      2       8400.00 paid      
ORD-1008   Oleh Melnyk          Studio Microphone RODE NT-USB        Audio            1       7600.00 new       
ORD-1006   Anna Koval           Laptop Stand Aluminum                Accessories      2       3900.00 shipped   
ORD-1004   Andrii Shevchenko    USB-C Docking Station                Accessories      1       3800.00 paid      
----------------------------------------------------------------------------------------------------------------

5. Statistics via collections.Counter:
   Orders by status:   {'paid': 3, 'shipped': 2, 'new': 2, 'cancelled': 1}
   Orders by category: {'Peripherals': 2, 'Monitors': 1, 'Accessories': 2, 'Audio': 2, 'Laptops': 1}

6. Grouping via collections.defaultdict (by category):
   Peripherals   -> 2 order(s)
   Monitors      -> 1 order(s)
   Accessories   -> 2 order(s)
   Audio         -> 2 order(s)
   Laptops       -> 1 order(s)

7. Nested Grouping (category -> status -> count):
   Peripherals   -> { paid: 1, new: 1 }
   Monitors      -> { shipped: 1 }
   Accessories   -> { paid: 1, shipped: 1 }
   Audio         -> { cancelled: 1, new: 1 }
   Laptops       -> { paid: 1 }

8. Search by Order ID (ORD-1002):
   Dict index O(1):  {'id': 'ORD-1002', 'customer': 'Oleh Melnyk', 'item': 'Monitor Dell UltraSharp 27', 'category': 'Monitors', 'quantity': 1, 'unit_price': 16500.0, 'amount': 14850.0, 'status': 'shipped'}
   Linear scan O(n): ORD-1002

9. Filtered via Closure & Universal Filter (amount >= 10,000 UAH)
----------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                 Category       Qty  Amount (UAH) Status    
----------------------------------------------------------------------------------------------------------------
ORD-1002   Oleh Melnyk          Monitor Dell UltraSharp 27           Monitors         1      14850.00 shipped   
ORD-1003   Iryna Bondar         Wireless Mouse Logitech MX Master 3S Peripherals      3      12150.00 new       
ORD-1005   Natalia Boyko        Noise-Cancelling Headphones Sony     Audio            1      10080.00 cancelled 
ORD-1007   Dmytro Tkachenko     Laptop ThinkPad X1 Carbon            Laptops          1      55800.00 paid      
----------------------------------------------------------------------------------------------------------------

10. Pipeline Processing Result (4 records verified via @repeat(2))
----------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                 Category       Qty  Amount (UAH) Status    
----------------------------------------------------------------------------------------------------------------
ORD-1007   Dmytro Tkachenko     Laptop ThinkPad X1 Carbon            Laptops          1      55800.00 paid      
ORD-1002   Oleh Melnyk          Monitor Dell UltraSharp 27           Monitors         1      14850.00 shipped   
ORD-1003   Iryna Bondar         Wireless Mouse Logitech MX Master 3S Peripherals      3      12150.00 new       
ORD-1001   Anna Koval           Mechanical Keyboard Keychron K8      Peripherals      2       8400.00 paid      
----------------------------------------------------------------------------------------------------------------

11. Average via *args: 22800.00 UAH
12. Created record via **kwargs (with auto-discount): {'id': 'ORD-1009', 'customer': 'Taras Novak', 'item': '4K Webcam Logitech Brio', 'category': 'Peripherals', 'quantity': 2, 'unit_price': 6200.0, 'status': 'paid', 'amount': 11160.0}
calculate_total_revenue: 0.00000350 s
calculate_average_order: 0.00000320 s

13. Summary Report Keys: ['total_orders', 'unique_customers_count', 'unique_categories', 'total_active_revenue', 'average_active_order', 'min_active_amount', 'max_active_amount', 'most_expensive_order_id', 'orders_by_status', 'orders_by_category']
```

---

## 7. Аналіз часової складності операцій та результати Benchmark

### 7.1. Теоретична оцінка складності реалізованих операцій

| Операція у проєкті | Реалізація | Середня складність | Пояснення |
| :--- | :--- | :---: | :--- |
| **Лінійний пошук у `list`** (`find_order_linear`) | `for order in orders: if order["id"] == target` | $O(n)$ | У гіршому випадку переглядаються всі $n$ елементів списку. |
| **Побудова `dict`-індексу** (`create_order_index`) | `{order["id"]: order for order in orders}` | $O(n)$ | Одноразовий прохід по $n$ записах із вставкою у хеш-таблицю за $O(1)$. |
| **Пошук за ключем у `dict`** (`find_order_by_index`) | `order_index.get(order_id)` | $O(1)$ | Обчислення хешу ключа та прямий доступ до комірки хеш-таблиці не залежать від $n$. |
| **Перевірка входження у `set`** | `category in allowed_categories` | $O(1)$ | Множина базується на хеш-таблиці, тому перевірка належності виконується за сталий час. |
| **Сортування замовлень** (`sort_orders_by_amount`) | `sorted(orders, key=lambda o: o["amount"])` | $O(n \log n)$ | Алгоритм Timsort виконує $O(n \log n)$ порівнянь у середньому та гіршому випадках. |

### 7.2. Експериментальна частина (Benchmark: 500 пошукових запитів)

| Кількість records | `list` search $O(n)$ (500 запитів) | `dict` search $O(1)$ (500 запитів) | `set` lookup $O(1)$ (500 запитів) | Побудова `dict` index $O(n)$ | Прискорення (`list` / `dict`) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| **1 000** | 0.054444 s | 0.000066 s | 0.000017 s | 0.000151 s | **822.4x** |
| **10 000** | 0.604365 s | 0.000095 s | 0.000019 s | 0.002929 s | **6 355.0x** |
| **100 000** | 7.847244 s | 0.000106 s | 0.000044 s | 0.038022 s | **74 311.0x** |

**Висновок із результатів бенчмарку:**
- При збільшенні розміру вибірки у **10 разів** (з 1 000 до 10 000 і з 10 000 до 100 000 записів) час лінійного пошуку в `list` зростає пропорційно до $n$ (приблизно у 11–13 разів: `0.054 s` $\to$ `0.604 s` $\to$ `7.847 s`), що повністю підтверджує лінійну асимптотичну складність $O(n)$.
- Час пошуку за ключем у `dict` (`0.000066 s` $\to$ `0.000095 s` $\to$ `0.000106 s`) та перевірки входження у `set` залишається практично незмінним незалежно від кількості записів, що підтверджує константну середню складність $O(1)$.
- Навіть з урахуванням одноразових витрат на побудову індексу (`0.038 s` для 100 000 записів), використання `dict`-індексу окупається вже після 3–4 пошукових запитів, а на 500 запитах дає прискорення у **понад 74 000 разів**.

---

## 8. Відповіді на контрольні запитання

1. **Що таке `list`?** — Впорядкована змінювана (`mutable`) динамічна колекція об'єктів довільних типів, реалізована як динамічний масив посилань.
2. **Чим `list` відрізняється від `tuple`?** — `list` є змінюваним (підтримує додавання, видалення, заміну елементів), а `tuple` — незмінюваним (`immutable`), займає менше пам'яті і може бути ключем у `dict` (якщо всі його елементи hashable).
3. **Чому `tuple` називається immutable?** — Тому що після створення кортежу неможливо змінити кількість його елементів або переприсвоїти посилання за індексом.
4. **Для чого використовується `set`?** — Для зберігання унікальних елементів, швидкого видалення дублікатів, перевірки належності за $O(1)$ та виконання операцій над множинами (об'єднання, перетин, різниця).
5. **Яка властивість елементів `set` є важливою?** — Кожен елемент множини обов'язково повинен бути хешованим (`hashable`), а всі елементи в множині є унікальними.
6. **Що таке `dict`?** — Вбудована асоціативна структура даних (хеш-таблиця), яка зберігає пари `key -> value` з унікальними хешованими ключами.
7. **Що таке key-value structure?** — Спосіб організації даних, за якого доступ до значення (`value`) здійснюється не за числовим позиційним індексом, а за унікальним ідентифікатором — ключем (`key`).
8. **Чому пошук `key` у `dict` зазвичай швидкий?** — Завдяки хеш-таблиці: Python обчислює `hash(key)` і за $O(1)$ одразу визначає індекс комірки в пам'яті без перебору всіх елементів.
9. **Що таке hashability?** — Властивість об'єкта мати незмінне протягом життєвого циклу цілочисельне хеш-значення (`__hash__`) та підтримувати порівняння на рівність (`__eq__`).
10. **Чому `list` не може бути `key` у `dict`?** — Тому що `list` є змінюваним (`mutable`): якби його вміст змінився після вставки у словник, змінився б і його хеш, що порушило б інваріант хеш-таблиці та зробило елемент недоступним.
11. **Для чого використовується `Counter`?** — Підклас `dict` із модуля `collections` для швидкого підрахунку кількості входжень хешованих об'єктів та пошуку найчастіших елементів (`most_common()`).
12. **Для чого використовується `defaultdict`?** — Підклас `dict`, який при зверненні до неіснуючого ключа автоматично викликає фабричну функцію (наприклад, `list`, `int`, `set`) для створення значення за замовчуванням, що дуже зручно для групування.
13. **Для чого використовується `deque`?** — Двостороння черга з модуля `collections`, оптимізована для додавання і видалення елементів з обох кінців (`append`, `appendleft`, `pop`, `popleft`) за час $O(1)$, а також для зберігання останніх $N$ операцій (`maxlen=N`).
14. **Що таке list comprehension?** — Компактна декларативна синтаксична конструкція `[expr for item in iterable if cond]` для створення нового списку на основі ітерованого об'єкта.
15. **Що таке set comprehension?** — Синтаксична конструкція `{expr for item in iterable if cond}`, яка створює нову множину (`set`) унікальних значень.
16. **Що таке dict comprehension?** — Синтаксична конструкція `{key_expr: val_expr for item in iterable if cond}` для генерації словника (`dict`), наприклад для побудови пошукових індексів.
17. **Що таке generator expression?** — Вираз у круглих дужках `(expr for item in iterable if cond)`, який обчислює елементи ліниво (по одному на вимогу) і не створює проміжний список у пам'яті.
18. **Що означає $O(1)$?** — Константна часова складність: час виконання операції не залежить від кількості елементів $n$ у колекції.
19. **Що означає $O(n)$?** — Лінійна часова складність: час виконання зростає прямо пропорційно до кількості елементів $n$.
20. **Що означає $O(n \log n)$?** — Квазілінійна складність, характерна для ефективних алгоритмів сортування порівняннями (зокрема Timsort у Python `sort()` / `sorted()`).
21. **Що означає $O(n^2)$?** — Квадратична складність: при збільшенні вхідних даних у 10 разів кількість операцій зростає у 100 разів (характерна для вкладених циклів по тій самій колекції).
22. **Яка приблизна складність пошуку у `list`?** — $O(n)$ у середньому та гіршому випадках, оскільки потрібне послідовне порівняння елементів.
23. **Яка середня складність пошуку у `set`?** — $O(1)$ у середньому завдяки хеш-таблиці.
24. **Яка середня складність пошуку `key` у `dict`?** — $O(1)$ у середньому завдяки хешуванню ключів.
25. **Чому правильна структура даних може прискорити програму?** — Заміна лінійного пошуку в `list` ($O(n)$) на пошук у `dict` або `set` ($O(1)$) при багаторазових запитах усуває вузьке місце алгоритму і прискорює виконання в тисячі разів на великих обсягах даних.
26. **Що таке функціональна декомпозиція?** — Поділ складної програми або задачі обробки даних на невеликі ізольовані функції, кожна з яких виконує рівно одну чітко визначену логічну операцію.
27. **Які переваги малих functions?** — Висока читабельність, простота модульного тестування (`pytest`), відсутність дублювання коду, легкість повторного використання та комбінування у конвеєри (`pipelines`).
28. **Що таке positional argument?** — Аргумент функції, який прив'язується до параметра за своєю позицією (порядковим місцем) у виклику функції.
29. **Що таке keyword argument?** — Іменований аргумент, який передається у форматі `param_name=value`, що робить виклик самодокументованим і незалежним від порядку іменованих аргументів.
30. **Для чого використовується `*args`?** — Дозволяє функції приймати довільну кількість позиційних аргументів, які всередині функції упаковуються в кортеж (`tuple`).
31. **Для чого використовується `**kwargs`?** — Дозволяє функції приймати довільну кількість іменованих аргументів, які всередині функції упаковуються у словник (`dict[str, Any]`).
32. **Що таке `lambda` function?** — Коротка однорядкова анонімна функція вигляду `lambda params: expression`, яка повертає результат обчислення виразу.
33. **Де доцільно використовувати `lambda`?** — Як компактний аргумент `key` або `predicate` у функціях вищого порядку (`sorted()`, `max()`, `min()`, `filter_items()`) для простих однорядкових правил.
34. **Чому складну business logic не варто записувати в `lambda`?** — Тому що `lambda` не має власного імені у трасуванні стеків помилок (`<lambda>`), не підтримує docstrings, багаторядкові інструкції та погіршує читабельність коду.
35. **Що таке `closure`?** — Вкладена функція, яка запам'ятовує і зберігає доступ до змінних лексичної області видимості зовнішньої функції (`enclosing scope`) навіть після того, як зовнішня функція завершила виконання.
36. **Які variables може пам'ятати `closure`?** — Параметри та локальні змінні зовнішньої функції (`nonlocal` / `free variables`), які використовуються всередині вкладеної функції (наприклад, поріг `minimum_amount`).
37. **Що таке `decorator`?** — Функція вищого порядку (або клас), що приймає функцію як аргумент і повертає нову обгорнуту функцію, додаючи наскрізну поведінку без модифікації вихідного коду самої функції.
38. **Для чого застосовуються `decorators`?** — Для логування викликів, профілювання часу виконання (`@measure_time`), кешування, перевірки прав доступу, валідації аргументів та повторних спроб (`@repeat`).
39. **Для чого використовується `functools.wraps`?** — Копіює службові атрибути оригінальної функції (`__name__`, `__doc__`, `__qualname__`, `__annotations__`, `__wrapped__`) на функцію-обгортку `wrapper` усередині декоратора.
40. **Чому потрібно оцінювати складність алгоритму?** — Щоб передбачити масштабованість програми при зростанні обсягу даних ($10^3 \to 10^5 \to 10^7$ записів) і запобігти деградації продуктивності ще на етапі проєктування.

---

## 9. Висновок

У ході виконання лабораторної роботи №2 було розроблено модуль обробки структурованих даних замовлень інтернет-магазину (`data_processor`, **Варіант №7**, узгоджений із Лабораторною роботою №1). Програму декомпозовано на окремі модулі (`data.py`, `decorators.py`, `processors.py`, `analytics.py`, `main.py`) та протестовано за допомогою `pytest`, `ruff` і `mypy --strict`. У проєкті практично застосовано вбудовані колекції (`list`, `tuple`, `set`, `dict`), спеціалізовані структури з модуля `collections` (`Counter`, `defaultdict`, `deque`), генератори колекцій (`list/set/dict comprehensions` та `generator expressions`), `*args`, `**kwargs`, `lambda`-функції, замикання (`closures`), звичайні та параметризовані декоратори (`@measure_time`, `@log_call`, `@repeat`), а також проведено експериментальне дослідження складності операцій на вибірках до 100 000 записів, яке наочно підтвердило перевагу хеш-індексації $O(1)$ над лінійним пошуком $O(n)$ (прискорення у понад 74 000 разів).
