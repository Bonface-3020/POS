import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List
from config import CURRENCY_SYMBOL
from services.sale_service import SaleService
from services.inventory_service import InventoryService
from services.auth_service import AuthService
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_WARNING,
    COLOR_DANGER,
    get_font,
)


class ReportsView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        sale_service: SaleService,
        inventory_service: InventoryService,
        auth_service: AuthService,
    ):
        super().__init__(parent, fg_color="transparent")
        self.sale_service = sale_service
        self.inventory_service = inventory_service
        self.auth_service = auth_service

        self._build_ui()
        self.refresh_report()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        title = ctk.CTkLabel(
            hdr,
            text="📊 Analytics, Sales Reports & Inventory Health",
            font=get_font(16, "bold"),
        )
        title.pack(side="left", padx=14, pady=12)

        refresh_btn = ctk.CTkButton(
            hdr,
            text="🔄 Refresh Metrics",
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(12, "bold"),
            height=34,
            command=self.refresh_report,
        )
        refresh_btn.pack(side="right", padx=12, pady=10)

        # Scrollable container for all sections
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.scroll.grid_columnconfigure((0, 1), weight=1)

        # 1. Top KPI Row (5 metrics)
        self.kpi_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.kpi_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.kpi_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.kpi_today_rev = self._create_metric_card(self.kpi_row, 0, "Today's Revenue", f"{CURRENCY_SYMBOL}0.00", "#10B981")
        self.kpi_total_rev = self._create_metric_card(self.kpi_row, 1, "Total Revenue", f"{CURRENCY_SYMBOL}0.00", "#3B82F6")
        self.kpi_total_sales = self._create_metric_card(self.kpi_row, 2, "Total Orders", "0", "#8B5CF6")
        self.kpi_avg_ticket = self._create_metric_card(self.kpi_row, 3, "Avg Order Value", f"{CURRENCY_SYMBOL}0.00", "#06B6D4")
        self.kpi_items_sold = self._create_metric_card(self.kpi_row, 4, "Items Sold", "0", "#F59E0B")

        # 2. Split section: Left = Top 5 Products, Right = Payment Methods Breakdown
        # Left: Top Products Card
        self.top_products_card = ctk.CTkFrame(self.scroll, corner_radius=10)
        self.top_products_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 15))
        ctk.CTkLabel(self.top_products_card, text="🏆 Top Selling Products", font=get_font(14, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        self.top_prods_list = ctk.CTkFrame(self.top_products_card, fg_color="transparent")
        self.top_prods_list.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Right: Payment Methods Card
        self.payment_card = ctk.CTkFrame(self.scroll, corner_radius=10)
        self.payment_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 15))
        ctk.CTkLabel(self.payment_card, text="💳 Revenue by Payment Method", font=get_font(14, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        self.payment_list = ctk.CTkFrame(self.payment_card, fg_color="transparent")
        self.payment_list.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # 3. Bottom: Low Stock Action Center
        self.alerts_card = ctk.CTkFrame(self.scroll, corner_radius=10)
        self.alerts_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(self.alerts_card, text="⚠️ Low Stock & Reorder Alerts", font=get_font(14, "bold"), text_color=COLOR_WARNING).pack(anchor="w", padx=14, pady=(12, 8))
        self.alerts_list = ctk.CTkFrame(self.alerts_card, fg_color="transparent")
        self.alerts_list.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _create_metric_card(self, parent, col: int, title: str, value: str, color: str):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1E293B")
        card.grid(row=0, column=col, padx=4, sticky="ew")

        ctk.CTkLabel(card, text=title, font=get_font(11, "bold"), text_color="#94A3B8").pack(anchor="w", padx=12, pady=(12, 2))
        lbl = ctk.CTkLabel(card, text=value, font=get_font(20, "bold"), text_color=color)
        lbl.pack(anchor="w", padx=12, pady=(0, 12))
        return lbl

    def refresh_report(self):
        analytics = self.sale_service.get_analytics()

        # Update KPI Cards
        self.kpi_today_rev.configure(text=f"{CURRENCY_SYMBOL}{analytics['today_revenue']:,.2f}")
        self.kpi_total_rev.configure(text=f"{CURRENCY_SYMBOL}{analytics['total_revenue']:,.2f}")
        self.kpi_total_sales.configure(text=f"{analytics['total_sales']:,}")
        self.kpi_avg_ticket.configure(text=f"{CURRENCY_SYMBOL}{analytics['avg_order_value']:,.2f}")
        self.kpi_items_sold.configure(text=f"{analytics['total_items_sold']:,}")

        # Populate Top Products
        for w in self.top_prods_list.winfo_children():
            w.destroy()

        top_prods = analytics.get("top_products", [])
        if not top_prods:
            ctk.CTkLabel(self.top_prods_list, text="No sales data recorded yet.", text_color="gray").pack(pady=20)
        else:
            for rank, item in enumerate(top_prods, 1):
                row = ctk.CTkFrame(self.top_prods_list, corner_radius=6, fg_color="#1E293B")
                row.pack(fill="x", pady=3)

                ctk.CTkLabel(row, text=f"#{rank}", font=get_font(12, "bold"), width=30, text_color=COLOR_PRIMARY).pack(side="left", padx=8, pady=6)
                ctk.CTkLabel(row, text=item["name"], font=get_font(12), anchor="w").pack(side="left", fill="x", expand=True, padx=4)
                ctk.CTkLabel(row, text=f"{item['total_qty']} sold", font=get_font(11, "bold"), text_color="#94A3B8", width=70, anchor="e").pack(side="left", padx=4)
                ctk.CTkLabel(row, text=f"{CURRENCY_SYMBOL}{item['total_revenue']:.2f}", font=get_font(12, "bold"), text_color=COLOR_PRIMARY, width=80, anchor="e").pack(side="right", padx=10)

        # Populate Payment Methods
        for w in self.payment_list.winfo_children():
            w.destroy()

        payments = analytics.get("payment_methods", [])
        total_rev = analytics["total_revenue"] or 1.0

        if not payments:
            ctk.CTkLabel(self.payment_list, text="No payment data recorded yet.", text_color="gray").pack(pady=20)
        else:
            for p in payments:
                row = ctk.CTkFrame(self.payment_list, corner_radius=6, fg_color="#1E293B")
                row.pack(fill="x", pady=4)

                pct = (p["total"] / total_rev) * 100.0 if total_rev > 0 else 0

                top_sub = ctk.CTkFrame(row, fg_color="transparent")
                top_sub.pack(fill="x", padx=10, pady=(6, 2))

                ctk.CTkLabel(top_sub, text=f"{p['method']} ({p['count']} txns)", font=get_font(12, "bold")).pack(side="left")
                ctk.CTkLabel(top_sub, text=f"{CURRENCY_SYMBOL}{p['total']:.2f} ({pct:.1f}%)", font=get_font(12, "bold"), text_color=COLOR_PRIMARY).pack(side="right")

                # Visual progress bar
                bar = ctk.CTkProgressBar(row, height=8, corner_radius=4)
                bar.pack(fill="x", padx=10, pady=(2, 8))
                bar.set(min(1.0, max(0.0, pct / 100.0)))

        # Populate Low Stock Alerts
        for w in self.alerts_list.winfo_children():
            w.destroy()

        low_items = self.inventory_service.get_low_stock_alerts()
        if not low_items:
            good_box = ctk.CTkFrame(self.alerts_list, fg_color="transparent")
            good_box.pack(fill="x", pady=10)
            ctk.CTkLabel(good_box, text="✓ All products are adequately stocked.", font=get_font(13), text_color="#10B981").pack()
        else:
            for item in low_items:
                row = ctk.CTkFrame(self.alerts_list, corner_radius=6, fg_color="#1E293B")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=item.sku, font=get_font(12, "bold"), width=80, anchor="w").pack(side="left", padx=10, pady=6)
                ctk.CTkLabel(row, text=item.name, font=get_font(12), anchor="w").pack(side="left", fill="x", expand=True, padx=4)

                status_col = COLOR_DANGER if item.stock_qty == 0 else COLOR_WARNING
                status_txt = "OUT OF STOCK (0)" if item.stock_qty == 0 else f"Only {item.stock_qty} left (Threshold: {item.reorder_threshold})"
                ctk.CTkLabel(row, text=status_txt, font=get_font(11, "bold"), text_color=status_col, width=220, anchor="center").pack(side="left", padx=6)

                restock_btn = ctk.CTkButton(
                    row,
                    text="Restock +10",
                    width=90,
                    height=26,
                    font=get_font(11, "bold"),
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    command=lambda s=item.sku, n=item.name: self._restock_quick(s, n),
                )
                restock_btn.pack(side="right", padx=10)

    def _restock_quick(self, sku: str, name: str):
        self.inventory_service.restock(sku, 10)
        self.refresh_report()
        messagebox.showinfo("Restocked", f"Added 10 units to '{name}'.", parent=self)
