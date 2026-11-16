"""
RetailPulse POS Theme and Styling Constants
"""

# Palette
COLOR_PRIMARY = "#10B981"          # Emerald Green
COLOR_PRIMARY_HOVER = "#059669"
COLOR_PRIMARY_LIGHT = "#D1FAE5"

COLOR_SECONDARY = "#3B82F6"        # Royal Blue
COLOR_SECONDARY_HOVER = "#2563EB"

COLOR_DANGER = "#EF4444"           # Crimson Red
COLOR_DANGER_HOVER = "#DC2626"
COLOR_DANGER_LIGHT = "#FEE2E2"

COLOR_WARNING = "#F59E0B"          # Amber Orange
COLOR_WARNING_HOVER = "#D97706"

COLOR_SUCCESS = "#10B981"
COLOR_INFO = "#06B6D4"

# Dark Mode Palette
DARK_BG = "#0F172A"               # Main app background (Slate 900)
DARK_CARD = "#1E293B"             # Cards / Sidebars (Slate 800)
DARK_CARD_HOVER = "#2D3B4F"
DARK_SURFACE = "#334155"          # Table headers / inputs (Slate 700)
DARK_BORDER = "#475569"           # Borders
DARK_TEXT_PRIMARY = "#F8FAFC"     # Slate 50
DARK_TEXT_SECONDARY = "#94A3B8"   # Slate 400

# Light Mode Palette
LIGHT_BG = "#F1F5F9"              # Slate 100
LIGHT_CARD = "#FFFFFF"            # White
LIGHT_CARD_HOVER = "#F8FAFC"
LIGHT_SURFACE = "#E2E8F0"         # Slate 200
LIGHT_BORDER = "#CBD5E1"          # Slate 300
LIGHT_TEXT_PRIMARY = "#0F172A"    # Slate 900
LIGHT_TEXT_SECONDARY = "#64748B"  # Slate 500

# Fonts (Platform Adaptive)
FONT_FAMILY = "Helvetica Neue"
FONT_MONO = "Courier"

def get_font(size: int = 13, weight: str = "normal", mono: bool = False):
    fam = FONT_MONO if mono else FONT_FAMILY
    return (fam, size, weight)
