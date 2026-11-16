# RetailPulse POS (Point of Sale System)

A complete, production-grade Point of Sale (POS) desktop application engineered with a **Python** backend, **CustomTkinter** modern graphical user interface, and **SQLite** database using the **Data Access Object (DAO)** pattern with atomic transactions.

---

## Architecture & Project Structure

The project strictly follows separation of concerns:

```
POS/
├── main.py                     # Application entry point
├── config.py                   # App settings (tax rate, currency, theme constants)
├── retail_pulse.db             # SQLite database file
├── retail_schema.sql           # Base database schema DDL & initial seed data
├── transaction.sql             # SQL transaction documentation
├── database/
│   ├── __init__.py
│   └── connection.py           # Thread-safe SQLite connection & transaction manager
├── models/
│   ├── __init__.py
│   ├── cashier.py              # Cashier data model
│   ├── product.py              # Product data model with stock calculation
│   ├── customer.py             # Customer data model & loyalty tracking
│   └── sale.py                 # Sale & SaleItem data models
├── dao/
│   ├── __init__.py
│   ├── base_dao.py             # Base DAO helper
│   ├── cashier_dao.py          # Cashier authentication & CRUD operations
│   ├── product_dao.py          # Product catalog, barcode/SKU lookup, stock adjust
│   ├── customer_dao.py         # Customer search, registration, points adjust
│   └── sale_dao.py             # Atomic transaction checkout & analytics engine
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # Session management & role checks
│   ├── cart_service.py         # Cart state, discounts, taxes, hold/recall
│   ├── sale_service.py         # Checkout orchestration, receipt generation
│   ├── inventory_service.py    # Stock management, low stock alerts
│   └── customer_service.py     # CRM & loyalty services
├── ui/
│   ├── __init__.py
│   ├── app.py                  # CustomTkinter main application shell
│   ├── theme.py                # Styling, colors, typography
│   ├── components/
│   │   ├── __init__.py
│   │   ├── payment_modal.py    # Cash / Card / Mobile payment dialog with change calculator
│   │   ├── receipt_modal.py    # Digital receipt viewer with print & save options
│   │   ├── product_modal.py    # Add / Edit product dialog
│   │   └── customer_modal.py   # Add / Edit customer dialog
│   └── views/
│       ├── __init__.py
│       ├── login_view.py       # Staff login screen with numeric keypad
│       ├── pos_view.py         # Core POS terminal (catalog, search, cart, checkout)
│       ├── inventory_view.py   # Inventory management, stock monitor, restock
│       ├── sales_view.py       # Transactions history & receipt inspector
│       ├── customer_view.py    # Customer loyalty & registration
│       └── reports_view.py     # Analytics dashboard, KPIs, top products
└── tests/
    ├── __init__.py
    ├── test_dao.py             # DAO unit tests
    ├── test_services.py        # Business logic unit tests
    └── test_e2e.py             # Full end-to-end checkout & stock reduction test
```

---

## Features

### 1. Point of Sale Terminal (Register)
- **Visual Product Catalog**: Product cards with real-time stock badges (`In Stock`, `Low Stock`, `Out of Stock`).
- **Category Filter Pills**: Fast category switching (`All`, `Beverages`, `Snacks`, `Electronics`, `Produce`, `General`).
- **Omni-Search Bar**: Instant search across product name, SKU, or Barcode (supports physical barcode scanner input on Enter).
- **Interactive Cart**: Quantity increment/decrement buttons, individual item removal, clear cart.
- **Hold & Recall Cart**: Park active customer orders if a customer steps away and recall them later.
- **Discount Engine**: Quick percentage discounts (5%, 10%, 15%) or custom amounts.
- **Dynamic Tax Calculation**: Configurable tax rate (default 8% or 16%).

### 2. Multi-Payment Checkout & Receipts
- **Cash**: Preset tender bills ($5, $10, $20, $50, $100, Exact) with real-time change calculation.
- **Card**: Ready for EMV card readers.
- **Mobile**: Mobile money payments (M-Pesa, QR, etc.).
- **Digital Receipt Generator**: Itemized receipt preview with "Print Receipt" simulation and "Save to File" (`receipts/receipt_<id>.txt`).

### 3. Inventory Management
- Full catalog view with price, stock quantity, barcode, reorder threshold, and status.
- Add and edit products with validations.
- Quick restock dialog to top up items in seconds.
- Safe delete / deactivation (prevents deleting items linked to existing sales).
- Automatic low-stock notifications.

### 4. Sales History & Receipt Inspector
- Chronological list of all sales transactions.
- Filter by payment method, cashier, or customer.
- Instant itemized receipt preview for any past transaction.
- Option to re-print or re-save receipts.

### 5. Customer Loyalty (CRM)
- Search customers by phone number or name.
- Register new customers with phone and address.
- Automatic loyalty points accrual on each purchase (1 point per \$1 spent).
- Manual point adjustment option.

### 6. Analytics & Executive Reports
- Real-time KPI summary: Today's Revenue, Total Revenue, Total Orders, Average Order Value, Total Units Sold.
- Top 5 Selling Products by quantity and revenue.
- Revenue breakdown by payment method with progress visualization.
- Low-stock reorder center with 1-click restock.

### 7. Modern UI / UX
- Built with **CustomTkinter** for high-DPI crisp rendering.
- Dark mode and Light mode toggle.
- On-screen touch-friendly numeric keypad for touch monitors.
- Live digital clock in the header.

---

## Default Login Credentials

| Cashier Name | ID | PIN | Role |
| :--- | :--- | :--- | :--- |
| **Mercy Chebet** | `C101` | `1234` | Cashier |
| **Kiprotich Koech** | `M901` | `9999` | Manager |

> **Tip**: You can also use the one-click demo login buttons directly on the login screen.

---

## How to Run

1. Ensure Python 3.8+ and CustomTkinter are installed:
   ```bash
   pip install customtkinter pillow
   ```

2. Run the application:
   ```bash
   python3 main.py
   ```

3. Run automated tests:
   ```bash
   python3 -m unittest discover tests
   ```
