from typing import List, Optional
from models.cashier import Cashier
from .base_dao import BaseDAO


class CashierDAO(BaseDAO):
    def get_by_id(self, cashier_id: str) -> Optional[Cashier]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cashier_id, full_name, pin_code, role, is_active FROM cashiers WHERE cashier_id = ?",
                (cashier_id,),
            )
            row = cursor.fetchone()
            return Cashier.from_row(row) if row else None

    def authenticate(self, cashier_id: str, pin_code: str) -> Optional[Cashier]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cashier_id, full_name, pin_code, role, is_active "
                "FROM cashiers WHERE cashier_id = ? AND pin_code = ? AND is_active = 1",
                (cashier_id, str(pin_code)),
            )
            row = cursor.fetchone()
            return Cashier.from_row(row) if row else None

    def authenticate_by_pin(self, pin_code: str) -> Optional[Cashier]:
        """Allows single-step PIN-only login for POS terminal convenience."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cashier_id, full_name, pin_code, role, is_active "
                "FROM cashiers WHERE pin_code = ? AND is_active = 1",
                (str(pin_code),),
            )
            row = cursor.fetchone()
            return Cashier.from_row(row) if row else None

    def get_all(self, only_active: bool = False) -> List[Cashier]:
        query = "SELECT cashier_id, full_name, pin_code, role, is_active FROM cashiers"
        if only_active:
            query += " WHERE is_active = 1"
        query += " ORDER BY role DESC, full_name ASC"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [Cashier.from_row(r) for r in cursor.fetchall()]

    def create(self, cashier: Cashier) -> Cashier:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cashiers (cashier_id, full_name, pin_code, role, is_active) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    cashier.cashier_id,
                    cashier.full_name,
                    str(cashier.pin_code),
                    cashier.role,
                    cashier.is_active,
                ),
            )
            conn.commit()
            return cashier

    def update(self, cashier: Cashier) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cashiers SET full_name = ?, pin_code = ?, role = ?, is_active = ? "
                "WHERE cashier_id = ?",
                (
                    cashier.full_name,
                    str(cashier.pin_code),
                    cashier.role,
                    cashier.is_active,
                    cashier.cashier_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def deactivate(self, cashier_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cashiers SET is_active = 0 WHERE cashier_id = ?",
                (cashier_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
