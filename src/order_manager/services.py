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
