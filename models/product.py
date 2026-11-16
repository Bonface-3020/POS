from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    sku: str
    name: str
    category: str
    unit_price: float
    stock_qty: int
    is_active: int = 1
    barcode: Optional[str] = None
    reorder_threshold: int = 5

    @property
    def is_in_stock(self) -> bool:
        return self.stock_qty > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock_qty <= self.reorder_threshold

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock_qty <= 0

    @property
    def status_label(self) -> str:
        if self.is_out_of_stock:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"

    @classmethod
    def from_row(cls, row) -> "Product":
        return cls(
            sku=row["sku"],
            name=row["name"],
            category=row["category"],
            unit_price=float(row["unit_price"]),
            stock_qty=int(row["stock_qty"]),
            is_active=int(row["is_active"]),
            barcode=row["barcode"] if "barcode" in row.keys() else None,
            reorder_threshold=int(row["reorder_threshold"]) if "reorder_threshold" in row.keys() else 5,
        )
