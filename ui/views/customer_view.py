import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from models.customer import Customer
from services.customer_service import CustomerService
from ui.components.modal_overlay import ModalOverlay
from ui.components.customer_modal import CustomerModal
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    get_font,
)


class CustomerView(ctk.CTkFrame):
    def __init__(self, parent, customer_service: CustomerService):
        super().__init__(parent, fg_color="transparent")
        self.customer_service = customer_service

        self.search_var = ctk.StringVar()

        self._build_ui()
        self.refresh_customers()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Bar
        hdr = ctk.CTkFrame(self, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.search_entry = ctk.CTkEntry(
            hdr,
            textvariable=self.search_var,
            placeholder_text="🔍 Search customer by name, phone number, or ID...",
            font=get_font(13),
            height=36,
            width=340,
        )
        self.search_entry.pack(side="left", padx=12, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_customers())

        new_btn = ctk.CTkButton(
            hdr,
            text="+ Add Customer",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=36,
            command=self._open_add_modal,
        )
        new_btn.pack(side="right", padx=12, pady=10)

        refresh_btn = ctk.CTkButton(
            hdr,
            text="🔄 Refresh",
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(12, "bold"),
            height=36,
            width=90,
            command=self.refresh_customers,
        )
        refresh_btn.pack(side="right", padx=4, pady=10)

        # Table Container
        table_card = ctk.CTkFrame(self, corner_radius=10)
        table_card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)

        # Headers
        thdr = ctk.CTkFrame(table_card, fg_color="#334155", height=38, corner_radius=6)
        thdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        thdr.pack_propagate(False)

        ctk.CTkLabel(thdr, text="Customer ID", font=get_font(12, "bold"), width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(thdr, text="Customer Name", font=get_font(12, "bold"), width=220, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(thdr, text="Phone Number", font=get_font(12, "bold"), width=160, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(thdr, text="Loyalty Points", font=get_font(12, "bold"), width=130, anchor="center").pack(side="left", padx=6)
        ctk.CTkLabel(thdr, text="Actions", font=get_font(12, "bold"), width=150, anchor="center").pack(side="right", padx=10)

        # Scrollable Rows
        self.cust_scroll = ctk.CTkScrollableFrame(table_card, corner_radius=8)
        self.cust_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def refresh_customers(self):
        query = self.search_var.get().strip()
        customers = self.customer_service.search(query)

        for w in self.cust_scroll.winfo_children():
            w.destroy()

        if not customers:
            empty = ctk.CTkLabel(self.cust_scroll, text="No customers found.", font=get_font(13), text_color="gray")
            empty.pack(pady=30)
            return

        for c in customers:
            row = self._create_customer_row(self.cust_scroll, c)
            row.pack(fill="x", pady=2)

    def _create_customer_row(self, parent, cust: Customer) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, corner_radius=6, fg_color="#1E293B", height=42)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text=cust.customer_id, font=get_font(12, "bold"), width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(row, text=cust.name, font=get_font(12), width=220, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(row, text=cust.phone_number, font=get_font(12), width=160, anchor="w", text_color="#94A3B8").pack(side="left", padx=6)

        ctk.CTkLabel(
            row,
            text=f"⭐ {cust.loyalty_points} pts",
            font=get_font(12, "bold"),
            width=130,
            text_color="#10B981",
            anchor="center",
        ).pack(side="left", padx=6)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=10)

        edit_btn = ctk.CTkButton(
            actions,
            text="Edit",
            width=55,
            height=26,
            font=get_font(11, "bold"),
            fg_color="#334155",
            hover_color=COLOR_SECONDARY_HOVER,
            command=lambda c=cust: self._open_edit_modal(c),
        )
        edit_btn.pack(side="left", padx=2)

        pts_btn = ctk.CTkButton(
            actions,
            text="+ Points",
            width=65,
            height=26,
            font=get_font(11, "bold"),
            fg_color="#334155",
            hover_color=COLOR_PRIMARY_HOVER,
            command=lambda c=cust: self._adjust_points_dialog(c),
        )
        pts_btn.pack(side="left", padx=2)

        return row

    def _open_add_modal(self):
        def on_save(data):
            self.customer_service.create_customer(
                name=data["name"],
                phone=data["phone_number"],
                initial_points=data["loyalty_points"],
            )
            self.refresh_customers()
            messagebox.showinfo("Success", f"Customer '{data['name']}' registered successfully!")

        CustomerModal(self, on_save=on_save)

    def _open_edit_modal(self, cust: Customer):
        def on_save(data):
            self.customer_service.update_customer(
                customer_id=cust.customer_id,
                name=data["name"],
                phone=data["phone_number"],
                points=data["loyalty_points"],
            )
            self.refresh_customers()
            messagebox.showinfo("Success", f"Customer '{cust.name}' updated successfully!")

        CustomerModal(self, customer=cust, on_save=on_save)

    def _adjust_points_dialog(self, cust: Customer):
        dialog = ModalOverlay(self, width=420, height=270)
        card = dialog.card

        ctk.CTkLabel(card, text=f"Adjust Loyalty Points", font=get_font(16, "bold")).pack(padx=20, pady=(20, 4), anchor="w")
        ctk.CTkLabel(card, text=f"Customer: {cust.name}\nCurrent balance: {cust.loyalty_points} pts", font=get_font(12), text_color="gray").pack(padx=20, pady=(0, 10), anchor="w")

        ctk.CTkLabel(card, text="Points to add (or subtract with -):", font=get_font(12, "bold")).pack(padx=20, pady=(4, 2), anchor="w")
        entry = ctk.CTkEntry(card, font=get_font(14, "bold"), height=36, justify="center")
        entry.pack(fill="x", padx=20, pady=4)
        entry.insert(0, "10")
        entry.focus_set()

        def do_adjust():
            val = entry.get().strip()
            try:
                pts = int(val)
                self.customer_service.customer_dao.adjust_loyalty_points(cust.customer_id, pts)
                dialog.destroy()
                self.refresh_customers()
                messagebox.showinfo("Points Updated", f"Updated loyalty points for {cust.name}.")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid whole number.")

        entry.bind("<Return>", lambda e: do_adjust())

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(15, 20))

        cancel_b = ctk.CTkButton(footer, text="Cancel", fg_color="gray", hover_color="#4B5563", font=get_font(12, "bold"), height=36, command=dialog.destroy)
        cancel_b.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ok_b = ctk.CTkButton(footer, text="Save Points", fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=get_font(12, "bold"), height=36, command=do_adjust)
        ok_b.pack(side="right", fill="x", expand=True, padx=(5, 0))
