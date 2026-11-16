import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    APP_TITLE,
    BASE_DIR,
    CURRENCY_SYMBOL,
    LOYALTY_RATE,
    STORE_ADDRESS,
    STORE_NAME,
    STORE_PHONE,
)
from dao.sale_dao import SaleDAO
from models.cashier import Cashier
from models.sale import Sale, SaleItem
from services.cart_service import CartService


class SaleService:
    def __init__(self, sale_dao: Optional[SaleDAO] = None):
        self.sale_dao = sale_dao or SaleDAO()

    def process_checkout(
        self,
        cashier: Cashier,
        cart: CartService,
        payment_method: str,
        tendered_amount: float = 0.0,
    ) -> Tuple[Sale, float, str]:
        """
        Completes the sale transaction, updates stock and loyalty,
        and generates a formatted receipt.
        Returns: (completed_sale, change_due, receipt_text)
        """
        if cart.is_empty:
            raise ValueError("Cart is empty.")

        if payment_method not in ["Cash", "Card", "Mobile"]:
            raise ValueError(f"Invalid payment method: {payment_method}")

        total_payable = cart.grand_total

        change_due = 0.0
        if payment_method == "Cash":
            if tendered_amount < total_payable:
                raise ValueError(
                    f"Tendered amount {CURRENCY_SYMBOL}{tendered_amount:.2f} is less than total payable {CURRENCY_SYMBOL}{total_payable:.2f}."
                )
            change_due = round(tendered_amount - total_payable, 2)
        else:
            tendered_amount = total_payable

        # Loyalty points calculation
        loyalty_points_earned = int(cart.taxable_amount * LOYALTY_RATE) if cart.customer else 0

        # Construct Sale object
        sale = Sale(
            cashier_id=cashier.cashier_id,
            customer_id=cart.customer.customer_id if cart.customer else None,
            subtotal=cart.taxable_amount,  # After discount
            tax_amount=cart.tax_amount,
            total_amount=total_payable,
            payment_method=payment_method,
            cashier_name=cashier.full_name,
            customer_name=cart.customer.name if cart.customer else "Walk-in Customer",
        )

        sale_items = cart.to_sale_items()
        sale.items = sale_items

        # Perform atomic database transaction
        sale_id = self.sale_dao.create_sale(
            sale=sale,
            items=sale_items,
            loyalty_points_earned=loyalty_points_earned,
        )
        sale.sale_id = sale_id
        sale.sale_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate receipt
        receipt_text = self.format_receipt(
            sale=sale,
            discount_amount=cart.discount_amount,
            original_subtotal=cart.subtotal,
            tendered_amount=tendered_amount,
            change_due=change_due,
            loyalty_earned=loyalty_points_earned,
        )

        # Clear cart upon success
        cart.clear()

        return sale, change_due, receipt_text

    def format_receipt(
        self,
        sale: Sale,
        discount_amount: float = 0.0,
        original_subtotal: float = 0.0,
        tendered_amount: float = 0.0,
        change_due: float = 0.0,
        loyalty_earned: int = 0,
    ) -> str:
        width = 44
        sep = "-" * width
        dsep = "=" * width

        lines = [
            dsep,
            STORE_NAME.center(width),
            STORE_ADDRESS.center(width),
            f"Tel: {STORE_PHONE}".center(width),
            dsep,
            f"Receipt #: {sale.sale_id:<14} Date: {sale.sale_timestamp or datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Cashier: {sale.cashier_name or sale.cashier_id}",
            f"Customer: {sale.customer_name or 'Walk-in'}",
            sep,
            f"{'Item':<22} {'Qty':>4} {'Price':>7} {'Total':>8}",
            sep,
        ]

        for item in sale.items:
            name = item.product_name or item.sku
            if len(name) > 20:
                name = name[:18] + ".."
            price_str = f"{CURRENCY_SYMBOL}{item.unit_price_at_sale:.2f}"
            line_str = f"{CURRENCY_SYMBOL}{item.line_total:.2f}"
            lines.append(f"{name:<22} {item.quantity:>4} {price_str:>7} {line_str:>8}")

        lines.append(sep)

        if discount_amount > 0:
            orig = original_subtotal if original_subtotal > 0 else (sale.subtotal + discount_amount)
            lines.append(f"{'Items Total:':<30} {CURRENCY_SYMBOL}{orig:>11.2f}")
            lines.append(f"{'Discount:':<30} -{CURRENCY_SYMBOL}{discount_amount:>10.2f}")

        lines.append(f"{'Subtotal:':<30} {CURRENCY_SYMBOL}{sale.subtotal:>11.2f}")
        lines.append(f"{'Tax / VAT:':<30} {CURRENCY_SYMBOL}{sale.tax_amount:>11.2f}")
        lines.append(dsep)
        lines.append(f"{'TOTAL PAYABLE:':<30} {CURRENCY_SYMBOL}{sale.total_amount:>11.2f}")
        lines.append(dsep)
        lines.append(f"{'Payment Method:':<30} {sale.payment_method:>12}")

        if sale.payment_method == "Cash":
            lines.append(f"{'Cash Tendered:':<30} {CURRENCY_SYMBOL}{tendered_amount:>11.2f}")
            lines.append(f"{'Change Due:':<30} {CURRENCY_SYMBOL}{change_due:>11.2f}")

        if loyalty_earned > 0:
            lines.append(sep)
            lines.append(f"Loyalty Points Earned: +{loyalty_earned}".center(width))

        lines.extend([
            sep,
            "Thank you for shopping with us!".center(width),
            "Please retain receipt for exchange".center(width),
            dsep,
        ])

        return "\n".join(lines)

    def save_receipt_file(self, receipt_text: str, sale_id: int) -> Path:
        receipts_dir = BASE_DIR / "receipts"
        receipts_dir.mkdir(exist_ok=True)
        filepath = receipts_dir / f"receipt_{sale_id}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(receipt_text)
        return filepath

    def get_sale_details(self, sale_id: int) -> Optional[Sale]:
        return self.sale_dao.get_sale_by_id(sale_id)

    def get_recent_sales(
        self,
        limit: int = 50,
        query: Optional[str] = None,
        cashier_id: Optional[str] = None,
        payment_method: Optional[str] = None,
    ) -> List[Sale]:
        return self.sale_dao.get_recent_sales(
            limit=limit,
            query=query,
            cashier_id=cashier_id,
            payment_method=payment_method,
        )

    def get_analytics(self) -> Dict:
        return self.sale_dao.get_analytics_summary()
