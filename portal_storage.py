import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta


DB_PATH = os.path.join("data", "lost_found.db")


def _connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_portal():
    os.makedirs("data", exist_ok=True)
    with closing(_connection()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL CHECK(item_type IN ('lost', 'found')),
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                date_reported TEXT NOT NULL,
                color TEXT,
                contact_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                contact_phone TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                claimant_name TEXT NOT NULL,
                claimant_email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
            """
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if count == 0:
            _seed_items(conn)
            conn.commit()


def _seed_items(conn):
    today = date.today()
    examples = [
        ("lost", "Navy blue water bottle", "Personal items", "Insulated 750 ml bottle with a small mountain sticker near the base.", "Library, second floor", today - timedelta(days=1), "Navy blue", "Maya Chen", "maya@example.com", "555-0142"),
        ("found", "Silver wireless earbuds", "Electronics", "Pair of earbuds in a pale grey charging case. Found near a study desk.", "North Hall, Room 204", today, "Silver", "Jordan Lee", "jordan@example.com", "555-0189"),
        ("lost", "Black canvas tote bag", "Bags", "Black tote with an orange book and a metal keychain inside.", "Campus café patio", today - timedelta(days=2), "Black", "Sofia Patel", "sofia@example.com", "555-0171"),
        ("found", "Set of house keys", "Keys & IDs", "Three keys on a green fabric lanyard with a round brass keyring.", "East parking lot", today - timedelta(days=1), "Brass and green", "Avery Kim", "avery@example.com", "555-0128"),
        ("lost", "Cream knit cardigan", "Clothing", "Soft cream cardigan with pearlescent buttons, size medium.", "Arts building, studio 3", today - timedelta(days=3), "Cream", "Noah Williams", "noah@example.com", "555-0164"),
        ("found", "Student ID card", "Keys & IDs", "Campus ID card. Name is intentionally hidden until ownership is verified.", "Student center reception", today, "White and blue", "Campus Desk", "desk@example.com", "555-0110"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    conn.executemany(
        """
        INSERT INTO items
        (item_type, title, category, description, location, date_reported, color, contact_name, contact_email, contact_phone, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(*item[:5], item[5].isoformat(), *item[6:], now) for item in examples],
    )


def get_categories():
    return ["Bags", "Clothing", "Electronics", "Keys & IDs", "Personal items", "Sports & fitness", "Other"]


def create_item(**values):
    now = datetime.now().isoformat(timespec="seconds")
    fields = (
        "item_type", "title", "category", "description", "location", "date_reported",
        "color", "contact_name", "contact_email", "contact_phone",
    )
    with closing(_connection()) as conn:
        cursor = conn.execute(
            f"INSERT INTO items ({', '.join(fields)}, created_at) VALUES ({', '.join('?' for _ in fields)}, ?)",
            [values[field] for field in fields] + [now],
        )
        conn.commit()
        return cursor.lastrowid


def _serialize(row):
    item = dict(row)
    created = datetime.fromisoformat(item["created_at"])
    item["created_label"] = created.strftime("%b %d")
    item["date_label"] = datetime.strptime(item["date_reported"], "%Y-%m-%d").strftime("%b %d, %Y")
    item["icon"] = {
        "Bags": "bag", "Clothing": "shirt", "Electronics": "bolt", "Keys & IDs": "key",
        "Personal items": "sparkle", "Sports & fitness": "ball",
    }.get(item["category"], "box")
    return item


def list_items(query="", category="", item_type="", limit=12, exclude_id=None):
    conditions = ["status = 'active'"]
    params = []
    if query:
        conditions.append("(title LIKE ? OR description LIKE ? OR location LIKE ?)")
        term = f"%{query}%"
        params.extend([term, term, term])
    if category:
        conditions.append("category = ?")
        params.append(category)
    if item_type in ("lost", "found"):
        conditions.append("item_type = ?")
        params.append(item_type)
    if exclude_id:
        conditions.append("id != ?")
        params.append(exclude_id)
    params.append(limit)
    with closing(_connection()) as conn:
        rows = conn.execute(
            f"SELECT * FROM items WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [_serialize(row) for row in rows]


def get_recent_items(limit=3):
    return list_items(limit=limit)


def get_item(item_id):
    with closing(_connection()) as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ? AND status = 'active'", (item_id,)).fetchone()
    return _serialize(row) if row else None


def add_claim(item_id, claimant_name, claimant_email, message):
    with closing(_connection()) as conn:
        conn.execute(
            "INSERT INTO claims (item_id, claimant_name, claimant_email, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, claimant_name, claimant_email, message, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()


def get_portal_stats():
    with closing(_connection()) as conn:
        total = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'active'").fetchone()[0]
        found = conn.execute("SELECT COUNT(*) FROM items WHERE item_type = 'found' AND status = 'active'").fetchone()[0]
        claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    return {"total": total, "found": found, "claims": claims}
