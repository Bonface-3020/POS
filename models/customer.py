from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    customer_id: str
    name: str
    phone_number: str
    loyalty_points: int = 0

    @classmethod
    def from_row(cls, row) -> "Customer":
        return cls(
            customer_id=row["customer_id"],
            name=row["name"],
            phone_number=row["phone_number"],
            loyalty_points=int(row["loyalty_points"]),
        )
