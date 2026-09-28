# Face Recognition Attendance System

A complete desktop attendance project for second-year Computer Science Engineering students. The system uses Tkinter for its GUI, SQLite for local records, OpenCV Haar Cascade for face detection, and OpenCV LBPH for face recognition. It is designed for Windows and Python 3.11+.

## Features

- Password-protected administrator login
- Student registration with ID, name, department, and semester
- Webcam capture of 50-100 face images per student
- OpenCV LBPH model training and retraining
- Real-time recognition with an on-screen confidence percentage
- Automatic attendance marking with one record per student per day
- SQLite attendance search by date, student ID, or name
- CSV export to `attendance/attendance.csv` or a chosen location
- Student deletion, including face images and attendance history
- Dark-mode dashboard, live statistics, and database backup

## Project Layout

```text
FaceRecognitionAttendance/
├── main.py                 # Application entry point and dashboard
├── login.py                # Administrator authentication dialog
├── register.py             # Student registration and face-image capture
├── train.py                # LBPH training workflow
├── recognize.py            # Real-time recognition and attendance marking
├── attendance.py           # Searchable attendance viewer and CSV export
├── database.py             # SQLite repository layer
├── utils.py                # Paths, OpenCV setup, validation, camera helpers
├── requirements.txt
├── database/               # attendance.db is created on first launch
├── dataset/                # Captured `user.<database-id>.<image>.jpg` files
├── trainer/                # trainer.yml is created after model training
├── haarcascade/            # Cascade copied here from OpenCV on first launch
├── attendance/             # Default CSV exports
├── docs/
│   ├── INSTALLATION_GUIDE.md
│   ├── TEST_CASES.md
│   └── diagrams/
└── tests/
```

## Quick Start on Windows

1. Open the `FaceRecognitionAttendance` folder in VS Code.
2. Create and activate a Python 3.11+ virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies and run the app:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python main.py
   ```

4. Sign in with the default administrator credentials:

   - Username: `admin`
   - Password: `admin123`

   Change them before a real deployment by setting environment variables:

   ```powershell
   $env:FACE_ATTENDANCE_ADMIN_USER = "your-admin-name"
   $env:FACE_ATTENDANCE_ADMIN_PASSWORD = "a-strong-password"
   python main.py
   ```

## Recommended Workflow

1. Register a student and capture at least 50 well-lit face images.
2. Click **Train Model** after all intended students are registered.
3. Click **Take Attendance** and press `Q` or `Esc` in the camera window to stop.
4. Search records in **View Attendance**, or use **Export CSV**.
5. Retrain after adding or deleting any student.

## Important Notes

- This is an educational local application. Obtain consent before collecting biometric data.
- LBPH distance is converted to a useful visual percentage, but it is not a calibrated probability.
- Make sure no other application is holding the webcam when capture or recognition begins.
- The required Haar Cascade XML is supplied by OpenCV and copied into `haarcascade/` automatically the first time the application starts.

See [Installation Guide](docs/INSTALLATION_GUIDE.md), [Test Cases](docs/TEST_CASES.md), and the [Project Report](docs/Face_Recognition_Attendance_System_Project_Report.docx).
