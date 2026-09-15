"""
CappadociaOps - Hotel & Agency Operations Platform
Built by a hotel owner in Cappadocia, Turkey.

Core functionality:
- Unified booking management (Booking.com, Airbnb, Expedia)
- Automated WhatsApp price notifications
- AI-powered multilingual review responses
- Dynamic pricing suggestions based on demand & weather
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
import os
import secrets

app = FastAPI(
    title="CappadociaOps",
    version="0.1.0",
    description="Hotel operations platform for Cappadocia tourism"
)

# Database setup
def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, guest_name TEXT, guest_phone TEXT,
                  platform TEXT, check_in TEXT, check_out TEXT, room TEXT,
                  status TEXT, created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS balloon_prices
                 (id INTEGER PRIMARY KEY, date TEXT UNIQUE, operator TEXT,
                  price_eur REAL, availability INTEGER, weather_ok BOOLEAN,
                  updated_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, guest_phone TEXT, message TEXT,
                  sent_at TEXT, status TEXT, message_type TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY, guest_name TEXT, rating INTEGER,
                  review_text TEXT, language TEXT, response TEXT,
                  responded_at TEXT, status TEXT)''')

    # Bookable experiences you can broker for a commission
    # (balloon flights, airport transfers, ATV, jeep safari, Turkish night, ...)
    # Resale catalog. Your model: the operator gives a daily COST; you add a
    # MARKUP; the guest pays you the SELL price (cost + markup). Your profit is
    # the markup. price_eur = the sell price shown to the guest.
    c.execute('''CREATE TABLE IF NOT EXISTS experiences
                 (id INTEGER PRIMARY KEY, category TEXT, operator TEXT,
                  title TEXT, price_eur REAL, commission_pct REAL,
                  availability INTEGER, active BOOLEAN, updated_at TEXT,
                  booking_url TEXT, cost_eur REAL, markup_eur REAL)''')
    ecols = [r[1] for r in c.execute("PRAGMA table_info(experiences)").fetchall()]
    for col in ("booking_url", "cost_eur", "markup_eur"):
        if col not in ecols:
            c.execute("ALTER TABLE experiences ADD COLUMN %s %s"
                      % (col, "TEXT" if col == "booking_url" else "REAL"))

    # Guest bookings routed through the hotel — the profit-earning table.
    # Each row is markup you would otherwise have left on the table.
    c.execute('''CREATE TABLE IF NOT EXISTS experience_bookings
                 (id INTEGER PRIMARY KEY, token TEXT UNIQUE, guest_name TEXT,
                  guest_phone TEXT, experience_id INTEGER, category TEXT,
                  operator TEXT, title TEXT, pax INTEGER, price_eur REAL,
                  commission_pct REAL, commission_eur REAL, status TEXT,
                  created_at TEXT, confirmed_at TEXT,
                  cost_total_eur REAL, profit_eur REAL)''')
    bcols = [r[1] for r in c.execute("PRAGMA table_info(experience_bookings)").fetchall()]
    for col in ("cost_total_eur", "profit_eur"):
        if col not in bcols:
            c.execute("ALTER TABLE experience_bookings ADD COLUMN %s REAL" % col)

    conn.commit()
    conn.close()

init_db()

# Pydantic Models
class Booking(BaseModel):
    guest_name: str
    guest_phone: str
    platform: str  # booking.com, airbnb, expedia, direct
    check_in: str
    check_out: str
    room: str

class BalloonPrice(BaseModel):
    date: str
    operator: str
    price_eur: float
    availability: int
    weather_ok: bool

class GuestMessage(BaseModel):
    guest_phone: str
    message: str
    message_type: str = "price_update"  # price_update, confirmation, reminder

class ReviewResponse(BaseModel):
    guest_name: str
    rating: int
    review_text: str
    language: str = "en"

class Experience(BaseModel):
    category: str          # balloon, transfer, atv, safari, dinner, tour
    operator: str
    title: str
    cost_eur: float        # what the operator charges you (changes daily)
    markup_eur: float      # what you add on top — your profit per person
    availability: int = 0

class DailyPrice(BaseModel):
    cost_eur: float                 # today's operator cost per person
    markup_eur: float | None = None # optional: change your markup too

class Quote(BaseModel):
    guest_name: str
    guest_phone: str
    experience_id: int
    pax: int = 1
    language: str = "en"

# Routes
@app.get("/")
def root():
    """Health check and basic info."""
    return {
        "app": "CappadociaOps",
        "version": "0.1.0",
        "status": "running",
        "dogfooding": "Cappadocia hotel (20 rooms)",
        "daily_messages": 200,
        "beta_users": 5
    }

@app.post("/bookings")
def create_booking(booking: Booking):
    """Create new booking from OTA or direct booking."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    
    c.execute("""INSERT INTO bookings 
                 (guest_name, guest_phone, platform, check_in, check_out, room, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (booking.guest_name, booking.guest_phone, booking.platform,
               booking.check_in, booking.check_out, booking.room, "confirmed", created_at))
    
    conn.commit()
    booking_id = c.lastrowid
    conn.close()
    
    return {
        "id": booking_id,
        **booking.dict(),
        "status": "confirmed",
        "created_at": created_at
    }

@app.get("/bookings")
def get_bookings(check_in: str = None):
    """Get all bookings, optionally filtered by check-in date."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    
    if check_in:
        c.execute("SELECT * FROM bookings WHERE check_in = ? ORDER BY check_in", (check_in,))
    else:
        c.execute("SELECT * FROM bookings ORDER BY check_in")
    
    bookings = c.fetchall()
    conn.close()
    
    return [
        {
            "id": b[0],
            "guest": b[1],
            "phone": b[2],
            "platform": b[3],
            "check_in": b[4],
            "check_out": b[5],
            "room": b[6],
            "status": b[7],
            "created_at": b[8]
        } for b in bookings
    ]

@app.post("/balloon-prices")
def update_balloon_price(price: BalloonPrice):
    """Update daily balloon price from operators. Called every morning at 5 AM."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    updated_at = datetime.now().isoformat()
    
    c.execute("""INSERT OR REPLACE INTO balloon_prices 
                 (date, operator, price_eur, availability, weather_ok, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (price.date, price.operator, price.price_eur,
               price.availability, price.weather_ok, updated_at))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "price_updated",
        "date": price.date,
        "operator": price.operator,
        "price_eur": price.price_eur,
        "availability": price.availability,
        "weather_ok": price.weather_ok,
        "auto_notifications_queued": True
    }

@app.get("/balloon-prices/{date}")
def get_balloon_prices(date: str):
    """Get all operator prices for a specific date."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT * FROM balloon_prices WHERE date = ? ORDER BY price_eur", (date,))
    prices = c.fetchall()
    conn.close()
    
    if not prices:
        raise HTTPException(status_code=404, detail="No prices found for this date")
    
    return [
        {
            "operator": p[2],
            "price_eur": p[3],
            "availability": p[4],
            "weather_ok": p[5],
            "updated_at": p[6]
        } for p in prices
    ]

@app.post("/messages/send")
def send_message(msg: GuestMessage):
    """Send WhatsApp/SMS to guest with pricing or updates."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    sent_at = datetime.now().isoformat()
    
    c.execute("""INSERT INTO messages 
                 (guest_phone, message, sent_at, status, message_type)
                 VALUES (?, ?, ?, ?, ?)""",
              (msg.guest_phone, msg.message, sent_at, "sent", msg.message_type))
    
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    
    # TODO: Integrate WhatsApp Business API here
    # whatsapp_client.send_message(msg.guest_phone, msg.message)
    
    return {
        "id": msg_id,
        "to": msg.guest_phone,
        "message": msg.message,
        "type": msg.message_type,
        "sent_at": sent_at,
        "channel": "whatsapp"
    }

@app.get("/messages")
def get_messages(limit: int = 50):
    """Get recent sent messages."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY sent_at DESC LIMIT ?", (limit,))
    messages = c.fetchall()
    conn.close()
    
    return [
        {
            "id": m[0],
            "phone": m[1],
            "message": m[2],
            "sent_at": m[3],
            "status": m[4],
            "type": m[5]
        } for m in messages
    ]

@app.post("/reviews/auto-respond")
def auto_respond_review(review: ReviewResponse):
    """
    Generate AI-powered review response in guest's language.
    In production: integrates with Claude API for personalized responses.
    """
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    responded_at = datetime.now().isoformat()
    
    # Placeholder responses by language
    responses = {
        "en": f"Thank you for your {review.rating}-star review! We appreciate your feedback and look forward to welcoming you back to Cappadocia.",
        "tr": f"{review.rating} yıldızlı değerlendirmeniz için teşekkürler! Geri bildiriminizi takdir ediyoruz ve Kapadokya'da sizi tekrar karşılamaktan heyecan duyuyoruz.",
        "de": f"Vielen Dank für Ihre {review.rating}-Sterne-Bewertung! Wir schätzen Ihr Feedback und freuen uns darauf, Sie bald wieder in Kappadokien begrüßen zu dürfen.",
        "ru": f"Спасибо за вашу оценку в {review.rating} звезд! Мы ценим ваш отзыв и с нетерпением ждем встречи с вами в Каппадокии.",
        "zh": f"感谢您的{review.rating}星评价！我们非常感谢您的反馈，期待再次在卡帕多奇亚欢迎您。"
    }
    
    response_text = responses.get(review.language, responses["en"])
    
    c.execute("""INSERT INTO reviews 
                 (guest_name, rating, review_text, language, response, responded_at, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (review.guest_name, review.rating, review.review_text,
               review.language, response_text, responded_at, "pending"))
    
    conn.commit()
    review_id = c.lastrowid
    conn.close()
    
    return {
        "id": review_id,
        "guest": review.guest_name,
        "rating": review.rating,
        "language": review.language,
        "response": response_text,
        "status": "pending",
        "responded_at": responded_at
    }

@app.get("/reviews")
def get_reviews(status: str = None):
    """Get reviews and responses."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    
    if status:
        c.execute("SELECT * FROM reviews WHERE status = ? ORDER BY responded_at DESC", (status,))
    else:
        c.execute("SELECT * FROM reviews ORDER BY responded_at DESC")
    
    reviews = c.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "guest": r[1],
            "rating": r[2],
            "review": r[3],
            "language": r[4],
            "response": r[5],
            "responded_at": r[6],
            "status": r[7]
        } for r in reviews
    ]

# ---------------------------------------------------------------------------
# Resale / markup booking flow
# ---------------------------------------------------------------------------
# Your model: the operator gives you a daily COST (e.g. ~150€, changes daily).
# You add a MARKUP and sell to your own guest, who pays YOU directly (like the
# room). Your profit is the markup. No commission platform, no card, no login.

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")

# Guest-facing booking-confirmation messages, ready to paste into WhatsApp.
QUOTE_TEMPLATES = {
    "en": ("Hi {name}! Here is your {title} for {pax} "
           "({price_pp:.0f}€/person, total {total:.0f}€). "
           "Tap to confirm your spot: {link}"),
    "tr": ("Merhaba {name}! {pax} kişi için {title} teklifiniz "
           "(kişi başı {price_pp:.0f}€, toplam {total:.0f}€). "
           "Yerinizi onaylamak için: {link}"),
    "de": ("Hallo {name}! Ihr Angebot: {title} für {pax} Personen "
           "({price_pp:.0f}€/Person, gesamt {total:.0f}€). "
           "Jetzt Platz bestätigen: {link}"),
    "ru": ("Здравствуйте, {name}! Ваше предложение: {title} на {pax} чел. "
           "({price_pp:.0f}€/чел., итого {total:.0f}€). "
           "Подтвердить бронь: {link}"),
    "zh": ("您好 {name}！您的预订：{title}，{pax} 人 "
           "（每人 {price_pp:.0f}€，共 {total:.0f}€）。"
           "点击确认名额：{link}"),
}


@app.post("/experiences")
def upsert_experience(exp: Experience):
    """Add a resale experience: operator cost + your markup = the guest price."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    updated_at = datetime.now().isoformat()
    sell = round(exp.cost_eur + exp.markup_eur, 2)
    c.execute("""INSERT INTO experiences
                 (category, operator, title, price_eur, commission_pct,
                  availability, active, updated_at, booking_url, cost_eur, markup_eur)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (exp.category, exp.operator, exp.title, sell, 0,
               exp.availability, True, updated_at, "", exp.cost_eur, exp.markup_eur))
    conn.commit()
    exp_id = c.lastrowid
    conn.close()
    return {"id": exp_id, **exp.dict(), "sell_eur": sell,
            "active": True, "updated_at": updated_at}


@app.post("/experiences/{exp_id}/price")
def set_daily_price(exp_id: int, price: DailyPrice):
    """
    Update today's operator cost (and optionally your markup). Call this each
    morning when the operator gives you the day's balloon/tour price.
    """
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT markup_eur FROM experiences WHERE id = ?", (exp_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Experience not found")
    markup = price.markup_eur if price.markup_eur is not None else (row[0] or 0)
    sell = round(price.cost_eur + markup, 2)
    updated_at = datetime.now().isoformat()
    c.execute("""UPDATE experiences SET cost_eur = ?, markup_eur = ?, price_eur = ?,
                 updated_at = ? WHERE id = ?""",
              (price.cost_eur, markup, sell, updated_at, exp_id))
    conn.commit()
    conn.close()
    return {"id": exp_id, "cost_eur": price.cost_eur, "markup_eur": markup,
            "sell_eur": sell, "updated_at": updated_at}


@app.get("/experiences")
def list_experiences(category: str = None):
    """List resale experiences with your cost, markup and sell price."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    if category:
        c.execute("""SELECT * FROM experiences WHERE active = 1 AND category = ?
                     ORDER BY markup_eur DESC""", (category,))
    else:
        c.execute("SELECT * FROM experiences WHERE active = 1 ORDER BY category, markup_eur DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "category": r[1], "operator": r[2], "title": r[3],
            "sell_eur": r[4], "availability": r[6], "updated_at": r[8],
            "cost_eur": r[10], "markup_eur": r[11],
            "your_profit_per_person_eur": r[11],
        } for r in rows
    ]


@app.post("/quotes")
def create_quote(quote: Quote):
    """
    Create a personalized quote for a guest and return a one-tap booking link
    plus a ready-to-send WhatsApp message. The commission is locked to the
    experience's current rate so a later price change doesn't erase your margin.
    """
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT * FROM experiences WHERE id = ? AND active = 1", (quote.experience_id,))
    exp = c.fetchone()
    if not exp:
        conn.close()
        raise HTTPException(status_code=404, detail="Experience not found or inactive")

    price_pp = exp[4]                 # sell price per person (cost + markup)
    cost_pp = exp[10] or 0
    markup_pp = exp[11] or 0
    total = round(price_pp * quote.pax, 2)
    cost_total = round(cost_pp * quote.pax, 2)
    profit = round(markup_pp * quote.pax, 2)
    token = secrets.token_urlsafe(9)
    created_at = datetime.now().isoformat()

    c.execute("""INSERT INTO experience_bookings
                 (token, guest_name, guest_phone, experience_id, category, operator,
                  title, pax, price_eur, commission_pct, commission_eur, status,
                  created_at, cost_total_eur, profit_eur)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (token, quote.guest_name, quote.guest_phone, exp[0], exp[1], exp[2],
               exp[3], quote.pax, total, 0, profit, "quoted", created_at,
               cost_total, profit))
    conn.commit()
    conn.close()

    link = f"{PUBLIC_BASE_URL}/book/{token}"
    template = QUOTE_TEMPLATES.get(quote.language, QUOTE_TEMPLATES["en"])
    whatsapp_message = template.format(
        name=quote.guest_name, title=exp[3], pax=quote.pax,
        price_pp=price_pp, total=total, link=link,
    )

    return {
        "token": token,
        "guest": quote.guest_name,
        "title": exp[3],
        "operator": exp[1],
        "pax": quote.pax,
        "guest_pays_eur": total,
        "your_cost_eur": cost_total,
        "your_profit_eur": profit,
        "status": "quoted",
        "booking_link": link,
        "whatsapp_message": whatsapp_message,
    }


@app.get("/book/{token}", response_class=HTMLResponse)
def guest_booking_page(token: str):
    """Guest-facing booking page opened from the WhatsApp link."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT * FROM experience_bookings WHERE token = ?", (token,))
    b = c.fetchone()
    conn.close()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    guest, title, operator, pax, total, status = b[2], b[7], b[6], b[8], b[9], b[12]
    confirmed = status in ("confirmed", "paid")
    cta = (
        '<p style="color:#16794a;font-weight:600">✓ Your spot is confirmed. See you soon!</p>'
        if confirmed else
        f'<button onclick="fetch(\'/book/{token}/confirm\',{{method:\'POST\'}})'
        f'.then(()=>location.reload())" '
        'style="background:#e8590c;color:#fff;border:0;padding:14px 28px;'
        'border-radius:10px;font-size:17px;cursor:pointer">Confirm my booking</button>'
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="font-family:system-ui,sans-serif;max-width:420px;margin:40px auto;padding:0 20px">
  <h2>Hi {guest} 👋</h2>
  <div style="border:1px solid #eee;border-radius:14px;padding:20px">
    <h3 style="margin:0 0 4px">{title}</h3>
    <p style="color:#666;margin:0 0 16px">{operator}</p>
    <p>Guests: <b>{pax}</b></p>
    <p style="font-size:22px">Total: <b>{total:.0f}€</b></p>
    {cta}
  </div>
  <p style="color:#999;font-size:13px;margin-top:24px">Cappadocia Hotel · booked with care</p>
</body></html>"""


@app.post("/book/{token}/confirm")
def confirm_booking(token: str):
    """Guest confirms — your markup profit is now booked (collect at the hotel)."""
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("SELECT status, profit_eur FROM experience_bookings WHERE token = ?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")
    if row[0] in ("confirmed", "paid"):
        conn.close()
        return {"token": token, "status": row[0], "message": "Already confirmed"}

    confirmed_at = datetime.now().isoformat()
    c.execute("""UPDATE experience_bookings
                 SET status = 'confirmed', confirmed_at = ? WHERE token = ?""",
              (confirmed_at, token))
    conn.commit()
    conn.close()
    return {"token": token, "status": "confirmed",
            "your_profit_eur": row[1], "confirmed_at": confirmed_at}


@app.get("/profit")
def profit_summary():
    """
    Your money dashboard: markup profit earned and still pending, plus the
    total the guests pay and your cost, broken down by status and category.
    """
    conn = sqlite3.connect("cappadocia_ops.db")
    c = conn.cursor()
    c.execute("""SELECT status, COUNT(*), COALESCE(SUM(profit_eur), 0),
                        COALESCE(SUM(price_eur), 0), COALESCE(SUM(cost_total_eur), 0)
                 FROM experience_bookings GROUP BY status""")
    by_status = {r[0]: {"bookings": r[1], "profit_eur": round(r[2], 2),
                        "guest_pays_eur": round(r[3], 2), "cost_eur": round(r[4], 2)}
                 for r in c.fetchall()}
    c.execute("""SELECT category, COUNT(*), COALESCE(SUM(profit_eur), 0)
                 FROM experience_bookings
                 WHERE status IN ('confirmed', 'paid')
                 GROUP BY category ORDER BY 3 DESC""")
    by_category = [{"category": r[0], "bookings": r[1], "profit_eur": round(r[2], 2)}
                   for r in c.fetchall()]
    earned = sum(v["profit_eur"] for k, v in by_status.items() if k in ("confirmed", "paid"))
    pending = by_status.get("quoted", {}).get("profit_eur", 0)
    conn.close()
    return {
        "profit_earned_eur": round(earned, 2),
        "profit_pending_in_quotes_eur": round(pending, 2),
        "by_status": by_status,
        "by_category": by_category,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
