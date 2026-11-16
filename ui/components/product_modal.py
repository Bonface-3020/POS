import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from config import CATEGORIES
from models.product import Product
from ui.components.modal_overlay import ModalOverlay
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    get_font,
)


class ProductModal(ModalOverlay):
    def __init__(
        self,
        parent,
        product: Optional[Product] = None,
        on_save: Optional[Callable[[dict], None]] = None,
    ):
        super().__init__(parent, width=540, height=640)
        self.product = product
        self.on_save = on_save
        self.is_edit = product is not None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title_text = f"Edit Product: {self.product.sku}" if self.is_edit else "Add New Product"
        ctk.CTkLabel(
            header,
            text=title_text,
            font=get_font(18, "bold"),
        ).pack(anchor="w")

        # Form Container
        form = ctk.CTkScrollableFrame(self.card, corner_radius=10, fg_color="#0F172A")
        form.pack(fill="both", expand=True, padx=25, pady=8)

        # SKU
        ctk.CTkLabel(form, text="SKU (Product Code)*", font=get_font(12, "bold")).pack(anchor="w", pady=(8, 2))
        self.sku_entry = ctk.CTkEntry(form, font=get_font(13), height=36)
        self.sku_entry.pack(fill="x", pady=(0, 6))
        if self.product:
            self.sku_entry.insert(0, self.product.sku)
            self.sku_entry.configure(state="disabled")

        # Name
        ctk.CTkLabel(form, text="Product Name*", font=get_font(12, "bold")).pack(anchor="w", pady=(6, 2))
        self.name_entry = ctk.CTkEntry(form, font=get_font(13), height=36)
        self.name_entry.pack(fill="x", pady=(0, 6))
        if self.product:
            self.name_entry.insert(0, self.product.name)

        # Category
        ctk.CTkLabel(form, text="Category*", font=get_font(12, "bold")).pack(anchor="w", pady=(6, 2))
        self.category_var = ctk.StringVar(value=self.product.category if self.product else CATEGORIES[0])
        self.cat_menu = ctk.CTkOptionMenu(
            form,
            variable=self.category_var,
            values=CATEGORIES,
            font=get_font(13),
            height=36,
        )
        self.cat_menu.pack(fill="x", pady=(0, 6))

        # Price and Stock in two columns
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=6)

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col1, text="Unit Price ($)*", font=get_font(12, "bold")).pack(anchor="w", pady=(0, 2))
        self.price_entry = ctk.CTkEntry(col1, font=get_font(13), height=36)
        self.price_entry.pack(fill="x")
        if self.product:
            self.price_entry.insert(0, f"{self.product.unit_price:.2f}")

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col2, text="Stock Quantity*", font=get_font(12, "bold")).pack(anchor="w", pady=(0, 2))
        self.stock_entry = ctk.CTkEntry(col2, font=get_font(13), height=36)
        self.stock_entry.pack(fill="x")
        if self.product:
            self.stock_entry.insert(0, str(self.product.stock_qty))

        # Barcode & Reorder Threshold
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", pady=6)

        bcol = ctk.CTkFrame(row2, fg_color="transparent")
        bcol.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(bcol, text="Barcode (Optional)", font=get_font(12, "bold")).pack(anchor="w", pady=(0, 2))
        self.barcode_entry = ctk.CTkEntry(bcol, font=get_font(13), height=36)
        self.barcode_entry.pack(fill="x")
        if self.product and self.product.barcode:
            self.barcode_entry.insert(0, self.product.barcode)

        rcol = ctk.CTkFrame(row2, fg_color="transparent")
        rcol.pack(side="right", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(rcol, text="Low Stock Alert Qty*", font=get_font(12, "bold")).pack(anchor="w", pady=(0, 2))
        self.threshold_entry = ctk.CTkEntry(rcol, font=get_font(13), height=36)
        self.threshold_entry.pack(fill="x")
        self.threshold_entry.insert(
            0, str(self.product.reorder_threshold if self.product else 5)
        )

        # Active status toggle
        self.active_var = ctk.BooleanVar(value=bool(self.product.is_active) if self.product else True)
        self.active_switch = ctk.CTkSwitch(
            form,
            text="Product is Active (available for sale)",
            variable=self.active_var,
            font=get_font(12),
        )
        self.active_switch.pack(anchor="w", pady=(12, 6))

        # Buttons
        footer = ctk.CTkFrame(self.card, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(10, 20))

        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="gray",
            hover_color="#4B5563",
            font=get_font(13, "bold"),
            height=40,
            command=self.destroy,
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        save_btn = ctk.CTkButton(
            footer,
            text="Save Product",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=40,
            command=self._handle_save,
        )
        save_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _handle_save(self):
        sku = self.sku_entry.get().strip().upper()
        name = self.name_entry.get().strip()
        category = self.category_var.get()
        barcode = self.barcode_entry.get().strip() or None

        if not sku or not name:
            messagebox.showerror("Validation Error", "SKU and Name are required.")
            return

        try:
            price = float(self.price_entry.get().strip())
            if price <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Price must be a positive number.")
            return

        try:
            stock = int(self.stock_entry.get().strip())
            if stock < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Stock must be a non-negative integer.")
            return

        try:
            threshold = int(self.threshold_entry.get().strip())
            if threshold < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Alert threshold must be non-negative.")
            return

        data = {
            "sku": sku,
            "name": name,
            "category": category,
            "unit_price": price,
            "stock_qty": stock,
            "barcode": barcode,
            "reorder_threshold": threshold,
            "is_active": 1 if self.active_var.get() else 0,
        }

        if self.on_save:
            try:
                self.on_save(data)
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
