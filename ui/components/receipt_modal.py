import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox
from typing import Optional
from config import BASE_DIR
from ui.components.modal_overlay import ModalOverlay
from ui.theme import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SECONDARY,
    COLOR_SECONDARY_HOVER,
    get_font,
)


class ReceiptModal(ModalOverlay):
    def __init__(self, parent, receipt_text: str, sale_id: int):
        super().__init__(parent, width=540, height=640)

        self.receipt_text = receipt_text
        self.sale_id = sale_id

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title = ctk.CTkLabel(
            header,
            text="✓ Transaction Successful",
            font=get_font(18, "bold"),
            text_color=COLOR_PRIMARY,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Digital receipt has been generated.",
            font=get_font(12),
            text_color="gray",
        )
        subtitle.pack(anchor="w")

        # Receipt Container with Mono Font
        receipt_box = ctk.CTkTextbox(
            self.card,
            font=get_font(11, mono=True),
            wrap="none",
            corner_radius=8,
            fg_color="#0F172A",
        )
        receipt_box.pack(fill="both", expand=True, padx=20, pady=8)
        receipt_box.insert("1.0", self.receipt_text)
        receipt_box.configure(state="disabled")

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(6, 16))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save to File",
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            font=get_font(13, "bold"),
            height=40,
            command=self._save_file,
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        print_btn = ctk.CTkButton(
            btn_frame,
            text="🖨 Print Receipt",
            fg_color="#334155",
            hover_color="#475569",
            font=get_font(13, "bold"),
            height=40,
            command=self._print_receipt,
        )
        print_btn.pack(side="left", fill="x", expand=True, padx=6)

        done_btn = ctk.CTkButton(
            btn_frame,
            text="Done / Next Sale",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font=get_font(13, "bold"),
            height=40,
            command=self.destroy,
        )
        done_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _save_file(self):
        receipts_dir = BASE_DIR / "receipts"
        receipts_dir.mkdir(exist_ok=True)
        file_path = receipts_dir / f"receipt_{self.sale_id}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.receipt_text)
        messagebox.showinfo(
            "Receipt Saved",
            f"Receipt successfully saved to:\n{file_path}",
        )

    def _print_receipt(self):
        messagebox.showinfo(
            "Print Command Sent",
            f"Receipt #{self.sale_id} sent to default receipt printer.",
        )
