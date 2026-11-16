import time
from datetime import datetime
from typing import Optional
import customtkinter as ctk

from config import (
    APP_TITLE,
    APP_VERSION,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from models.cashier import Cashier
from services.auth_service import AuthService
from services.cart_service import CartService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService
from services.sale_service import SaleService
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    get_font,
)
from ui.views.customer_view import CustomerView
from ui.views.inventory_view import InventoryView
from ui.views.login_view import LoginView
from ui.views.pos_view import POSView
from ui.views.reports_view import ReportsView
from ui.views.sales_view import SalesView


class RetailPulseApp(ctk.CTk):
    def __init__(
        self,
        auth_service: Optional[AuthService] = None,
        inventory_service: Optional[InventoryService] = None,
        cart_service: Optional[CartService] = None,
        sale_service: Optional[SaleService] = None,
        customer_service: Optional[CustomerService] = None,
    ):
        super().__init__()

        # Service Container
        self.auth_service = auth_service or AuthService()
        self.inventory_service = inventory_service or InventoryService()
        self.cart_service = cart_service or CartService()
        self.sale_service = sale_service or SaleService()
        self.customer_service = customer_service or CustomerService()

        # Appearance & Dimensions
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Track views
        self.current_view: Optional[ctk.CTkFrame] = None
        self.nav_buttons = {}

        # Build initial UI
        self._build_main_shell()
        self._start_clock()

        # Bring window to foreground and force active focus on macOS
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)
        self.focus_force()

        # Start with Login screen
        self.show_login()

    def _build_main_shell(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ==========================================
        # TOP HEADER / STATUS BAR
        # ==========================================
        self.header = ctk.CTkFrame(self, height=58, corner_radius=0, fg_color="#0F172A")
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.pack_propagate(False)

        # Logo & App Name
        brand_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        brand_frame.pack(side="left", padx=20)

        ctk.CTkLabel(
            brand_frame,
            text="⚡ RetailPulse POS",
            font=get_font(18, "bold"),
            text_color=COLOR_PRIMARY,
        ).pack(side="left")

        # Navigation Bar Buttons (Visible after login)
        self.nav_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.nav_frame.pack(side="left", padx=30)

        nav_items = [
            ("pos", "🛒 Terminal", self.show_pos),
            ("inventory", "📦 Inventory", self.show_inventory),
            ("sales", "📜 Sales History", self.show_sales),
            ("customers", "👥 Customers", self.show_customers),
            ("reports", "📊 Reports", self.show_reports),
        ]

        for key, text, cmd in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=get_font(13, "bold"),
                height=36,
                fg_color="transparent",
                hover_color="#1E293B",
                text_color="#94A3B8",
                command=cmd,
            )
            btn.pack(side="left", padx=4)
            self.nav_buttons[key] = btn

        # Right-side status: Clock, Theme toggle, Cashier Badge, Logout
        self.status_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.status_frame.pack(side="right", padx=20)

        # Real-time Clock
        self.clock_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=get_font(12, mono=True),
            text_color="#94A3B8",
        )
        self.clock_label.pack(side="left", padx=12)

        # Dark/Light Mode Toggle Switch
        self.mode_switch = ctk.CTkSwitch(
            self.status_frame,
            text="Dark",
            font=get_font(11),
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light",
        )
        self.mode_switch.select()
        self.mode_switch.pack(side="left", padx=8)

        # Cashier Profile Badge
        self.cashier_badge = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=get_font(12, "bold"),
            text_color="#F8FAFC",
            fg_color="#1E293B",
            corner_radius=6,
            padx=10,
            pady=4,
        )

        # Logout Button
        self.logout_btn = ctk.CTkButton(
            self.status_frame,
            text="Sign Out",
            font=get_font(12, "bold"),
            height=32,
            width=80,
            fg_color="#334155",
            hover_color=COLOR_DANGER_HOVER,
            command=self._handle_logout,
        )

        # ==========================================
        # MAIN CONTENT CONTAINER
        # ==========================================
        self.content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

    def _start_clock(self):
        def update():
            now_str = datetime.now().strftime("%a, %d %b %Y  %H:%M:%S")
            self.clock_label.configure(text=now_str)
            self.after(1000, update)

        update()

    def _toggle_theme(self):
        if self.mode_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.mode_switch.configure(text="Dark")
        else:
            ctk.set_appearance_mode("light")
            self.mode_switch.configure(text="Light")

    # ==========================================
    # VIEW MANAGEMENT
    # ==========================================
    def _switch_view(self, new_view: ctk.CTkFrame, active_key: Optional[str] = None):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = new_view
        self.current_view.grid(row=0, column=0, sticky="nsew")

        # Update nav button highlights
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color="#1E293B", text_color="#10B981")
            else:
                btn.configure(fg_color="transparent", text_color="#94A3B8")

    def show_login(self):
        # Hide navigation and user info
        self.nav_frame.pack_forget()
        self.cashier_badge.pack_forget()
        self.logout_btn.pack_forget()

        login_view = LoginView(
            self.content_container,
            auth_service=self.auth_service,
            on_login_success=self._on_login_success,
        )
        self._switch_view(login_view)

    def _on_login_success(self, cashier: Cashier):
        # Display navigation and cashier details
        self.nav_frame.pack(side="left", padx=30)
        self.cashier_badge.pack(side="left", padx=8)
        self.logout_btn.pack(side="left", padx=4)

        role_icon = "⭐" if cashier.is_manager else "👤"
        self.cashier_badge.configure(
            text=f"{role_icon} {cashier.full_name} ({cashier.role})"
        )

        self.show_pos()

    def _handle_logout(self):
        self.auth_service.logout()
        self.cart_service.clear()
        self.show_login()

    def show_pos(self):
        pos_view = POSView(
            self.content_container,
            auth_service=self.auth_service,
            inventory_service=self.inventory_service,
            cart_service=self.cart_service,
            sale_service=self.sale_service,
            customer_service=self.customer_service,
            on_sale_completed=self._on_data_synchronized,
        )
        self._switch_view(pos_view, active_key="pos")

    def show_inventory(self):
        inv_view = InventoryView(
            self.content_container,
            inventory_service=self.inventory_service,
            on_data_changed=self._on_data_synchronized,
        )
        self._switch_view(inv_view, active_key="inventory")

    def show_sales(self):
        sales_view = SalesView(
            self.content_container,
            sale_service=self.sale_service,
        )
        self._switch_view(sales_view, active_key="sales")

    def show_customers(self):
        cust_view = CustomerView(
            self.content_container,
            customer_service=self.customer_service,
        )
        self._switch_view(cust_view, active_key="customers")

    def show_reports(self):
        reports_view = ReportsView(
            self.content_container,
            sale_service=self.sale_service,
            inventory_service=self.inventory_service,
            auth_service=self.auth_service,
        )
        self._switch_view(reports_view, active_key="reports")

    def _on_data_synchronized(self):
        # Callback for when a sale or inventory mutation occurs
        pass
