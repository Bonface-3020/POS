from typing import List, Optional
from dao.customer_dao import CustomerDAO
from models.customer import Customer


class CustomerService:
    def __init__(self, customer_dao: Optional[CustomerDAO] = None):
        self.customer_dao = customer_dao or CustomerDAO()

    def get_all(self) -> List[Customer]:
        return self.customer_dao.get_all()

    def search(self, query: str = "") -> List[Customer]:
        return self.customer_dao.search(query)

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        return self.customer_dao.get_by_phone(phone)

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return self.customer_dao.get_by_id(customer_id)

    def create_customer(self, name: str, phone: str, initial_points: int = 0) -> Customer:
        name = name.strip()
        phone = phone.strip()
        if not name:
            raise ValueError("Customer name cannot be empty.")
        if not phone:
            raise ValueError("Phone number cannot be empty.")

        existing = self.customer_dao.get_by_phone(phone)
        if existing:
            raise ValueError(f"Customer with phone '{phone}' already exists ({existing.name}).")

        customer = Customer(
            customer_id="",
            name=name,
            phone_number=phone,
            loyalty_points=max(0, initial_points),
        )
        return self.customer_dao.create(customer)

    def update_customer(self, customer_id: str, name: str, phone: str, points: int) -> bool:
        name = name.strip()
        phone = phone.strip()
        if not name or not phone:
            raise ValueError("Name and Phone cannot be empty.")

        customer = Customer(
            customer_id=customer_id,
            name=name,
            phone_number=phone,
            loyalty_points=max(0, points),
        )
        return self.customer_dao.update(customer)
