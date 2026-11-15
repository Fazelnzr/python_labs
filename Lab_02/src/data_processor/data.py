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

