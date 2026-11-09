"""Unit tests for the order_manager package."""

import pytest

from order_manager.exceptions import (
    DuplicateOrderError,
    OrderNotFoundError,
    OrderValidationError,
)
from order_manager.models import Order
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


def test_order_discount_calculation() -> None:
    """Orders reaching 10,000 UAH should receive a 10% discount."""
    order = Order(
        order_id="ORD-2001",
        customer_name="Test User",
        item_name="Laptop",
        quantity=1,
        unit_price=20000.0,
        status="new",
    )
    assert order.total_price == 20000.0
    assert order.discount_amount == 2000.0
    assert order.final_price == 18000.0


def test_order_validation_raises_custom_exception() -> None:
    """Invalid quantity, price, or status must raise OrderValidationError."""
    with pytest.raises(OrderValidationError):
        Order("ORD-1", "User", "Item", quantity=0, unit_price=100.0)

    with pytest.raises(OrderValidationError):
        Order("ORD-1", "User", "Item", quantity=1, unit_price=-50.0)

    with pytest.raises(OrderValidationError):
        Order("ORD-1", "User", "Item", quantity=1, unit_price=100.0, status="invalid")


def test_add_and_duplicate_order() -> None:
    """Adding an order with a duplicate ID must raise DuplicateOrderError."""
    orders: list[Order] = []
    order = Order("ORD-101", "Anna Koval", "Book", 2, 500.0)
    add_order(orders, order)
    assert len(orders) == 1

    with pytest.raises(DuplicateOrderError):
        add_order(orders, Order("ord-101", "Other", "Pen", 1, 50.0))


def test_statistics_and_sorting() -> None:
    """Revenue, average check, best order, and sorting should exclude cancelled orders appropriately."""
    orders = [
        Order("ORD-1", "A", "Item 1", 1, 1000.0, "paid"),
        Order("ORD-2", "B", "Item 2", 1, 3000.0, "shipped"),
        Order("ORD-3", "C", "Item 3", 1, 5000.0, "cancelled"),
    ]
    assert calculate_total_revenue(orders, active_only=True) == 4000.0
    assert calculate_average_check(orders) == 2000.0

    best = find_most_expensive_order(orders)
    assert best is not None
    assert best.order_id == "ORD-2"

    sorted_list = sort_orders_by_price(orders, descending=True)
    assert [o.order_id for o in sorted_list] == ["ORD-3", "ORD-2", "ORD-1"]


def test_update_status_and_search() -> None:
    """Updating status and multi-criteria search should work as expected."""
    orders = [
        Order("ORD-10", "Anna Koval", "Keyboard", 1, 2500.0, "new"),
        Order("ORD-11", "Oleh Melnyk", "Mouse", 1, 1200.0, "paid"),
    ]
    updated = update_order_status(orders, "ord-10", "paid")
    assert updated.status == "paid"
    assert len(filter_by_status(orders, "paid")) == 2

    found = search_orders(orders, customer_query="anna", min_total=2000.0)
    assert len(found) == 1
    assert found[0].order_id == "ORD-10"

    assert find_order_by_id(orders, "ORD-999") is None
    with pytest.raises(OrderNotFoundError):
        update_order_status(orders, "ORD-999", "shipped")
