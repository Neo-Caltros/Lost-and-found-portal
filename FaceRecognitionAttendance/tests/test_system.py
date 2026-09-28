"""Automated tests for database, training, recognition helper, and export logic."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from database import AttendanceDatabase
from recognize import confidence_percentage, is_known_prediction
from train import train_model
from utils import CameraError, open_camera


class FaceAttendanceSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_directory.name)
        self.database = AttendanceDatabase(self.temp_path / "attendance.db")
        self.database.initialize()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_student_registration_and_duplicate_id(self) -> None:
        student = self.database.add_student("CSE101", "Asha Sharma", "CSE", "4")
        self.assertEqual(student.student_id, "CSE101")
        with self.assertRaises(ValueError):
            self.database.add_student("CSE101", "Another Asha", "CSE", "4")

    def test_attendance_is_marked_once_per_day(self) -> None:
        student = self.database.add_student("CSE102", "Rahul Das", "CSE", "4")
        first, record = self.database.mark_attendance(student, datetime(2026, 7, 22, 9, 5))
        second, duplicate = self.database.mark_attendance(student, datetime(2026, 7, 22, 10, 5))
        self.assertTrue(first)
        self.assertEqual(record.status, "Present")
        self.assertFalse(second)
        self.assertIsNone(duplicate)
        self.assertEqual(len(self.database.list_attendance()), 1)

    def test_csv_export(self) -> None:
        student = self.database.add_student("CSE103", "Priya Nair", "CSE", "4")
        self.database.mark_attendance(student, datetime(2026, 7, 22, 9, 0))
        output = self.temp_path / "report.csv"
        count = self.database.export_attendance(output)
        self.assertEqual(count, 1)
        content = output.read_text(encoding="utf-8-sig")
        self.assertIn("Student ID,Student Name,Date,Time,Status", content)
        self.assertIn("CSE103,Priya Nair,2026-07-22,09:00:00,Present", content)

    def test_model_training(self) -> None:
        if not hasattr(cv2, "face"):
            self.skipTest("opencv-contrib-python is required for LBPH training")
        dataset = self.temp_path / "dataset"
        trainer = self.temp_path / "trainer" / "trainer.yml"
        metadata = self.temp_path / "trainer" / "metadata.json"
        dataset.mkdir()
        image_one = np.full((200, 200), 110, dtype=np.uint8)
        image_two = np.full((200, 200), 170, dtype=np.uint8)
        cv2.circle(image_one, (100, 100), 55, 220, -1)
        cv2.rectangle(image_two, (45, 45), (155, 155), 30, -1)
        cv2.imwrite(str(dataset / "user.1.1.jpg"), image_one)
        cv2.imwrite(str(dataset / "user.2.1.jpg"), image_two)
        result = train_model(dataset, trainer, metadata)
        self.assertEqual(result.image_count, 2)
        self.assertEqual(result.student_count, 2)
        self.assertTrue(trainer.exists())
        self.assertTrue(metadata.exists())

    def test_unknown_face_threshold_and_confidence(self) -> None:
        self.assertTrue(is_known_prediction(35))
        self.assertFalse(is_known_prediction(85))
        self.assertEqual(confidence_percentage(35), 65)
        self.assertEqual(confidence_percentage(150), 0)

    @patch("utils.cv2.VideoCapture")
    def test_invalid_webcam(self, mock_camera) -> None:
        mock_camera.return_value.isOpened.return_value = False
        with self.assertRaises(CameraError):
            open_camera(99)
        mock_camera.return_value.release.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
