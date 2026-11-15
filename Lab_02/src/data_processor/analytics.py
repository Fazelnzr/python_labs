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
        target_id = f"ORD-{size:06d}"  # Last element (worst-case linear scan)

        # Build dict index once — O(n)
        idx_start = perf_counter()
        index = create_order_index(dataset)
        index_build_sec = perf_counter() - idx_start

        # Variant A: Linear search in list — O(n) per lookup
        list_start = perf_counter()
        for _ in range(lookups):
            find_order_linear(dataset, target_id)
        list_search_sec = perf_counter() - list_start

        # Variant B: Key lookup in dict — O(1) average per lookup
        dict_start = perf_counter()
        for _ in range(lookups):
            find_order_by_index(index, target_id)
        dict_search_sec = perf_counter() - dict_start

        # Set vs List membership check for IDs
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

