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
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
import os

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
