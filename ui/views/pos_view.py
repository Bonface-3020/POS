import time
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Optional
from config import CATEGORIES, CURRENCY_SYMBOL, DEFAULT_TAX_RATE
from models.customer import Customer
from models.product import Product
from services.cart_service import CartService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService
from services.sale_service import SaleService
from services.auth_service import AuthService
from ui.components.modal_overlay import ModalOverlay
from ui.components.customer_modal import CustomerModal
from ui.components.payment_modal import PaymentModal
from ui.components.receipt_modal import ReceiptModal
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_WARNING,
    COLOR_WARNING_HOVER,
    get_font,
)


class POSView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        auth_service: AuthService,
        inventory_service: InventoryService,
        cart_service: CartService,
        sale_service: SaleService,
        customer_service: CustomerService,
        on_sale_completed: Optional[callable] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.auth_service = auth_service
        self.inventory_service = inventory_service
        self.cart_service = cart_service
        self.sale_service = sale_service
        self.customer_service = customer_service
        self.on_sale_completed = on_sale_completed

        self.selected_category = "All"
        self.search_var = ctk.StringVar()
        self.discount_var = ctk.StringVar(value="0")

        self._build_ui()
        self.refresh_catalog()
        self.refresh_cart()

    def _build_ui(self):
        # Two-pane layout: Left (Catalog) and Right (Cart & Checkout)
        self.grid_columnconfigure(0, weight=6)  # Catalog 60%
        self.grid_columnconfigure(1, weight=4)  # Cart 40%
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANE: CATALOG & SEARCH
        # ==========================================
        left_pane = ctk.CTkFrame(self, corner_radius=12)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        left_pane.grid_rowconfigure(2, weight=1)
        left_pane.grid_columnconfigure(0, weight=1)

        # Search Bar
        search_frame = ctk.CTkFrame(left_pane, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="🔍 Search product name, SKU, or scan barcode...",
            font=get_font(13),
            height=40,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_catalog())
        self.search_entry.bind("<Return>", lambda event: self._on_barcode_or_sku_enter())

        clear_search_btn = ctk.CTkButton(
            search_frame,
            text="✕ Clear",
            width=70,
            height=40,
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(12, "bold"),
            command=self._clear_search,
        )
        clear_search_btn.pack(side="right")

        # Category Filter Pills
        category_bar = ctk.CTkFrame(left_pane, fg_color="transparent")
        category_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self.category_buttons: Dict[str, ctk.CTkButton] = {}
        all_cats = ["All"] + CATEGORIES

        for cat in all_cats:
            btn = ctk.CTkButton(
                category_bar,
                text=cat,
                height=32,
                corner_radius=16,
                font=get_font(12, "bold"),
                fg_color=COLOR_PRIMARY if cat == "All" else "#334155",
                hover_color=COLOR_PRIMARY_HOVER,
                command=lambda c=cat: self._set_category(c),
            )
            btn.pack(side="left", padx=3)
            self.category_buttons[cat] = btn

        # Product Catalog Grid Container
        self.catalog_scroll = ctk.CTkScrollableFrame(left_pane, corner_radius=10)
        self.catalog_scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.catalog_scroll.grid_columnconfigure((0, 1, 2), weight=1)

        # ==========================================
        # RIGHT PANE: CART & CHECKOUT
        # ==========================================
        right_pane = ctk.CTkFrame(self, corner_radius=12)
        right_pane.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_pane.grid_rowconfigure(2, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)

        # Customer Header
        cust_bar = ctk.CTkFrame(right_pane, corner_radius=10)
        cust_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.cust_info_label = ctk.CTkLabel(
            cust_bar,
            text="👤 Walk-in Customer",
            font=get_font(13, "bold"),
        )
        self.cust_info_label.pack(side="left", padx=12, pady=10)

        cust_btn_frame = ctk.CTkFrame(cust_bar, fg_color="transparent")
        cust_btn_frame.pack(side="right", padx=10, pady=6)

        self.select_cust_btn = ctk.CTkButton(
            cust_btn_frame,
            text="Select / Add",
            height=28,
            width=90,
            font=get_font(11, "bold"),
            command=self._open_customer_selector,
        )
        self.select_cust_btn.pack(side="left", padx=2)

        self.clear_cust_btn = ctk.CTkButton(
            cust_btn_frame,
            text="✕",
            height=28,
            width=28,
            fg_color="#475569",
            hover_color="#334155",
            font=get_font(11, "bold"),
            command=self._clear_customer,
        )
        self.clear_cust_btn.pack(side="left", padx=2)

        # Cart Table Header
        cart_header = ctk.CTkFrame(right_pane, fg_color="#334155", height=32, corner_radius=6)
        cart_header.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 4))
        cart_header.pack_propagate(False)

        ctk.CTkLabel(cart_header, text="Item", font=get_font(11, "bold"), width=140, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(cart_header, text="Qty", font=get_font(11, "bold"), width=70, anchor="center").pack(side="left")
        ctk.CTkLabel(cart_header, text="Price", font=get_font(11, "bold"), width=60, anchor="e").pack(side="left", padx=5)
        ctk.CTkLabel(cart_header, text="Total", font=get_font(11, "bold"), width=70, anchor="e").pack(side="left", padx=5)

        # Cart Items Scrollable List
        self.cart_scroll = ctk.CTkScrollableFrame(right_pane, corner_radius=8)
        self.cart_scroll.grid(row=2, column=0, sticky="nsew", padx=14, pady=4)

        # Summary & Actions Area
        summary_frame = ctk.CTkFrame(right_pane, corner_radius=10)
        summary_frame.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 14))

        # Discount & Details Row
        calc_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        calc_row.pack(fill="x", padx=14, pady=(10, 4))

        # Subtotal
        sub_row = ctk.CTkFrame(calc_row, fg_color="transparent")
        sub_row.pack(fill="x", pady=2)
        ctk.CTkLabel(sub_row, text="Subtotal:", font=get_font(12)).pack(side="left")
        self.subtotal_label = ctk.CTkLabel(sub_row, text=f"{CURRENCY_SYMBOL}0.00", font=get_font(12, "bold"))
        self.subtotal_label.pack(side="right")

        # Discount Selector
        disc_row = ctk.CTkFrame(calc_row, fg_color="transparent")
        disc_row.pack(fill="x", pady=2)
        ctk.CTkLabel(disc_row, text="Discount:", font=get_font(12)).pack(side="left")

        disc_btns = ctk.CTkFrame(disc_row, fg_color="transparent")
        disc_btns.pack(side="right")
        for pct in [0, 5, 10, 15]:
            dbtn = ctk.CTkButton(
                disc_btns,
                text=f"{pct}%",
                width=38,
                height=22,
                font=get_font(10, "bold"),
                fg_color="#334155",
                hover_color="#475569",
                command=lambda p=pct: self._apply_discount_pct(p),
            )
            dbtn.pack(side="left", padx=2)

        # Tax
        tax_row = ctk.CTkFrame(calc_row, fg_color="transparent")
        tax_row.pack(fill="x", pady=2)
        ctk.CTkLabel(tax_row, text=f"Tax / VAT ({int(DEFAULT_TAX_RATE*100)}%):", font=get_font(12)).pack(side="left")
        self.tax_label = ctk.CTkLabel(tax_row, text=f"{CURRENCY_SYMBOL}0.00", font=get_font(12, "bold"))
        self.tax_label.pack(side="right")

        # Divider
        ctk.CTkFrame(summary_frame, height=1, fg_color="#475569").pack(fill="x", padx=14, pady=6)

        # Grand Total
        total_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        total_row.pack(fill="x", padx=14, pady=(2, 10))
        ctk.CTkLabel(total_row, text="TOTAL DUE:", font=get_font(16, "bold")).pack(side="left")
        self.grand_total_label = ctk.CTkLabel(
            total_row,
            text=f"{CURRENCY_SYMBOL}0.00",
            font=get_font(24, "bold"),
            text_color=COLOR_PRIMARY,
        )
        self.grand_total_label.pack(side="right")

        # Cart Action Buttons
        actions_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        actions_row.pack(fill="x", padx=14, pady=(0, 6))

        self.clear_cart_btn = ctk.CTkButton(
            actions_row,
            text="Clear",
            font=get_font(12, "bold"),
            height=34,
            fg_color="#334155",
            hover_color=COLOR_DANGER_HOVER,
            command=self._clear_cart,
        )
        self.clear_cart_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.hold_btn = ctk.CTkButton(
            actions_row,
            text="Hold Cart",
            font=get_font(12, "bold"),
            height=34,
            fg_color="#334155",
            hover_color=COLOR_WARNING_HOVER,
            command=self._hold_cart,
        )
        self.hold_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.recall_btn = ctk.CTkButton(
            actions_row,
            text="Recall (0)",
            font=get_font(12, "bold"),
            height=34,
            fg_color="#334155",
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._recall_cart_dialog,
        )
        self.recall_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Main Checkout Button
        self.checkout_btn = ctk.CTkButton(
            summary_frame,
            text="Checkout & Pay",
            font=get_font(16, "bold"),
            height=46,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._open_payment,
        )
        self.checkout_btn.pack(fill="x", padx=14, pady=(4, 12))

    # ==========================================
    # CATALOG LOGIC
    # ==========================================
    def refresh_catalog(self):
        query = self.search_var.get().strip()
        products = self.inventory_service.get_products(
            query=query,
            category=self.selected_category if self.selected_category != "All" else None,
            only_active=True,
        )

        for widget in self.catalog_scroll.winfo_children():
            widget.destroy()

        if not products:
            empty_msg = ctk.CTkLabel(
                self.catalog_scroll,
                text="No matching products found.",
                font=get_font(14),
                text_color="gray",
            )
            empty_msg.pack(pady=40)
            return

        columns = 3
        for i, prod in enumerate(products):
            row = i // columns
            col = i % columns
            card = self._create_product_card(self.catalog_scroll, prod)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def _create_product_card(self, parent, prod: Product) -> ctk.CTkFrame:
        is_avail = prod.is_in_stock
        hand_cursor = "pointinghand" if is_avail else "arrow"

        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1E293B", cursor=hand_cursor)
        card.grid_columnconfigure(0, weight=1)

        cat_badge = ctk.CTkLabel(
            card,
            text=prod.category.upper(),
            font=get_font(9, "bold"),
            text_color="#94A3B8",
            cursor=hand_cursor,
        )
        cat_badge.pack(anchor="w", padx=12, pady=(10, 0))

        name_label = ctk.CTkLabel(
            card,
            text=prod.name,
            font=get_font(13, "bold"),
            wraplength=140,
            justify="left",
            anchor="w",
            cursor=hand_cursor,
        )
        name_label.pack(anchor="w", padx=12, pady=(2, 4))

        sku_text = f"SKU: {prod.sku}"
        sku_label = ctk.CTkLabel(
            card,
            text=sku_text,
            font=get_font(10),
            text_color="#64748B",
            cursor=hand_cursor,
        )
        sku_label.pack(anchor="w", padx=12, pady=(0, 6))

        bottom_bar = ctk.CTkFrame(card, fg_color="transparent", cursor=hand_cursor)
        bottom_bar.pack(fill="x", padx=12, pady=(0, 8))

        price_label = ctk.CTkLabel(
            bottom_bar,
            text=f"{CURRENCY_SYMBOL}{prod.unit_price:.2f}",
            font=get_font(15, "bold"),
            text_color=COLOR_PRIMARY,
            cursor=hand_cursor,
        )
        price_label.pack(side="left")

        if prod.is_out_of_stock:
            stock_color = COLOR_DANGER
            stock_text = "Out of Stock"
        elif prod.is_low_stock:
            stock_color = COLOR_WARNING
            stock_text = f"Low: {prod.stock_qty}"
        else:
            stock_color = "#10B981"
            stock_text = f"{prod.stock_qty} left"

        stock_badge = ctk.CTkLabel(
            bottom_bar,
            text=stock_text,
            font=get_font(10, "bold"),
            text_color=stock_color,
            cursor=hand_cursor,
        )
        stock_badge.pack(side="right")

        add_btn = ctk.CTkButton(
            card,
            text="+ Add to Cart" if is_avail else "Out of Stock",
            height=34,
            font=get_font(12, "bold"),
            fg_color=COLOR_PRIMARY if is_avail else "#475569",
            hover_color=COLOR_PRIMARY_HOVER if is_avail else "#475569",
            state="normal" if is_avail else "disabled",
            command=lambda p=prod: self._add_product_to_cart(p),
        )
        add_btn.pack(fill="x", padx=12, pady=(0, 12))

        # Make entire card responsive to trackpad taps
        if is_avail:
            card_last_click = [0.0]
            def on_card_click(event=None):
                now = time.time()
                if now - card_last_click[0] < 0.22:
                    return
                card_last_click[0] = now
                self._add_product_to_cart(prod)

            for w in [card, cat_badge, name_label, sku_label, bottom_bar, price_label, stock_badge]:
                w.bind("<Button-1>", on_card_click)
                w.bind("<ButtonRelease-1>", on_card_click)

        return card

    def _set_category(self, cat: str):
        self.selected_category = cat
        for c, btn in self.category_buttons.items():
            if c == cat:
                btn.configure(fg_color=COLOR_PRIMARY)
            else:
                btn.configure(fg_color="#334155")
        self.refresh_catalog()

    def _clear_search(self):
        self.search_var.set("")
        self.refresh_catalog()
        self.search_entry.focus_set()

    def _on_barcode_or_sku_enter(self):
        code = self.search_var.get().strip()
        if not code:
            return
        prod = self.inventory_service.find_by_code(code)
        if prod:
            self._add_product_to_cart(prod)
            self.search_var.set("")
            self.refresh_catalog()
        else:
            self.refresh_catalog()

    # ==========================================
    # CART LOGIC
    # ==========================================
    def _add_product_to_cart(self, prod: Product):
        try:
            self.cart_service.add_item(prod, quantity=1)
            self.refresh_cart()
        except Exception as e:
            messagebox.showwarning("Cannot Add Item", str(e))

    def refresh_cart(self):
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()

        if self.cart_service.is_empty:
            empty_card = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
            empty_card.pack(fill="both", expand=True, pady=40)
            ctk.CTkLabel(
                empty_card,
                text="🛒",
                font=get_font(32),
            ).pack()
            ctk.CTkLabel(
                empty_card,
                text="Cart is empty.\nSelect products to begin sale.",
                font=get_font(13),
                text_color="gray",
            ).pack(pady=6)
            self.checkout_btn.configure(state="disabled")
            self.clear_cart_btn.configure(state="disabled")
            self.hold_btn.configure(state="disabled")
        else:
            self.checkout_btn.configure(state="normal")
            self.clear_cart_btn.configure(state="normal")
            self.hold_btn.configure(state="normal")

            for sku, item in self.cart_service.items.items():
                row = self._create_cart_row(self.cart_scroll, item)
                row.pack(fill="x", pady=3)

        self.subtotal_label.configure(text=f"{CURRENCY_SYMBOL}{self.cart_service.subtotal:.2f}")
        self.tax_label.configure(text=f"{CURRENCY_SYMBOL}{self.cart_service.tax_amount:.2f}")
        self.grand_total_label.configure(text=f"{CURRENCY_SYMBOL}{self.cart_service.grand_total:.2f}")
        self.checkout_btn.configure(
            text=f"Checkout ({CURRENCY_SYMBOL}{self.cart_service.grand_total:.2f})"
        )

        if self.cart_service.customer:
            cust = self.cart_service.customer
            self.cust_info_label.configure(
                text=f"👤 {cust.name} ({cust.loyalty_points} pts)"
            )
            self.clear_cust_btn.configure(state="normal")
        else:
            self.cust_info_label.configure(text="👤 Walk-in Customer")
            self.clear_cust_btn.configure(state="disabled")

        held_count = len(self.cart_service.held_carts)
        self.recall_btn.configure(text=f"Recall ({held_count})")

    def _create_cart_row(self, parent, item) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, corner_radius=6, fg_color="#1E293B")

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        name_lbl = ctk.CTkLabel(
            left,
            text=item.product.name,
            font=get_font(12, "bold"),
            anchor="w",
            wraplength=120,
        )
        name_lbl.pack(anchor="w")

        price_lbl = ctk.CTkLabel(
            left,
            text=f"{CURRENCY_SYMBOL}{item.unit_price:.2f} each",
            font=get_font(10),
            text_color="#94A3B8",
            anchor="w",
        )
        price_lbl.pack(anchor="w")

        qty_box = ctk.CTkFrame(row, fg_color="transparent")
        qty_box.pack(side="left", padx=4)

        minus_btn = ctk.CTkButton(
            qty_box,
            text="-",
            width=24,
            height=24,
            font=get_font(11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda s=item.product.sku: self._change_qty(s, -1),
        )
        minus_btn.pack(side="left", padx=1)

        qty_lbl = ctk.CTkLabel(
            qty_box,
            text=str(item.quantity),
            font=get_font(12, "bold"),
            width=28,
        )
        qty_lbl.pack(side="left")

        plus_btn = ctk.CTkButton(
            qty_box,
            text="+",
            width=24,
            height=24,
            font=get_font(11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda s=item.product.sku: self._change_qty(s, 1),
        )
        plus_btn.pack(side="left", padx=1)

        total_lbl = ctk.CTkLabel(
            row,
            text=f"{CURRENCY_SYMBOL}{item.line_total:.2f}",
            font=get_font(12, "bold"),
            width=65,
            anchor="e",
        )
        total_lbl.pack(side="left", padx=4)

        del_btn = ctk.CTkButton(
            row,
            text="✕",
            width=24,
            height=24,
            font=get_font(11, "bold"),
            fg_color="transparent",
            hover_color=COLOR_DANGER_HOVER,
            text_color="#94A3B8",
            command=lambda s=item.product.sku: self._remove_item(s),
        )
        del_btn.pack(side="right", padx=(2, 6))

        return row

    def _change_qty(self, sku: str, delta: int):
        if sku not in self.cart_service.items:
            return
        curr = self.cart_service.items[sku].quantity
        try:
            self.cart_service.set_quantity(sku, curr + delta)
            self.refresh_cart()
        except Exception as e:
            messagebox.showwarning("Stock Limit", str(e))

    def _remove_item(self, sku: str):
        self.cart_service.remove_item(sku)
        self.refresh_cart()

    def _clear_cart(self):
        if self.cart_service.is_empty:
            return
        if messagebox.askyesno("Clear Cart", "Are you sure you want to clear the entire cart?"):
            self.cart_service.clear()
            self.refresh_cart()

    def _apply_discount_pct(self, pct: float):
        self.cart_service.apply_discount(percent=pct)
        self.refresh_cart()

    def _hold_cart(self):
        try:
            note = f"Held by {self.auth_service.current_cashier.full_name if self.auth_service.current_cashier else 'Cashier'}"
            cart_id = self.cart_service.hold_current_cart(note)
            messagebox.showinfo("Cart Held", f"Cart saved under ID: {cart_id}\nYou can recall it anytime.")
            self.refresh_cart()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _recall_cart_dialog(self):
        held = self.cart_service.list_held_carts()
        if not held:
            messagebox.showinfo("Held Carts", "There are currently no held carts.")
            return

        dialog = ModalOverlay(self, width=480, height=420)
        card = dialog.card

        ctk.CTkLabel(card, text="Recall Held Cart", font=get_font(16, "bold")).pack(padx=20, pady=(15, 10), anchor="w")

        scroll = ctk.CTkScrollableFrame(card, fg_color="#0F172A")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        for hc in held:
            row = ctk.CTkFrame(scroll, corner_radius=6, fg_color="#1E293B")
            row.pack(fill="x", pady=4)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(info, text=f"{hc['id']} ({hc['time']})", font=get_font(12, "bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{hc['note']} - Total: {CURRENCY_SYMBOL}{hc['total']:.2f}", font=get_font(11), text_color="gray").pack(anchor="w")

            recall_btn = ctk.CTkButton(
                row,
                text="Recall",
                width=75,
                height=30,
                font=get_font(11, "bold"),
                command=lambda cid=hc["id"]: self._do_recall(cid, dialog),
            )
            recall_btn.pack(side="right", padx=10)

        close_btn = ctk.CTkButton(
            card,
            text="Close",
            fg_color="gray",
            hover_color="#4B5563",
            font=get_font(12, "bold"),
            height=36,
            command=dialog.destroy,
        )
        close_btn.pack(fill="x", padx=20, pady=(10, 15))

    def _do_recall(self, cart_id: str, dialog):
        if not self.cart_service.is_empty:
            if not messagebox.askyesno("Overwrite Cart?", "Your active cart has items. Overwrite with held cart?"):
                return
        self.cart_service.recall_cart(cart_id)
        dialog.destroy()
        self.refresh_cart()

    # ==========================================
    # CUSTOMER SELECTION
    # ==========================================
    def _open_customer_selector(self):
        dialog = ModalOverlay(self, width=540, height=520)
        card = dialog.card

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        ctk.CTkLabel(header, text="Customer Loyalty Lookup", font=get_font(16, "bold")).pack(side="left")

        new_btn = ctk.CTkButton(
            header,
            text="+ New Customer",
            font=get_font(12, "bold"),
            height=32,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=lambda: self._open_new_customer_modal(dialog),
        )
        new_btn.pack(side="right")

        search_box = ctk.CTkEntry(card, placeholder_text="Search by name or phone number...", font=get_font(13), height=38)
        search_box.pack(fill="x", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(card, fg_color="#0F172A")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        def populate(q=""):
            for w in scroll.winfo_children():
                w.destroy()
            custs = self.customer_service.search(q)
            for c in custs:
                crow = ctk.CTkFrame(scroll, corner_radius=6, fg_color="#1E293B")
                crow.pack(fill="x", pady=3)

                info = ctk.CTkFrame(crow, fg_color="transparent")
                info.pack(side="left", padx=10, pady=6)
                ctk.CTkLabel(info, text=f"{c.name} ({c.phone_number})", font=get_font(12, "bold")).pack(anchor="w")
                ctk.CTkLabel(info, text=f"ID: {c.customer_id} | Loyalty: {c.loyalty_points} pts", font=get_font(11), text_color="#10B981").pack(anchor="w")

                select_b = ctk.CTkButton(
                    crow,
                    text="Select",
                    width=70,
                    height=28,
                    font=get_font(11, "bold"),
                    command=lambda cust=c: self._select_customer_done(cust, dialog),
                )
                select_b.pack(side="right", padx=10)

        search_box.bind("<KeyRelease>", lambda event: populate(search_box.get()))
        populate()

        close_btn = ctk.CTkButton(
            card,
            text="Close",
            fg_color="gray",
            hover_color="#4B5563",
            font=get_font(12, "bold"),
            height=36,
            command=dialog.destroy,
        )
        close_btn.pack(fill="x", padx=20, pady=(10, 15))

    def _select_customer_done(self, customer: Customer, dialog):
        self.cart_service.set_customer(customer)
        dialog.destroy()
        self.refresh_cart()

    def _clear_customer(self):
        self.cart_service.set_customer(None)
        self.refresh_cart()

    def _open_new_customer_modal(self, parent_dialog):
        def on_saved(data):
            c = self.customer_service.create_customer(
                name=data["name"],
                phone=data["phone_number"],
                initial_points=data["loyalty_points"],
            )
            self.cart_service.set_customer(c)
            parent_dialog.destroy()
            self.refresh_cart()

        CustomerModal(self, on_save=on_saved)

    # ==========================================
    # CHECKOUT & PAYMENT
    # ==========================================
    def _open_payment(self):
        if self.cart_service.is_empty:
            return

        cust_name = self.cart_service.customer.name if self.cart_service.customer else "Walk-in Guest"

        PaymentModal(
            self,
            total_amount=self.cart_service.grand_total,
            customer_name=cust_name,
            on_confirm=self._finalize_payment,
        )

    def _finalize_payment(self, payment_method: str, tendered_amount: float):
        try:
            cashier = self.auth_service.current_cashier
            sale, change, receipt_text = self.sale_service.process_checkout(
                cashier=cashier,
                cart=self.cart_service,
                payment_method=payment_method,
                tendered_amount=tendered_amount,
            )

            # Auto save receipt to file
            self.sale_service.save_receipt_file(receipt_text, sale.sale_id)

            # Refresh views
            self.refresh_cart()
            self.refresh_catalog()

            if self.on_sale_completed:
                self.on_sale_completed()

            # Show receipt modal
            ReceiptModal(self, receipt_text=receipt_text, sale_id=sale.sale_id)

        except Exception as e:
            messagebox.showerror("Checkout Failed", str(e))
