import customtkinter as ctk
from typing import Callable, List
from services.auth_service import AuthService
from models.cashier import Cashier
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_DANGER,
    get_font,
)


class LoginView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        auth_service: AuthService,
        on_login_success: Callable[[Cashier], None],
    ):
        super().__init__(parent, fg_color="transparent")
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        self.cashiers: List[Cashier] = self.auth_service.get_all_active_cashiers()
        self.selected_cashier_id = ctk.StringVar(
            value=self.cashiers[0].cashier_id if self.cashiers else ""
        )
        self.pin_var = ctk.StringVar()

        self._build_ui()

    def _build_ui(self):
        # Outer center container
        self.center_box = ctk.CTkFrame(self, corner_radius=16, width=460)
        self.center_box.place(relx=0.5, rely=0.5, anchor="center")

        # Top Banner / Logo
        banner = ctk.CTkFrame(self.center_box, fg_color="transparent")
        banner.pack(fill="x", padx=30, pady=(30, 15))

        logo_badge = ctk.CTkLabel(
            banner,
            text="⚡ RetailPulse POS",
            font=get_font(26, "bold"),
            text_color=COLOR_PRIMARY,
        )
        logo_badge.pack()

        subtitle = ctk.CTkLabel(
            banner,
            text="Point of Sale Terminal & Store Management",
            font=get_font(13),
            text_color="gray",
        )
        subtitle.pack(pady=(4, 0))

        # Cashier Dropdown
        form_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        form_frame.pack(fill="x", padx=35, pady=10)

        ctk.CTkLabel(
            form_frame,
            text="Select Cashier / Staff:",
            font=get_font(12, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        cashier_options = [
            f"{c.cashier_id} - {c.full_name} ({c.role})" for c in self.cashiers
        ]
        self.cashier_menu = ctk.CTkOptionMenu(
            form_frame,
            values=cashier_options,
            command=self._on_cashier_selected,
            font=get_font(13),
            height=38,
        )
        self.cashier_menu.pack(fill="x", pady=(0, 12))

        # PIN Entry
        ctk.CTkLabel(
            form_frame,
            text="Enter Security PIN:",
            font=get_font(12, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        self.pin_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.pin_var,
            font=get_font(22, "bold"),
            show="●",
            justify="center",
            height=45,
        )
        self.pin_entry.pack(fill="x", pady=(0, 10))
        self.pin_entry.bind("<Return>", lambda event: self._attempt_login())
        self.pin_entry.focus_set()

        # Touch Keypad (3x4)
        keypad_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        keypad_frame.pack(padx=35, pady=5)

        buttons = [
            ("1", "2", "3"),
            ("4", "5", "6"),
            ("7", "8", "9"),
            ("C", "0", "⌫"),
        ]

        for row in buttons:
            row_frame = ctk.CTkFrame(keypad_frame, fg_color="transparent")
            row_frame.pack(pady=3)
            for key in row:
                btn = ctk.CTkButton(
                    row_frame,
                    text=key,
                    width=75,
                    height=45,
                    font=get_font(16, "bold"),
                    fg_color="#334155",
                    hover_color="#475569",
                    command=lambda k=key: self._on_keypad_press(k),
                )
                btn.pack(side="left", padx=4)

        # Error display label
        self.error_label = ctk.CTkLabel(
            self.center_box,
            text="",
            font=get_font(12, "bold"),
            text_color=COLOR_DANGER,
        )
        self.error_label.pack(pady=4)

        # Login Button
        self.login_btn = ctk.CTkButton(
            self.center_box,
            text="Sign In to Terminal",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(15, "bold"),
            height=46,
            command=self._attempt_login,
        )
        self.login_btn.pack(fill="x", padx=35, pady=(5, 15))

        # Quick Demo Account Switchers
        quick_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        quick_frame.pack(fill="x", padx=35, pady=(0, 25))

        ctk.CTkLabel(
            quick_frame,
            text="Quick Demo Login:",
            font=get_font(11, "bold"),
            text_color="gray",
        ).pack(anchor="w", pady=(0, 4))

        quick_btns = ctk.CTkFrame(quick_frame, fg_color="transparent")
        quick_btns.pack(fill="x")

        c101_btn = ctk.CTkButton(
            quick_btns,
            text="Mercy (Cashier: 1234)",
            font=get_font(11),
            height=30,
            fg_color="#1E293B",
            hover_color="#334155",
            command=lambda: self._quick_login("C101", "1234"),
        )
        c101_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        m901_btn = ctk.CTkButton(
            quick_btns,
            text="Kiprotich (Manager: 9999)",
            font=get_font(11),
            height=30,
            fg_color="#1E293B",
            hover_color="#334155",
            command=lambda: self._quick_login("M901", "9999"),
        )
        m901_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _on_cashier_selected(self, choice: str):
        cid = choice.split(" - ")[0]
        self.selected_cashier_id.set(cid)
        self.pin_var.set("")
        self.error_label.configure(text="")
        self.pin_entry.focus_set()

    def _on_keypad_press(self, key: str):
        current = self.pin_var.get()
        if key == "C":
            self.pin_var.set("")
        elif key == "⌫":
            self.pin_var.set(current[:-1])
        else:
            self.pin_var.set(current + key)

    def _quick_login(self, cashier_id: str, pin: str):
        self.selected_cashier_id.set(cashier_id)
        self.pin_var.set(pin)
        self._attempt_login()

    def _attempt_login(self):
        cid = self.selected_cashier_id.get()
        pin = self.pin_var.get().strip()

        if not pin:
            self.error_label.configure(text="Please enter PIN code.")
            return

        try:
            cashier = self.auth_service.login(cid, pin)
            self.error_label.configure(text="")
            self.on_login_success(cashier)
        except Exception as e:
            self.error_label.configure(text=str(e))
            self.pin_var.set("")
            self.pin_entry.focus_set()
