from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SaleItem:
    sku: str
    quantity: int
    unit_price_at_sale: float
    line_total: float
    sale_item_id: Optional[int] = None
    sale_id: Optional[int] = None
    product_name: Optional[str] = None
    category: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "SaleItem":
        keys = row.keys()
        return cls(
            sale_item_id=row["sale_item_id"] if "sale_item_id" in keys else None,
            sale_id=row["sale_id"] if "sale_id" in keys else None,
            sku=row["sku"],
            quantity=int(row["quantity"]),
            unit_price_at_sale=float(row["unit_price_at_sale"]),
            line_total=float(row["line_total"]),
            product_name=row["product_name"] if "product_name" in keys else (row["name"] if "name" in keys else None),
            category=row["category"] if "category" in keys else None,
        )


@dataclass
class Sale:
    cashier_id: str
    subtotal: float
    tax_amount: float
    total_amount: float
    payment_method: str
    sale_id: Optional[int] = None
    customer_id: Optional[str] = None
    sale_timestamp: Optional[str] = None
    cashier_name: Optional[str] = None
    customer_name: Optional[str] = None
    items: List[SaleItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "Sale":
        keys = row.keys()
        return cls(
            sale_id=row["sale_id"] if "sale_id" in keys else None,
            cashier_id=row["cashier_id"],
            customer_id=row["customer_id"] if "customer_id" in keys else None,
            sale_timestamp=row["sale_timestamp"] if "sale_timestamp" in keys else None,
            subtotal=float(row["subtotal"]),
            tax_amount=float(row["tax_amount"]),
            total_amount=float(row["total_amount"]),
            payment_method=row["payment_method"],
            cashier_name=row["cashier_name"] if "cashier_name" in keys else None,
            customer_name=row["customer_name"] if "customer_name" in keys else None,
        )
