"""
Seed the CappadociaOps experiences catalog with a realistic Cappadocia tour lineup.

Prices are PLACEHOLDERS — the owner sets real prices. commission_pct reflects
typical travel-affiliate rates (GetYourGuide / Viator ~8-12%); booking_url is the
affiliate deep link you paste after signing up. Run:  python seed_tours.py
"""
import sqlite3
from datetime import datetime

# (category, operator, title, price_eur, commission_pct, availability, booking_url)
CATALOG = [
    ("balloon",   "TBD operator", "Sunrise Hot-Air Balloon Flight (Standard, ~60 min)", 180.0, 8.0, 16, ""),
    ("balloon",   "TBD operator", "Deluxe Sunrise Balloon Flight (small basket, ~75 min)", 250.0, 8.0, 8, ""),
    ("balloon",   "TBD operator", "Private Hot-Air Balloon Flight", 900.0, 8.0, 2, ""),
    ("tour",      "TBD operator", "Red Tour — North Cappadocia (Göreme, valleys, Uçhisar)", 45.0, 10.0, 20, ""),
    ("tour",      "TBD operator", "Green Tour — South (Ihlara Valley, Derinkuyu underground city)", 55.0, 10.0, 20, ""),
    ("atv",       "TBD operator", "Sunset ATV / Quad Safari (2 hours)", 40.0, 10.0, 20, ""),
    ("horse",     "TBD operator", "Sunset Horseback Ride through the Valleys (2 hours)", 55.0, 10.0, 12, ""),
    ("transfer",  "TBD operator", "Private Airport Transfer (NAV/ASR ↔ hotel)", 45.0, 12.0, 30, ""),
    ("dinner",    "TBD operator", "Turkish Night Cultural Show with Dinner", 45.0, 12.0, 30, ""),
    ("tour",      "TBD operator", "Cappadocia Sunrise Photography Tour", 60.0, 10.0, 10, ""),
    ("experience","TBD operator", "Pottery Workshop in Avanos", 25.0, 10.0, 15, ""),
    ("experience","TBD operator", "Cappadocia Cooking Class", 45.0, 10.0, 10, ""),
]

def seed(reset=True):
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    # ensure table + booking_url column exist (matches main.init_db)
    c.execute('''CREATE TABLE IF NOT EXISTS experiences
                 (id INTEGER PRIMARY KEY, category TEXT, operator TEXT,
                  title TEXT, price_eur REAL, commission_pct REAL,
                  availability INTEGER, active BOOLEAN, updated_at TEXT,
                  booking_url TEXT)''')
    cols = [r[1] for r in c.execute("PRAGMA table_info(experiences)").fetchall()]
    if "booking_url" not in cols:
        c.execute("ALTER TABLE experiences ADD COLUMN booking_url TEXT")
    if reset:
        c.execute("DELETE FROM experiences")
    now = datetime.now().isoformat()
    for cat, op, title, price, comm, avail, url in CATALOG:
        c.execute("""INSERT INTO experiences
                     (category, operator, title, price_eur, commission_pct,
                      availability, active, updated_at, booking_url)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (cat, op, title, price, comm, avail, True, now, url))
    conn.commit()
    n = c.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
    conn.close()
    print(f"Seeded {n} experiences into cappadocia_ops.db")

if __name__ == "__main__":
    seed()
