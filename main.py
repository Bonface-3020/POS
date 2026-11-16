#!/usr/bin/env python3
"""
RetailPulse POS - Complete Point of Sale System
Backend: Python 3 with SQLite (DAO Pattern & Transactions)
Frontend: CustomTkinter (Modern Responsive Desktop UI)
"""

import sys
import os
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

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
from ui.app import RetailPulseApp
from ui.trackpad_patch import apply_macos_trackpad_patch


def main():
    # 0. Apply macOS trackpad & tap-to-click compatibility patch
    apply_macos_trackpad_patch()

    # 1. Initialize Database & verify schema
    db = DatabaseManager()

    # 2. Initialize Data Access Objects (DAOs)
    cashier_dao = CashierDAO(db)
    product_dao = ProductDAO(db)
    customer_dao = CustomerDAO(db)
    sale_dao = SaleDAO(db)

    # 3. Initialize Business Services
    auth_service = AuthService(cashier_dao)
    inventory_service = InventoryService(product_dao)
    cart_service = CartService()
    sale_service = SaleService(sale_dao)
    customer_service = CustomerService(customer_dao)

    # 4. Launch CustomTkinter GUI
    app = RetailPulseApp(
        auth_service=auth_service,
        inventory_service=inventory_service,
        cart_service=cart_service,
        sale_service=sale_service,
        customer_service=customer_service,
    )

    print("⚡ RetailPulse POS is running...")
    app.mainloop()


if __name__ == "__main__":
    main()
