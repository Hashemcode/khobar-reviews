from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import uuid
import datetime
import re

app = FastAPI()
DB_NAME = "elite.db"

# --- 🎨 CSS STYLING (Looks like an App) ---
HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Club</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: -apple-system, system-ui, sans-serif; background:#f4f7f6; margin:0; display:flex; justify-content:center; min-height:100vh; padding: 20px; }
        .card { background:white; width:100%; max-width:400px; padding:30px; border-radius:24px; box-shadow:0 10px 30px rgba(0,0,0,0.05); text-align:center; height: fit-content; align-self: center; }
        h1 { margin:0 0 10px; font-size:22px; color:#333; }
        p { color:#666; line-height:1.5; margin-bottom:20px; }
        .btn { display:block; width:100%; padding:16px; border:none; border-radius:16px; font-size:16px; font-weight:bold; cursor:pointer; margin-top:10px; text-decoration:none; }
        .btn-primary { background:#25D366; color:white; }
        .btn-google { background:#4285F4; color:white; }
        .btn-staff { background:#333; color:white; opacity:0.8; font-size:14px; }
        input, textarea { width:100%; padding:15px; border:2px solid #eee; border-radius:12px; font-size:16px; margin-bottom:15px; outline:none; }
        input:focus, textarea:focus { border-color:#25D366; }
        .stars { font-size:45px; color:#ddd; margin:20px 0; cursor:pointer; }
        .gold { color:#FFD700; }
        .coupon-box { border:2px dashed #FF9F43; background:#FFFDF2; padding:20px; border-radius:15px; margin-bottom:20px; }
    </style>
</head>
<body>
<div class="card">
{content}
</div>
</body>
</html>
"""

# --- 🗄️ DATABASE ENGINE ---

def db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        # 1. CLIENTS (Restaurants)
        c.execute("""CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            name TEXT,
            google_link TEXT,
            prize TEXT
        )""")
        # 2. CUSTOMERS (Phone Numbers)
        c.execute("""CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            phone TEXT,
            client_id INTEGER,
            UNIQUE(phone, client_id)
        )""")
        # 3. VISITS (Ratings)
        c.execute("""CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            rating INTEGER,
            created_at TEXT
        )""")
        # 4. COUPONS (The Rewards)
        c.execute("""CREATE TABLE IF NOT EXISTS coupons (
            id TEXT PRIMARY KEY,
            customer_id INTEGER,
            reward TEXT,
            expires_at TEXT,
            redeemed_at TEXT
        )""")
        # 5. FEEDBACK (Bad Reviews)
        c.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            customer_id INTEGER,
            message TEXT,
            created_at TEXT
        )""")

# --- 🛠️ HELPER FUNCTIONS ---

def normalize_phone(phone: str) -> str:
    # Remove non-digits
    p = re.sub(r"\D", "", phone)
    return p

def get_or_create_customer(phone, client_id):
    with db() as c:
        row = c.execute("SELECT id FROM customers WHERE phone=? AND client_id=?", (phone, client_id)).fetchone()
        if row:
            return row["id"]
        c.execute("INSERT INTO customers (phone, client_id) VALUES (?, ?)", (phone, client_id))
        return c.lastrowid

def issue_coupon(customer_id, reward):
    cid = str(uuid.uuid4())
    # Coupon valid for 14 days
    expires = (datetime.datetime.utcnow() + datetime.timedelta(days=14)).isoformat()
    with db() as c:
        c.execute("INSERT INTO coupons (id, customer_id, reward, expires_at) VALUES (?,?,?,?)", 
                  (cid, customer_id, reward, expires))
    return cid

# --- 🌐 ROUTES ---

@app.on_event("startup")
def startup():
    init_db()
    # ✨ AUTO-BOOTSTRAP: Add your clients here so they exist in DB
    with db() as c:
        # Example 1: Owl
        c.execute("""INSERT OR IGNORE INTO clients (slug, name, google_link, prize) 
            VALUES ('owl', 'Owl Bakehouse', 'https://goo.gl/maps/YOUR_REAL_LINK_HERE', 'Free Cookie 🍪')""")
        # Example 2: Unico
        c.execute("""INSERT OR IGNORE INTO clients (slug, name, google_link, prize) 
            VALUES ('unico', 'Unico Cafe', 'https://goo.gl/maps/YOUR_REAL_LINK_HERE', 'Free Coffee ☕')""")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML_BASE.format(content="<h1>System Online 🟢</h1><p>Ready for customers.</p>"))

# 1. RATING PAGE
@app.get("/{slug}", response_class=HTMLResponse)
def rate_page(slug: str):
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (slug,)).fetchone()
    if not client: return HTMLResponse("Client not found", 404)

    return HTMLResponse(HTML_BASE.format(content=f"""
        <h1>{client['name']}</h1>
        <p>How was your experience?</p>
        <form action="/rate" method="post" id="rForm">
            <input type="hidden" name="client_slug" value="{slug}">
            <input type="hidden" name="stars" id="stars">
            <div class="stars">
                <span onclick="rate(1)">★</span>
                <span onclick="rate(2)">★</span>
                <span onclick="rate(3)">★</span>
                <span onclick="rate(4)">★</span>
                <span onclick="rate(5)">★</span>
            </div>
        </form>
        <script>
            function rate(n) {{
                document.querySelectorAll('span').forEach((s,i) => s.classList.toggle('gold', i<n));
                document.getElementById('stars').value = n;
                setTimeout(() => document.getElementById('rForm').submit(), 300);
            }}
        </script>
    """))

# 2. PROCESS RATING (Logic Split)
@app.post("/rate")
def process_rate(client_slug: str = Form(...), stars: int = Form(...)):
    if stars >= 4:
        # Good Rating -> Go to Phone Capture
        return RedirectResponse(f"/claim/{client_slug}/{stars}", 303)
    else:
        # Bad Rating -> Go to Feedback
        return RedirectResponse(f"/feedback/{client_slug}", 303)

# 3. CLAIM PAGE (Capture Phone)
@app.get("/claim/{slug}/{stars}", response_class=HTMLResponse)
def claim_page(slug: str, stars: int):
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (slug,)).fetchone()
    
    return HTMLResponse(HTML_BASE.format(content=f"""
        <div style="font-size:50px">🎁</div>
        <h1>You Won!</h1>
        <p>Because you rated us {stars} stars, you unlocked: <strong>{client['prize']}</strong></p>
        <p>Enter your mobile number to save your coupon:</p>
        <form action="/complete" method="post">
            <input type="hidden" name="client_slug" value="{slug}">
            <input type="hidden" name="stars" value="{stars}">
            <input type="tel" name="phone" placeholder="05xxxxxxxx" required>
            <button class="btn btn-primary">Unlock Prize 🔓</button>
        </form>
    """))

# 4. SAVE DATA & ISSUE COUPON
@app.post("/complete")
def complete(client_slug: str = Form(...), stars: int = Form(...), phone: str = Form(...)):
    phone = normalize_phone(phone)
    
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (client_slug,)).fetchone()
    
    # Save Customer & Visit
    cust_id = get_or_create_customer(phone, client['id'])
    with db() as c:
        c.execute("INSERT INTO visits (customer_id, rating, created_at) VALUES (?,?,?)", 
                  (cust_id, stars, datetime.datetime.utcnow().isoformat()))
    
    # Issue Coupon
    cid = issue_coupon(cust_id, client['prize'])
    return RedirectResponse(f"/coupon/{cid}", 303)

# 5. COUPON PAGE (With Google Link + Redeem)
@app.get("/coupon/{cid}", response_class=HTMLResponse)
def view_coupon(cid: str):
    with db() as c:
        # Join tables to get Client info for the Google Link
        row = c.execute("""
            SELECT coupons.*, clients.google_link 
            FROM coupons 
            JOIN customers ON coupons.customer_id = customers.id 
            JOIN clients ON customers.client_id = clients.id 
            WHERE coupons.id=?""", (cid,)).fetchone()
    
    if not row: return HTMLResponse("Invalid Coupon")

    if row['redeemed_at']:
        return HTMLResponse(HTML_BASE.format(content=f"""
            <h2 style="color:#aaa">❌ Redeemed</h2>
            <p>Used on: {row['redeemed_at'][:10]}</p>
        """))

    return HTMLResponse(HTML_BASE.format(content=f"""
        <div style="font-size:50px">🎉</div>
        <h1>Congratulations!</h1>
        <div class="coupon-box">
            <h2>{row['reward']}</h2>
            <small>Valid until: {row['expires_at'][:10]}</small>
        </div>
        
        <p><strong>Step 1:</strong> Support us on Google</p>
        <a href="{row['google_link']}" target="_blank" style="text-decoration:none">
            <button class="btn btn-google">Write Review ➜</button>
        </a>
        
        <br>
        <p><strong>Step 2:</strong> Show staff to redeem</p>
        <form action="/redeem" method="post" onsubmit="return confirm('Staff Only: Redeem now?')">
            <input type="hidden" name="cid" value="{cid}">
            <button class="btn btn-staff">🔘 Mark as Used</button>
        </form>
    """))

# 6. REDEEM ACTION
@app.post("/redeem")
def redeem(cid: str = Form(...)):
    now = datetime.datetime.utcnow().isoformat()
    with db() as c:
        c.execute("UPDATE coupons SET redeemed_at=? WHERE id=?", (now, cid))
    return RedirectResponse(f"/coupon/{cid}", 303)

# 7. FEEDBACK PAGE (Bad Rating)
@app.get("/feedback/{slug}", response_class=HTMLResponse)
def feedback_page(slug: str):
    return HTMLResponse(HTML_BASE.format(content=f"""
        <h1>We're Sorry 😔</h1>
        <p>Please tell us what went wrong so we can fix it.</p>
        <form action="/feedback_submit" method="post">
            <input type="hidden" name="slug" value="{slug}">
            <textarea name="msg" placeholder="Your feedback..." required></textarea>
            <button class="btn btn-primary">Send to Manager</button>
        </form>
    """))

@app.post("/feedback_submit")
def save_feedback(slug: str = Form(...), msg: str = Form(...)):
    # Here you would ideally look up client phone and send WhatsApp
    # For now, we just save to DB
    with db() as c:
        client = c.execute("SELECT id FROM clients WHERE slug=?", (slug,)).fetchone()
        c.execute("INSERT INTO feedback (client_id, message, created_at) VALUES (?,?,?)", 
                  (client['id'], msg, datetime.datetime.utcnow().isoformat()))
        
    return HTMLResponse(HTML_BASE.format(content="<h1>Thank You</h1><p>Your message has been sent.</p>"))
