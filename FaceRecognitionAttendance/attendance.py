"""Tkinter attendance record viewer, search, and CSV export screen."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from database import AttendanceDatabase
from utils import ATTENDANCE_CSV_PATH


class AttendanceWindow(tk.Toplevel):
    """Search attendance by date/student and export the current result set."""

    def __init__(
        self,
        parent: tk.Misc,
        database: AttendanceDatabase,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.on_status = on_status
        self.title("View Attendance Records")
        self.minsize(900, 520)
        self.transient(parent)
        self._build()
        self.search()

    def _build(self) -> None:
        container = ttk.Frame(self, padding=18, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        ttk.Label(container, text="Attendance Records", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="Use YYYY-MM-DD for a date search. Student search matches ID or name.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        filters = ttk.Frame(container, style="Card.TFrame")
        filters.pack(fill="x", pady=(0, 14))
        self.date_var = tk.StringVar()
        self.student_var = tk.StringVar()
        ttk.Label(filters, text="Date").grid(row=0, column=0, sticky="w")
        ttk.Entry(filters, textvariable=self.date_var, width=16).grid(
            row=1, column=0, sticky="w", padx=(0, 12)
        )
        ttk.Label(filters, text="Student ID or name").grid(row=0, column=1, sticky="w")
        ttk.Entry(filters, textvariable=self.student_var, width=30).grid(
            row=1, column=1, sticky="w", padx=(0, 12)
        )
        ttk.Button(filters, text="Search", command=self.search, style="Accent.TButton").grid(
            row=1, column=2, sticky="w", padx=(0, 8)
        )
        ttk.Button(filters, text="Clear", command=self.clear_filters).grid(row=1, column=3, sticky="w")
        self.bind("<Return>", lambda _event: self.search())

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)
        columns = ("student_id", "name", "date", "time", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        widths = (140, 250, 115, 105, 110)
        headings = ("Student ID", "Student Name", "Date", "Time", "Status")
        for column, heading, width in zip(columns, headings, widths):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="center" if column != "name" else "w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        bottom = ttk.Frame(container, style="Card.TFrame")
        bottom.pack(fill="x", pady=(14, 0))
        self.count_var = tk.StringVar(value="0 record(s)")
        ttk.Label(bottom, textvariable=self.count_var, style="Muted.TLabel").pack(side="left")
        ttk.Button(bottom, text="Export Current Results", command=self.export_current).pack(side="right")

    def search(self) -> None:
        records = self.database.list_attendance(self.date_var.get(), self.student_var.get())
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            self.tree.insert(
                "",
                "end",
                values=(record.student_id, record.name, record.date, record.time, record.status),
            )
        self.count_var.set(f"{len(records)} record(s)")

    def clear_filters(self) -> None:
        self.date_var.set("")
        self.student_var.set("")
        self.search()

    def export_current(self) -> None:
        suggested_path = ATTENDANCE_CSV_PATH
        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Export Attendance CSV",
            initialdir=suggested_path.parent,
            initialfile=suggested_path.name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not destination:
            return
        count = self.database.export_attendance(
            Path(destination), self.date_var.get(), self.student_var.get()
        )
        message = f"Exported {count} attendance record(s) to {destination}."
        if self.on_status:
            self.on_status(message)
        messagebox.showinfo("Export complete", message, parent=self)
