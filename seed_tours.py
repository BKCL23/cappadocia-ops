"""
Seed the CappadociaOps resale catalog with a realistic Cappadocia tour lineup.

Your model: the operator gives a daily COST; you add a MARKUP; the guest pays
you the SELL price (cost + markup) directly. Your profit is the markup.
Numbers below are PLACEHOLDERS — set your real daily cost and markup. Run:
    python seed_tours.py
"""
import sqlite3
from datetime import datetime

# (category, operator, title, cost_eur, markup_eur, availability)
CATALOG = [
    ("balloon",    "TBD operator", "Sunrise Hot-Air Balloon Flight (Standard, ~60 min)", 150.0, 30.0, 16),
    ("balloon",    "TBD operator", "Deluxe Sunrise Balloon Flight (small basket, ~75 min)", 210.0, 40.0, 8),
    ("balloon",    "TBD operator", "Private Hot-Air Balloon Flight", 800.0, 100.0, 2),
    ("tour",       "TBD operator", "Red Tour — North Cappadocia (Göreme, valleys, Uçhisar)", 35.0, 10.0, 20),
    ("tour",       "TBD operator", "Green Tour — South (Ihlara Valley, Derinkuyu underground city)", 45.0, 10.0, 20),
    ("atv",        "TBD operator", "Sunset ATV / Quad Safari (2 hours)", 30.0, 10.0, 20),
    ("horse",      "TBD operator", "Sunset Horseback Ride through the Valleys (2 hours)", 45.0, 10.0, 12),
    ("transfer",   "TBD operator", "Private Airport Transfer (NAV/ASR ↔ hotel)", 35.0, 10.0, 30),
    ("dinner",     "TBD operator", "Turkish Night Cultural Show with Dinner", 35.0, 10.0, 30),
    ("tour",       "TBD operator", "Cappadocia Sunrise Photography Tour", 50.0, 10.0, 10),
    ("experience", "TBD operator", "Pottery Workshop in Avanos", 20.0, 5.0, 15),
    ("experience", "TBD operator", "Cappadocia Cooking Class", 35.0, 10.0, 10),
]

def seed(reset=True):
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS experiences
                 (id INTEGER PRIMARY KEY, category TEXT, operator TEXT,
                  title TEXT, price_eur REAL, commission_pct REAL,
                  availability INTEGER, active BOOLEAN, updated_at TEXT,
                  booking_url TEXT, cost_eur REAL, markup_eur REAL)''')
    cols = [r[1] for r in c.execute("PRAGMA table_info(experiences)").fetchall()]
    for col in ("booking_url", "cost_eur", "markup_eur"):
        if col not in cols:
            c.execute("ALTER TABLE experiences ADD COLUMN %s %s"
                      % (col, "TEXT" if col == "booking_url" else "REAL"))
    if reset:
        c.execute("DELETE FROM experiences")
    now = datetime.now().isoformat()
    for cat, op, title, cost, markup, avail in CATALOG:
        sell = round(cost + markup, 2)
        c.execute("""INSERT INTO experiences
                     (category, operator, title, price_eur, commission_pct,
                      availability, active, updated_at, booking_url, cost_eur, markup_eur)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (cat, op, title, sell, 0, avail, True, now, "", cost, markup))
    conn.commit()
    n = c.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
    conn.close()
    print(f"Seeded {n} experiences into cappadocia_ops.db")

if __name__ == "__main__":
    seed()
