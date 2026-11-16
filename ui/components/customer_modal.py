import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from models.customer import Customer
from ui.components.modal_overlay import ModalOverlay
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    get_font,
)


class CustomerModal(ModalOverlay):
    def __init__(
        self,
        parent,
        customer: Optional[Customer] = None,
        on_save: Optional[Callable[[dict], None]] = None,
    ):
        super().__init__(parent, width=480, height=440)
        self.customer = customer
        self.on_save = on_save
        self.is_edit = customer is not None

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title_text = f"Edit Customer: {self.customer.customer_id}" if self.is_edit else "Add New Customer"
        ctk.CTkLabel(header, text=title_text, font=get_font(18, "bold")).pack(anchor="w")

        form = ctk.CTkFrame(self.card, corner_radius=10, fg_color="#0F172A")
        form.pack(fill="both", expand=True, padx=25, pady=10)

        # Name
        ctk.CTkLabel(form, text="Full Name*", font=get_font(12, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
        self.name_entry = ctk.CTkEntry(form, font=get_font(13), height=36)
        self.name_entry.pack(fill="x", padx=15, pady=(0, 10))
        if self.customer:
            self.name_entry.insert(0, self.customer.name)

        # Phone
        ctk.CTkLabel(form, text="Phone Number*", font=get_font(12, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.phone_entry = ctk.CTkEntry(form, font=get_font(13), height=36, placeholder_text="+254700000000")
        self.phone_entry.pack(fill="x", padx=15, pady=(0, 10))
        if self.customer:
            self.phone_entry.insert(0, self.customer.phone_number)

        # Points
        ctk.CTkLabel(form, text="Loyalty Points", font=get_font(12, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.points_entry = ctk.CTkEntry(form, font=get_font(13), height=36)
        self.points_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.points_entry.insert(0, str(self.customer.loyalty_points if self.customer else 0))

        # Footer Buttons
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
            text="Save Customer",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=40,
            command=self._handle_save,
        )
        save_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _handle_save(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Name is required.")
            return
        if not phone:
            messagebox.showerror("Validation Error", "Phone number is required.")
            return

        try:
            points = int(self.points_entry.get().strip())
            if points < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Points must be a non-negative integer.")
            return

        data = {
            "customer_id": self.customer.customer_id if self.customer else "",
            "name": name,
            "phone_number": phone,
            "loyalty_points": points,
        }

        if self.on_save:
            try:
                self.on_save(data)
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
