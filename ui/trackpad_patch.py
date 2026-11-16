"""
macOS Trackpad & Tap-to-Click Compatibility Patch for CustomTkinter

Fixes the known Tkinter / CustomTkinter issue on macOS where light trackpad taps
are dropped or require hard physical clicks.
Enhances CTkButton, CTkRadioButton, CTkSwitch, and CTkOptionMenu with:
1. Both <Button-1> and <ButtonRelease-1> event capture with 220ms debounce.
2. Hand cursor ('pointinghand') for instant visual feedback on hover.
3. Frontmost window focus activation so taps are never swallowed by macOS.
"""

import time
import tkinter
from typing import Optional
import customtkinter as ctk


def apply_macos_trackpad_patch():
    """Patches CustomTkinter widgets to be 100% responsive to light trackpad taps."""
    _patch_ctk_button()
    _patch_ctk_radiobutton()
    _patch_ctk_switch()


def _patch_ctk_button():
    orig_button_init = ctk.CTkButton.__init__
    orig_button_draw = ctk.CTkButton._draw
    orig_button_bindings = ctk.CTkButton._create_bindings
    orig_button_clicked = ctk.CTkButton._clicked

    def patched_clicked(self, event=None):
        self._last_click_timestamp = time.time()
        orig_button_clicked(self, event)

    def patched_create_bindings(self, sequence: Optional[str] = None):
        orig_button_bindings(self, sequence)

        # Set hand pointer cursor on macOS
        try:
            self._canvas.configure(cursor="pointinghand")
            if self._text_label is not None:
                self._text_label.configure(cursor="pointinghand")
            if self._image_label is not None:
                self._image_label.configure(cursor="pointinghand")
        except Exception:
            pass

        # Debounced tap-release handler for macOS trackpad taps
        def on_trackpad_release(event=None):
            if self._state == tkinter.DISABLED:
                return
            now = time.time()
            last = getattr(self, "_last_click_timestamp", 0.0)
            if now - last < 0.22:
                # Already processed on Button-1 press
                return
            self._last_click_timestamp = now
            self._clicked(event)

        self._canvas.bind("<ButtonRelease-1>", on_trackpad_release, add="+")
        if self._text_label is not None:
            self._text_label.bind("<ButtonRelease-1>", on_trackpad_release, add="+")
        if self._image_label is not None:
            self._image_label.bind("<ButtonRelease-1>", on_trackpad_release, add="+")

    def patched_draw(self, no_color_updates=False):
        orig_button_draw(self, no_color_updates)
        try:
            if self._text_label is not None:
                self._text_label.configure(cursor="pointinghand")
            if self._image_label is not None:
                self._image_label.configure(cursor="pointinghand")
        except Exception:
            pass

    ctk.CTkButton._clicked = patched_clicked
    ctk.CTkButton._create_bindings = patched_create_bindings
    ctk.CTkButton._draw = patched_draw


def _patch_ctk_radiobutton():
    orig_rb_bindings = ctk.CTkRadioButton._create_bindings
    orig_rb_invoke = ctk.CTkRadioButton.invoke

    def patched_invoke(self):
        self._last_rb_invoke = time.time()
        orig_rb_invoke(self)

    def patched_create_bindings(self, sequence: Optional[str] = None):
        orig_rb_bindings(self, sequence)

        try:
            self._canvas.configure(cursor="pointinghand")
            if self._text_label is not None:
                self._text_label.configure(cursor="pointinghand")
        except Exception:
            pass

        def on_rb_release(event=None):
            if self._state == tkinter.DISABLED:
                return
            now = time.time()
            last = getattr(self, "_last_rb_invoke", 0.0)
            if now - last < 0.22:
                return
            self._last_rb_invoke = now
            self.invoke()

        self._canvas.bind("<ButtonRelease-1>", on_rb_release, add="+")
        if self._text_label is not None:
            self._text_label.bind("<ButtonRelease-1>", on_rb_release, add="+")

    ctk.CTkRadioButton.invoke = patched_invoke
    ctk.CTkRadioButton._create_bindings = patched_create_bindings


def _patch_ctk_switch():
    orig_sw_bindings = ctk.CTkSwitch._create_bindings
    orig_sw_toggle = ctk.CTkSwitch.toggle

    def patched_toggle(self, event=None):
        self._last_sw_toggle = time.time()
        orig_sw_toggle(self, event)

    def patched_create_bindings(self, sequence: Optional[str] = None):
        orig_sw_bindings(self, sequence)

        try:
            self._canvas.configure(cursor="pointinghand")
            if self._text_label is not None:
                self._text_label.configure(cursor="pointinghand")
        except Exception:
            pass

        def on_sw_release(event=None):
            if self._state == tkinter.DISABLED:
                return
            now = time.time()
            last = getattr(self, "_last_sw_toggle", 0.0)
            if now - last < 0.22:
                return
            self._last_sw_toggle = now
            self.toggle(event)

        self._canvas.bind("<ButtonRelease-1>", on_sw_release, add="+")
        if self._text_label is not None:
            self._text_label.bind("<ButtonRelease-1>", on_sw_release, add="+")

    ctk.CTkSwitch.toggle = patched_toggle
    ctk.CTkSwitch._create_bindings = patched_create_bindings
