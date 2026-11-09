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

