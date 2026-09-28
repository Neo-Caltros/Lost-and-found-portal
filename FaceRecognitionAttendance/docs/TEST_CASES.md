# Test Cases

| ID | Feature | Steps | Expected Result |
| --- | --- | --- | --- |
| TC-01 | Student registration | Enter valid details and capture at least one face image in the test environment. | Student is inserted once and images are stored using its internal database ID. |
| TC-02 | Duplicate student ID | Register a second student using an existing Student ID. | Registration is rejected with a clear duplicate-ID message. |
| TC-03 | Model training | Place valid captured images in the dataset and run training. | `trainer.yml` is created and reports the image/student totals. |
| TC-04 | Missing training data | Run training with an empty dataset. | Training stops with an actionable error. |
| TC-05 | Face recognition | Train a model, show a registered student's face to the camera. | Label shows student ID/name and confidence; attendance is marked. |
| TC-06 | Unknown face | Show an unregistered face to the camera. | Label shows `Unknown`; no attendance is created. |
| TC-07 | Duplicate attendance | Recognize the same student twice on the same date. | Only the first recognition creates a `Present` record. |
| TC-08 | Search attendance | Search exact date and partial name/ID. | The table lists only matching records. |
| TC-09 | CSV export | Export all or filtered attendance records. | A UTF-8 CSV with the header and matching records is created. |
| TC-10 | Invalid webcam | Disconnect/lock the camera or mock it as unavailable. | The application reports a camera error without crashing. |
| TC-11 | Delete student | Select a student and confirm deletion. | Student, their face images, and attendance history are deleted; model retraining is requested. |
| TC-12 | Database backup | Click Backup Database. | A timestamped `.db` copy appears in `database/backups/`. |

The automated subset is implemented in `tests/test_system.py`; manual camera tests should be executed on the target Windows machine.
