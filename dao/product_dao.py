from typing import List, Optional
from models.product import Product
from .base_dao import BaseDAO


class ProductDAO(BaseDAO):
    def get_by_sku(self, sku: str) -> Optional[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sku, name, category, unit_price, stock_qty, is_active, barcode, reorder_threshold "
                "FROM products WHERE sku = ?",
                (sku,),
            )
            row = cursor.fetchone()
            return Product.from_row(row) if row else None

    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        if not barcode:
            return None
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sku, name, category, unit_price, stock_qty, is_active, barcode, reorder_threshold "
                "FROM products WHERE barcode = ?",
                (barcode,),
            )
            row = cursor.fetchone()
            return Product.from_row(row) if row else None

    def find_by_code(self, code: str) -> Optional[Product]:
        """Finds product by SKU or Barcode."""
        if not code:
            return None
        code = code.strip()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sku, name, category, unit_price, stock_qty, is_active, barcode, reorder_threshold "
                "FROM products WHERE sku = ? OR barcode = ?",
                (code, code),
            )
            row = cursor.fetchone()
            return Product.from_row(row) if row else None

    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        only_active: bool = True,
        only_low_stock: bool = False,
    ) -> List[Product]:
        sql = "SELECT sku, name, category, unit_price, stock_qty, is_active, barcode, reorder_threshold FROM products WHERE 1=1"
        params = []

        if only_active:
            sql += " AND is_active = 1"

        if category and category.lower() != "all":
            sql += " AND category = ?"
            params.append(category)

        if only_low_stock:
            sql += " AND stock_qty <= reorder_threshold"

        if query:
            clean_query = f"%{query.strip()}%"
            sql += " AND (sku LIKE ? OR name LIKE ? OR barcode LIKE ?)"
            params.extend([clean_query, clean_query, clean_query])

        sql += " ORDER BY name ASC"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [Product.from_row(row) for row in cursor.fetchall()]

    def get_all(self, category: Optional[str] = None, only_active: bool = True) -> List[Product]:
        return self.search(category=category, only_active=only_active)

    def get_low_stock(self) -> List[Product]:
        return self.search(only_low_stock=True)

    def create(self, product: Product) -> Product:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (sku, name, category, unit_price, stock_qty, is_active, barcode, reorder_threshold) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    product.sku,
                    product.name,
                    product.category,
                    product.unit_price,
                    product.stock_qty,
                    product.is_active,
                    product.barcode or None,
                    product.reorder_threshold,
                ),
            )
            conn.commit()
            return product

    def update(self, product: Product) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET name = ?, category = ?, unit_price = ?, stock_qty = ?, "
                "is_active = ?, barcode = ?, reorder_threshold = ? WHERE sku = ?",
                (
                    product.name,
                    product.category,
                    product.unit_price,
                    product.stock_qty,
                    product.is_active,
                    product.barcode or None,
                    product.reorder_threshold,
                    product.sku,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def adjust_stock(self, sku: str, delta: int) -> bool:
        """Adjusts stock by delta (positive to restock, negative to deduct)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET stock_qty = stock_qty + ? WHERE sku = ? AND (stock_qty + ?) >= 0",
                (delta, sku, delta),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, sku: str) -> bool:
        """Deletes product, or soft-deactivates if referenced in existing sales."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM sale_items WHERE sku = ?", (sku,))
            count = cursor.fetchone()[0]
            if count > 0:
                # Referenced in sales, soft deactivate to preserve historical records
                cursor.execute("UPDATE products SET is_active = 0 WHERE sku = ?", (sku,))
            else:
                cursor.execute("DELETE FROM products WHERE sku = ?", (sku,))
            conn.commit()
            return cursor.rowcount > 0
