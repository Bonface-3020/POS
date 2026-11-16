PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales(sale_timestamp);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);

BEGIN TRANSACTION;

INSERT INTO sales (sale_id, cashier_id, customer_id, subtotal, tax_amount, total_amount, payment_method)
VALUES (1003, 'C101', 'CUS-001', 21.00, 3.36, 24.36, 'Mobile');

INSERT INTO sale_items (sale_id, sku, quantity, unit_price_at_sale, line_total)
VALUES
    (1003, 'BEV-01', 2, 4.50, 9.00),
    (1003, 'ELC-01', 1, 12.00, 12.00);

UPDATE products
SET stock_qty = stock_qty - 2
WHERE sku = 'BEV-01';

UPDATE products
SET stock_qty = stock_qty - 1
WHERE sku = 'ELC-01';

UPDATE customers
SET loyalty_points = loyalty_points + CAST(21.00 AS INTEGER)
WHERE customer_id = 'CUS-001';

COMMIT;

