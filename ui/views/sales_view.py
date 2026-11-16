import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from config import CURRENCY_SYMBOL
from models.sale import Sale
from services.sale_service import SaleService
from ui.components.receipt_modal import ReceiptModal
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    get_font,
)


class SalesView(ctk.CTkFrame):
    def __init__(self, parent, sale_service: SaleService):
        super().__init__(parent, fg_color="transparent")
        self.sale_service = sale_service
        self.selected_sale: Optional[Sale] = None

        self.search_var = ctk.StringVar()
        self.method_var = ctk.StringVar(value="All")

        self._build_ui()
        self.refresh_sales()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=6)  # Table 60%
        self.grid_columnconfigure(1, weight=4)  # Receipt preview 40%
        self.grid_rowconfigure(1, weight=1)

        # Filter Header Bar
        filter_bar = ctk.CTkFrame(self, corner_radius=10)
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            textvariable=self.search_var,
            placeholder_text="🔍 Search Receipt #, customer, or cashier...",
            font=get_font(13),
            height=36,
            width=320,
        )
        self.search_entry.pack(side="left", padx=12, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_sales())

        method_menu = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.method_var,
            values=["All", "Cash", "Card", "Mobile"],
            command=lambda val: self.refresh_sales(),
            font=get_font(12),
            height=36,
            width=120,
        )
        method_menu.pack(side="left", padx=6, pady=10)

        refresh_btn = ctk.CTkButton(
            filter_bar,
            text="🔄 Refresh",
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(12, "bold"),
            height=36,
            width=90,
            command=self.refresh_sales,
        )
        refresh_btn.pack(side="right", padx=12, pady=10)

        # ==========================================
        # LEFT PANE: SALES HISTORY TABLE
        # ==========================================
        left_pane = ctk.CTkFrame(self, corner_radius=10)
        left_pane.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(0, 15))
        left_pane.grid_columnconfigure(0, weight=1)
        left_pane.grid_rowconfigure(1, weight=1)

        # Table Headers
        table_hdr = ctk.CTkFrame(left_pane, fg_color="#334155", height=38, corner_radius=6)
        table_hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        table_hdr.pack_propagate(False)

        ctk.CTkLabel(table_hdr, text="Receipt #", font=get_font(12, "bold"), width=80, anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(table_hdr, text="Date / Time", font=get_font(12, "bold"), width=130, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(table_hdr, text="Cashier", font=get_font(12, "bold"), width=110, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(table_hdr, text="Customer", font=get_font(12, "bold"), width=120, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(table_hdr, text="Payment", font=get_font(12, "bold"), width=80, anchor="center").pack(side="left", padx=4)
        ctk.CTkLabel(table_hdr, text="Total", font=get_font(12, "bold"), width=90, anchor="e").pack(side="right", padx=10)

        # Scrollable Rows
        self.sales_scroll = ctk.CTkScrollableFrame(left_pane, corner_radius=8)
        self.sales_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # ==========================================
        # RIGHT PANE: RECEIPT DETAIL PREVIEW
        # ==========================================
        self.right_pane = ctk.CTkFrame(self, corner_radius=10)
        self.right_pane.grid(row=1, column=1, sticky="nsew", padx=(8, 15), pady=(0, 15))
        self.right_pane.grid_columnconfigure(0, weight=1)
        self.right_pane.grid_rowconfigure(1, weight=1)

        # Receipt Title Bar
        r_hdr = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        r_hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 6))

        self.preview_title = ctk.CTkLabel(
            r_hdr,
            text="Receipt Inspector",
            font=get_font(15, "bold"),
        )
        self.preview_title.pack(side="left")

        # Receipt Mono Textbox
        self.receipt_box = ctk.CTkTextbox(
            self.right_pane,
            font=get_font(11, mono=True),
            corner_radius=8,
            wrap="none",
        )
        self.receipt_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=6)
        self.receipt_box.insert("1.0", "Select a sale from the list to view full receipt details.")
        self.receipt_box.configure(state="disabled")

        # Receipt Actions
        r_actions = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        r_actions.grid(row=2, column=0, sticky="ew", padx=14, pady=(6, 14))

        self.reprint_btn = ctk.CTkButton(
            r_actions,
            text="🖨 Print / Save Receipt",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=38,
            state="disabled",
            command=self._open_receipt_modal,
        )
        self.reprint_btn.pack(fill="x")

    def refresh_sales(self):
        query = self.search_var.get().strip()
        method = self.method_var.get()

        sales = self.sale_service.get_recent_sales(
            limit=100,
            query=query,
            payment_method=method if method != "All" else None,
        )

        for w in self.sales_scroll.winfo_children():
            w.destroy()

        if not sales:
            empty = ctk.CTkLabel(
                self.sales_scroll,
                text="No transaction records found.",
                font=get_font(13),
                text_color="gray",
            )
            empty.pack(pady=30)
            return

        for s in sales:
            row = self._create_sale_row(self.sales_scroll, s)
            row.pack(fill="x", pady=2)

    def _create_sale_row(self, parent, sale: Sale) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, corner_radius=6, fg_color="#1E293B", height=42)
        row.pack_propagate(False)

        # Receipt #
        ctk.CTkLabel(row, text=f"#{sale.sale_id}", font=get_font(12, "bold"), width=80, anchor="w").pack(side="left", padx=8)

        # Date
        dt_str = sale.sale_timestamp or "-"
        ctk.CTkLabel(row, text=dt_str, font=get_font(11), width=130, anchor="w", text_color="#94A3B8").pack(side="left", padx=4)

        # Cashier
        c_name = sale.cashier_name or sale.cashier_id
        ctk.CTkLabel(row, text=c_name, font=get_font(11), width=110, anchor="w").pack(side="left", padx=4)

        # Customer
        cust_name = sale.customer_name or "Walk-in"
        ctk.CTkLabel(row, text=cust_name, font=get_font(11), width=120, anchor="w", text_color="#64748B").pack(side="left", padx=4)

        # Payment Method Pill
        method_colors = {"Cash": "#10B981", "Card": "#3B82F6", "Mobile": "#8B5CF6"}
        m_color = method_colors.get(sale.payment_method, "#94A3B8")
        ctk.CTkLabel(row, text=sale.payment_method, font=get_font(11, "bold"), width=80, text_color=m_color, anchor="center").pack(side="left", padx=4)

        # Total
        ctk.CTkLabel(row, text=f"{CURRENCY_SYMBOL}{sale.total_amount:.2f}", font=get_font(13, "bold"), width=90, anchor="e", text_color=COLOR_PRIMARY).pack(side="right", padx=10)

        # Bind click to select
        row.bind("<Button-1>", lambda event, s=sale: self._select_sale(s))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda event, s=sale: self._select_sale(s))

        return row

    def _select_sale(self, sale_header: Sale):
        # Fetch full sale with line items
        full_sale = self.sale_service.get_sale_details(sale_header.sale_id)
        if not full_sale:
            return
        self.selected_sale = full_sale

        receipt_text = self.sale_service.format_receipt(
            sale=full_sale,
            discount_amount=0.0,
            original_subtotal=full_sale.subtotal,
            tendered_amount=full_sale.total_amount,
            change_due=0.0,
        )

        self.receipt_box.configure(state="normal")
        self.receipt_box.delete("1.0", "end")
        self.receipt_box.insert("1.0", receipt_text)
        self.receipt_box.configure(state="disabled")

        self.preview_title.configure(text=f"Receipt #{full_sale.sale_id}")
        self.reprint_btn.configure(state="normal")

    def _open_receipt_modal(self):
        if not self.selected_sale:
            return
        receipt_text = self.receipt_box.get("1.0", "end").strip()
        ReceiptModal(self, receipt_text=receipt_text, sale_id=self.selected_sale.sale_id)
