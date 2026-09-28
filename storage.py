import csv
import os
import sqlite3
from contextlib import closing
from datetime import datetime

CSV_PATH = os.path.join("data", "attendance.csv")
DB_PATH = os.path.join("data", "attendance.db")


def ensure_storage():
    os.makedirs("data", exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                confidence REAL NOT NULL,
                mask_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(student_id, date)
            )
            """
        )
        conn.commit()

    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["student_id", "name", "date", "time", "confidence", "mask_status"])

    ensure_mysql_schema()


def get_mysql_connection():
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    if not all([host, user, password, database]):
        return None

    import mysql.connector

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    )


def ensure_mysql_schema():
    conn = get_mysql_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(64) NOT NULL,
                name VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                confidence FLOAT NOT NULL,
                mask_status VARCHAR(64) NOT NULL,
                created_at DATETIME NOT NULL,
                UNIQUE KEY unique_student_date (student_id, date)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_student(student_id, name):
    now = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO students (student_id, name, created_at) VALUES (?, ?, ?)",
            (student_id, name, now),
        )
        conn.commit()


def list_students():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT student_id, name, created_at FROM students ORDER BY name").fetchall()
        return [dict(row) for row in rows]


def get_student(student_id):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT student_id, name, created_at FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        return dict(row) if row else None


def get_student_map():
    return {student["student_id"]: student["name"] for student in list_students()}


def mark_attendance(student_id, name, confidence, mask_status):
    now = datetime.now()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M:%S")
    created_at = now.isoformat(timespec="seconds")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO attendance
                (student_id, name, date, time, confidence, mask_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (student_id, name, date_text, time_text, float(confidence), mask_status, created_at),
        )
        conn.commit()
        inserted = cursor.rowcount > 0

    if inserted:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([student_id, name, date_text, time_text, round(float(confidence), 2), mask_status])
        mark_mysql_attendance(student_id, name, date_text, time_text, confidence, mask_status, created_at)

    return inserted


def mark_mysql_attendance(student_id, name, date_text, time_text, confidence, mask_status, created_at):
    conn = get_mysql_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT IGNORE INTO attendance
                (student_id, name, date, time, confidence, mask_status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (student_id, name, date_text, time_text, float(confidence), mask_status, created_at),
        )
        conn.commit()
    finally:
        conn.close()


def list_attendance(limit=200):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT student_id, name, date, time, confidence, mask_status
            FROM attendance
            ORDER BY date DESC, time DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def dashboard_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        today_present = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (today,),
        ).fetchone()[0]
        total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    return {
        "total_students": total_students,
        "today_present": today_present,
        "total_records": total_records,
    }
