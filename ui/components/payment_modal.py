import customtkinter as ctk
from typing import Callable, Optional
from config import CURRENCY_SYMBOL
from ui.components.modal_overlay import ModalOverlay
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_DANGER,
    get_font,
)


class PaymentModal(ModalOverlay):
    def __init__(
        self,
        parent,
        total_amount: float,
        on_confirm: Callable[[str, float], None],
        customer_name: Optional[str] = None,
    ):
        super().__init__(parent, width=540, height=620)

        self.total_amount = round(total_amount, 2)
        self.on_confirm = on_confirm
        self.customer_name = customer_name or "Walk-in Customer"

        self.selected_method = ctk.StringVar(value="Cash")
        self.tendered_var = ctk.StringVar(value=f"{self.total_amount:.2f}")
        self.change_var = ctk.StringVar(value=f"{CURRENCY_SYMBOL}0.00")

        self._build_ui()
        self._on_method_change("Cash")
        self._calculate_change()

    def _build_ui(self):
        # Header banner
        header = ctk.CTkFrame(self.card, corner_radius=0, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="Checkout & Payment",
            font=get_font(20, "bold"),
        )
        title.pack(anchor="w")

        cust_label = ctk.CTkLabel(
            header,
            text=f"Customer: {self.customer_name}",
            font=get_font(13),
            text_color="gray",
        )
        cust_label.pack(anchor="w")

        # Big Total Card
        total_card = ctk.CTkFrame(self.card, corner_radius=12, fg_color="#0F172A")
        total_card.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(
            total_card,
            text="TOTAL AMOUNT DUE",
            font=get_font(12, "bold"),
            text_color="gray",
        ).pack(pady=(12, 2))

        ctk.CTkLabel(
            total_card,
            text=f"{CURRENCY_SYMBOL}{self.total_amount:.2f}",
            font=get_font(32, "bold"),
            text_color=COLOR_PRIMARY,
        ).pack(pady=(0, 12))

        # Payment Method Tabs
        method_frame = ctk.CTkFrame(self.card, corner_radius=10, fg_color="#0F172A")
        method_frame.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(
            method_frame,
            text="Select Payment Method:",
            font=get_font(12, "bold"),
        ).pack(anchor="w", padx=15, pady=(8, 4))

        btn_row = ctk.CTkFrame(method_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 10))

        for method in ["Cash", "Card", "Mobile"]:
            rb = ctk.CTkRadioButton(
                btn_row,
                text=method,
                value=method,
                variable=self.selected_method,
                command=lambda m=method: self._on_method_change(m),
                font=get_font(13, "bold"),
            )
            rb.pack(side="left", expand=True)

        # Dynamic Content Container
        self.content_frame = ctk.CTkFrame(self.card, corner_radius=10, fg_color="#0F172A")
        self.content_frame.pack(fill="both", expand=True, padx=25, pady=5)

        # Cash Details Area
        self.cash_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        tendered_label = ctk.CTkLabel(
            self.cash_frame,
            text="Amount Tendered:",
            font=get_font(12, "bold"),
        )
        tendered_label.pack(anchor="w", padx=10, pady=(8, 2))

        self.tendered_entry = ctk.CTkEntry(
            self.cash_frame,
            textvariable=self.tendered_var,
            font=get_font(18, "bold"),
            height=38,
            justify="center",
        )
        self.tendered_entry.pack(fill="x", padx=10, pady=4)
        self.tendered_var.trace_add("write", lambda *args: self._calculate_change())

        # Quick Bill Buttons
        bills_frame = ctk.CTkFrame(self.cash_frame, fg_color="transparent")
        bills_frame.pack(fill="x", padx=10, pady=4)

        bills = ["Exact", "5", "10", "20", "50", "100"]
        for b in bills:
            btn = ctk.CTkButton(
                bills_frame,
                text=f"{CURRENCY_SYMBOL}{b}" if b != "Exact" else "Exact",
                width=52,
                height=28,
                font=get_font(11, "bold"),
                command=lambda val=b: self._set_tendered_preset(val),
            )
            btn.pack(side="left", expand=True, padx=2)

        # Change Display Card
        change_card = ctk.CTkFrame(self.cash_frame, corner_radius=8, fg_color="#1E293B")
        change_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            change_card,
            text="Change Due:",
            font=get_font(12, "bold"),
            text_color="gray",
        ).pack(side="left", padx=12, pady=8)

        self.change_label = ctk.CTkLabel(
            change_card,
            textvariable=self.change_var,
            font=get_font(18, "bold"),
            text_color=COLOR_PRIMARY,
        )
        self.change_label.pack(side="right", padx=12, pady=8)

        # Non-cash Note Area
        self.non_cash_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.non_cash_label = ctk.CTkLabel(
            self.non_cash_frame,
            text="Ready for processing. Ask customer to present card or scan QR/Mobile payment code.",
            font=get_font(13),
            wraplength=400,
        )
        self.non_cash_label.pack(padx=20, pady=30)

        # Action Buttons Footer
        footer = ctk.CTkFrame(self.card, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(10, 20))

        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="gray",
            hover_color="#4B5563",
            font=get_font(13, "bold"),
            height=42,
            command=self.destroy,
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.confirm_btn = ctk.CTkButton(
            footer,
            text="Complete Sale",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(14, "bold"),
            height=42,
            command=self._confirm,
        )
        self.confirm_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _on_method_change(self, method: str):
        if method == "Cash":
            self.non_cash_frame.pack_forget()
            self.cash_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self._calculate_change()
        else:
            self.cash_frame.pack_forget()
            self.non_cash_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.confirm_btn.configure(state="normal")
            if method == "Card":
                self.non_cash_label.configure(
                    text="Card Terminal ready.\nTap, insert, or swipe customer card on the terminal reader."
                )
            else:
                self.non_cash_label.configure(
                    text="Mobile Payment selected (e.g. M-Pesa / Mobile Money).\nVerify reference and confirm to complete."
                )

    def _set_tendered_preset(self, val: str):
        if val == "Exact":
            self.tendered_var.set(f"{self.total_amount:.2f}")
        else:
            try:
                amt = float(val)
                self.tendered_var.set(f"{amt:.2f}")
            except ValueError:
                pass

    def _calculate_change(self):
        if self.selected_method.get() != "Cash":
            return
        try:
            val_str = self.tendered_var.get().replace(CURRENCY_SYMBOL, "").strip()
            tendered = float(val_str) if val_str else 0.0
            diff = tendered - self.total_amount
            if diff >= 0:
                self.change_var.set(f"{CURRENCY_SYMBOL}{diff:.2f}")
                self.change_label.configure(text_color=COLOR_PRIMARY)
                self.confirm_btn.configure(state="normal")
            else:
                shortage = abs(diff)
                self.change_var.set(f"Short by {CURRENCY_SYMBOL}{shortage:.2f}")
                self.change_label.configure(text_color=COLOR_DANGER)
                self.confirm_btn.configure(state="disabled")
        except ValueError:
            self.change_var.set("Invalid amount")
            self.change_label.configure(text_color=COLOR_DANGER)
            self.confirm_btn.configure(state="disabled")

    def _confirm(self):
        method = self.selected_method.get()
        tendered = self.total_amount
        if method == "Cash":
            try:
                val_str = self.tendered_var.get().replace(CURRENCY_SYMBOL, "").strip()
                tendered = float(val_str)
                if tendered < self.total_amount:
                    return
            except ValueError:
                return

        self.destroy()
        self.on_confirm(method, tendered)
