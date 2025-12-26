from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse

app = FastAPI()

# --- ⚙️ CONFIGURATION: THE DATABASE ---
CLIENTS = {
    # --- أضف هذا إلى قائمة CLIENTS في ملف main.py ---
    "masra": {
        "name_en": "Masra Tea",
        "name_ar": "شاي مسرى",
        "phone": "966553144059", 
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJJd-3LBvpST4RWO6uzJyTpVQ"
    },
    "unico": {
        "name_en": "Unico Cafe",
        "name_ar": "اونيكو كافيه",
        "phone": "966580996680", 
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJ1fUVjUrpST4RJOfdZ6qTqTs"
    },
    "effect": {
        "name_en": "Effect Coffee",
        "name_ar": "ايفيكت كوفي",
        "phone": "966502443461", 
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJTSi3q9nnST4RsFE7lnuMp28"
    },
    "lagioia": {
        "name_en": "La Gioia",
        "name_ar": "مطعم لاجويا",
        "phone": "966539979957", 
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJiUENOXjpST4R07Il0f6NCPI" 
    },
    "thirdplace": {
        "name_en": "The 3rd Place",
        "name_ar": "ذا ثيرد بليس",
        "phone": "966550461742", # ⚠️ ضع رقم جوالهم هنا إذا كان لديك، أو رقمك مؤقتاً
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJWX9dW_vpST4RD4-byDMcoVQ" # ل وضعه هنا
    }
}

HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rate Us</title>
<style>
body { font-family: system-ui, -apple-system, sans-serif; background: #f4f6f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; user-select: none; -webkit-user-select: none; }
.card { background: white; padding: 35px 28px; border-radius: 24px; box-shadow: 0 15px 35px rgba(0,0,0,0.08); max-width: 400px; width: 85%; text-align: center; }
h1 { font-size: 22px; margin-bottom: 8px; color: #1a1a1a; }
p { color: #666; margin-bottom: 25px; font-size: 16px; }
.lang-toggle { position: absolute; top: 25px; right: 25px; cursor: pointer; font-weight: 700; font-size: 14px; color: #555; background: #fff; padding: 8px 16px; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.stars { display: flex; justify-content: center; gap: 8px; direction: ltr; }
.star { font-size: 46px; color: #e0e0e0; cursor: pointer; transition: color 0.15s ease, transform 0.1s; -webkit-tap-highlight-color: transparent; }
.star.gold { color: #FFD700; transform: scale(1.1); }
textarea { width: 100%; padding: 16px; border-radius: 16px; border: 1px solid #eee; background: #f9f9f9; resize: none; font-size: 16px; box-sizing: border-box; outline: none; font-family: inherit; }
textarea:focus { border-color: #000; background: #fff; }
button { margin-top: 18px; width: 100%; padding: 16px; border: none; border-radius: 16px; background: #25D366; color: white; font-size: 17px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); }
</style>
</head>
<body>
<div class="lang-toggle" onclick="toggleLang()">AR / EN</div>
<div class="card" id="app" data-lang="en">
{content}
</div>
<script>
function toggleLang() {
    const app = document.getElementById('app');
    const newLang = app.getAttribute('data-lang') === 'en' ? 'ar' : 'en';
    app.setAttribute('data-lang', newLang);
    document.documentElement.lang = newLang;
    document.dir = newLang === 'en' ? 'ltr' : 'rtl';
    updateText();
}
function updateText() {
    const lang = document.getElementById('app').getAttribute('data-lang');
    document.querySelectorAll('[data-en]').forEach(el => {
        el.innerText = el.getAttribute(lang === 'en' ? 'data-en' : 'data-ar');
    });
}
updateText();
</script>
</body>
</html>
"""

# --- 1. DYNAMIC ROUTING WITH LOGGING ---
@app.get("/{client_id}", response_class=HTMLResponse)
async def rate_page(client_id: str, request: Request):
    # --- LOGGING START ---
    # This prints to the Render System Log
    user_agent = request.headers.get('user-agent', 'Unknown')
    ip = request.client.host if request.client else "Unknown"
    print(f"🔔 NEW SCAN: {client_id.upper()} | IP: {ip} | Device: {user_agent}")
    # --- LOGGING END ---

    # Check if this restaurant exists in our list
    client = CLIENTS.get(client_id)
    if not client:
        return HTMLResponse("<h1>Error: Restaurant Not Found</h1>", status_code=404)

    content = f"""
    <h1 data-en="How was {client['name_en']}?" data-ar="كيف كانت تجربتك في {client['name_ar']}؟"></h1>
    <p data-en="Tap to rate" data-ar="اضغط للتقييم"></p>

    <form action="/process" method="post" id="ratingForm">
        <input type="hidden" name="client_id" value="{client_id}">
        <input type="hidden" name="stars" id="starsInput">
        <div class="stars" id="starContainer">
            <span class="star" id="s1" onclick="submitRate(1)" onmouseenter="hoverStar(1)">★</span>
            <span class="star" id="s2" onclick="submitRate(2)" onmouseenter="hoverStar(2)">★</span>
            <span class="star" id="s3" onclick="submitRate(3)" onmouseenter="hoverStar(3)">★</span>
            <span class="star" id="s4" onclick="submitRate(4)" onmouseenter="hoverStar(4)">★</span>
            <span class="star" id="s5" onclick="submitRate(5)" onmouseenter="hoverStar(5)">★</span>
        </div>
    </form>

    <script>
    const container = document.getElementById('starContainer');
    container.addEventListener('mouseleave', () => {{ resetStars(); }});
    function hoverStar(v) {{ fillStars(v); }}
    function resetStars() {{ for (let i=1; i<=5; i++) document.getElementById('s'+i).classList.remove('gold'); }}
    function fillStars(v) {{ resetStars(); for (let i=1; i<=v; i++) document.getElementById('s'+i).classList.add('gold'); }}
    function submitRate(v) {{
        fillStars(v);
        document.getElementById('starsInput').value = v;
        setTimeout(() => {{ document.getElementById('ratingForm').submit(); }}, 300);
    }}
    </script>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

@app.post("/process")
def process_rating(client_id: str = Form(...), stars: int = Form(...)):
    client = CLIENTS.get(client_id)
    if stars >= 4:
        # Redirect to THEIR specific Google Map
        return RedirectResponse(client['google_link'], status_code=303)
    # Redirect to feedback page (keeping the client_id)
    return RedirectResponse(f"/{client_id}/feedback", status_code=303)

@app.get("/{client_id}/feedback", response_class=HTMLResponse)
def feedback_page(client_id: str):
    content = f"""
    <h1 data-en="We are sorry 😞" data-ar="نأسف لسماع ذلك 😞"></h1>
    <p data-en="Tell the manager directly" data-ar="أخبر المدير مباشرة"></p>
    <form action="/submit" method="post">
        <input type="hidden" name="client_id" value="{client_id}">
        <textarea name="complaint" rows="5" placeholder="..."></textarea>
        <button data-en="Continue to Chat ➜" data-ar="المتابعة للمحادثة ➜"></button>
    </form>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))

# --- 🔥 FIX IS HERE: Made complaint optional with default="" ---
@app.post("/submit")
def submit_feedback(client_id: str = Form(...), complaint: str = Form(default="")):
    client = CLIENTS.get(client_id)
    
    formatted_text = f"🚨 *{client['name_en']} Feedback*\n\n{complaint}"
    encoded_text = urllib.parse.quote(formatted_text)
    
    # Send to the specific phone number for this client
    whatsapp_link = f"https://wa.me/{client['phone']}?text={encoded_text}"
    
    return RedirectResponse(whatsapp_link, status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



