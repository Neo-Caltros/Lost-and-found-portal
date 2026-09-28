"""Shared paths, validation helpers, and OpenCV utility functions."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import cv2


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "attendance.db"
DATASET_DIR = BASE_DIR / "dataset"
TRAINER_DIR = BASE_DIR / "trainer"
TRAINER_PATH = TRAINER_DIR / "trainer.yml"
MODEL_METADATA_PATH = TRAINER_DIR / "model_metadata.json"
HAAR_DIR = BASE_DIR / "haarcascade"
HAAR_PATH = HAAR_DIR / "haarcascade_frontalface_default.xml"
ATTENDANCE_DIR = BASE_DIR / "attendance"
ATTENDANCE_CSV_PATH = ATTENDANCE_DIR / "attendance.csv"


class FaceAttendanceError(Exception):
    """Base exception for expected application errors."""


class CameraError(FaceAttendanceError):
    """Raised when the webcam cannot be accessed."""


class ModelError(FaceAttendanceError):
    """Raised when an LBPH model cannot be created or loaded."""


def ensure_project_directories() -> None:
    """Create runtime folders when the project is first launched."""
    for folder in (DATABASE_DIR, DATASET_DIR, TRAINER_DIR, HAAR_DIR, ATTENDANCE_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def get_cascade_path() -> Path:
    """Return a usable local Haar cascade, copying OpenCV's packaged file once.

    OpenCV distributes this official cascade with its Python package. Copying it
    into the project keeps the required local ``haarcascade`` folder portable
    after the first run while avoiding a separate manual download.
    """
    ensure_project_directories()
    if HAAR_PATH.exists() and HAAR_PATH.stat().st_size > 0:
        return HAAR_PATH

    packaged_cascade = Path(cv2.data.haarcascades) / HAAR_PATH.name
    if not packaged_cascade.exists():
        raise FaceAttendanceError(
            "OpenCV's Haar cascade file was not found. Reinstall "
            "opencv-contrib-python."
        )
    shutil.copy2(packaged_cascade, HAAR_PATH)
    return HAAR_PATH


def load_face_detector() -> cv2.CascadeClassifier:
    """Load and validate the Haar cascade classifier."""
    detector = cv2.CascadeClassifier(str(get_cascade_path()))
    if detector.empty():
        raise FaceAttendanceError("The Haar cascade could not be loaded.")
    return detector


def create_lbph_recognizer():
    """Create the OpenCV-contrib LBPH recognizer with a helpful error."""
    face_module = getattr(cv2, "face", None)
    factory = getattr(face_module, "LBPHFaceRecognizer_create", None)
    if factory is None:
        raise ModelError(
            "LBPH recognition is unavailable. Install opencv-contrib-python, "
            "not opencv-python."
        )
    return factory()


def open_camera(camera_index: int = 0):
    """Open a webcam and raise an actionable error if it is unavailable."""
    if os.name == "nt":
        camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    else:
        camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        camera.release()
        raise CameraError(
            "Camera could not be opened. Check that it is connected and not "
            "being used by another application."
        )
    return camera


def validate_student_fields(
    student_id: str, name: str, department: str, semester: str
) -> tuple[str, str, str, str]:
    """Normalize and validate registration fields before database insertion."""
    values = tuple(value.strip() for value in (student_id, name, department, semester))
    if not all(values):
        raise FaceAttendanceError("All student registration fields are required.")
    if len(values[0]) > 30:
        raise FaceAttendanceError("Student ID must be 30 characters or fewer.")
    if len(values[1]) > 100:
        raise FaceAttendanceError("Student name must be 100 characters or fewer.")
    if len(values[2]) > 80 or len(values[3]) > 30:
        raise FaceAttendanceError("Department or semester value is too long.")
    return values
