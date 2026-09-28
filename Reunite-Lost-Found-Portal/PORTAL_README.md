# Reunite — Lost & Found Portal

## Run it

1. Install Python 3.10 or newer.
2. In this folder, run:

   ```powershell
   python -m pip install -r portal_requirements.txt
   python app.py
   ```

3. Open `http://127.0.0.1:5000` in a browser.

The portal automatically creates a local SQLite database with example listings the first time it starts. New listings and claims are saved only on that computer in `data/lost_found.db`.
