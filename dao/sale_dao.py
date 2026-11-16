from typing import Dict, List, Optional
from datetime import datetime
from models.sale import Sale, SaleItem
from .base_dao import BaseDAO


class SaleDAO(BaseDAO):
    def create_sale(
        self,
        sale: Sale,
        items: List[SaleItem],
        loyalty_points_earned: int = 0,
    ) -> int:
        """
        Executes a sale transaction atomically:
        - Validates stock for all items
        - Inserts sale header
        - Inserts all line items
        - Decrements inventory stock
        - Awards customer loyalty points
        Rolls back automatically if any step fails.
        """
        if not items:
            raise ValueError("Sale must contain at least one item.")

        with self.db.transaction() as cursor:
            # 1. Validate stock availability for all items
            for item in items:
                cursor.execute(
                    "SELECT name, stock_qty, is_active FROM products WHERE sku = ?",
                    (item.sku,),
                )
                prod = cursor.fetchone()
                if not prod:
                    raise ValueError(f"Product with SKU '{item.sku}' does not exist.")
                if not prod["is_active"]:
                    raise ValueError(f"Product '{prod['name']}' ({item.sku}) is inactive.")
                if prod["stock_qty"] < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for '{prod['name']}': available {prod['stock_qty']}, requested {item.quantity}."
                    )

            # 2. Insert Sale record
            cursor.execute(
                "INSERT INTO sales (cashier_id, customer_id, sale_timestamp, subtotal, tax_amount, total_amount, payment_method) "
                "VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?, ?)",
                (
                    sale.cashier_id,
                    sale.customer_id if sale.customer_id else None,
                    round(sale.subtotal, 2),
                    round(sale.tax_amount, 2),
                    round(sale.total_amount, 2),
                    sale.payment_method,
                ),
            )
            sale_id = cursor.lastrowid

            # 3. Insert items and decrement stock
            for item in items:
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, sku, quantity, unit_price_at_sale, line_total) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        sale_id,
                        item.sku,
                        item.quantity,
                        round(item.unit_price_at_sale, 2),
                        round(item.line_total, 2),
                    ),
                )
                cursor.execute(
                    "UPDATE products SET stock_qty = stock_qty - ? WHERE sku = ?",
                    (item.quantity, item.sku),
                )

            # 4. Award loyalty points to customer if applicable
            if sale.customer_id and loyalty_points_earned > 0:
                cursor.execute(
                    "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE customer_id = ?",
                    (loyalty_points_earned, sale.customer_id),
                )

            return sale_id

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.sale_id, s.cashier_id, s.customer_id, s.sale_timestamp,
                       s.subtotal, s.tax_amount, s.total_amount, s.payment_method,
                       c.full_name AS cashier_name,
                       cust.name AS customer_name
                FROM sales s
                LEFT JOIN cashiers c ON s.cashier_id = c.cashier_id
                LEFT JOIN customers cust ON s.customer_id = cust.customer_id
                WHERE s.sale_id = ?
                """,
                (sale_id,),
            )
            sale_row = cursor.fetchone()
            if not sale_row:
                return None

            sale = Sale.from_row(sale_row)

            # Fetch line items with product details
            cursor.execute(
                """
                SELECT si.sale_item_id, si.sale_id, si.sku, si.quantity,
                       si.unit_price_at_sale, si.line_total,
                       p.name AS product_name, p.category
                FROM sale_items si
                LEFT JOIN products p ON si.sku = p.sku
                WHERE si.sale_id = ?
                ORDER BY si.sale_item_id ASC
                """,
                (sale_id,),
            )
            sale.items = [SaleItem.from_row(row) for row in cursor.fetchall()]
            return sale

    def get_recent_sales(
        self,
        limit: int = 50,
        query: Optional[str] = None,
        cashier_id: Optional[str] = None,
        payment_method: Optional[str] = None,
    ) -> List[Sale]:
        sql = """
            SELECT s.sale_id, s.cashier_id, s.customer_id, s.sale_timestamp,
                   s.subtotal, s.tax_amount, s.total_amount, s.payment_method,
                   c.full_name AS cashier_name,
                   cust.name AS customer_name
            FROM sales s
            LEFT JOIN cashiers c ON s.cashier_id = c.cashier_id
            LEFT JOIN customers cust ON s.customer_id = cust.customer_id
            WHERE 1=1
        """
        params = []

        if cashier_id:
            sql += " AND s.cashier_id = ?"
            params.append(cashier_id)

        if payment_method and payment_method.lower() != "all":
            sql += " AND s.payment_method = ?"
            params.append(payment_method)

        if query:
            clean = f"%{query.strip()}%"
            sql += " AND (CAST(s.sale_id AS TEXT) LIKE ? OR cust.name LIKE ? OR c.full_name LIKE ?)"
            params.extend([clean, clean, clean])

        sql += " ORDER BY s.sale_id DESC LIMIT ?"
        params.append(limit)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            sales = []
            for row in cursor.fetchall():
                sales.append(Sale.from_row(row))
            return sales

    def get_analytics_summary(self) -> Dict:
        """Calculates revenue, transactions, payment breakdown, and top sellers."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Overall summary
            cursor.execute(
                """
                SELECT COUNT(*) as total_sales,
                       COALESCE(SUM(total_amount), 0.0) as total_revenue,
                       COALESCE(SUM(subtotal), 0.0) as total_subtotal,
                       COALESCE(SUM(tax_amount), 0.0) as total_tax,
                       COALESCE(AVG(total_amount), 0.0) as avg_order_value
                FROM sales
                """
            )
            overall = cursor.fetchone()

            # Today summary
            cursor.execute(
                """
                SELECT COUNT(*) as today_sales,
                       COALESCE(SUM(total_amount), 0.0) as today_revenue
                FROM sales
                WHERE date(sale_timestamp) = date('now', 'localtime')
                """
            )
            today = cursor.fetchone()

            # Total items sold
            cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM sale_items")
            total_items_sold = cursor.fetchone()[0]

            # Payment breakdown
            cursor.execute(
                """
                SELECT payment_method, COUNT(*) as count, SUM(total_amount) as total
                FROM sales
                GROUP BY payment_method
                ORDER BY total DESC
                """
            )
            payment_methods = [
                {"method": row["payment_method"], "count": row["count"], "total": row["total"]}
                for row in cursor.fetchall()
            ]

            # Top 5 products by quantity sold
            cursor.execute(
                """
                SELECT p.sku, p.name, p.category,
                       SUM(si.quantity) as total_qty,
                       SUM(si.line_total) as total_revenue
                FROM sale_items si
                JOIN products p ON si.sku = p.sku
                GROUP BY p.sku
                ORDER BY total_qty DESC
                LIMIT 5
                """
            )
            top_products = [
                {
                    "sku": row["sku"],
                    "name": row["name"],
                    "category": row["category"],
                    "total_qty": row["total_qty"],
                    "total_revenue": row["total_revenue"],
                }
                for row in cursor.fetchall()
            ]

            return {
                "total_sales": overall["total_sales"],
                "total_revenue": overall["total_revenue"],
                "total_subtotal": overall["total_subtotal"],
                "total_tax": overall["total_tax"],
                "avg_order_value": overall["avg_order_value"],
                "today_sales": today["today_sales"],
                "today_revenue": today["today_revenue"],
                "total_items_sold": total_items_sold,
                "payment_methods": payment_methods,
                "top_products": top_products,
            }
