"""Unit tests for the data_processor package (Laboratory Work No. 2, Variant 7)."""

from pathlib import Path

import pytest

from data_processor.analytics import (
    build_summary_report,
    calculate_average_order,
    calculate_average_values,
    calculate_total_revenue,
    create_category_filter,
    create_min_amount_filter,
    create_record,
    export_summary_to_json,
    find_most_expensive_order,
    get_amount_bounds,
    run_pipeline,
    run_search_benchmark,
    sort_items,
    sort_orders_by_amount,
    verify_pipeline_integrity,
)
from data_processor.data import generate_synthetic_orders, orders
from data_processor.decorators import (
    clear_operation_history,
    get_operation_history,
    repeat,
)
from data_processor.processors import (
    analyze_customer_segments,
    count_orders_by_category,
    count_orders_by_status,
    create_order_index,
    filter_by_min_amount,
    filter_by_status,
    filter_items,
    find_order_by_index,
    find_order_linear,
    get_unique_categories,
    get_unique_customers,
    get_unique_statuses,
    group_orders_by_category,
    group_orders_by_status,
    group_orders_nested,
)


def test_sets_and_comprehensions() -> None:
    """Verify set comprehensions and set algebra operations."""
    statuses = get_unique_statuses(orders)
    assert statuses == {"new", "paid", "shipped", "cancelled"}

    categories = get_unique_categories(orders)
    assert "Peripherals" in categories
    assert "Laptops" in categories

    customers = get_unique_customers(orders)
    assert len(customers) == 6

    segments = analyze_customer_segments(orders)
    assert "Anna Koval" in segments["both_paid_and_shipped_intersection"]
    assert segments["both_paid_and_shipped_intersection"].issubset(
        segments["paid_or_shipped_union"]
    )


def test_dict_index_and_search() -> None:
    """Verify dict comprehension index and O(1) vs O(n) search equivalence."""
    index = create_order_index(orders)
    assert len(index) == len(orders)

    found_fast = find_order_by_index(index, "ord-1002")
    found_linear = find_order_linear(orders, "ord-1002")
    assert found_fast is not None
    assert found_fast == found_linear
    assert found_fast["customer"] == "Oleh Melnyk"

    assert find_order_by_index(index, "ORD-9999") is None
    assert find_order_linear(orders, "ORD-9999") is None


def test_filtering_and_closures() -> None:
    """Verify list comprehensions, closures, and universal filter_items."""
    paid_orders = filter_by_status(orders, "paid")
    assert len(paid_orders) == 3
    assert all(item["status"] == "paid" for item in paid_orders)

    min_filtered = filter_by_min_amount(orders, 12000.0)
    assert all(float(item["amount"]) >= 12000.0 for item in min_filtered)

    closure_pred = create_min_amount_filter(14000.0)
    via_universal = filter_items(orders, closure_pred)
    assert {item["id"] for item in via_universal} == {"ORD-1002", "ORD-1007"}

    cat_pred = create_category_filter({"Audio"}, active_only=True)
    active_audio = filter_items(orders, cat_pred)
    assert len(active_audio) == 1
    assert active_audio[0]["id"] == "ORD-1008"


def test_grouping_and_counters() -> None:
    """Verify defaultdict grouping, nested grouping, and Counter statistics."""
    by_status = group_orders_by_status(orders)
    assert len(by_status["paid"]) == 3
    assert len(by_status["cancelled"]) == 1

    by_category = group_orders_by_category(orders)
    assert len(by_category["Peripherals"]) == 2

    nested = group_orders_nested(orders)
    assert len(nested["Audio"]["cancelled"]) == 1
    assert len(nested["Audio"]["new"]) == 1

    status_counts = count_orders_by_status(orders)
    assert status_counts["paid"] == 3
    assert sum(status_counts.values()) == len(orders)

    cat_counts = count_orders_by_category(orders)
    assert cat_counts["Accessories"] == 2


def test_aggregations_and_sorting() -> None:
    """Verify revenue, average check, tuple bounds, max order, and sorting."""
    total_active = calculate_total_revenue(orders, active_only=True)
    assert total_active == 106500.0

    avg_active = calculate_average_order(orders, active_only=True)
    assert avg_active == round(106500.0 / 7, 2)

    assert calculate_average_order([], active_only=True) == 0.0
    assert find_most_expensive_order([], active_only=True) is None
    assert get_amount_bounds([], active_only=True) == (0.0, 0.0)

    min_amt, max_amt = get_amount_bounds(orders, active_only=True)
    assert min_amt == 3800.0
    assert max_amt == 55800.0

    best = find_most_expensive_order(orders, active_only=True)
    assert best is not None
    assert best["id"] == "ORD-1007"

    sorted_desc = sort_orders_by_amount(orders, reverse=True)
    amounts = [float(item["amount"]) for item in sorted_desc]
    assert amounts == sorted(amounts, reverse=True)

    sorted_by_qty = sort_items(
        orders, key_func=lambda item: int(item["quantity"]), reverse=False
    )
    assert int(sorted_by_qty[0]["quantity"]) == 1
    assert int(sorted_by_qty[-1]["quantity"]) == 3


def test_args_kwargs_pipeline_and_decorators(tmp_path: Path) -> None:
    """Verify *args, **kwargs, pipeline processing, @repeat, deque, and export."""
    assert calculate_average_values() == 0.0
    assert calculate_average_values(10.0, 20.0, 30.0) == 20.0

    rec = create_record(
        id="ORD-2001",
        customer="Test User",
        item="Gaming Monitor",
        category="Monitors",
        quantity=2,
        unit_price=10000.0,
        status="new",
    )
    assert rec["amount"] == 18000.0  # 10% discount applied automatically

    clear_operation_history()
    pipeline_out = run_pipeline(
        orders,
        lambda items: filter_by_status(items, "paid"),
        lambda items: sort_orders_by_amount(items, reverse=True),
    )
    assert len(pipeline_out) == 3
    assert pipeline_out[0]["id"] == "ORD-1007"

    assert verify_pipeline_integrity(pipeline_out) == 3
    history = get_operation_history()
    assert any("Repeated verify_pipeline_integrity x2" in entry for entry in history)

    with pytest.raises(ValueError):
        repeat(0)

    summary = build_summary_report(orders)
    assert summary["total_orders"] == 8
    export_file = export_summary_to_json(orders, tmp_path / "summary.json")
    assert export_file.exists()


def test_synthetic_generator_and_benchmark() -> None:
    """Verify synthetic dataset generation and search benchmark execution."""
    synthetic = generate_synthetic_orders(250)
    assert len(synthetic) == 250
    assert synthetic[0]["id"] == "ORD-000001"

    bench = run_search_benchmark(sizes=(100, 500), lookups=20)
    assert len(bench) == 2
    assert bench[0]["records"] == 100
    assert bench[1]["records"] == 500
    assert float(bench[1]["list_search_s"]) >= 0.0

