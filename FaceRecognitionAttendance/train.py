"""LBPH model training from locally captured face images."""

from __future__ import annotations

import json
import re
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

import cv2
import numpy as np

from utils import (
    DATASET_DIR,
    MODEL_METADATA_PATH,
    TRAINER_PATH,
    FaceAttendanceError,
    create_lbph_recognizer,
    ensure_project_directories,
)


DATASET_IMAGE_PATTERN = re.compile(r"^user\.(\d+)\.(\d+)\.jpg$", re.IGNORECASE)


@dataclass(frozen=True)
class TrainingResult:
    """Summary returned after writing a new trained model."""

    image_count: int
    student_count: int
    model_path: Path


def train_model(
    dataset_dir: Path | str = DATASET_DIR,
    trainer_path: Path | str = TRAINER_PATH,
    metadata_path: Path | str = MODEL_METADATA_PATH,
) -> TrainingResult:
    """Train and save the LBPH model using all valid captured images."""
    ensure_project_directories()
    source_directory = Path(dataset_dir)
    output_model = Path(trainer_path)
    output_metadata = Path(metadata_path)

    faces: list[np.ndarray] = []
    labels: list[int] = []
    for image_path in sorted(source_directory.glob("user.*.*.jpg")):
        match = DATASET_IMAGE_PATTERN.match(image_path.name)
        if match is None:
            continue
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None or image.size == 0:
            continue
        faces.append(cv2.resize(image, (200, 200)))
        labels.append(int(match.group(1)))

    if not faces:
        raise FaceAttendanceError(
            "No usable face images were found. Register a student and capture faces first."
        )

    recognizer = create_lbph_recognizer()
    recognizer.train(faces, np.array(labels, dtype=np.int32))
    output_model.parent.mkdir(parents=True, exist_ok=True)
    output_metadata.parent.mkdir(parents=True, exist_ok=True)
    recognizer.write(str(output_model))

    output_metadata.write_text(
        json.dumps(
            {
                "trained_at": datetime.now().isoformat(timespec="seconds"),
                "images": len(faces),
                "students": len(set(labels)),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return TrainingResult(len(faces), len(set(labels)), output_model)


class TrainingWindow(tk.Toplevel):
    """Small GUI flow for starting model training and showing its result."""

    def __init__(
        self,
        parent: tk.Misc,
        on_complete: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.on_complete = on_complete
        self.title("Train Face Recognition Model")
        self.resizable(False, False)
        self.transient(parent)
        self._build()
        self.geometry("500x280")

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=24, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=14, pady=14)
        ttk.Label(frame, text="Train LBPH Model", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text=(
                "The trainer reads face crops from the dataset folder and creates "
                "trainer/trainer.yml. Retrain whenever students are added or removed."
            ),
            wraplength=430,
            style="Muted.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(8, 20))
        self.status_var = tk.StringVar(value="Ready to train.")
        ttk.Label(frame, textvariable=self.status_var, wraplength=430).pack(anchor="w", pady=(0, 18))
        self.train_button = ttk.Button(
            frame, text="Start Training", command=self._run_training, style="Accent.TButton"
        )
        self.train_button.pack(fill="x")

    def _run_training(self) -> None:
        self.train_button.configure(state="disabled")
        self.status_var.set("Training model. Please wait...")
        self.update_idletasks()
        try:
            result = train_model()
        except (FaceAttendanceError, cv2.error, OSError) as exc:
            message = f"Training failed: {exc}"
            self.status_var.set(message)
            messagebox.showerror("Training failed", message, parent=self)
            self.train_button.configure(state="normal")
            return
        message = (
            f"Model trained successfully with {result.image_count} images from "
            f"{result.student_count} student(s)."
        )
        self.status_var.set(message)
        if self.on_complete:
            self.on_complete(message)
        messagebox.showinfo("Training complete", message, parent=self)
