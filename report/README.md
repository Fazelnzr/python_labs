# ЗВІТ З ЛАБОРАТОРНОЇ РОБОТИ №1

**Дисципліна:** «Професійний Python»  
**Тема:** Організація професійного Python-проєкту та Git  
**Варіант:** №7 — Система управління замовленнями інтернет-магазину (`order_manager`)  
**Виконав:** студент Назар Поцелуйко  

---

## 1. Мета роботи

Ознайомитися з основними принципами організації професійного Python-проєкту, навчитися створювати ізольоване віртуальне середовище розробки (`.venv`), формувати структуру проєкту за принципом `src-layout`, працювати з модулями та пакетами Python, створювати конфігураційний файл `pyproject.toml`, використовувати систему контролю версій Git для фіксації логічних етапів розробки та оформлювати базову документацію проєкту (`README.md`).

---

## 2. Індивідуальне завдання (Варіант №7)

### Постановка задачі (Варіант №7 — Система управління замовленнями)

Для кожного замовлення (`Order`) необхідно зберігати:
- унікальний номер замовлення (`order_id: str`, наприклад, `"ORD-1001"`);
- ім'я та прізвище клієнта (`customer_name: str`);
- назву товару (`item_name: str`);
- кількість одиниць товару (`quantity: int`);
- ціну за одиницю (`unit_price: float`);
- статус замовлення (`status: str`: `"new"`, `"paid"`, `"shipped"`, `"cancelled"`).

**Необхідно реалізувати:**
1. Модель даних на базі `@dataclass` з автоматичною валідацією полів у `__post_init__` та обчислюваними властивостями (`@property`): загальна сума (`total_price`), розмір знижки (`discount_amount` — 10% для замовлень від 10 000 грн) та підсумкова сума до сплати (`final_price`).
2. Кастомну ієрархію винятків (`OrderError`, `OrderValidationError`, `OrderNotFoundError`, `DuplicateOrderError`).
3. Модуль бізнес-логіки (`services.py`):
   - додавання нового замовлення з перевіркою унікальності номера (`add_order`);
   - пошук замовлення за номером (`find_order_by_id`);
   - фільтрація замовлень за статусом (`filter_by_status`);
   - багатокритеріальний пошук за клієнтом, назвою товару та мінімальною сумою (`search_orders`);
   - зміна статусу замовлення (`update_order_status`);
   - обчислення загальної виручки активних замовлень (`calculate_total_revenue`);
   - обчислення середнього чека (`calculate_average_check`);
   - пошук найдорожчого замовлення (`find_most_expensive_order`);
   - сортування замовлень за підсумковою вартістю (`sort_orders_by_price`).
4. Точку входу (`main.py`) із захистом `if __name__ == "__main__":`, демонстраційним звітом та інтерактивним консольним меню (`run_menu`) з введенням даних із клавіатури.

---

## 3. Структура проєкту (`src-layout`)

```text
Lab_1/
│
├── report/
│   ├── README.md
│   └── Lab_01_Report.docx
│
├── src/
│   └── order_manager/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── models.py
│       ├── services.py
│       └── main.py
│
├── tests/
│   └── test_services.py
│
├── .gitignore
├── README.md
└── pyproject.toml
```

### Опис створених модулів

| Файл | Призначення |
| :--- | :--- |
| `src/order_manager/__init__.py` | Ініціалізація пакета `order_manager` та метадані версії (`__version__ = "0.1.0"`). |
| `src/order_manager/exceptions.py` | Кастомні винятки предметної області (`OrderError`, `OrderValidationError`, `OrderNotFoundError`, `DuplicateOrderError`). |
| `src/order_manager/models.py` | Конфігураційні константи (`VALID_STATUSES`, `DISCOUNT_THRESHOLD`, `DISCOUNT_RATE`, `DEFAULT_CURRENCY`) та `@dataclass class Order`. |
| `src/order_manager/services.py` | Чиста бізнес-логіка обробки замовлень, пошуку, фільтрації, сортування та розрахунку фінансової статистики. |
| `src/order_manager/main.py` | Точка входу застосунку (`main()`), форматований вивід таблиць, демо-сценарій та інтерактивне CLI-меню. |
| `tests/test_services.py` | Модульні тести (`pytest`) для перевірки моделі, винятків та функцій бізнес-логіки. |

---

## 4. Лістинги основних модулів проєкту

### 4.1. Файл `src/order_manager/__init__.py`

```python
"""Order manager package for Laboratory Work No. 1 (Variant 7)."""

__version__ = "0.1.0"
```

### 4.2. Файл `src/order_manager/exceptions.py`

```python
"""Custom exceptions for the order management domain."""


class OrderError(Exception):
    """Base exception for all order-related domain errors."""


class OrderValidationError(OrderError):
    """Raised when order attributes fail business validation rules."""


class OrderNotFoundError(OrderError):
    """Raised when an order with the specified ID does not exist."""


class DuplicateOrderError(OrderError):
    """Raised when attempting to add an order with an existing ID."""
```

### 4.3. Файл `src/order_manager/models.py`

```python
"""Data models for the order management system (Variant 7)."""

from dataclasses import dataclass

from order_manager.exceptions import OrderValidationError

VALID_STATUSES: tuple[str, ...] = ("new", "paid", "shipped", "cancelled")
DISCOUNT_THRESHOLD: float = 10000.0
DISCOUNT_RATE: float = 0.10
DEFAULT_CURRENCY: str = "UAH"


@dataclass
class Order:
    """Represents a customer order in the online store."""

    order_id: str
    customer_name: str
    item_name: str
    quantity: int
    unit_price: float
    status: str = "new"

    def __post_init__(self) -> None:
        """Validate order fields immediately after initialization."""
        self.order_id = self.order_id.strip().upper()
        self.customer_name = self.customer_name.strip()
        self.item_name = self.item_name.strip()
        self.status = self.status.strip().lower()

        if not self.order_id:
            raise OrderValidationError("Order ID cannot be empty.")
        if not self.customer_name:
            raise OrderValidationError("Customer name cannot be empty.")
        if not self.item_name:
            raise OrderValidationError("Item name cannot be empty.")
        if self.quantity <= 0:
            raise OrderValidationError(
                f"Quantity must be greater than zero (got {self.quantity})."
            )
        if self.unit_price <= 0:
            raise OrderValidationError(
                f"Unit price must be greater than zero (got {self.unit_price})."
            )
        if self.status not in VALID_STATUSES:
            allowed = ", ".join(VALID_STATUSES)
            raise OrderValidationError(
                f"Invalid status '{self.status}'. Allowed statuses: {allowed}."
            )

    @property
    def total_price(self) -> float:
        """Calculate total order price before discount."""
        return round(self.quantity * self.unit_price, 2)

    @property
    def discount_amount(self) -> float:
        """Calculate discount amount if the order reaches the threshold."""
        if self.total_price >= DISCOUNT_THRESHOLD:
            return round(self.total_price * DISCOUNT_RATE, 2)
        return 0.0

    @property
    def final_price(self) -> float:
        """Calculate final payable price after applying discount."""
        return round(self.total_price - self.discount_amount, 2)
```

### 4.4. Файл `src/order_manager/services.py`

```python
"""Business logic services for managing customer orders."""

from order_manager.exceptions import (
    DuplicateOrderError,
    OrderNotFoundError,
    OrderValidationError,
)
from order_manager.models import VALID_STATUSES, Order


def find_order_by_id(
    orders: list[Order],
    order_id: str,
) -> Order | None:
    """Find an order by its unique ID (case-insensitive)."""
    normalized_id = order_id.strip().upper()
    for order in orders:
        if order.order_id == normalized_id:
            return order
    return None


def add_order(
    orders: list[Order],
    new_order: Order,
) -> Order:
    """Add a new validated order to the collection if its ID is unique."""
    if find_order_by_id(orders, new_order.order_id) is not None:
        raise DuplicateOrderError(
            f"Order with ID '{new_order.order_id}' already exists."
        )
    orders.append(new_order)
    return new_order


def filter_by_status(
    orders: list[Order],
    status: str,
) -> list[Order]:
    """Return all orders matching the specified status."""
    normalized_status = status.strip().lower()
    if normalized_status not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        raise OrderValidationError(
            f"Unknown status '{status}'. Allowed statuses: {allowed}."
        )
    return [
        order
        for order in orders
        if order.status == normalized_status
    ]


def search_orders(
    orders: list[Order],
    customer_query: str = "",
    item_query: str = "",
    min_total: float | None = None,
) -> list[Order]:
    """Search orders by multiple criteria: customer name, item name, and minimum total."""
    customer_part = customer_query.strip().lower()
    item_part = item_query.strip().lower()

    results: list[Order] = []
    for order in orders:
        if customer_part and customer_part not in order.customer_name.lower():
            continue
        if item_part and item_part not in order.item_name.lower():
            continue
        if min_total is not None and order.final_price < min_total:
            continue
        results.append(order)
    return results


def update_order_status(
    orders: list[Order],
    order_id: str,
    new_status: str,
) -> Order:
    """Update the status of an existing order."""
    normalized_status = new_status.strip().lower()
    if normalized_status not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        raise OrderValidationError(
            f"Invalid status '{new_status}'. Allowed statuses: {allowed}."
        )

    order = find_order_by_id(orders, order_id)
    if order is None:
        raise OrderNotFoundError(
            f"Order with ID '{order_id.strip().upper()}' was not found."
        )

    order.status = normalized_status
    return order


def calculate_total_revenue(
    orders: list[Order],
    active_only: bool = True,
) -> float:
    """Calculate total revenue (final price) across orders, excluding cancelled by default."""
    relevant_orders = [
        order
        for order in orders
        if not active_only or order.status != "cancelled"
    ]
    return round(sum(order.final_price for order in relevant_orders), 2)


def calculate_average_check(
    orders: list[Order],
) -> float:
    """Calculate the average final order value for non-cancelled orders."""
    active_orders = [
        order
        for order in orders
        if order.status != "cancelled"
    ]
    if not active_orders:
        return 0.0
    total = sum(order.final_price for order in active_orders)
    return round(total / len(active_orders), 2)


def find_most_expensive_order(
    orders: list[Order],
) -> Order | None:
    """Find the order with the highest final price among non-cancelled orders."""
    active_orders = [
        order
        for order in orders
        if order.status != "cancelled"
    ]
    if not active_orders:
        return None
    return max(
        active_orders,
        key=lambda order: order.final_price,
    )


def sort_orders_by_price(
    orders: list[Order],
    descending: bool = True,
) -> list[Order]:
    """Return a new list of orders sorted by final price."""
    return sorted(
        orders,
        key=lambda order: order.final_price,
        reverse=descending,
    )
```

### 4.5. Файл `src/order_manager/main.py`

```python
"""Application entry point and interactive CLI for the Order Manager."""

import sys

from order_manager.exceptions import OrderError
from order_manager.models import (
    DEFAULT_CURRENCY,
    DISCOUNT_RATE,
    DISCOUNT_THRESHOLD,
    VALID_STATUSES,
    Order,
)
from order_manager.services import (
    add_order,
    calculate_average_check,
    calculate_total_revenue,
    filter_by_status,
    find_most_expensive_order,
    find_order_by_id,
    search_orders,
    sort_orders_by_price,
    update_order_status,
)


def create_demo_orders() -> list[Order]:
    """Create initial demonstration dataset of customer orders."""
    return [
        Order(
            order_id="ORD-1001",
            customer_name="Anna Koval",
            item_name="Mechanical Keyboard Keychron K8",
            quantity=2,
            unit_price=4200.00,
            status="paid",
        ),
        Order(
            order_id="ORD-1002",
            customer_name="Oleh Melnyk",
            item_name="Monitor Dell UltraSharp 27",
            quantity=1,
            unit_price=16500.00,
            status="shipped",
        ),
        Order(
            order_id="ORD-1003",
            customer_name="Iryna Bondar",
            item_name="Wireless Mouse Logitech MX Master 3S",
            quantity=3,
            unit_price=4500.00,
            status="new",
        ),
        Order(
            order_id="ORD-1004",
            customer_name="Andrii Shevchenko",
            item_name="USB-C Docking Station",
            quantity=1,
            unit_price=3800.00,
            status="paid",
        ),
        Order(
            order_id="ORD-1005",
            customer_name="Natalia Boyko",
            item_name="Noise-Cancelling Headphones Sony",
            quantity=1,
            unit_price=11200.00,
            status="cancelled",
        ),
    ]


def print_orders(orders: list[Order]) -> None:
    """Format and print a table of orders to the console."""
    if not orders:
        print("\nNo orders found.")
        return

    header = (
        f"{'ID':<10} {'Customer':<20} {'Item':<36} "
        f"{'Qty':>4} {'Unit':>10} {'Discount':>10} {'Final':>11} {'Status':<10}"
    )
    separator = "-" * len(header)
    print(f"\n{separator}")
    print(header)
    print(separator)
    for order in orders:
        print(
            f"{order.order_id:<10} "
            f"{order.customer_name:<20} "
            f"{order.item_name:<36} "
            f"{order.quantity:>4d} "
            f"{order.unit_price:>10.2f} "
            f"{order.discount_amount:>10.2f} "
            f"{order.final_price:>11.2f} "
            f"{order.status:<10}"
        )
    print(separator)


def print_statistics(orders: list[Order]) -> None:
    """Display summary statistics for the current list of orders."""
    total_revenue = calculate_total_revenue(orders, active_only=True)
    average_check = calculate_average_check(orders)
    best_order = find_most_expensive_order(orders)

    print("\n--- Order Statistics (Active Orders) ---")
    print(
        f"Discount rule: {int(DISCOUNT_RATE * 100)}% off for orders >= "
        f"{DISCOUNT_THRESHOLD:.2f} {DEFAULT_CURRENCY}"
    )
    print(f"Total active revenue: {total_revenue:.2f} {DEFAULT_CURRENCY}")
    print(f"Average order check:  {average_check:.2f} {DEFAULT_CURRENCY}")
    if best_order is not None:
        print(
            f"Most expensive order: {best_order.order_id} | "
            f"{best_order.customer_name} | "
            f"{best_order.final_price:.2f} {DEFAULT_CURRENCY}"
        )


def run_demo_scenario(orders: list[Order]) -> None:
    """Run a non-interactive demonstration of the core business logic."""
    print("=== Order Management System (Variant 7) - Demo Report ===")
    print_orders(orders)

    target_status = "paid"
    paid_orders = filter_by_status(orders, target_status)
    print(f"\nOrders with status '{target_status}':")
    print_orders(paid_orders)

    print_statistics(orders)

    found = find_order_by_id(orders, "ORD-1002")
    if found is not None:
        print(
            f"\nFound order by ID: {found.order_id} - "
            f"{found.customer_name} ({found.item_name}, "
            f"{found.final_price:.2f} {DEFAULT_CURRENCY})"
        )


def print_menu() -> None:
    """Print available interactive CLI commands."""
    print("\n================ ORDER MANAGER MENU ================")
    print("1. Show all orders")
    print("2. Add a new order")
    print("3. Find order by ID")
    print("4. Filter orders by status")
    print("5. Multi-criteria search (customer / item / min sum)")
    print("6. Update order status")
    print("7. Show orders sorted by final price")
    print("8. Show revenue & statistics")
    print("9. Exit")
    print("====================================================")


def handle_add_order(orders: list[Order]) -> None:
    """Prompt user for order fields and add a new order."""
    order_id = input("Enter order ID (e.g., ORD-1006): ").strip()
    customer_name = input("Enter customer full name: ").strip()
    item_name = input("Enter item name: ").strip()
    quantity_raw = input("Enter quantity (integer > 0): ").strip()
    unit_price_raw = input("Enter unit price (float > 0): ").strip()
    allowed = "/".join(VALID_STATUSES)
    status = input(f"Enter status ({allowed}) [default: new]: ").strip() or "new"

    try:
        quantity = int(quantity_raw)
        unit_price = float(unit_price_raw)
    except ValueError:
        print("Error: Quantity must be an integer and unit price must be a number.")
        return

    new_order = Order(
        order_id=order_id,
        customer_name=customer_name,
        item_name=item_name,
        quantity=quantity,
        unit_price=unit_price,
        status=status,
    )
    add_order(orders, new_order)
    print(
        f"Order '{new_order.order_id}' added successfully! "
        f"Final price: {new_order.final_price:.2f} {DEFAULT_CURRENCY}"
    )


def handle_multi_search(orders: list[Order]) -> None:
    """Prompt user for optional search filters and display matching orders."""
    customer_query = input("Customer name contains (press Enter to skip): ").strip()
    item_query = input("Item name contains (press Enter to skip): ").strip()
    min_total_raw = input("Minimum final price (press Enter to skip): ").strip()

    min_total: float | None = None
    if min_total_raw:
        try:
            min_total = float(min_total_raw)
        except ValueError:
            print("Error: Minimum price must be a valid number.")
            return

    results = search_orders(
        orders,
        customer_query=customer_query,
        item_query=item_query,
        min_total=min_total,
    )
    print_orders(results)


def run_menu(orders: list[Order]) -> None:
    """Run the interactive command-line menu loop."""
    while True:
        print_menu()
        command = input("Select command (1-9): ").strip()

        try:
            if command == "1":
                print_orders(orders)
            elif command == "2":
                handle_add_order(orders)
            elif command == "3":
                order_id = input("Enter order ID: ").strip()
                order = find_order_by_id(orders, order_id)
                if order is not None:
                    print_orders([order])
                else:
                    print(f"Order '{order_id.upper()}' not found.")
            elif command == "4":
                allowed = ", ".join(VALID_STATUSES)
                status = input(f"Enter status ({allowed}): ").strip()
                filtered = filter_by_status(orders, status)
                print_orders(filtered)
            elif command == "5":
                handle_multi_search(orders)
            elif command == "6":
                order_id = input("Enter order ID to update: ").strip()
                allowed = ", ".join(VALID_STATUSES)
                new_status = input(f"Enter new status ({allowed}): ").strip()
                updated = update_order_status(orders, order_id, new_status)
                print(
                    f"Order '{updated.order_id}' status updated to '{updated.status}'."
                )
            elif command == "7":
                sorted_orders = sort_orders_by_price(orders, descending=True)
                print_orders(sorted_orders)
            elif command == "8":
                print_statistics(orders)
            elif command == "9":
                print("Goodbye.")
                break
            else:
                print("Unknown command. Please select a number from 1 to 9.")
        except OrderError as error:
            print(f"Validation / Domain Error: {error}")


def main() -> None:
    """Application entry point."""
    orders = create_demo_orders()
    if "--demo" in sys.argv:
        run_demo_scenario(orders)
        return

    run_demo_scenario(orders)
    run_menu(orders)


if __name__ == "__main__":
    main()
```

---

## 5. Пояснення `pyproject.toml`, `.gitignore` та `README.md`

### 5.1. Файл `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=70"]
build-backend = "setuptools.build_meta"

[project]
name = "order-manager"
version = "0.1.0"
description = "Order management laboratory project for the course 'Professional Python' (Variant 7)"
readme = "README.md"
requires-python = ">=3.11"

[project.scripts]
order-manager = "order_manager.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

### 5.2. Файл `.gitignore`

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.idea/
.vscode/
dist/
build/
*.egg-info/
.env
```

---

## 6. Результат роботи програми та Git

### 6.1. Результат запуску `python -m order_manager.main --demo`

```text
=== Order Management System (Variant 7) - Demo Report ===

----------------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                  Qty       Unit   Discount       Final Status    
----------------------------------------------------------------------------------------------------------------------
ORD-1001   Anna Koval           Mechanical Keyboard Keychron K8         2    4200.00       0.00     8400.00 paid      
ORD-1002   Oleh Melnyk          Monitor Dell UltraSharp 27              1   16500.00    1650.00    14850.00 shipped   
ORD-1003   Iryna Bondar         Wireless Mouse Logitech MX Master 3S    3    4500.00    1350.00    12150.00 new       
ORD-1004   Andrii Shevchenko    USB-C Docking Station                   1    3800.00       0.00     3800.00 paid      
ORD-1005   Natalia Boyko        Noise-Cancelling Headphones Sony        1   11200.00    1120.00    10080.00 cancelled 
----------------------------------------------------------------------------------------------------------------------

Orders with status 'paid':

----------------------------------------------------------------------------------------------------------------------
ID         Customer             Item                                  Qty       Unit   Discount       Final Status    
----------------------------------------------------------------------------------------------------------------------
ORD-1001   Anna Koval           Mechanical Keyboard Keychron K8         2    4200.00       0.00     8400.00 paid      
ORD-1004   Andrii Shevchenko    USB-C Docking Station                   1    3800.00       0.00     3800.00 paid      
----------------------------------------------------------------------------------------------------------------------

--- Order Statistics (Active Orders) ---
Discount rule: 10% off for orders >= 10000.00 UAH
Total active revenue: 39200.00 UAH
Average order check:  9800.00 UAH
Most expensive order: ORD-1002 | Oleh Melnyk | 14850.00 UAH

Found order by ID: ORD-1002 - Oleh Melnyk (Monitor Dell UltraSharp 27, 14850.00 UAH)
```

### 6.2. Вивід `git status` та `git log --oneline`

```text
On branch main
nothing to commit, working tree clean
```

```text
d4f8c21 Add laboratory report in Markdown and DOCX formats
789e7aa Add interactive CLI entry point, unit tests, and README documentation
e27df6e Add Order dataclass model, custom exceptions, and business logic
afff582 Create initial project structure and packaging config
```

---

## 7. Відповіді на контрольні запитання

1. **Що таке Python-проєкт?** — Структурована сукупність вихідного коду (пакетів і модулів), конфігураційних файлів (`pyproject.toml`, `.gitignore`), автоматизованих тестів (`tests/`), документації (`README.md`) та метаданих залежностей.
2. **Чим проєкт відрізняється від одного Python script?** — Скрипт складається з одного файлу для простої задачі, тоді як проєкт розділяє архітектурні шари (моделі, бізнес-логіку, точку входу, тести), встановлюється як пакет і підтримує масштабування.
3. **Що таке Python module?** — Окремий файл із розширенням `.py`, що містить функції, класи та змінні, які можна імпортувати.
4. **Що таке Python package?** — Каталог із модулями Python та файлом `__init__.py`, що формує єдиний простір імен.
5. **Для чого потрібний `__init__.py`?** — Позначає каталог як Python-пакет, виконує ініціалізацію пакета при імпорті та зберігає метадані (наприклад, `__version__`).
6. **Що таке `src-layout`?** — Схема організації проєкту, де весь код пакета міститься у підкаталозі `src/<package_name>/`.
7. **Які переваги має `src-layout`?** — Гарантує тестування встановленого пакета, а не локальних файлів робочого каталогу, і відокремлює код від конфігураційних файлів у корені.
8. **Для чого використовується virtual environment?** — Для ізоляції бібліотек і залежностей одного Python-проєкту від глобальної системи та інших проєктів.
9. **Як створити `.venv`?** — Командою `python -m venv .venv`.
10. **Як активувати virtual environment?** — У Windows PowerShell: `.venv\Scripts\Activate.ps1` (у CMD: `.venv\Scripts\activate`), у Linux/macOS: `source .venv/bin/activate`.
11. **Для чого використовується `pip`?** — Стандартний менеджер пакетів Python для встановлення, оновлення та видалення бібліотек.
12. **Чому рекомендується `python -m pip`?** — Гарантує виклик `pip`, прив'язаного саме до поточного активного інтерпретатора Python.
13. **Для чого потрібний `pyproject.toml`?** — Єдиний стандартний файл конфігурації збирання, метаданих, залежностей та інструментів проєкту.
14. **Що містить секція `[project]`?** — Назву пакета (`name`), версію (`version`), опис (`description`), вимоги до версії Python (`requires-python`), залежності та консольні скрипти.
15. **Що таке editable installation?** — Встановлення пакета командою `python -m pip install -e .`, за якого зміни у вихідному коді `src/` одразу застосовуються без перевстановлення пакета.
16. **Для чого використовується `if __name__ == "__main__"`?** — Щоб точка входу `main()` виконувалася лише при безпосередньому запуску файлу, а не під час його імпорту в інші модулі чи тести.
17. **Що таке Git?** — Розподілена система контролю версій (DVCS) для відстеження історії змін і командної розробки.
18. **Що таке repository?** — Сховище проєкту з робочими файлами та службовим каталогом `.git/`, де зберігається повна історія комітів.
19. **Що таке commit?** — Зафіксований атомарний знімок стану проєкту в певний момент часу з унікальним хешем, автором і коментарем.
20. **Для чого використовується `git status`?** — Показує поточний стан робочого каталогу та проіндексованих файлів (`staged`, `modified`, `untracked`).
21. **Для чого `git add`?** — Додає змінені файли до проміжної області (`staging area`) перед створенням коміту.
22. **Для чого `git commit`?** — Фіксує проіндексовані зміни в історії локального репозиторію.
23. **Що показує `git log`?** — Історію комітів у гілці (хеші, авторів, дати, повідомлення).
24. **Для чого потрібен `.gitignore`?** — Визначає файли та папки, які Git має ігнорувати (`.venv/`, `__pycache__/`, кеші IDE, артефакти збирання).
25. **Чому `.venv` не потрібно комітити?** — Віртуальне середовище містить платформозалежні бінарні файли великого обсягу і легко відтворюється через `pyproject.toml`.
26. **Для чого потрібний `README`?** — Основна документація проєкту з описом призначення, вимог, інструкцій зі встановлення та запуску.
27. **Що таке type hints?** — Анотації типів (PEP 484), які вказують очікувані типи змінних, параметрів і результатів функцій для статичної перевірки (`mypy`) і кращої читабельності.
28. **Для чого програму розділяють на modules?** — Для дотримання принципу єдиної відповідальності, зручності читання, повторного використання та ізольованого тестування.
29. **Що таке business logic?** — Правила та обчислення предметної області (наприклад, розрахунок знижок, виручки, фільтрація замовлень), незалежні від інтерфейсу користувача.
30. **Чому потрібно відокремлювати application entry point від business logic?** — Щоб бізнес-логіку можна було автоматизовано тестувати (`pytest`) і повторно використовувати з будь-яким інтерфейсом (CLI, Web API, GUI).

---

## 8. Висновок

У ході виконання лабораторної роботи №1 було розроблено професійний Python-проєкт **«Система управління замовленнями інтернет-магазину» (`order_manager`, Варіант №7)** із використанням структури **`src-layout`**, конфігураційного файлу `pyproject.toml`, `.gitignore`, документації `README.md`, суворих анотацій типів (`type hints`), `@dataclass`, кастомних винятків, модульних тестів `pytest` та системи контролю версій Git.
