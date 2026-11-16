import unittest
import sqlite3
import tempfile
import os
from pathlib import Path

from database.connection import DatabaseManager
from dao.cashier_dao import CashierDAO
from dao.product_dao import ProductDAO
from dao.customer_dao import CustomerDAO
from dao.sale_dao import SaleDAO
from models.cashier import Cashier
from models.product import Product
from models.customer import Customer
from models.sale import Sale, SaleItem


class TestDAOs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix=".db")
        cls.db = DatabaseManager(cls.temp_db_path)

        # Initialize schema
        schema_path = Path(__file__).resolve().parent.parent / "retail_schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

        with cls.db.get_connection() as conn:
            conn.executescript(sql)

        cls.cashier_dao = CashierDAO(cls.db)
        cls.product_dao = ProductDAO(cls.db)
        cls.customer_dao = CustomerDAO(cls.db)
        cls.sale_dao = SaleDAO(cls.db)

    @classmethod
    def tearDownClass(cls):
        os.close(cls.temp_db_fd)
        if os.path.exists(cls.temp_db_path):
            os.remove(cls.temp_db_path)

    def test_cashier_dao(self):
        # Auth existing
        cashier = self.cashier_dao.authenticate("C101", "1234")
        self.assertIsNotNone(cashier)
        self.assertEqual(cashier.full_name, "Mercy Chebet")

        # Wrong PIN
        wrong = self.cashier_dao.authenticate("C101", "0000")
        self.assertIsNone(wrong)

        # Pin-only auth
        mgr = self.cashier_dao.authenticate_by_pin("9999")
        self.assertIsNotNone(mgr)
        self.assertTrue(mgr.is_manager)

    def test_product_dao(self):
        products = self.product_dao.get_all()
        self.assertGreaterEqual(len(products), 10)

        # Search by query
        tea = self.product_dao.search(query="Tea")
        self.assertTrue(any(p.sku == "BEV-01" for p in tea))

        # Filter by category
        snacks = self.product_dao.search(category="Snacks")
        self.assertTrue(all(p.category == "Snacks" for p in snacks))

        # Update stock
        before = self.product_dao.get_by_sku("BEV-01").stock_qty
        self.product_dao.adjust_stock("BEV-01", 10)
        after = self.product_dao.get_by_sku("BEV-01").stock_qty
        self.assertEqual(after, before + 10)

    def test_customer_dao(self):
        cust = self.customer_dao.get_by_phone("+254700123456")
        self.assertIsNotNone(cust)
        self.assertEqual(cust.name, "Amina Njeri")

        # Create new customer
        new_c = Customer(
            customer_id="",
            name="John Doe",
            phone_number="+254711999888",
            loyalty_points=10,
        )
        created = self.customer_dao.create(new_c)
        self.assertTrue(created.customer_id.startswith("CUS-"))

        # Adjust points
        self.customer_dao.adjust_loyalty_points(created.customer_id, 25)
        updated = self.customer_dao.get_by_id(created.customer_id)
        self.assertEqual(updated.loyalty_points, 35)

    def test_sale_transaction_atomic(self):
        initial_stock = self.product_dao.get_by_sku("BEV-02").stock_qty
        sale = Sale(
            cashier_id="C101",
            customer_id="CUS-001",
            subtotal=2.40,
            tax_amount=0.19,
            total_amount=2.59,
            payment_method="Cash",
        )
        items = [
            SaleItem(sku="BEV-02", quantity=2, unit_price_at_sale=1.20, line_total=2.40),
        ]

        sale_id = self.sale_dao.create_sale(sale, items, loyalty_points_earned=2)
        self.assertGreater(sale_id, 1000)

        # Check stock decremented
        after_stock = self.product_dao.get_by_sku("BEV-02").stock_qty
        self.assertEqual(after_stock, initial_stock - 2)

        # Check retrieve sale with items
        fetched = self.sale_dao.get_sale_by_id(sale_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(len(fetched.items), 1)
        self.assertEqual(fetched.items[0].sku, "BEV-02")


if __name__ == "__main__":
    unittest.main()
