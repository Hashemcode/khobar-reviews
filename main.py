from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse

app = FastAPI()

# --- ⚙️ CLIENT CONFIGURATION ---
CLIENTS = {
    "masra": {
        "name_en": "Masra Tea",
        "name_ar": "شاي مسرى",
        "phone": "966553144059",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJJd-3LBvpST4RWO6uzJyTpVQ",
        "prize": None
    },
    "unico": {
        "name_en": "Unico Cafe",
        "name_ar": "اونيكو كافيه",
        "phone": "966580996680",
        "google_link": "https://search.google.com/local/writereview?placeid=ChIJ1fUVjUrpST4RJOfdZ6qTqTs",
        "prize": None
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
        "phone": "966500000000",  # ⚠️ UPDATE THIS
        "google_link": "https://goo.gl/maps/PLACEHOLDER", # ⚠️ UPDATE THIS REAL LINK
        "prize": "Free Cookie 🍪"  # ✅ PRIZE ACTIVE
    }
}

# --- 🎨 SUPERIOR UI TEMPLATES ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
<title>Rate Experience</title>
<style>
    /* MODERN RESET */
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
        background-color: #f4f7f6; 
        margin: 0; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        min-height: 100vh;
        color: #333;
    }

    /* THE CARD */
    .card { 
        background: white; 
        width: 90%; 
        max-width: 400px; 
        border-radius: 24px; 
        padding: 40px 30px; 
        box-shadow: 0 20px 40px rgba(0,0,0,0.08); 
        text-align: center; 
        transition: transform 0.3s ease;
    }

    /* TYPOGRAPHY */
    h1 { margin: 0 0 10px; font-size: 24px; font-weight: 700; color: #111; letter-spacing: -0.5px; }
    p { margin: 0 0 25px; color: #666; font-size: 16px; line-height: 1.5; }

    /* STARS */
    .stars { display: flex; justify-content: center; gap: 8px; direction: ltr; margin-bottom: 30px; }
    .star { font-size: 48px; color: #e0e0e0; cursor: pointer; transition: transform 0.1s, color 0.2s; }
    .star.gold { color: #FFD700; transform: scale(1.1); }
    .star:active { transform: scale(0.9); }

    /* INPUTS */
    textarea { 
        width: 100%; 
        padding: 16px; 
        border: 2px solid #eee; 
        border-radius: 16px; 
        background: #fafafa; 
        font-size: 16px; 
        font-family: inherit; 
        outline: none; 
        resize: none; 
        transition: border-color 0.2s;
    }
    textarea:focus { border-color: #25D366; background: #fff; }

    /* BUTTONS */
    .btn { 
        display: block; 
        width: 100%; 
        padding: 18px; 
        border: none; 
        border-radius: 16px; 
        font-size: 17px; 
        font-weight: 700; 
        cursor: pointer; 
        margin-top: 15px; 
        transition: transform 0.1s, box-shadow 0.2s; 
        text-decoration: none;
    }
    .btn:active { transform: scale(0.98); }
    
    .btn-primary { background: #25D366; color: white; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); }
    .btn-google { background: #4285F4; color: white; box-shadow: 0 4px 15px rgba(66, 133, 244, 0.3); }
    .btn-staff { background: #333; color: white; margin-top: 30px; font-size: 14px; padding: 12px; opacity: 0.8; }
    .btn-reset { background: transparent; color: #aaa; font-size: 12px; margin-top: 20px; border: 1px solid #eee; padding: 8px; }

    /* PRIZE TICKET STYLES */
    .ticket-container {
        border: 3px dashed #FF9F43;
        background-color: #FFFDF2;
        border-radius: 18px;
        padding: 25px;
        margin-bottom: 25px;
        position: relative;
    }
    .prize-title { color: #FF9F43; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin-bottom: 5px; }
    .prize-item { color: #333; font-size: 28px; font-weight: 900; margin: 10px 0; }
    .prize-note { font-size: 13px; color: #888; margin-bottom: 0; }

    /* REDEEMED STATE */
    .redeemed { opacity: 0.5; filter: grayscale(100%); background: #eee; border-color: #ccc; }
    .hidden { display: none; }
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
    return HTMLResponse(HTML_BASE.format(content="<h1>System Online ✅</h1><p>Please scan a specific QR code.</p>"))

# 1. RATING INTERFACE
@app.api_route("/{client_id}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def rate_page(client_id: str, request: Request):
    client = CLIENTS.get(client_id)
    if not client:
        return HTMLResponse("<h1>Error: Client Not Found</h1>", status_code=404)

    content = f"""
    <h1>{client['name_en']}</h1>
    <p>How was your experience today?</p>
    
    <form action="/process" method="post" id="ratingForm">
        <input type="hidden" name="client_id" value="{client_id}">
        <input type="hidden" name="stars" id="starsInput">
        <div class="stars">
            <span class="star" id="s1" onclick="rate(1)">★</span>
            <span class="star" id="s2" onclick="rate(2)">★</span>
            <span class="star" id="s3" onclick="rate(3)">★</span>
            <span class="star" id="s4" onclick="rate(4)">★</span>
            <span class="star" id="s5" onclick="rate(5)">★</span>
        </div>
    </form>
    
    <script>
    function rate(n) {{
        // Visual Update
        for(let i=1; i<=5; i++) {{
            let star = document.getElementById('s'+i);
            if(i <= n) star.classList.add('gold');
            else star.classList.remove('gold');
        }}
        // Submit Logic
        document.getElementById('starsInput').value = n;
        setTimeout(() => {{
            document.getElementById('ratingForm').submit();
        }}, 350); 
    }}
    </script>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 2. LOGIC ROUTER
@app.post("/process")
def process_rating(client_id: str = Form(...), stars: int = Form(...)):
    client = CLIENTS.get(client_id)
    
    # 4 or 5 Stars -> Check for Prize or Google
    if stars >= 4:
        if client.get("prize"):
            return RedirectResponse(f"/{client_id}/prize", status_code=303)
        else:
            return RedirectResponse(client['google_link'], status_code=303)
            
    # 1, 2, 3 Stars -> Internal Feedback
    return RedirectResponse(f"/{client_id}/feedback", status_code=303)

# 3. PRIZE PAGE (The Winner)
@app.get("/{client_id}/prize", response_class=HTMLResponse)
def prize_page(client_id: str):
    client = CLIENTS.get(client_id)
    prize_name = client.get("prize", "Special Gift")
    
    content = f"""
    <div id="activeTicket">
        <div style="font-size: 50px; margin-bottom: 10px;">🎉</div>
        <h1>Congratulations!</h1>
        <p>You rated us 5 stars. As a thank you:</p>
        
        <div class="ticket-container">
            <div class="prize-title">You Won</div>
            <div class="prize-item">{prize_name}</div>
            <p class="prize-note">Valid on your <strong>next visit</strong> with any purchase.</p>
        </div>

        <a href="{client['google_link']}" target="_blank" style="text-decoration:none;">
            <button class="btn btn-google">Step 1: Write Review ➜</button>
        </a>
        
        <p style="margin-top:20px; font-size:14px;">Show this screen to cashier when claiming.</p>
        <button onclick="redeem()" class="btn btn-staff">🔘 Staff Redeem Button</button>
    </div>

    <div id="redeemedTicket" class="hidden">
        <div class="ticket-container redeemed">
            <div class="prize-title">REDEEMED</div>
            <div class="prize-item">{prize_name}</div>
            <p class="prize-note">This coupon has been used.</p>
        </div>
        <p>Redeemed on:<br><span id="timeDate" style="font-weight:bold;"></span></p>
        <button onclick="resetTest()" class="btn btn-reset">🔄 Reset (Dev Only)</button>
    </div>

    <script>
        const storageKey = 'redeemed_{client_id}';

        // Check Logic
        if (localStorage.getItem(storageKey) === 'true') {{
            showRedeemed();
        }}

        function redeem() {{
            if (confirm('STAFF: Redeem this prize now? It will disappear forever.')) {{
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

        function resetTest() {{
            if(confirm('Reset this coupon for testing?')) {{
                localStorage.removeItem(storageKey);
                location.reload();
            }}
        }}
    </script>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 4. FEEDBACK PAGE
@app.get("/{client_id}/feedback", response_class=HTMLResponse)
def feedback_page(client_id: str):
    client = CLIENTS.get(client_id)
    content = f"""
    <div style="font-size: 50px; margin-bottom: 10px;">👋</div>
    <h1>We appreciate your honesty</h1>
    <p>Please tell the manager directly so we can fix it.</p>
    
    <form action="/submit" method="post">
        <input type="hidden" name="client_id" value="{client_id}">
        <textarea name="complaint" rows="5" placeholder="What went wrong? (Service, Food, etc.)" required></textarea>
        <button class="btn btn-primary">Send to Manager ➜</button>
    </form>
    """
    return HTMLResponse(HTML_BASE.format(content=content))

# 5. SUBMIT TO WHATSAPP
@app.post("/submit")
def submit_feedback(client_id: str = Form(...), complaint: str = Form(default="")):
    client = CLIENTS.get(client_id)
    
    # Formatted Message
    text = f"🚨 *Feedback for {client['name_en']}*\n\n{complaint}"
    wa_link = f"https://wa.me/{client['phone']}?text={urllib.parse.quote(text)}"
    
    return RedirectResponse(wa_link, status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
