"""Application entry point and interactive CLI for Order Data Processor (Variant 7)."""

import sys

from data_processor.analytics import (
    build_summary_report,
    calculate_average_order,
    calculate_average_values,
     calculate_total_revenue,
    create_category_filter,
    create_min_amount_filter,
    create_record,
    find_most_expensive_order,
    get_amount_bounds,
    run_pipeline,
    run_search_benchmark,
    sort_items,
    sort_orders_by_amount,
    verify_pipeline_integrity,
)
from data_processor.data import (
    DISCOUNT_RULE,
    VALID_STATUSES,
    WAREHOUSE_COORDINATES,
    OrderRecord,
    orders,
)
from data_processor.decorators import get_operation_history
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


def print_orders(title: str, items: list[OrderRecord]) -> None:
    """Format and print a table of structured order records."""
    print(f"\n{title}")
    header = (
        f"{'ID':<10} {'Customer':<20} {'Item':<36} "
        f"{'Category':<13} {'Qty':>4} {'Amount (UAH)':>13} {'Status':<10}"
    )
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)
    if not items:
        print("No matching orders.")
    else:
        for order in items:
            print(
                f"{str(order['id']):<10} "
                f"{str(order['customer']):<20} "
                f"{str(order['item']):<36} "
                f"{str(order['category']):<13} "
                f"{int(order['quantity']):>4d} "
                f"{float(order['amount']):>13.2f} "
                f"{str(order['status']):<10}"
            )
    print(separator)


def print_benchmark_table(results: list[dict[str, float | int]]) -> None:
    """Print the complexity benchmark table comparing list O(n) vs dict/set O(1)."""
    print("\nExperimental Complexity Benchmark (500 lookups per dataset size)")
    header = (
        f"{'Records':>10} | {'list search O(n)':>18} | "
        f"{'dict search O(1)':>18} | {'set lookup O(1)':>17} | "
        f"{'dict index build':>17} | {'Speedup':>10}"
    )
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)
    for row in results:
        print(
            f"{int(row['records']):>10,d} | "
            f"{float(row['list_search_s']):>16.6f} s | "
            f"{float(row['dict_search_s']):>16.6f} s | "
            f"{float(row['set_lookup_s']):>15.6f} s | "
            f"{float(row['index_build_s']):>15.6f} s | "
            f"{float(row['speedup_x']):>9.1f}x"
        )
    print(separator)


def run_demo_scenario(dataset: list[OrderRecord]) -> None:
    """Execute full non-interactive demonstration of all Laboratory Work No. 2 features."""
    print("=== Order Data Processor (Variant 7) - Laboratory Work No. 2 ===")

    # Tuple unpacking demonstration
    lat, lon = WAREHOUSE_COORDINATES
    threshold, discount_rate = DISCOUNT_RULE
    print(
        f"Warehouse hub coordinates (tuple): ({lat:.4f}, {lon:.4f}) | "
        f"Allowed statuses (tuple): {VALID_STATUSES} | "
        f"Discount rule: {int(discount_rate * 100)}% from {threshold:.0f} UAH"
    )

    print_orders("1. All Structured Orders (list[dict])", dataset)

    # Set comprehensions & set algebra
    categories = get_unique_categories(dataset)
    statuses = get_unique_statuses(dataset)
    customers = get_unique_customers(dataset)
    segments = analyze_customer_segments(dataset)
    print("\n2. Unique Sets & Set Operations:")
    print(f"   Unique categories (set): {sorted(categories)}")
    print(f"   Unique statuses (set):   {sorted(statuses)}")
    print(f"   Unique customers (set):  {sorted(customers)}")
    print(
        f"   Paid OR Shipped (union):         {sorted(segments['paid_or_shipped_union'])}"
    )
    print(
        f"   Paid AND Shipped (intersection): {sorted(segments['both_paid_and_shipped_intersection'])}"
    )

    # Aggregations with @measure_time decorator & generator expressions
    print("\n3. Aggregations & Decorator Timing (@measure_time):")
    total_revenue = calculate_total_revenue(dataset, active_only=True)
    average_order = calculate_average_order(dataset, active_only=True)
    min_amount, max_amount = get_amount_bounds(dataset, active_only=True)
    best_order = find_most_expensive_order(dataset, active_only=True)

    print(f"   Total active revenue:  {total_revenue:.2f} UAH")
    print(f"   Average active check:  {average_order:.2f} UAH")
    print(f"   Active amount bounds:  min={min_amount:.2f} UAH, max={max_amount:.2f} UAH")
    if best_order:
        print(
            f"   Most expensive order:  {best_order['id']} | "
            f"{best_order['customer']} | {best_order['item']} | "
            f"{best_order['amount']:.2f} UAH"
        )

    # Sorting (lambda)
    ranking = sort_orders_by_amount(dataset, reverse=True)
    print_orders("4. Orders Sorted by Amount Descending (lambda)", ranking)

    # Collections: Counter & defaultdict (including nested grouping)
    status_counter = count_orders_by_status(dataset)
    category_counter = count_orders_by_category(dataset)
    print("\n5. Statistics via collections.Counter:")
    print("   Orders by status:  ", dict(status_counter))
    print("   Orders by category:", dict(category_counter))

    grouped_by_cat = group_orders_by_category(dataset)
    print("\n6. Grouping via collections.defaultdict (by category):")
    for category, items in grouped_by_cat.items():
        print(f"   {category:<13} -> {len(items)} order(s)")

    nested_groups = group_orders_nested(dataset)
    print("\n7. Nested Grouping (category -> status -> count):")
    for category, status_map in nested_groups.items():
        counts_str = ", ".join(
            f"{st}: {len(ords)}" for st, ords in status_map.items()
        )
        print(f"   {category:<13} -> {{ {counts_str} }}")

    # Dict comprehension index & O(1) lookup vs O(n) linear search
    order_index = create_order_index(dataset)
    target_id = "ORD-1002"
    found_fast = find_order_by_index(order_index, target_id)
    found_linear = find_order_linear(dataset, target_id)
    print(f"\n8. Search by Order ID ({target_id}):")
    print(f"   Dict index O(1):  {found_fast}")
    print(f"   Linear scan O(n): {found_linear['id'] if found_linear else None}")

    # Closure & universal filter_items
    is_high_value = create_min_amount_filter(10000.0)
    high_value_orders = filter_items(dataset, is_high_value)
    print_orders(
        "9. Filtered via Closure & Universal Filter (amount >= 10,000 UAH)",
        high_value_orders,
    )

    # Pipeline processing (*args higher-order steps) & parameterized @repeat decorator
    pipeline_result = run_pipeline(
        dataset,
        lambda items: filter_items(
            items, create_category_filter({"Peripherals", "Monitors", "Laptops"})
        ),
        lambda items: filter_by_min_amount(items, 8000.0),
        lambda items: sort_items(
            items, key_func=lambda rec: float(rec["amount"]), reverse=True
        ),
    )
    verified_count = verify_pipeline_integrity(pipeline_result)
    print_orders(
        f"10. Pipeline Processing Result ({verified_count} records verified via @repeat(2))",
        pipeline_result,
    )

    # *args and **kwargs demonstration
    sample_avg = calculate_average_values(8400.0, 14850.0, 12150.0, 55800.0)
    print(f"\n11. Average via *args: {sample_avg:.2f} UAH")

    new_order = create_record(
        id="ORD-1009",
        customer="Taras Novak",
        item="4K Webcam Logitech Brio",
        category="Peripherals",
        quantity=2,
        unit_price=6200.00,
        status="paid",
    )
    print(f"12. Created record via **kwargs (with auto-discount): {new_order}")

    # Summary dictionary preview
    summary = build_summary_report(dataset)
    print("\n13. Summary Report Keys:", list(summary.keys()))

    # Experimental benchmark (1,000 / 10,000 / 100,000 records)
    benchmark_results = run_search_benchmark(
        sizes=(1_000, 10_000, 100_000),
        lookups=500,
    )
    print_benchmark_table(benchmark_results)

    # Operation history via collections.deque
    history = get_operation_history()
    print(f"\n14. Recent Operation History (collections.deque, last {len(history)}):")
    for idx, entry in enumerate(history, start=1):
        print(f"    {idx:2d}. {entry}")


def print_menu() -> None:
    """Display interactive CLI menu options."""
    print("\n================ DATA PROCESSOR MENU ================")
    print("1. Show all orders")
    print("2. Search order by ID (O(1) dict index)")
    print("3. Filter orders by status")
    print("4. Filter orders by minimum amount (closure)")
    print("5. Group orders by category & status")
    print("6. Sort orders by amount")
    print("7. Run O(n) vs O(1) benchmark (1k / 10k / 100k)")
    print("8. Show recent operation history (deque)")
    print("9. Exit")
    print("=====================================================")


def run_menu(dataset: list[OrderRecord]) -> None:
    """Run the interactive CLI menu loop."""
    order_index = create_order_index(dataset)
    while True:
        print_menu()
        choice = input("Select command (1-9): ").strip()
        if choice == "1":
            print_orders("All Orders", dataset)
        elif choice == "2":
            order_id = input("Enter order ID (e.g., ORD-1002): ").strip()
            found = find_order_by_index(order_index, order_id)
            print_orders(
                f"Search Result for '{order_id.upper()}'",
                [found] if found else [],
            )
        elif choice == "3":
            status = input(f"Enter status ({'/'.join(VALID_STATUSES)}): ").strip()
            print_orders(
                f"Orders with status '{status}'",
                filter_by_status(dataset, status),
            )
        elif choice == "4":
            raw_min = input("Enter minimum amount (UAH): ").strip()
            try:
                min_val = float(raw_min)
            except ValueError:
                print("Error: Please enter a valid number.")
                continue
            predicate = create_min_amount_filter(min_val)
            print_orders(
                f"Orders with amount >= {min_val:.2f} UAH",
                filter_items(dataset, predicate),
            )
        elif choice == "5":
            grouped = group_orders_by_status(dataset)
            for st, items in grouped.items():
                print(f"{st:<10} -> {len(items)} order(s)")
        elif choice == "6":
            print_orders(
                "Orders Sorted by Amount",
                sort_orders_by_amount(dataset, reverse=True),
            )
        elif choice == "7":
            print_benchmark_table(run_search_benchmark())
        elif choice == "8":
            for idx, entry in enumerate(get_operation_history(), start=1):
                print(f"{idx:2d}. {entry}")
        elif choice == "9":
            print("Goodbye.")
            break
        else:
            print("Unknown command. Please choose 1-9.")


def main() -> None:
    """Application entry point."""
    dataset = [dict(item) for item in orders]
    if "--demo" in sys.argv:
        run_demo_scenario(dataset)
        return

    run_demo_scenario(dataset)
    run_menu(dataset)


if __name__ == "__main__":
    main()

