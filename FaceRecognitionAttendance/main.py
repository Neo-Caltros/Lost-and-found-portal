"""Application entry point for the Face Recognition Attendance System."""

from __future__ import annotations

import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from attendance import AttendanceWindow
from database import AttendanceDatabase
from login import LoginWindow
from recognize import take_attendance
from register import RegistrationWindow
from train import TrainingWindow
from utils import ATTENDANCE_CSV_PATH, DATABASE_DIR, DATABASE_PATH, FaceAttendanceError, ensure_project_directories


class FaceAttendanceApp:
    """Coordinates login, dashboard actions, and status updates."""

    def __init__(self) -> None:
        ensure_project_directories()
        self.database = AttendanceDatabase()
        self.database.initialize()
        self.root = tk.Tk()
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("1020x680")
        self.root.minsize(920, 600)
        self._configure_style()
        self.dashboard: ttk.Frame | None = None
        self.status_var = tk.StringVar(value="Please sign in as administrator.")
        self.root.withdraw()
        LoginWindow(self.root, self.show_dashboard)

    def _configure_style(self) -> None:
        """Apply a restrained dark theme without external GUI dependencies."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        background = "#101827"
        card = "#182235"
        foreground = "#EDF2F7"
        muted = "#A8B3C7"
        accent = "#2E8BFF"
        danger = "#D84C5C"
        self.root.configure(background=background)
        style.configure(".", background=background, foreground=foreground, font=("Segoe UI", 10))
        style.configure("TFrame", background=background)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=background, foreground=foreground)
        style.configure("Card.TLabel", background=card, foreground=foreground)
        style.configure("Title.TLabel", background=card, foreground=foreground, font=("Segoe UI", 19, "bold"))
        style.configure("Section.TLabel", background=card, foreground=foreground, font=("Segoe UI", 15, "bold"))
        style.configure("Muted.TLabel", background=card, foreground=muted)
        style.configure("Hint.TLabel", background=card, foreground=muted, font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground="#243148", foreground=foreground, insertcolor=foreground)
        style.configure("TSpinbox", fieldbackground="#243148", foreground=foreground, arrowsize=14)
        style.configure("TButton", background="#30415F", foreground=foreground, padding=(12, 8))
        style.map("TButton", background=[("active", "#3B5277")])
        style.configure("Accent.TButton", background=accent, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1976D2")])
        style.configure("Danger.TButton", background=danger, foreground="white")
        style.map("Danger.TButton", background=[("active", "#B83748")])
        style.configure("Treeview", background="#202D43", fieldbackground="#202D43", foreground=foreground, rowheight=28)
        style.configure("Treeview.Heading", background="#30415F", foreground=foreground, font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "white")])

    def show_dashboard(self) -> None:
        self.root.deiconify()
        if self.dashboard is not None:
            self.dashboard.destroy()
        self.dashboard = ttk.Frame(self.root, padding=24)
        self.dashboard.pack(fill="both", expand=True)
        self.dashboard.columnconfigure((0, 1, 2), weight=1, uniform="columns")
        self.dashboard.rowconfigure(2, weight=1)

        header = ttk.Frame(self.dashboard)
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Face Recognition Attendance", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Secure local attendance management for your department",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(header, text="Log Out", command=self.logout).grid(row=0, column=1, rowspan=2, sticky="e")

        self.card_values: dict[str, tk.StringVar] = {}
        cards = (
            ("students", "Registered Students"),
            ("present_today", "Present Today"),
            ("attendance", "Attendance Records"),
        )
        for index, (key, label) in enumerate(cards):
            card = ttk.Frame(self.dashboard, padding=18, style="Card.TFrame")
            card.grid(row=1, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == 2 else 8), pady=(0, 18))
            value = tk.StringVar(value="0")
            self.card_values[key] = value
            ttk.Label(card, textvariable=value, style="Title.TLabel").pack(anchor="w")
            ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w", pady=(5, 0))

        actions = ttk.Frame(self.dashboard, padding=20, style="Card.TFrame")
        actions.grid(row=2, column=0, columnspan=3, sticky="nsew")
        actions.columnconfigure((0, 1), weight=1, uniform="actions")
        actions.rowconfigure((0, 1, 2), weight=1)
        button_specs = (
            ("Register Student", self.open_registration, "Add a student and capture 50-100 face images."),
            ("Train Model", self.open_training, "Build or retrain the LBPH recognition model."),
            ("Take Attendance", self.start_attendance, "Recognize faces from the connected webcam."),
            ("View Attendance", self.open_attendance, "Search records by date, name, or student ID."),
            ("Export CSV", self.export_all, "Write all attendance records to attendance/attendance.csv."),
            ("Backup Database", self.backup_database, "Create a timestamped copy of the SQLite database."),
        )
        for index, (title, command, subtitle) in enumerate(button_specs):
            row, column = divmod(index, 2)
            panel = ttk.Frame(actions, padding=14, style="Card.TFrame")
            panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
            panel.columnconfigure(0, weight=1)
            ttk.Label(panel, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(panel, text=subtitle, style="Muted.TLabel", wraplength=330).grid(
                row=1, column=0, sticky="w", pady=(3, 12)
            )
            ttk.Button(panel, text=title, command=command, style="Accent.TButton").grid(row=2, column=0, sticky="ew")

        footer = ttk.Frame(self.dashboard)
        footer.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(18, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Hint.TLabel", wraplength=740).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(footer, text="Exit", command=self.root.destroy, style="Danger.TButton").grid(
            row=0, column=1, sticky="e"
        )
        self.refresh_dashboard()

    def refresh_dashboard(self, message: str | None = None) -> None:
        stats = self.database.statistics()
        for key, value in stats.items():
            if key in self.card_values:
                self.card_values[key].set(str(value))
        if message:
            self.status_var.set(message)

    def open_registration(self) -> None:
        RegistrationWindow(self.root, self.database, self._on_data_changed)
        self.status_var.set("Student registration window opened.")

    def open_training(self) -> None:
        TrainingWindow(self.root, self._on_data_changed)
        self.status_var.set("Model training window opened.")

    def start_attendance(self) -> None:
        try:
            take_attendance(self.database, self.status_var.set)
        except (FaceAttendanceError, OSError) as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("Attendance unavailable", str(exc), parent=self.root)
        finally:
            self.refresh_dashboard()

    def open_attendance(self) -> None:
        AttendanceWindow(self.root, self.database, self._on_data_changed)
        self.status_var.set("Attendance records window opened.")

    def export_all(self) -> None:
        count = self.database.export_attendance(ATTENDANCE_CSV_PATH)
        message = f"Exported {count} attendance record(s) to {ATTENDANCE_CSV_PATH}."
        self.status_var.set(message)
        messagebox.showinfo("CSV export complete", message, parent=self.root)

    def backup_database(self) -> None:
        backup_dir = DATABASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_name = f"attendance_{datetime.now():%Y%m%d_%H%M%S}.db"
        destination = backup_dir / backup_name
        shutil.copy2(DATABASE_PATH, destination)
        message = f"Database backup created: {destination.name}"
        self.status_var.set(message)
        messagebox.showinfo("Backup complete", message, parent=self.root)

    def _on_data_changed(self, message: str) -> None:
        self.refresh_dashboard(message)

    def logout(self) -> None:
        if self.dashboard is not None:
            self.dashboard.destroy()
            self.dashboard = None
        self.root.withdraw()
        LoginWindow(self.root, self.show_dashboard)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    FaceAttendanceApp().run()
