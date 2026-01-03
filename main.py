from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import uuid
import datetime
import re

app = FastAPI()
DB_NAME = "elite.db"

# --- 🎨 CSS STYLING (SAUDI EDITION 🇸🇦) ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <title>Customer Club</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: 'Tajawal', sans-serif; background:#f4f7f6; margin:0; display:flex; justify-content:center; min-height:100vh; padding: 20px; }
        .card { background:white; width:100%; max-width:400px; padding:30px; border-radius:24px; box-shadow:0 10px 30px rgba(0,0,0,0.05); text-align:center; height: fit-content; align-self: center; }
        h1 { margin:0 0 10px; font-size:24px; color:#333; font-weight: 900; }
        p { color:#666; line-height:1.6; margin-bottom:20px; font-size: 16px; }
        .btn { display:block; width:100%; padding:16px; border:none; border-radius:16px; font-size:18px; font-weight:bold; cursor:pointer; margin-top:10px; text-decoration:none; }
        .btn-primary { background:#25D366; color:white; }
        .btn-google { background:#4285F4; color:white; }
        .btn-staff { background:#333; color:white; opacity:0.8; font-size:14px; margin-top: 25px; }
        input, textarea { width:100%; padding:15px; border:2px solid #eee; border-radius:12px; font-size:16px; margin-bottom:15px; outline:none; font-family: 'Tajawal', sans-serif;}
        input:focus, textarea:focus { border-color:#25D366; }
        .stars { font-size:45px; color:#ddd; margin:20px 0; cursor:pointer; direction: ltr; }
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
        c.execute("""CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            name TEXT,
            google_link TEXT,
            prize TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            phone TEXT,
            client_id INTEGER,
            UNIQUE(phone, client_id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            rating INTEGER,
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS coupons (
            id TEXT PRIMARY KEY,
            customer_id INTEGER,
            reward TEXT,
            expires_at TEXT,
            redeemed_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            customer_id INTEGER,
            message TEXT,
            created_at TEXT
        )""")

# --- 🛠️ HELPER FUNCTIONS ---

def normalize_phone(phone: str) -> str:
    p = re.sub(r"\D", "", phone)
    return p

def get_or_create_customer(phone, client_id):
    with db() as c:
        row = c.execute("SELECT id FROM customers WHERE phone=? AND client_id=?", (phone, client_id)).fetchone()
        if row:
            return row["id"]
        # FIXED: Use cursor to get ID
        cursor = c.execute("INSERT INTO customers (phone, client_id) VALUES (?, ?)", (phone, client_id))
        return cursor.lastrowid

def issue_coupon(customer_id, reward):
    cid = str(uuid.uuid4())
    expires = (datetime.datetime.utcnow() + datetime.timedelta(days=14)).isoformat()
    with db() as c:
        c.execute("INSERT INTO coupons (id, customer_id, reward, expires_at) VALUES (?,?,?,?)", 
                  (cid, customer_id, reward, expires))
    return cid

# --- 🌐 ROUTES ---

@app.on_event("startup")
def startup():
    init_db()
    with db() as c:
        # ⚠️ UPDATE THESE WITH REAL LINKS BEFORE DEPLOYING
        c.execute("""INSERT OR IGNORE INTO clients (slug, name, google_link, prize) 
            VALUES ('owl', 'Owl Bakehouse', 'https://goo.gl/maps/PLACEHOLDER', 'كوكيز مجاناً 🍪')""")
        
        c.execute("""INSERT OR IGNORE INTO clients (slug, name, google_link, prize) 
            VALUES ('unico', 'Unico Cafe', 'https://goo.gl/maps/PLACEHOLDER', 'قهوة مجاناً ☕')""")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML_BASE.replace("{content}", "<h1>النظام يعمل بنجاح ✅</h1><p>جاهز لاستقبال العملاء.</p>"))

# 1. RATING PAGE
@app.get("/{slug}", response_class=HTMLResponse)
def rate_page(slug: str):
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (slug,)).fetchone()
    if not client: return HTMLResponse("المتجر غير موجود", 404)

    content = f"""
        <h1>{client['name']}</h1>
        <p>كيف كانت تجربتك معنا اليوم؟</p>
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
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

# 2. LOGIC SPLIT
@app.post("/rate")
def process_rate(client_slug: str = Form(...), stars: int = Form(...)):
    if stars >= 4:
        return RedirectResponse(f"/claim/{client_slug}/{stars}", 303)
    else:
        return RedirectResponse(f"/feedback/{client_slug}", 303)

# 3. CLAIM PAGE
@app.get("/claim/{slug}/{stars}", response_class=HTMLResponse)
def claim_page(slug: str, stars: int):
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (slug,)).fetchone()
    
    content = f"""
        <div style="font-size:50px">🎁</div>
        <h1>ألف مبروك!</h1>
        <p>لأنك قيمتنا {stars} نجوم، حصلت على:<br><strong>{client['prize']}</strong></p>
        <p>سجل رقم جوالك عشان تحفظ هديتك وتستخدمها المرة الجاية:</p>
        <form action="/complete" method="post">
            <input type="hidden" name="client_slug" value="{slug}">
            <input type="hidden" name="stars" value="{stars}">
            <input type="tel" name="phone" placeholder="05xxxxxxxx" required style="direction:ltr; text-align:right;">
            <button class="btn btn-primary">احفظ هديتي 🔓</button>
        </form>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

# 4. SAVE DATA
@app.post("/complete")
def complete(client_slug: str = Form(...), stars: int = Form(...), phone: str = Form(...)):
    phone = normalize_phone(phone)
    
    with db() as c:
        client = c.execute("SELECT * FROM clients WHERE slug=?", (client_slug,)).fetchone()
    
    cust_id = get_or_create_customer(phone, client['id'])
    with db() as c:
        c.execute("INSERT INTO visits (customer_id, rating, created_at) VALUES (?,?,?)", 
                  (cust_id, stars, datetime.datetime.utcnow().isoformat()))
    
    cid = issue_coupon(cust_id, client['prize'])
    return RedirectResponse(f"/coupon/{cid}", 303)

# 5. COUPON PAGE
@app.get("/coupon/{cid}", response_class=HTMLResponse)
def view_coupon(cid: str):
    with db() as c:
        row = c.execute("""
            SELECT coupons.*, clients.google_link 
            FROM coupons 
            JOIN customers ON coupons.customer_id = customers.id 
            JOIN clients ON customers.client_id = clients.id 
            WHERE coupons.id=?""", (cid,)).fetchone()
    
    if not row: return HTMLResponse("الكوبون غير صحيح")

    if row['redeemed_at']:
        content = f"""
            <h2 style="color:#aaa">❌ تم الاستخدام</h2>
            <p>تم استخدام هذا الكوبون بتاريخ:<br>{row['redeemed_at'][:10]}</p>
        """
        return HTMLResponse(HTML_BASE.replace("{content}", content))

    content = f"""
        <div style="font-size:50px">🎉</div>
        <h1>تستاهل!</h1>
        <div class="coupon-box">
            <h2>{row['reward']}</h2>
            <small>صالح لغاية: {row['expires_at'][:10]}</small>
        </div>
        
        <p><strong>الخطوة ١:</strong> ادعمنا بتقييمك في قوقل</p>
        <a href="{row['google_link']}" target="_blank" style="text-decoration:none">
            <button class="btn btn-google">كتابة تقييم في قوقل ➜</button>
        </a>
        
        <br>
        <p><strong>الخطوة ٢:</strong> عند زيارتك القادمة، ورّي الموظف هالشاشة:</p>
        <form action="/redeem" method="post" onsubmit="return confirm('تنبيه للموظف: هل أنت متأكد من خصم الكوبون؟')">
            <input type="hidden" name="cid" value="{cid}">
            <button class="btn btn-staff">🔘 زر الموظف (خصم الكوبون)</button>
        </form>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

# 6. REDEEM ACTION
@app.post("/redeem")
def redeem(cid: str = Form(...)):
    now = datetime.datetime.utcnow().isoformat()
    with db() as c:
        c.execute("UPDATE coupons SET redeemed_at=? WHERE id=?", (now, cid))
    return RedirectResponse(f"/coupon/{cid}", 303)

# 7. FEEDBACK PAGE
@app.get("/feedback/{slug}", response_class=HTMLResponse)
def feedback_page(slug: str):
    content = f"""
        <h1>حقك علينا 🙏</h1>
        <p>نعتذر منك إذا قصرنا بشي. يهمنا رأيك، وش اللي ضايقك اليوم؟</p>
        <form action="/feedback_submit" method="post">
            <input type="hidden" name="slug" value="{slug}">
            <textarea name="msg" placeholder="اكتب ملاحظاتك هنا..." required></textarea>
            <button class="btn btn-primary">ارسل للمدير مباشرة</button>
        </form>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

@app.post("/feedback_submit")
def save_feedback(slug: str = Form(...), msg: str = Form(...)):
    with db() as c:
        client = c.execute("SELECT id FROM clients WHERE slug=?", (slug,)).fetchone()
        c.execute("INSERT INTO feedback (client_id, message, created_at) VALUES (?,?,?)", 
                  (client['id'], msg, datetime.datetime.utcnow().isoformat()))
        
    return HTMLResponse(HTML_BASE.replace("{content}", "<h1>وصلت رسالتك ❤️</h1><p>شكراً لوقتك، بنتابع الموضوع ونتحسّن.</p>"))

# 8. 📊 MANAGER DASHBOARD (The Secret Admin Page)
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(key: str = ""):
    # 🔒 Password Protection (Simple)
    if key != "123": 
        return HTMLResponse("<h1 style='color:red; text-align:center; margin-top:50px;'>⛔ ممنوع الدخول (Access Denied)</h1>")

    with db() as c:
        customers = c.execute("SELECT * FROM customers").fetchall()
        coupons = c.execute("SELECT * FROM coupons").fetchall()
        feedback = c.execute("SELECT * FROM feedback").fetchall()

    def make_rows(rows, cols):
        html = ""
        for r in rows:
            html += "<tr>" + "".join(f"<td>{r[col]}</td>" for col in cols) + "</tr>"
        return html

    style = """
    <style>
        body { font-family: 'Tajawal', sans-serif; direction: rtl; padding: 20px; background: #f4f7f6; display: block !important; }
        h2 { color: #333; border-bottom: 2px solid #25D366; padding-bottom: 10px; margin-top: 40px; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }
        th { background: #333; color: white; padding: 12px; text-align: right; }
        td { padding: 12px; border-bottom: 1px solid #eee; color: #555; }
        tr:hover { background: #f9f9f9; }
        .stat-card { display: inline-block; background: white; padding: 20px; border-radius: 12px; margin-left: 15px; width: 150px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .stat-num { font-size: 30px; font-weight: bold; color: #25D366; display: block; }
    </style>
    """

    content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <title>لوحة المدير</title>
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
        {style}
    </head>
    <body>
        <h1 style="text-align:center">📊 لوحة التحكم (Manager Dashboard)</h1>
        
        <div style="text-align:center; margin-bottom: 30px;">
            <div class="stat-card">
                <span class="stat-num">{len(customers)}</span>
                عملاء
            </div>
            <div class="stat-card">
                <span class="stat-num">{len(coupons)}</span>
                كوبونات
            </div>
            <div class="stat-card">
                <span class="stat-num">{len(feedback)}</span>
                شكاوي
            </div>
        </div>

        <h2>👥 أرقام العملاء (VIP Database)</h2>
        <table>
            <thead><tr><th>ID</th><th>رقم الجوال</th><th>ID المتجر</th></tr></thead>
            <tbody>{make_rows(customers, ['id', 'phone', 'client_id'])}</tbody>
        </table>

        <h2>📩 الشكاوي (Feedback)</h2>
        <table>
            <thead><tr><th>الرسالة</th><th>التاريخ</th></tr></thead>
            <tbody>{make_rows(feedback, ['message', 'created_at'])}</tbody>
        </table>
        
        <h2>🎟️ الكوبونات المصدرة</h2>
        <table>
            <thead><tr><th>الهدية</th><th>تاريخ الانتهاء</th><th>تاريخ الاستخدام</th></tr></thead>
            <tbody>{make_rows(coupons, ['reward', 'expires_at', 'redeemed_at'])}</tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
