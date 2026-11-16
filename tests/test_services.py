import unittest
import tempfile
import os
from pathlib import Path

from database.connection import DatabaseManager
from dao.cashier_dao import CashierDAO
from dao.product_dao import ProductDAO
from dao.customer_dao import CustomerDAO
from dao.sale_dao import SaleDAO
from services.auth_service import AuthService
from services.cart_service import CartService
from services.sale_service import SaleService
from services.inventory_service import InventoryService
from services.customer_service import CustomerService


class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix=".db")
        cls.db = DatabaseManager(cls.temp_db_path)

        schema_path = Path(__file__).resolve().parent.parent / "retail_schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

        with cls.db.get_connection() as conn:
            conn.executescript(sql)

        cls.cashier_dao = CashierDAO(cls.db)
        cls.product_dao = ProductDAO(cls.db)
        cls.customer_dao = CustomerDAO(cls.db)
        cls.sale_dao = SaleDAO(cls.db)

        cls.auth_svc = AuthService(cls.cashier_dao)
        cls.inv_svc = InventoryService(cls.product_dao)
        cls.cust_svc = CustomerService(cls.customer_dao)
        cls.sale_svc = SaleService(cls.sale_dao)

    @classmethod
    def tearDownClass(cls):
        os.close(cls.temp_db_fd)
        if os.path.exists(cls.temp_db_path):
            os.remove(cls.temp_db_path)

    def test_cart_service_calculations(self):
        cart = CartService(tax_rate=0.08)
        p1 = self.inv_svc.find_by_code("BEV-01")  # price 4.50
        p2 = self.inv_svc.find_by_code("SNK-01")  # price 2.00

        cart.add_item(p1, quantity=2)  # 9.00
        cart.add_item(p2, quantity=1)  # 2.00
        self.assertEqual(cart.subtotal, 11.00)

        # Test discount 10%
        cart.apply_discount(percent=10.0)
        self.assertEqual(cart.discount_amount, 1.10)
        self.assertEqual(cart.taxable_amount, 9.90)
        # Tax 8% of 9.90 = 0.792 -> 0.79
        self.assertEqual(cart.tax_amount, 0.79)
        self.assertEqual(cart.grand_total, 10.69)

        # Hold & recall
        hold_id = cart.hold_current_cart("Customer stepped away")
        self.assertTrue(cart.is_empty)
        cart.recall_cart(hold_id)
        self.assertEqual(len(cart.items), 2)
        self.assertEqual(cart.grand_total, 10.69)

    def test_sale_checkout_cash_and_receipt(self):
        cashier = self.auth_svc.login("C101", "1234")
        cart = CartService(tax_rate=0.08)
        p = self.inv_svc.find_by_code("PRD-01")  # Bananas 2.30
        cart.add_item(p, quantity=2)  # 4.60

        # Subtotal: 4.60, Tax (8% of 4.60 = 0.368 -> 0.37), Grand Total: 4.97
        sale, change, receipt = self.sale_svc.process_checkout(
            cashier=cashier,
            cart=cart,
            payment_method="Cash",
            tendered_amount=10.00,
        )

        self.assertIsNotNone(sale.sale_id)
        self.assertEqual(change, 5.03)
        self.assertIn("TOTAL PAYABLE:", receipt)
        self.assertIn("Change Due:", receipt)
        self.assertTrue(cart.is_empty)


if __name__ == "__main__":
    unittest.main()
