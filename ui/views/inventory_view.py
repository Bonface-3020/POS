import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Optional
from config import CATEGORIES, CURRENCY_SYMBOL
from models.product import Product
from services.inventory_service import InventoryService
from ui.components.modal_overlay import ModalOverlay
from ui.components.product_modal import ProductModal
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


class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, inventory_service: InventoryService, on_data_changed: Optional[callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.inventory_service = inventory_service
        self.on_data_changed = on_data_changed

        self.search_var = ctk.StringVar()
        self.category_var = ctk.StringVar(value="All")
        self.low_stock_only = ctk.BooleanVar(value=False)

        self._build_ui()
        self.refresh_products()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # KPI Summary Cards Header
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = self._create_kpi_card(kpi_frame, 0, "Total Products", "0", "#3B82F6")
        self.card_instock = self._create_kpi_card(kpi_frame, 1, "In Stock Units", "0", "#10B981")
        self.card_lowstock = self._create_kpi_card(kpi_frame, 2, "Low Stock Alerts", "0", "#F59E0B")
        self.card_val = self._create_kpi_card(kpi_frame, 3, "Inventory Valuation", f"{CURRENCY_SYMBOL}0.00", "#8B5CF6")

        # Action & Filter Bar
        action_bar = ctk.CTkFrame(self, corner_radius=10)
        action_bar.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Search
        self.search_entry = ctk.CTkEntry(
            action_bar,
            textvariable=self.search_var,
            placeholder_text="🔍 Search SKU, product name, or barcode...",
            font=get_font(13),
            height=36,
            width=300,
        )
        self.search_entry.pack(side="left", padx=12, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_products())

        # Category
        cat_options = ["All"] + CATEGORIES
        cat_menu = ctk.CTkOptionMenu(
            action_bar,
            variable=self.category_var,
            values=cat_options,
            command=lambda val: self.refresh_products(),
            font=get_font(12),
            height=36,
            width=140,
        )
        cat_menu.pack(side="left", padx=6, pady=10)

        # Low stock switch
        low_switch = ctk.CTkSwitch(
            action_bar,
            text="Low Stock Only",
            variable=self.low_stock_only,
            font=get_font(12),
            command=self.refresh_products,
        )
        low_switch.pack(side="left", padx=12, pady=10)

        # Right Action Buttons
        btn_box = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_box.pack(side="right", padx=12, pady=10)

        add_btn = ctk.CTkButton(
            btn_box,
            text="+ Add Product",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=36,
            command=self._open_add_modal,
        )
        add_btn.pack(side="left", padx=4)

        refresh_btn = ctk.CTkButton(
            btn_box,
            text="🔄 Refresh",
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(12, "bold"),
            height=36,
            width=90,
            command=self.refresh_products,
        )
        refresh_btn.pack(side="left", padx=4)

        # Table Container
        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1)

        # Table Column Headers
        col_header = ctk.CTkFrame(table_container, fg_color="#334155", height=38, corner_radius=6)
        col_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        col_header.pack_propagate(False)

        ctk.CTkLabel(col_header, text="SKU", font=get_font(12, "bold"), width=90, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(col_header, text="Product Name", font=get_font(12, "bold"), width=220, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Category", font=get_font(12, "bold"), width=120, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Price", font=get_font(12, "bold"), width=80, anchor="e").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Stock", font=get_font(12, "bold"), width=70, anchor="center").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Barcode", font=get_font(12, "bold"), width=110, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Status", font=get_font(12, "bold"), width=110, anchor="center").pack(side="left", padx=6)
        ctk.CTkLabel(col_header, text="Actions", font=get_font(12, "bold"), width=150, anchor="center").pack(side="right", padx=10)

        # Scrollable Rows List
        self.table_scroll = ctk.CTkScrollableFrame(table_container, corner_radius=8)
        self.table_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _create_kpi_card(self, parent, col: int, title: str, val: str, accent: str):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1E293B")
        card.grid(row=0, column=col, padx=5, sticky="ew")

        ctk.CTkLabel(card, text=title, font=get_font(11, "bold"), text_color="#94A3B8").pack(anchor="w", padx=14, pady=(12, 2))
        lbl = ctk.CTkLabel(card, text=val, font=get_font(20, "bold"), text_color=accent)
        lbl.pack(anchor="w", padx=14, pady=(0, 12))
        return lbl

    def refresh_products(self):
        query = self.search_var.get().strip()
        cat = self.category_var.get()
        low_only = self.low_stock_only.get()

        products = self.inventory_service.get_products(
            query=query,
            category=cat if cat != "All" else None,
            only_active=False,
            only_low_stock=low_only,
        )

        all_prods = self.inventory_service.get_products(only_active=False)
        total_count = len(all_prods)
        total_units = sum(p.stock_qty for p in all_prods)
        low_count = sum(1 for p in all_prods if p.is_low_stock or p.is_out_of_stock)
        total_val = sum(p.unit_price * p.stock_qty for p in all_prods)

        self.card_total.configure(text=str(total_count))
        self.card_instock.configure(text=f"{total_units:,}")
        self.card_lowstock.configure(text=str(low_count))
        self.card_val.configure(text=f"{CURRENCY_SYMBOL}{total_val:,.2f}")

        for w in self.table_scroll.winfo_children():
            w.destroy()

        if not products:
            empty = ctk.CTkLabel(self.table_scroll, text="No products found.", font=get_font(13), text_color="gray")
            empty.pack(pady=30)
            return

        for p in products:
            row = self._create_product_row(self.table_scroll, p)
            row.pack(fill="x", pady=2)

    def _create_product_row(self, parent, prod: Product) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, corner_radius=6, fg_color="#1E293B", height=42)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text=prod.sku, font=get_font(12, "bold"), width=90, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(row, text=prod.name, font=get_font(12), width=220, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(row, text=prod.category, font=get_font(11), width=120, anchor="w", text_color="#94A3B8").pack(side="left", padx=6)
        ctk.CTkLabel(row, text=f"{CURRENCY_SYMBOL}{prod.unit_price:.2f}", font=get_font(12, "bold"), width=80, anchor="e", text_color=COLOR_PRIMARY).pack(side="left", padx=6)
        ctk.CTkLabel(row, text=str(prod.stock_qty), font=get_font(12, "bold"), width=70, anchor="center").pack(side="left", padx=6)
        ctk.CTkLabel(row, text=prod.barcode or "-", font=get_font(11), width=110, anchor="w", text_color="#64748B").pack(side="left", padx=6)

        if not prod.is_active:
            status_text = "Inactive"
            status_color = "#64748B"
        elif prod.is_out_of_stock:
            status_text = "Out of Stock"
            status_color = COLOR_DANGER
        elif prod.is_low_stock:
            status_text = f"Low Stock ({prod.stock_qty})"
            status_color = COLOR_WARNING
        else:
            status_text = "In Stock"
            status_color = COLOR_PRIMARY

        badge = ctk.CTkLabel(row, text=status_text, font=get_font(11, "bold"), width=110, text_color=status_color, anchor="center")
        badge.pack(side="left", padx=6)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=10)

        restock_btn = ctk.CTkButton(
            actions,
            text="+ Stock",
            width=55,
            height=26,
            font=get_font(10, "bold"),
            fg_color="#334155",
            hover_color=COLOR_PRIMARY_HOVER,
            command=lambda p=prod: self._quick_restock_dialog(p),
        )
        restock_btn.pack(side="left", padx=2)

        edit_btn = ctk.CTkButton(
            actions,
            text="Edit",
            width=48,
            height=26,
            font=get_font(10, "bold"),
            fg_color="#334155",
            hover_color=COLOR_SECONDARY_HOVER,
            command=lambda p=prod: self._open_edit_modal(p),
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            actions,
            text="🗑",
            width=28,
            height=26,
            font=get_font(11, "bold"),
            fg_color="#334155",
            hover_color=COLOR_DANGER_HOVER,
            command=lambda p=prod: self._delete_product(p),
        )
        del_btn.pack(side="left", padx=2)

        return row

    def _open_add_modal(self):
        def on_save(data):
            self.inventory_service.add_product(
                sku=data["sku"],
                name=data["name"],
                category=data["category"],
                unit_price=data["unit_price"],
                stock_qty=data["stock_qty"],
                barcode=data["barcode"],
                reorder_threshold=data["reorder_threshold"],
            )
            self.refresh_products()
            if self.on_data_changed:
                self.on_data_changed()
            messagebox.showinfo("Success", f"Product '{data['name']}' added successfully!")

        ProductModal(self, on_save=on_save)

    def _open_edit_modal(self, prod: Product):
        def on_save(data):
            self.inventory_service.update_product(
                sku=prod.sku,
                name=data["name"],
                category=data["category"],
                unit_price=data["unit_price"],
                stock_qty=data["stock_qty"],
                barcode=data["barcode"],
                reorder_threshold=data["reorder_threshold"],
                is_active=data["is_active"],
            )
            self.refresh_products()
            if self.on_data_changed:
                self.on_data_changed()
            messagebox.showinfo("Success", f"Product '{prod.name}' updated successfully!")

        ProductModal(self, product=prod, on_save=on_save)

    def _quick_restock_dialog(self, prod: Product):
        dialog = ModalOverlay(self, width=420, height=270)
        card = dialog.card

        ctk.CTkLabel(card, text=f"Restock: {prod.sku}", font=get_font(16, "bold")).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkLabel(card, text=f"Item: {prod.name}\nCurrent stock: {prod.stock_qty} units", font=get_font(12), text_color="gray").pack(padx=20, pady=(0, 10), anchor="w")

        ctk.CTkLabel(card, text="Units to add:", font=get_font(12, "bold")).pack(padx=20, pady=(4, 2), anchor="w")
        entry = ctk.CTkEntry(card, font=get_font(14, "bold"), height=36, justify="center")
        entry.pack(fill="x", padx=20, pady=4)
        entry.insert(0, "10")
        entry.focus_set()

        def do_restock():
            val = entry.get().strip()
            try:
                qty = int(val)
                if qty <= 0:
                    raise ValueError()
                self.inventory_service.restock(prod.sku, qty)
                dialog.destroy()
                self.refresh_products()
                if self.on_data_changed:
                    self.on_data_changed()
                messagebox.showinfo("Restocked", f"Added {qty} units to '{prod.name}'.")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive whole number.")

        entry.bind("<Return>", lambda e: do_restock())

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(15, 20))

        cancel_b = ctk.CTkButton(footer, text="Cancel", fg_color="gray", hover_color="#4B5563", font=get_font(12, "bold"), height=36, command=dialog.destroy)
        cancel_b.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ok_b = ctk.CTkButton(footer, text="Add Stock", fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=get_font(12, "bold"), height=36, command=do_restock)
        ok_b.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _delete_product(self, prod: Product):
        confirm = messagebox.askyesno(
            "Confirm Delete / Deactivate",
            f"Are you sure you want to remove '{prod.name}' ({prod.sku})?\n"
            f"Note: If this product has existing sales records, it will be safely deactivated.",
        )
        if confirm:
            self.inventory_service.delete_product(prod.sku)
            self.refresh_products()
            if self.on_data_changed:
                self.on_data_changed()
            messagebox.showinfo("Done", f"Product '{prod.name}' removed or deactivated.")
