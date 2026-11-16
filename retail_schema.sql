PRAGMA foreign_keys = ON;

-- Run with: sqlite3 -header -column retail_pulse.db < retail_schema.sql
BEGIN TRANSACTION;

DROP TABLE IF EXISTS sale_items;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS cashiers;

CREATE TABLE cashiers (
    cashier_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    pin_code NOT NULL,
    role TEXT NOT NULL DEFAULT 'Cashier' CHECK (role IN ('Cashier', 'Manager')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('Beverages', 'Snacks', 'Electronics', 'Produce', 'General')),
    unit_price REAL NOT NULL CHECK (unit_price > 0.0),
    stock_qty INTEGER NOT NULL CHECK (stock_qty >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    barcode TEXT UNIQUE,
    reorder_threshold INTEGER NOT NULL DEFAULT 5 CHECK (reorder_threshold >= 0)
);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL UNIQUE,
    loyalty_points INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cashier_id TEXT NOT NULL,
    customer_id TEXT,
    sale_timestamp TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    subtotal REAL NOT NULL CHECK (subtotal >= 0.0),
    tax_amount REAL NOT NULL CHECK (tax_amount >= 0.0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0.0),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Cash', 'Card', 'Mobile')),

    FOREIGN KEY (cashier_id) REFERENCES cashiers(cashier_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE sale_items (
    sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_at_sale REAL NOT NULL CHECK (unit_price_at_sale > 0.0),
    line_total REAL NOT NULL CHECK (line_total > 0.0),

    FOREIGN KEY (sale_id) REFERENCES sales(sale_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (sku) REFERENCES products(sku)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

INSERT INTO cashiers (cashier_id, full_name, pin_code, role) VALUES
('C101', 'Mercy Chebet', '1234', 'Cashier'),
('M901', 'Kiprotich Koech', '9999', 'Manager');

INSERT INTO customers (customer_id, name, phone_number, loyalty_points) VALUES
('CUS-001', 'Amina Njeri', '+254700123456', 25);

INSERT INTO products (sku, name, category, unit_price, stock_qty) VALUES
('BEV-01', 'Kenyan Highlands Tea 500g', 'Beverages', 4.50, 45),
('BEV-02', 'Mount Kenya Spring Water 1L', 'Beverages', 1.20, 120),
('SNK-01', 'Roasted Spiced Peanuts 200g', 'Snacks', 2.00, 30),
('ELC-01', 'USB-C Fast Charging Cable', 'Electronics', 12.00, 15),
('BEV-03', 'Kenyan Arabica Coffee 250g', 'Beverages', 6.80, 24),
('BEV-04', 'Tropical Mango Juice 500ml', 'Beverages', 2.40, 36),
('SNK-02', 'Salted Maize Crisps 100g', 'Snacks', 1.50, 40),
('ELC-02', 'AA Batteries 4-pack', 'Electronics', 5.75, 18),
('PRD-01', 'Ripe Bananas 1kg', 'Produce', 2.30, 28),
('GEN-01', 'Laundry Detergent 1kg', 'General', 5.80, 20),
('GEN-02', 'Multipurpose Cleaning Cloth', 'General', 1.90, 32);

INSERT INTO sales (sale_id, cashier_id, subtotal, tax_amount, total_amount, payment_method)
VALUES (1001, 'C101', 7.70, 0.62, 8.32, 'Cash');

INSERT INTO sale_items (sale_id, sku, quantity, unit_price_at_sale, line_total) VALUES
(1001, 'BEV-01', 1, 4.50, 4.50),
(1001, 'SNK-01', 1, 2.00, 2.00),
(1001, 'BEV-02', 1, 1.20, 1.20);

INSERT INTO sales (sale_id, cashier_id, customer_id, subtotal, tax_amount, total_amount, payment_method)
VALUES (1002, 'C101', 'CUS-001', 3.50, 0.28, 3.78, 'Mobile');

INSERT INTO sale_items (sale_id, sku, quantity, unit_price_at_sale, line_total) VALUES
(1002, 'PRD-01', 1, 2.30, 2.30),
(1002, 'BEV-02', 1, 1.20, 1.20);

COMMIT;

SELECT
    s.sale_id AS receipt,
    p.name AS item,
    si.quantity AS qty,
    printf('%.2f', si.unit_price_at_sale) AS unit_price,
    printf('%.2f', si.line_total) AS line_total,
    printf('%.2f', s.total_amount) AS sale_total
FROM sales AS s
INNER JOIN sale_items AS si ON si.sale_id = s.sale_id
INNER JOIN products AS p ON p.sku = si.sku
WHERE s.sale_id = 1002
ORDER BY si.sale_item_id;
