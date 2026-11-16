import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "retail_pulse.db"
SCHEMA_PATH = BASE_DIR / "retail_schema.sql"

# Store & Business Info
APP_TITLE = "RetailPulse POS"
APP_VERSION = "1.0.0"
STORE_NAME = "RetailPulse Superstore"
STORE_ADDRESS = "104 Commercial Street, Nairobi, Kenya"
STORE_PHONE = "+254 700 000 000"
STORE_EMAIL = "info@retailpulse.com"

# POS Settings
CURRENCY_SYMBOL = "$"
DEFAULT_TAX_RATE = 0.08  # 8%
LOYALTY_RATE = 1.0  # 1 point per $1 spent

CATEGORIES = [
    "Beverages",
    "Snacks",
    "Electronics",
    "Produce",
    "General",
]

PAYMENT_METHODS = ["Cash", "Card", "Mobile"]
ROLES = ["Cashier", "Manager"]

# UI Design Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 1080
MIN_WINDOW_HEIGHT = 700

# Theme Color Palette (Clean modern slate & emerald accents)
THEME = {
    "primary": "#10B981",          # Emerald
    "primary_hover": "#059669",
    "primary_text": "#FFFFFF",
    "secondary": "#3B82F6",        # Blue
    "secondary_hover": "#2563EB",
    "danger": "#EF4444",           # Red
    "danger_hover": "#DC2626",
    "warning": "#F59E0B",          # Amber
    "warning_hover": "#D97706",
    "info": "#06B6D4",             # Cyan
    "dark_bg": "#0F172A",          # Dark Slate 900
    "dark_card": "#1E293B",        # Slate 800
    "dark_surface": "#334155",     # Slate 700
    "light_bg": "#F8FAFC",         # Slate 50
    "light_card": "#FFFFFF",       # White
    "light_surface": "#E2E8F0",    # Slate 200
    "text_muted": "#94A3B8",
}
