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
from services.inventory_service import InventoryService
from services.cart_service import CartService
from services.sale_service import SaleService
from services.customer_service import CustomerService


class TestEndToEndPOS(unittest.TestCase):
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

    def test_complete_checkout_workflow(self):
        # 1. Staff login
        cashier = self.auth_svc.login("C101", "1234")
        self.assertIsNotNone(cashier)

        # 2. Select customer
        customer = self.cust_svc.get_by_phone("+254700123456")
        initial_points = customer.loyalty_points

        # 3. Create Cart and add products
        cart = CartService(tax_rate=0.08)
        cart.set_customer(customer)

        tea = self.inv_svc.find_by_code("BEV-01")  # $4.50
        initial_stock = tea.stock_qty

        cart.add_item(tea, quantity=2)  # $9.00
        self.assertEqual(cart.subtotal, 9.00)

        # 4. Apply 5% discount
        cart.apply_discount(percent=5.0)
        # 5% of 9.00 = 0.45, taxable = 8.55, tax = 0.68, total = 9.23
        self.assertEqual(cart.taxable_amount, 8.55)
        self.assertEqual(cart.grand_total, 9.23)

        # 5. Process checkout with cash ($10 tendered)
        sale, change, receipt = self.sale_svc.process_checkout(
            cashier=cashier,
            cart=cart,
            payment_method="Cash",
            tendered_amount=10.00,
        )

        self.assertIsNotNone(sale.sale_id)
        self.assertEqual(change, 0.77)
        self.assertIn("TOTAL PAYABLE:", receipt)
        self.assertIn("Change Due:", receipt)

        # 6. Verify inventory was decremented
        tea_after = self.inv_svc.find_by_code("BEV-01")
        self.assertEqual(tea_after.stock_qty, initial_stock - 2)

        # 7. Verify customer loyalty points were updated (+8 points for $8.55 spent)
        cust_after = self.cust_svc.get_by_id(customer.customer_id)
        self.assertEqual(cust_after.loyalty_points, initial_points + 8)

        # 8. Check analytics reflects new sale
        analytics = self.sale_svc.get_analytics()
        self.assertGreater(analytics["total_revenue"], 0)


if __name__ == "__main__":
    unittest.main()
