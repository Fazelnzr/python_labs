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
