from dataclasses import dataclass
from typing import Optional


@dataclass
class Cashier:
    cashier_id: str
    full_name: str
    pin_code: str
    role: str = "Cashier"
    is_active: int = 1

    @property
    def is_manager(self) -> bool:
        return self.role.lower() == "manager"

    @classmethod
    def from_row(cls, row) -> "Cashier":
        return cls(
            cashier_id=row["cashier_id"],
            full_name=row["full_name"],
            pin_code=str(row["pin_code"]),
            role=row["role"],
            is_active=row["is_active"],
        )
