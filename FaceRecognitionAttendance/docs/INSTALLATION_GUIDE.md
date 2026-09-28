# Installation Guide - Face Recognition Attendance System

## Prerequisites

- Windows 10 or Windows 11
- Python 3.11 or newer (install from [python.org](https://www.python.org/downloads/))
- Visual Studio Code with the Python extension
- A working USB or integrated webcam

## Install the Project

Open the project folder in VS Code. In the integrated PowerShell terminal, run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this for the current terminal only and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run

```powershell
python main.py
```

On the first launch, the application creates:

- `database/attendance.db` - SQLite database and schema
- `haarcascade/haarcascade_frontalface_default.xml` - local face detector copied from OpenCV
- `dataset/`, `trainer/`, and `attendance/` folders if they do not exist

## Default Login

| Field | Value |
| --- | --- |
| Username | `admin` |
| Password | `admin123` |

For a real demonstration, set both variables before launching the application:

```powershell
$env:FACE_ATTENDANCE_ADMIN_USER = "cse-admin"
$env:FACE_ATTENDANCE_ADMIN_PASSWORD = "change-this-password"
python main.py
```

## Camera Setup

1. Close Teams, Zoom, Camera, or another program that may use the webcam.
2. In Windows **Settings > Privacy & security > Camera**, allow desktop apps to access the camera.
3. Register a student in even light and keep only one face in the frame.
4. During capture or recognition, press `Q` or `Esc` while the OpenCV camera window is focused to stop.

## Training and Attendance

1. Register one or more students and capture 50-100 samples each.
2. Select **Train Model**. A `trainer/trainer.yml` file is generated.
3. Select **Take Attendance**. The app automatically writes `Present` once per student per day.
4. Select **View Attendance** to search by date (format `YYYY-MM-DD`) or student name/ID.
5. Select **Export CSV** to create `attendance/attendance.csv`.

## Troubleshooting

| Problem | Resolution |
| --- | --- |
| `LBPH recognition is unavailable` | Remove `opencv-python` if installed and reinstall `opencv-contrib-python` from `requirements.txt`. |
| Camera could not be opened | Check cable/privacy settings and close programs using the camera. |
| Model not found | Register/capture face images, then click **Train Model**. |
| Unknown face is displayed | Capture more varied, well-lit images and retrain. Keep the face centered during recognition. |
| Cascade could not load | Reinstall dependencies; OpenCV supplies the cascade automatically. |

## Run Tests

```powershell
python -m unittest discover -s tests -v
```
