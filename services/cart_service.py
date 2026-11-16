from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from models.product import Product
from models.customer import Customer
from models.sale import SaleItem
from config import DEFAULT_TAX_RATE


@dataclass
class CartItem:
    product: Product
    quantity: int = 1

    @property
    def unit_price(self) -> float:
        return self.product.unit_price

    @property
    def line_total(self) -> float:
        return round(self.product.unit_price * self.quantity, 2)


class CartService:
    def __init__(self, tax_rate: float = DEFAULT_TAX_RATE):
        self.items: Dict[str, CartItem] = {}  # sku -> CartItem
        self.customer: Optional[Customer] = None
        self.tax_rate = tax_rate
        self.discount_percent: float = 0.0  # 0 to 100
        self.discount_fixed: float = 0.0
        self.held_carts: Dict[str, dict] = {}

    def add_item(self, product: Product, quantity: int = 1) -> CartItem:
        if not product.is_active:
            raise ValueError(f"Product '{product.name}' is inactive.")
        if product.stock_qty <= 0:
            raise ValueError(f"Product '{product.name}' is out of stock.")

        if product.sku in self.items:
            current_qty = self.items[product.sku].quantity
            new_qty = current_qty + quantity
            if new_qty > product.stock_qty:
                raise ValueError(
                    f"Cannot add {quantity} more. In stock: {product.stock_qty}, currently in cart: {current_qty}."
                )
            self.items[product.sku].quantity = new_qty
            return self.items[product.sku]
        else:
            if quantity > product.stock_qty:
                raise ValueError(
                    f"Requested {quantity} but only {product.stock_qty} in stock."
                )
            cart_item = CartItem(product=product, quantity=quantity)
            self.items[product.sku] = cart_item
            return cart_item

    def set_quantity(self, sku: str, quantity: int):
        if sku not in self.items:
            return
        if quantity <= 0:
            self.remove_item(sku)
            return

        item = self.items[sku]
        if quantity > item.product.stock_qty:
            raise ValueError(
                f"Cannot set quantity to {quantity}. Only {item.product.stock_qty} available in stock."
            )
        item.quantity = quantity

    def remove_item(self, sku: str):
        if sku in self.items:
            del self.items[sku]

    def clear(self):
        self.items.clear()
        self.customer = None
        self.discount_percent = 0.0
        self.discount_fixed = 0.0

    def set_customer(self, customer: Optional[Customer]):
        self.customer = customer

    def apply_discount(self, percent: float = 0.0, fixed: float = 0.0):
        self.discount_percent = max(0.0, min(100.0, percent))
        self.discount_fixed = max(0.0, fixed)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @property
    def total_items_count(self) -> int:
        return sum(item.quantity for item in self.items.values())

    @property
    def subtotal(self) -> float:
        return round(sum(item.line_total for item in self.items.values()), 2)

    @property
    def discount_amount(self) -> float:
        sub = self.subtotal
        pct_discount = sub * (self.discount_percent / 100.0)
        total_discount = pct_discount + self.discount_fixed
        return round(min(sub, total_discount), 2)

    @property
    def taxable_amount(self) -> float:
        return max(0.0, round(self.subtotal - self.discount_amount, 2))

    @property
    def tax_amount(self) -> float:
        return round(self.taxable_amount * self.tax_rate, 2)

    @property
    def grand_total(self) -> float:
        return round(self.taxable_amount + self.tax_amount, 2)

    def to_sale_items(self) -> List[SaleItem]:
        return [
            SaleItem(
                sku=item.product.sku,
                quantity=item.quantity,
                unit_price_at_sale=item.unit_price,
                line_total=item.line_total,
                product_name=item.product.name,
                category=item.product.category,
            )
            for item in self.items.values()
        ]

    # Hold & Recall cart capability
    def hold_current_cart(self, note: str = "") -> str:
        if self.is_empty:
            raise ValueError("Cannot hold an empty cart.")
        cart_id = f"CART-{int(time.time())}"
        self.held_carts[cart_id] = {
            "items": dict(self.items),
            "customer": self.customer,
            "discount_percent": self.discount_percent,
            "discount_fixed": self.discount_fixed,
            "time": time.strftime("%H:%M:%S"),
            "note": note or f"Customer: {self.customer.name if self.customer else 'Guest'}",
            "total": self.grand_total,
        }
        self.clear()
        return cart_id

    def recall_cart(self, cart_id: str):
        if cart_id not in self.held_carts:
            raise ValueError("Held cart not found.")
        data = self.held_carts.pop(cart_id)
        self.items = data["items"]
        self.customer = data["customer"]
        self.discount_percent = data["discount_percent"]
        self.discount_fixed = data["discount_fixed"]

    def list_held_carts(self) -> List[dict]:
        return [
            {"id": cid, **data}
            for cid, data in self.held_carts.items()
        ]
