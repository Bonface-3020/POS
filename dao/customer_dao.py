from typing import List, Optional
import random
from models.customer import Customer
from .base_dao import BaseDAO


class CustomerDAO(BaseDAO):
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_id, name, phone_number, loyalty_points FROM customers WHERE customer_id = ?",
                (customer_id,),
            )
            row = cursor.fetchone()
            return Customer.from_row(row) if row else None

    def get_by_phone(self, phone_number: str) -> Optional[Customer]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_id, name, phone_number, loyalty_points FROM customers WHERE phone_number = ?",
                (phone_number.strip(),),
            )
            row = cursor.fetchone()
            return Customer.from_row(row) if row else None

    def search(self, query: str = "") -> List[Customer]:
        sql = "SELECT customer_id, name, phone_number, loyalty_points FROM customers"
        params = []
        if query:
            clean = f"%{query.strip()}%"
            sql += " WHERE name LIKE ? OR phone_number LIKE ? OR customer_id LIKE ?"
            params.extend([clean, clean, clean])
        sql += " ORDER BY name ASC"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [Customer.from_row(row) for row in cursor.fetchall()]

    def get_all(self) -> List[Customer]:
        return self.search()

    def create(self, customer: Customer) -> Customer:
        if not customer.customer_id:
            customer.customer_id = self.generate_next_id()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (customer_id, name, phone_number, loyalty_points) VALUES (?, ?, ?, ?)",
                (
                    customer.customer_id,
                    customer.name.strip(),
                    customer.phone_number.strip(),
                    customer.loyalty_points,
                ),
            )
            conn.commit()
            return customer

    def update(self, customer: Customer) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET name = ?, phone_number = ?, loyalty_points = ? WHERE customer_id = ?",
                (
                    customer.name.strip(),
                    customer.phone_number.strip(),
                    customer.loyalty_points,
                    customer.customer_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def adjust_loyalty_points(self, customer_id: str, points_delta: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET loyalty_points = MAX(0, loyalty_points + ?) WHERE customer_id = ?",
                (points_delta, customer_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def generate_next_id(self) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT customer_id FROM customers ORDER BY customer_id DESC LIMIT 1")
            row = cursor.fetchone()
            if row and row[0].startswith("CUS-"):
                try:
                    num = int(row[0].replace("CUS-", "")) + 1
                    return f"CUS-{num:03d}"
                except ValueError:
                    pass
            # Fallback
            return f"CUS-{random.randint(100, 999)}"
