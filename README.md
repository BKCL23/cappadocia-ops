# CappadociaOps

Operations platform for dynamic-experience tourism. Built by a hotel owner in Cappadocia, Turkey.

## The Problem

Cappadocia has 500+ hotels and 200+ agencies. Every morning, hot-air balloon prices change based on:
- Wind conditions (flights cancelled = price spikes next day)
- Operator availability
- Seasonal demand

Current workflow: Google Calendar + WhatsApp + Excel. 3-4 hours of manual updates daily. Wrong prices quoted = angry guests = bad reviews.

## What It Does

| Feature | Status |
|---------|--------|
| Unified booking calendar (Booking.com, Airbnb, Expedia) | 🚧 In Progress |
| Auto WhatsApp price updates to guests | ✅ Working |
| Auto review responses (5 languages) | ✅ Working |
| Multi-property agency dashboard | 📋 Planned |
| Operator inventory & commission tracking | 📋 Planned |

## Live Usage

- Dogfooding at: My own Cappadocia hotel (20 rooms, 80+ guests/week in peak season)
- Beta waitlist: 3 neighboring hotels, 2 local agencies
- Messages sent: 200+ automated WhatsApp updates daily

## Tech Stack

- Python 3.11
- FastAPI (backend)
- SQLite (database, upgrading to PostgreSQL)
- WhatsApp Business API
- OpenAI/Claude API (multilingual auto-reviews)

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Server runs at `http://localhost:8000`

## API Endpoints

### Bookings
- `GET /bookings` — List all bookings
- `POST /bookings` — Create new booking from OTA

### Balloon Prices
- `GET /balloon-prices/{date}` — Get prices for a specific date
- `POST /balloon-prices` — Update operator prices (called 5 AM daily)

### Messages
- `GET /messages` — View sent WhatsApp messages
- `POST /messages/send` — Send price update to guest

### Reviews
- `POST /reviews/auto-respond` — Generate multilingual review response

### Commission Bookings 💶
Turn the balloon/tour prices you already quote every morning into commission
income instead of a €0 referral to someone else.
- `POST /experiences` — Register a bookable experience + the commission you earn (e.g. 20%)
- `GET /experiences` — List bookable experiences (shows your €/booking)
- `POST /quotes` — Create a per-guest quote → returns a one-tap booking link + ready-to-send WhatsApp message (5 languages)
- `GET /book/{token}` — Guest-facing booking page (opened from the link)
- `POST /book/{token}/confirm` — Guest confirms → commission earned
- `GET /commissions` — Earnings dashboard (earned vs. pending, by category)

## Roadmap

### Phase 1: Single Property (Current)
- [x] Basic booking import
- [x] Balloon price tracking
- [x] WhatsApp message templates
- [ ] Claude API integration for auto-reviews

### Phase 2: Multi-Property Beta (Month 2-3)
- [ ] Agency dashboard (manage 5-20 properties)
- [ ] Two-way OTA sync
- [ ] Operator commission tracking

### Phase 3: Dynamic Pricing Engine (Month 4-5)
- [ ] Scrape operator websites for live pricing
- [ ] Weather API integration for cancellation predictions
- [ ] Demand-based price suggestions

### Phase 4: Expand (Month 6+)
- [ ] Antalya (boat tours)
- [ ] Safari markets (Kenya, Tanzania)
- [ ] Northern Lights (Iceland, Norway)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start server with auto-reload
uvicorn main:app --reload
```

## License

MIT
