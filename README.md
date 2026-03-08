# Secure Shield Web — Purchase (College Project)

A simple e-commerce flow: **Login → Products → Cart → Checkout** with a SQLite database backend.

**Purpose:** Example model for a college security project — demonstrates **known** and **unknown** web attacks and how they are **fixed** or **mitigated**. See **[SECURITY.md](SECURITY.md)** for full documentation.

## How to run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server (serves both API and static files):
   ```bash
   python app.py
   ```

3. Open **http://localhost:5000** in your browser.

## Access from other PCs and phones

The server listens on all interfaces, so other devices on the **same Wi‑Fi network** can open the site:

1. Start the server: `python app.py`
2. In the terminal you’ll see something like:
   - **On same WiFi:  http://192.168.1.5:5000/**
3. On another PC or phone (connected to the same Wi‑Fi), open that link in the browser.

**If it doesn’t load:** allow Python through Windows Firewall when prompted, or add an inbound rule for port **5000** (TCP).

**From the internet (optional):** use a tunnel (e.g. [ngrok](https://ngrok.com)): run `ngrok http 5000` and open the HTTPS link ngrok gives you.

## Database

- **SQLite** database stored as `purchase.db` in the project folder.
- Tables: `users`, `products`, `sessions`, `orders`, `order_items`.
- Products are seeded automatically on first run.
- Users must **register** before logging in (no demo accounts).

## Flow

1. **Register / Login** (`index.html`) — Create an account or sign in.
2. **Products** (`products.html`) — Browse products from the database, add to cart.
3. **Cart** (`cart.html`) — Adjust quantities, remove items, go to checkout.
4. **Checkout** (`checkout.html`) — Enter shipping details, place order (saved to database).

## Tech

- **Backend:** Flask + SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Auth:** Session tokens, password hashing (Werkzeug)
- **Cart:** `localStorage` (client-side until checkout)
- **Orders:** Stored in database with user, items, and shipping info

## Security Dashboard (Owner)

The **first registered user** (or user with `ADMIN_EMAIL` env var) can access the **Security Dashboard** at `/dashboard.html`:

- **All attacks** (SQL injection, XSS) are detected, auto-fixed, and logged
- **Clear messages** for each event: attack type, fixed/blocked status
- **Attacker info**: name/email, IP address, location (via geolocation)
- **Owner-only**: Set `ADMIN_EMAIL=you@example.com` to designate a specific owner; otherwise user id 1 is owner

## Security (College Project)

This project demonstrates **known** and **unknown** web attacks and their mitigations:

- **SQL Injection** — Parameterized queries (live demo on login page)
- **XSS** — Output encoding, `textContent`, `escapeHtml()`
- **CSRF** — Bearer token auth (not cookies)
- **Passwords** — Werkzeug secure hashing
- **Unknown attacks** — Defense in depth (validation, encoding, least privilege)

See **[SECURITY.md](SECURITY.md)** for full documentation and report-ready explanations.

## Files

- `app.py` — Flask server and API routes
- `database.py` — SQLite schema and helpers
- `SECURITY.md` — **Attacks & mitigations** (college project documentation)
- `requirements.txt` — Python dependencies
- `index.html` — Login / Register
- `products.html` — Product catalog
- `cart.html` — Shopping cart
- `checkout.html` — Checkout
- `css/style.css` — Styles
- `js/app.js` — API client, auth, cart logic
