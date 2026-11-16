from typing import List, Optional
from models.cashier import Cashier
from dao.cashier_dao import CashierDAO


class AuthService:
    def __init__(self, cashier_dao: Optional[CashierDAO] = None):
        self.cashier_dao = cashier_dao or CashierDAO()
        self.current_cashier: Optional[Cashier] = None

    def login(self, cashier_id: str, pin_code: str) -> Cashier:
        cashier = self.cashier_dao.authenticate(cashier_id, pin_code)
        if not cashier:
            raise ValueError("Invalid Cashier ID or PIN code.")
        self.current_cashier = cashier
        return cashier

    def login_by_pin(self, pin_code: str) -> Cashier:
        cashier = self.cashier_dao.authenticate_by_pin(pin_code)
        if not cashier:
            raise ValueError("Invalid PIN code.")
        self.current_cashier = cashier
        return cashier

    def logout(self):
        self.current_cashier = None

    @property
    def is_authenticated(self) -> bool:
        return self.current_cashier is not None

    @property
    def is_manager(self) -> bool:
        return bool(self.current_cashier and self.current_cashier.is_manager)

    def get_all_active_cashiers(self) -> List[Cashier]:
        return self.cashier_dao.get_all(only_active=True)
