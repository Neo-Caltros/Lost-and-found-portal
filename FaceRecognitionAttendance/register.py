"""Student registration, webcam capture, and student deletion screen."""

from __future__ import annotations

import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

import cv2

from database import AttendanceDatabase, Student
from utils import DATASET_DIR, CameraError, FaceAttendanceError, load_face_detector, open_camera, validate_student_fields


class RegistrationWindow(tk.Toplevel):
    """Register students and capture 50-100 face samples from a webcam."""

    def __init__(
        self,
        parent: tk.Misc,
        database: AttendanceDatabase,
        on_changed: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.on_changed = on_changed
        self.title("Register Student")
        self.minsize(900, 590)
        self.transient(parent)
        self._build()
        self.refresh_students()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        form_card = ttk.Frame(self, padding=22, style="Card.TFrame")
        form_card.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        table_card = ttk.Frame(self, padding=18, style="Card.TFrame")
        table_card.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        ttk.Label(form_card, text="Student Registration", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", columnspan=2
        )
        ttk.Label(
            form_card,
            text="Capture clear, front-facing images under normal lighting.",
            style="Muted.TLabel",
            wraplength=260,
        ).grid(row=1, column=0, sticky="w", columnspan=2, pady=(5, 20))

        self.student_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.department_var = tk.StringVar()
        self.semester_var = tk.StringVar()
        self.sample_count_var = tk.IntVar(value=70)
        fields = (
            ("Student ID", self.student_id_var),
            ("Full Name", self.name_var),
            ("Department", self.department_var),
            ("Semester", self.semester_var),
        )
        for index, (label, variable) in enumerate(fields, start=2):
            ttk.Label(form_card, text=label).grid(row=index * 2, column=0, sticky="w", pady=(0, 4))
            ttk.Entry(form_card, textvariable=variable, width=30).grid(
                row=index * 2 + 1, column=0, sticky="ew", pady=(0, 10)
            )

        ttk.Label(form_card, text="Face images (50-100)").grid(row=11, column=0, sticky="w", pady=(0, 4))
        ttk.Spinbox(
            form_card,
            from_=50,
            to=100,
            increment=5,
            textvariable=self.sample_count_var,
            width=8,
        ).grid(row=12, column=0, sticky="w", pady=(0, 18))
        self.capture_button = ttk.Button(
            form_card,
            text="Save Student and Capture Faces",
            command=self.save_and_capture,
            style="Accent.TButton",
        )
        self.capture_button.grid(row=13, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Enter student details, then begin capture.")
        ttk.Label(
            form_card, textvariable=self.status_var, style="Hint.TLabel", wraplength=270
        ).grid(row=14, column=0, sticky="w", pady=(16, 0))
        form_card.columnconfigure(0, weight=1)

        ttk.Label(table_card, text="Registered Students", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            table_card,
            text="Deleting a student also removes their face images and attendance history. Retrain the model afterward.",
            style="Muted.TLabel",
            wraplength=540,
        ).pack(anchor="w", pady=(5, 12))
        table_frame = ttk.Frame(table_card)
        table_frame.pack(fill="both", expand=True)
        columns = ("student_id", "name", "department", "semester")
        self.student_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        headings = ("Student ID", "Name", "Department", "Semester")
        widths = (105, 170, 150, 85)
        for column, heading, width in zip(columns, headings, widths):
            self.student_tree.heading(column, text=heading)
            self.student_tree.column(column, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        self.student_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        actions = ttk.Frame(table_card, style="Card.TFrame")
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Refresh", command=self.refresh_students).pack(side="left")
        ttk.Button(actions, text="Delete Selected", command=self.delete_selected, style="Danger.TButton").pack(
            side="right"
        )

    def save_and_capture(self) -> None:
        """Create the student first, then collect the requested face crops."""
        try:
            student_id, name, department, semester = validate_student_fields(
                self.student_id_var.get(),
                self.name_var.get(),
                self.department_var.get(),
                self.semester_var.get(),
            )
            requested_samples = int(self.sample_count_var.get())
            if not 50 <= requested_samples <= 100:
                raise FaceAttendanceError("Choose between 50 and 100 face images.")
            student = self.database.add_student(student_id, name, department, semester)
        except (FaceAttendanceError, ValueError) as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("Registration failed", str(exc), parent=self)
            return

        self.capture_button.configure(state="disabled")
        self.status_var.set("Opening camera. Press Q or Escape to end capture early.")
        self.update_idletasks()
        try:
            captured = self._capture_faces(student, requested_samples)
        except (CameraError, FaceAttendanceError, cv2.error, OSError) as exc:
            captured = 0
            self.status_var.set(f"Capture failed: {exc}")
            messagebox.showerror("Face capture failed", str(exc), parent=self)
        finally:
            self.capture_button.configure(state="normal")

        if captured < 50:
            self.database.delete_student(student.id)
            for image_path in DATASET_DIR.glob(f"user.{student.id}.*.jpg"):
                image_path.unlink(missing_ok=True)
            self.status_var.set(
                f"Only {captured} images were captured. At least 50 are required, so the new student record was removed."
            )
            messagebox.showwarning("Capture incomplete", self.status_var.get(), parent=self)
        else:
            message = (
                f"Registered {student.name} and captured {captured} face image(s). "
                "Train the model before taking attendance."
            )
            self.status_var.set(message)
            messagebox.showinfo("Registration complete", message, parent=self)
            self._clear_form()
            if self.on_changed:
                self.on_changed(message)
        self.refresh_students()

    def _capture_faces(self, student: Student, target: int) -> int:
        """Capture one largest detected face approximately every 180 milliseconds."""
        detector = load_face_detector()
        camera = open_camera()
        saved = 0
        last_saved = 0.0
        window_name = "Capture Face Images - Press Q to stop"
        try:
            while saved < target:
                success, frame = camera.read()
                if not success:
                    raise CameraError("Camera frame could not be read.")
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100)
                )
                if len(faces):
                    x_pos, y_pos, width, height = max(faces, key=lambda face: face[2] * face[3])
                    cv2.rectangle(
                        frame, (x_pos, y_pos), (x_pos + width, y_pos + height), (40, 190, 90), 2
                    )
                    now = time.monotonic()
                    if now - last_saved >= 0.18:
                        face_crop = gray[y_pos : y_pos + height, x_pos : x_pos + width]
                        face_crop = cv2.resize(face_crop, (200, 200))
                        saved += 1
                        image_path = DATASET_DIR / f"user.{student.id}.{saved}.jpg"
                        if not cv2.imwrite(str(image_path), face_crop):
                            raise FaceAttendanceError("A face image could not be saved to the dataset folder.")
                        last_saved = now
                        self.status_var.set(f"Capturing images: {saved}/{target}")
                        self.update_idletasks()
                cv2.putText(
                    frame,
                    f"Images: {saved}/{target} | Look at camera | Q: stop",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
        finally:
            camera.release()
            cv2.destroyAllWindows()
        return saved

    def refresh_students(self) -> None:
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        for student in self.database.list_students():
            self.student_tree.insert(
                "",
                "end",
                iid=str(student.id),
                values=(student.student_id, student.name, student.department, student.semester),
            )

    def delete_selected(self) -> None:
        selection = self.student_tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a student to delete.", parent=self)
            return
        student = self.database.get_student(int(selection[0]))
        if student is None:
            self.refresh_students()
            return
        approved = messagebox.askyesno(
            "Delete student",
            f"Delete {student.name} ({student.student_id}), all their face images, and attendance history?",
            parent=self,
        )
        if not approved:
            return
        self.database.delete_student(student.id)
        for image_path in DATASET_DIR.glob(f"user.{student.id}.*.jpg"):
            image_path.unlink(missing_ok=True)
        message = f"Deleted {student.name}. Retrain the model before taking attendance."
        self.status_var.set(message)
        self.refresh_students()
        if self.on_changed:
            self.on_changed(message)

    def _clear_form(self) -> None:
        self.student_id_var.set("")
        self.name_var.set("")
        self.department_var.set("")
        self.semester_var.set("")
