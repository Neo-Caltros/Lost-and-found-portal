"""Real-time webcam recognition and automatic attendance marking."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import cv2

from database import AttendanceDatabase
from utils import (
    TRAINER_PATH,
    FaceAttendanceError,
    ModelError,
    create_lbph_recognizer,
    load_face_detector,
    open_camera,
)


RECOGNITION_DISTANCE_THRESHOLD = 65.0


def confidence_percentage(distance: float) -> int:
    """Convert LBPH distance (lower is better) into a user-friendly percentage."""
    return max(0, min(100, round(100 - float(distance))))


def is_known_prediction(distance: float) -> bool:
    """Apply the conservative LBPH distance threshold for a known face."""
    return float(distance) <= RECOGNITION_DISTANCE_THRESHOLD


def take_attendance(
    database: AttendanceDatabase,
    on_status: Callable[[str], None] | None = None,
    camera_index: int = 0,
    trainer_path: Path | str = TRAINER_PATH,
) -> dict[str, int]:
    """Run the webcam recognition loop until the user presses Q or Escape."""
    model_path = Path(trainer_path)
    if not model_path.exists() or model_path.stat().st_size == 0:
        raise ModelError("Model not found. Train the face recognition model first.")

    detector = load_face_detector()
    recognizer = create_lbph_recognizer()
    try:
        recognizer.read(str(model_path))
    except cv2.error as exc:
        raise ModelError("The saved model is invalid. Retrain the model and try again.") from exc

    camera = open_camera(camera_index)
    marked_ids: set[int] = set()
    summary = {"marked": 0, "already_marked": 0, "unknown_frames": 0}
    window_name = "Face Recognition Attendance - Press Q to stop"
    if on_status:
        on_status("Recognition started. Look at the camera; press Q in the camera window to stop.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                raise FaceAttendanceError("Camera frame could not be read. Try reconnecting the webcam.")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100)
            )

            for x_pos, y_pos, width, height in faces:
                face_image = cv2.resize(
                    gray[y_pos : y_pos + height, x_pos : x_pos + width], (200, 200)
                )
                predicted_id, distance = recognizer.predict(face_image)
                confidence = confidence_percentage(distance)
                color = (0, 0, 255)
                label = f"Unknown | {confidence}%"

                if is_known_prediction(distance):
                    student = database.get_student(int(predicted_id))
                    if student is not None:
                        color = (40, 190, 90)
                        label = f"{student.student_id} | {student.name} | {confidence}%"
                        if student.id not in marked_ids:
                            was_added, _record = database.mark_attendance(student)
                            marked_ids.add(student.id)
                            if was_added:
                                summary["marked"] += 1
                                if on_status:
                                    on_status(f"Attendance marked for {student.name} ({student.student_id}).")
                            else:
                                summary["already_marked"] += 1
                    else:
                        summary["unknown_frames"] += 1
                else:
                    summary["unknown_frames"] += 1

                cv2.rectangle(frame, (x_pos, y_pos), (x_pos + width, y_pos + height), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (x_pos, max(28, y_pos - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    color,
                    2,
                )

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    if on_status:
        on_status(
            f"Recognition stopped. New attendance: {summary['marked']}; "
            f"already present today: {summary['already_marked']}."
        )
    return summary
