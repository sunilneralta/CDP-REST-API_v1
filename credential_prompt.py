"""
Native OS credential dialog for IDMC login using tkinter.
Opens a small popup window — works from any desktop MCP client
(Claude Code, VS Code, Cursor, etc.) with no browser or terminal required.
"""

import tkinter as tk
from tkinter import messagebox


def collect_credentials_via_dialog() -> tuple[str, str]:
    """
    Show a native OS login dialog. Blocks until the user submits or cancels.
    Returns (username, password). Raises RuntimeError if cancelled.
    """
    result = {"username": "", "password": "", "submitted": False}

    root = tk.Tk()
    root.title("IDMC Login")
    root.resizable(False, False)
    root.configure(bg="#f0f2f5")

    # Centre on screen
    root.update_idletasks()
    w, h = 360, 260
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    # Keep window on top
    root.lift()
    root.attributes("-topmost", True)

    # ── Styles ────────────────────────────────────────────────────────────
    BG        = "#f0f2f5"
    CARD_BG   = "#ffffff"
    ORANGE    = "#ff6d00"
    TEXT      = "#333333"
    SUBTLE    = "#888888"
    FONT      = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_H    = ("Segoe UI", 13, "bold")

    # ── Card frame ────────────────────────────────────────────────────────
    card = tk.Frame(root, bg=CARD_BG, padx=28, pady=24,
                    highlightbackground="#dddddd", highlightthickness=1)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    # Header
    tk.Label(card, text="Informatica IDMC", font=FONT_H,
             fg=ORANGE, bg=CARD_BG).grid(row=0, column=0, columnspan=2,
                                          sticky="w", pady=(0, 2))
    tk.Label(card, text="Enter your credentials to continue", font=FONT,
             fg=SUBTLE, bg=CARD_BG).grid(row=1, column=0, columnspan=2,
                                          sticky="w", pady=(0, 16))

    # Username
    tk.Label(card, text="Username (email)", font=FONT_BOLD,
             fg=TEXT, bg=CARD_BG).grid(row=2, column=0, columnspan=2,
                                        sticky="w", pady=(0, 4))
    username_var = tk.StringVar()
    username_entry = tk.Entry(card, textvariable=username_var, font=FONT,
                              width=32, relief="solid", bd=1)
    username_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))

    # Password
    tk.Label(card, text="Password", font=FONT_BOLD,
             fg=TEXT, bg=CARD_BG).grid(row=4, column=0, columnspan=2,
                                        sticky="w", pady=(0, 4))
    password_var = tk.StringVar()
    password_entry = tk.Entry(card, textvariable=password_var, show="●",
                              font=FONT, width=32, relief="solid", bd=1)
    password_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 20))

    # ── Buttons ───────────────────────────────────────────────────────────
    def on_submit(event=None):
        u = username_var.get().strip()
        p = password_var.get()
        if not u:
            messagebox.showwarning("Missing field", "Please enter your username.", parent=root)
            username_entry.focus_set()
            return
        if not p:
            messagebox.showwarning("Missing field", "Please enter your password.", parent=root)
            password_entry.focus_set()
            return
        result["username"] = u
        result["password"] = p
        result["submitted"] = True
        root.destroy()

    def on_cancel():
        root.destroy()

    btn_frame = tk.Frame(card, bg=CARD_BG)
    btn_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    tk.Button(btn_frame, text="Cancel", font=FONT, fg=SUBTLE, bg="#eeeeee",
              relief="flat", cursor="hand2", command=on_cancel,
              padx=12, pady=6).grid(row=0, column=0, sticky="ew", padx=(0, 6))

    tk.Button(btn_frame, text="Login", font=FONT_BOLD, fg="#ffffff", bg=ORANGE,
              activebackground="#e56200", relief="flat", cursor="hand2",
              command=on_submit, padx=12, pady=6).grid(row=0, column=1, sticky="ew")

    # Keyboard shortcuts
    root.bind("<Return>", on_submit)
    root.bind("<Escape>", lambda e: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    username_entry.focus_set()
    root.mainloop()

    if not result["submitted"]:
        raise RuntimeError("Login cancelled by user.")

    return result["username"], result["password"]
