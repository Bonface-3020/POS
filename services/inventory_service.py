from typing import List, Optional
from config import CATEGORIES
from dao.product_dao import ProductDAO
from models.product import Product


class InventoryService:
    def __init__(self, product_dao: Optional[ProductDAO] = None):
        self.product_dao = product_dao or ProductDAO()

    def get_products(
        self,
        query: str = "",
        category: Optional[str] = None,
        only_active: bool = True,
        only_low_stock: bool = False,
    ) -> List[Product]:
        return self.product_dao.search(
            query=query,
            category=category,
            only_active=only_active,
            only_low_stock=only_low_stock,
        )

    def find_by_code(self, code: str) -> Optional[Product]:
        return self.product_dao.find_by_code(code)

    def add_product(
        self,
        sku: str,
        name: str,
        category: str,
        unit_price: float,
        stock_qty: int,
        barcode: Optional[str] = None,
        reorder_threshold: int = 5,
    ) -> Product:
        sku = sku.strip().upper()
        name = name.strip()
        category = category.strip()

        if not sku or not name:
            raise ValueError("SKU and Name cannot be empty.")
        if category not in CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}")
        if unit_price <= 0:
            raise ValueError("Unit price must be greater than 0.")
        if stock_qty < 0:
            raise ValueError("Stock quantity cannot be negative.")
        if reorder_threshold < 0:
            raise ValueError("Reorder threshold cannot be negative.")

        # Check existing SKU
        existing = self.product_dao.get_by_sku(sku)
        if existing:
            raise ValueError(f"Product with SKU '{sku}' already exists.")

        # Check existing Barcode
        if barcode:
            barcode = barcode.strip()
            existing_barcode = self.product_dao.get_by_barcode(barcode)
            if existing_barcode:
                raise ValueError(f"Product with barcode '{barcode}' already exists ({existing_barcode.name}).")

        product = Product(
            sku=sku,
            name=name,
            category=category,
            unit_price=unit_price,
            stock_qty=stock_qty,
            is_active=1,
            barcode=barcode or None,
            reorder_threshold=reorder_threshold,
        )
        return self.product_dao.create(product)

    def update_product(
        self,
        sku: str,
        name: str,
        category: str,
        unit_price: float,
        stock_qty: int,
        barcode: Optional[str] = None,
        reorder_threshold: int = 5,
        is_active: int = 1,
    ) -> bool:
        sku = sku.strip().upper()
        name = name.strip()
        category = category.strip()

        if not name:
            raise ValueError("Name cannot be empty.")
        if category not in CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}")
        if unit_price <= 0:
            raise ValueError("Unit price must be greater than 0.")
        if stock_qty < 0:
            raise ValueError("Stock quantity cannot be negative.")

        product = Product(
            sku=sku,
            name=name,
            category=category,
            unit_price=unit_price,
            stock_qty=stock_qty,
            is_active=is_active,
            barcode=barcode.strip() if barcode else None,
            reorder_threshold=reorder_threshold,
        )
        return self.product_dao.update(product)

    def restock(self, sku: str, quantity_to_add: int) -> bool:
        if quantity_to_add <= 0:
            raise ValueError("Quantity to add must be positive.")
        return self.product_dao.adjust_stock(sku, quantity_to_add)

    def delete_product(self, sku: str) -> bool:
        return self.product_dao.delete(sku)

    def get_low_stock_alerts(self) -> List[Product]:
        return self.product_dao.get_low_stock()
