from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse

app = FastAPI()

# --- ⚙️ CONFIGURATION: THE DATABASE ---
# Add "prize": "Description" to any client you want to offer a reward.
# If "prize": None, it behaves normally (Direct Google Link).

CLIENTS = {
    "masra": {
        "name_en": "Masra Tea",
        "name_ar": "شاي مسرى",
        "phone": "966553144059",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJJd-3LBvpST4RWO6uzJyTpVQ",
        "prize": None  # Normal Mode
    },
    "unico": {
        "name_en": "Unico Cafe",
        "name_ar": "اونيكو كافيه",
        "phone": "966580996680",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJ1fUVjUrpST4RJOfdZ6qTqTs",
        "prize": None  # Normal Mode
    },
    "effect": {
        "name_en": "Effect Coffee",
        "name_ar": "ايفيكت كوفي",
        "phone": "966502443461",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJTSi3q9nnST4RsFE7lnuMp28",
        "prize": None
    },
    "thirdplace": {
        "name_en": "The 3rd Place",
        "name_ar": "ذا ثيرد بليس",
        "phone": "966550461742",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJWX9dW_vpST4RD4-byDMcoVQ",
        "prize": None
    },
    "owl": {
        "name_en": "Owl Bakehouse",
        "name_ar": "آول بيك هاوس",
        "phone": "966500000000", # ⚠️ Update Phone
       "google_link": "https://search.google.com/local/writereview?placeid=ChIJ1fUVjUrpST4RJOfdZ6qTqTs", # ⚠️ Update Link
        "prize": "Free Cookie 🍪"  # ✅ PRIZE MODE ACTIVE
    }
}

# --- HTML TEMPLATES ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feedback</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; background: #f4f6f8; margin: 0; display: flex; justify-content: center; min-height: 100vh; }}
.card {{ background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 90%; max-width: 400px; text-align: center; margin-top: 5vh; height: fit-content; }}
h1 {{ color: #333; font-size: 22px; }}
p {{ color: #666; }}
.stars {{ display: flex; justify-content: center; gap: 5px; direction: ltr; margin: 20px 0; }}
.star {{ font-size: 45px; color: #ddd; cursor: pointer; transition: 0.2s; }}
.star.gold {{ color: #ffc107; transform: scale(1.1); }}
textarea {{ width: 100%; padding: 15px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 15px; font-family: inherit; box-sizing: border-box; }}
button {{ background: #25D366; color: white; border: none; padding: 15px; width: 100%; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; }}
.prize-box {{ border: 2px dashed #ff9800; background: #fff8e1; padding: 20px; border-radius: 15px; margin-top: 20px; }}
.redeemed {{ opacity: 0.6; filter: grayscale(1); border: 2px solid #ccc; background: #eee; }}
.hidden {{ display: none; }}
</style>
</head>
<body>
<div class="card">
{content}
</div>
</body>
</html>
"""

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
def home_page():
    return HTMLResponse("<h1>System Online ✅</h1><p>Ready to scan.</p>")

# 1. THE RATING PAGE
@app.api_route("/{client_id}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def rate_page(client_id: str, request: Request):
    client = CLIENTS.get(client_id)
    if not client:
        return HTMLResponse("<h1>Error: Client Not Found</h1>", status_code=404)

    content = f"""
    <h1>How was {client['name_en']}?</h1>
    <p>Tap a star to rate us</p>
    <form action="/process" method="post" id="ratingForm">
        <input type="hidden" name="client_id" value="{client_id}">
        <input type="hidden" name="stars" id="starsInput">
        <div class="stars">
            <span class="star" onclick="rate(1)">★</span>
            <span class="star" onclick="rate(2)">★</span>
            <span class="star" onclick="rate(3)">★</span>
            <span class="star" onclick="rate(4)">★</span>
            <span class="star" onclick="rate(5)">★</span>
        </div>
    </form>
    <script>
    function rate(n) {{
        document.querySelectorAll('.star').forEach((s, i) => {{
            s.classList.toggle('gold', i < n);
        }});
        document.getElementById('starsInput').value = n;
        setTimeout(() => document.getElementById('ratingForm').submit(), 300);
    }}
    </script>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 2. LOGIC PROCESSOR
@app.post("/process")
def process_rating(client_id: str = Form(...), stars: int = Form(...)):
    client = CLIENTS.get(client_id)
    
    # CASE A: GOOD RATING (4-5 Stars)
    if stars >= 4:
        # Check if they have a PRIZE system active
        if client.get("prize"):
            return RedirectResponse(f"/{client_id}/prize", status_code=303)
        else:
            # No prize, just send to Google Maps
            return RedirectResponse(client['google_link'], status_code=303)
            
    # CASE B: BAD RATING (1-3 Stars) -> FEEDBACK
    return RedirectResponse(f"/{client_id}/feedback", status_code=303)

# 3. WINNER / PRIZE PAGE (ANTI-FRAUD)
@app.get("/{client_id}/prize", response_class=HTMLResponse)
def prize_page(client_id: str):
    client = CLIENTS.get(client_id)
    
    prize_name = client.get("prize", "Surprise Gift")
    
    content = f"""
    <div id="activeTicket">
        <h1 style="color: #ff9800;">🎉 CONGRATULATIONS!</h1>
        <p>You rated us 5 stars!</p>
        
        <div class="prize-box">
            <h2>YOU WON:</h2>
            <h1 style="margin: 10px 0; font-size: 30px;">{prize_name}</h1>
            <p style="font-size: 12px; color: #888;">Valid on your NEXT visit with any purchase.</p>
        </div>

        <br>
        <p><strong>Step 1:</strong> Save this screen.</p>
        <a href="{client['google_link']}" target="_blank" style="display:block; text-decoration:none; margin-bottom: 10px;">
            <button style="background: #4285F4;">Review on Google Maps ➜</button>
        </a>
        
        <p><strong>Step 2:</strong> When you return, ask staff to tap below:</p>
        <button onclick="redeem()" style="background: #333;">🔘 Staff Redeem Button</button>
    </div>

    <div id="redeemedTicket" class="hidden prize-box redeemed">
        <h1>❌ REDEEMED</h1>
        <p>This coupon has already been used.</p>
        <p id="timeDate"></p>
    </div>

    <script>
        // Unique Key for this specific restaurant
        const storageKey = 'redeemed_{client_id}';

        // 1. Check if already used
        if (localStorage.getItem(storageKey) === 'true') {{
            showRedeemed();
        }}

        function redeem() {{
            if (confirm('STAFF CHECK: Are you sure you want to redeem this prize? It will disappear forever.')) {{
                localStorage.setItem(storageKey, 'true');
                localStorage.setItem(storageKey + '_time', new Date().toLocaleString());
                showRedeemed();
            }}
        }}

        function showRedeemed() {{
            document.getElementById('activeTicket').classList.add('hidden');
            document.getElementById('redeemedTicket').classList.remove('hidden');
            document.getElementById('timeDate').innerText = localStorage.getItem(storageKey + '_time');
        }}
    </script>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 4. FEEDBACK PAGE (BAD RATING)
@app.get("/{client_id}/feedback", response_class=HTMLResponse)
def feedback_page(client_id: str):
    content = f"""
    <h1>We are sorry 😔</h1>
    <p>Please tell the manager directly. This message goes to WhatsApp, not public.</p>
    <form action="/submit" method="post">
        <input type="hidden" name="client_id" value="{client_id}">
        <textarea name="complaint" rows="4" placeholder="What went wrong?"></textarea>
        <button>Send to Manager ➜</button>
    </form>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 5. WHATSAPP SENDER
@app.post("/submit")
def submit_feedback(client_id: str = Form(...), complaint: str = Form(default="")):
    client = CLIENTS.get(client_id)
    text = f"🚨 *New Feedback for {client['name_en']}*\n\n{complaint}"
    wa_link = f"https://wa.me/{client['phone']}?text={urllib.parse.quote(text)}"
    return RedirectResponse(wa_link, status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


