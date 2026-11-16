import customtkinter as ctk


class ModalOverlay(ctk.CTkFrame):
    """
    Rock-solid in-app modal overlay.
    Eliminates native macOS Cocoa window manager crashes (Segmentation fault 11)
    and provides a seamless, focused modern POS experience.
    """

    def __init__(self, parent, width: int = 540, height: int = 620):
        root = parent.winfo_toplevel()
        super().__init__(root, fg_color="#090D16", corner_radius=0)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        self.card = ctk.CTkFrame(
            self,
            width=width,
            height=height,
            corner_radius=16,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155",
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

    def close(self):
        self.destroy()
