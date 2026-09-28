# Reunite — Lost & Found Portal

Reunite is a responsive Flask portal that helps a community reconnect people with lost belongings. It includes a polished public listing board, search and filters, item detail pages, private claim requests, and a guided report flow.

## Features

- Browse active lost and found listings
- Search by item, description, or location
- Filter listings by type and category
- Submit lost or found reports with contact details
- View complete listing details and send a private claim request
- SQLite persistence with sample listings for a ready-to-explore experience
- Responsive layout for desktop and mobile screens

## Run locally

1. Install the project dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Start the site:

   ```powershell
   python app.py
   ```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The portal creates `data/lost_found.db` automatically on first run. The included sample listings make it easy to explore the interface; new reports and claim requests are stored in the same local database.
