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

