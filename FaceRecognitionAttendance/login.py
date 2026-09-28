"""Password-protected administrator login dialog."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


class LoginWindow(tk.Toplevel):
    """A compact modal login window for the local administrator."""

    def __init__(self, parent: tk.Tk, on_success: Callable[[], None]) -> None:
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.admin_username = os.getenv("FACE_ATTENDANCE_ADMIN_USER", DEFAULT_ADMIN_USERNAME)
        self.admin_password = os.getenv("FACE_ATTENDANCE_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

        self.title("Admin Login | Face Recognition Attendance")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.parent.destroy)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._center_window(420, 330)

    def _build(self) -> None:
        container = ttk.Frame(self, padding=30, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(container, text="FACE ATTENDANCE", style="Title.TLabel").pack()
        ttk.Label(
            container,
            text="Administrator sign in",
            style="Muted.TLabel",
        ).pack(pady=(3, 22))

        form = ttk.Frame(container, style="Card.TFrame")
        form.pack(fill="x")
        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form, textvariable=self.username_var, width=35)
        username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        ttk.Label(form, text="Password").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            form, textvariable=self.password_var, show="*", width=35
        )
        password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        form.columnconfigure(0, weight=1)

        ttk.Button(container, text="Login", command=self.authenticate, style="Accent.TButton").pack(
            fill="x"
        )
        ttk.Label(
            container,
            text="Set FACE_ATTENDANCE_ADMIN_USER and FACE_ATTENDANCE_ADMIN_PASSWORD\n"
            "environment variables to change the default credentials.",
            style="Hint.TLabel",
            justify="center",
        ).pack(pady=(15, 0))
        username_entry.focus_set()
        self.bind("<Return>", lambda _event: self.authenticate())

    def authenticate(self) -> None:
        if (
            self.username_var.get().strip() == self.admin_username
            and self.password_var.get() == self.admin_password
        ):
            self.grab_release()
            self.destroy()
            self.on_success()
            return
        self.password_var.set("")
        messagebox.showerror("Login failed", "Invalid administrator username or password.", parent=self)

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        x_position = (self.winfo_screenwidth() - width) // 2
        y_position = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x_position}+{y_position}")
