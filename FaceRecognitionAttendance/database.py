"""SQLite persistence for students and daily attendance records."""

from __future__ import annotations

import csv
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Sequence

from utils import ATTENDANCE_CSV_PATH, DATABASE_PATH, ensure_project_directories


@dataclass(frozen=True)
class Student:
    """A student stored in the local database."""

    id: int
    student_id: str
    name: str
    department: str
    semester: str


@dataclass(frozen=True)
class AttendanceRecord:
    """An attendance record displayed in the GUI and exported to CSV."""

    id: int
    student_id: str
    name: str
    date: str
    time: str
    status: str


class AttendanceDatabase:
    """Small repository layer that keeps SQL out of the Tkinter modules."""

    def __init__(self, db_path: Path | str = DATABASE_PATH) -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the schema and its uniqueness constraints if needed."""
        ensure_project_directories()
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    semester TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Present',
                    UNIQUE(student_id, date)
                );

                CREATE INDEX IF NOT EXISTS idx_attendance_date
                    ON attendance(date);
                CREATE INDEX IF NOT EXISTS idx_attendance_student
                    ON attendance(student_id);
                """
            )

    def add_student(
        self, student_id: str, name: str, department: str, semester: str
    ) -> Student:
        """Insert a student or raise ValueError for a duplicate student ID."""
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO students (student_id, name, department, semester)
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, name, department, semester),
                )
                db_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Student ID '{student_id}' already exists.") from exc
        return Student(db_id, student_id, name, department, semester)

    def get_student(self, db_id: int) -> Student | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE id = ?", (db_id,)
            ).fetchone()
        return self._student_from_row(row)

    def get_student_by_student_id(self, student_id: str) -> Student | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
        return self._student_from_row(row)

    def list_students(self) -> list[Student]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM students ORDER BY name COLLATE NOCASE, student_id"
            ).fetchall()
        return [self._student_from_row(row) for row in rows if row is not None]

    def delete_student(self, db_id: int) -> Student | None:
        """Remove a student and their attendance history in one transaction."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE id = ?", (db_id,)
            ).fetchone()
            if row is None:
                return None
            student = self._student_from_row(row)
            connection.execute(
                "DELETE FROM attendance WHERE student_id = ?", (student.student_id,)
            )
            connection.execute("DELETE FROM students WHERE id = ?", (db_id,))
        return student

    def mark_attendance(
        self, student: Student, when: datetime | None = None
    ) -> tuple[bool, AttendanceRecord | None]:
        """Store one Present record per student per calendar date.

        The database-level UNIQUE constraint is the final protection against
        double marking, even if multiple recognition frames arrive quickly.
        """
        moment = when or datetime.now()
        record_date = moment.strftime("%Y-%m-%d")
        record_time = moment.strftime("%H:%M:%S")
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO attendance (student_id, name, date, time, status)
                    VALUES (?, ?, ?, ?, 'Present')
                    """,
                    (student.student_id, student.name, record_date, record_time),
                )
                record_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return False, None
        return True, AttendanceRecord(
            record_id,
            student.student_id,
            student.name,
            record_date,
            record_time,
            "Present",
        )

    def list_attendance(
        self, date_filter: str = "", student_filter: str = ""
    ) -> list[AttendanceRecord]:
        """Find attendance by exact date and/or partial student ID/name."""
        sql = "SELECT * FROM attendance WHERE 1 = 1"
        parameters: list[str] = []
        if date_filter.strip():
            sql += " AND date = ?"
            parameters.append(date_filter.strip())
        if student_filter.strip():
            sql += " AND (student_id LIKE ? OR name LIKE ?)"
            query = f"%{student_filter.strip()}%"
            parameters.extend((query, query))
        sql += " ORDER BY date DESC, time DESC, name COLLATE NOCASE"
        with self._connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [self._attendance_from_row(row) for row in rows]

    def export_attendance(
        self,
        destination: Path | str = ATTENDANCE_CSV_PATH,
        date_filter: str = "",
        student_filter: str = "",
    ) -> int:
        """Export the selected attendance records to a UTF-8 CSV file."""
        records = self.list_attendance(date_filter, student_filter)
        output = Path(destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Student ID", "Student Name", "Date", "Time", "Status"])
            writer.writerows(
                (record.student_id, record.name, record.date, record.time, record.status)
                for record in records
            )
        return len(records)

    def statistics(self) -> dict[str, int]:
        """Return lightweight dashboard totals."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._connection() as connection:
            total_students = connection.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]
            total_attendance = connection.execute(
                "SELECT COUNT(*) FROM attendance"
            ).fetchone()[0]
            present_today = connection.execute(
                "SELECT COUNT(*) FROM attendance WHERE date = ?", (today,)
            ).fetchone()[0]
        return {
            "students": int(total_students),
            "attendance": int(total_attendance),
            "present_today": int(present_today),
        }

    @staticmethod
    def _student_from_row(row: sqlite3.Row | None) -> Student | None:
        if row is None:
            return None
        return Student(
            int(row["id"]),
            str(row["student_id"]),
            str(row["name"]),
            str(row["department"]),
            str(row["semester"]),
        )

    @staticmethod
    def _attendance_from_row(row: sqlite3.Row) -> AttendanceRecord:
        return AttendanceRecord(
            int(row["id"]),
            str(row["student_id"]),
            str(row["name"]),
            str(row["date"]),
            str(row["time"]),
            str(row["status"]),
        )
