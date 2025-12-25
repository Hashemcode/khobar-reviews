from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse

app = FastAPI()

# --- ⚙️ CONFIGURATION (EDIT THESE 2 LINES) ---
# 1. The Manager's Phone Number (Must start with country code, NO + sign)
OWNER_PHONE = "966537960319"

# 2. The Google Maps Review Link (Get this from the business Google Profile)
GOOGLE_MAPS_LINK = "https://search.google.com/local/writereview?placeid=ChIJ4RTT3cHpST4Rd9t20amBAFo"

# --- BUSINESS INFO ---
BUSINESS_NAME_EN = "Harat Ward Co."
BUSINESS_NAME_AR = "مطعم حاره ورد الخبر"

HTML_BASE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rate Us</title>
<style>
/* --- PREMIUM STYLES --- */
body {{
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f4f6f8;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    user-select: none;
    -webkit-user-select: none;
}}
.card {{
    background: white;
    padding: 35px 28px;
    border-radius: 24px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    max-width: 400px;
    width: 85%;
    text-align: center;
    transition: transform 0.2s;
}}
h1 {{ font-size: 22px; margin-bottom: 8px; color: #1a1a1a; }}
p {{ color: #666; margin-bottom: 25px; font-size: 16px; }}

/* Language Toggle */
.lang-toggle {{
    position: absolute;
    top: 25px;
    right: 25px;
    cursor: pointer;
    font-weight: 700;
    font-size: 14px;
    color: #555;
    background: #fff;
    padding: 8px 16px;
    border-radius: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}

/* Interactive Stars */
.stars {{ display: flex; justify-content: center; gap: 8px; direction: ltr; }}
.star {{
    font-size: 46px;
    color: #e0e0e0;
    cursor: pointer;
    transition: color 0.15s ease, transform 0.1s;
    -webkit-tap-highlight-color: transparent;
}}
.star.gold {{ color: #FFD700; transform: scale(1.1); }}

/* Inputs */
textarea {{
    width: 100%;
    padding: 16px;
    border-radius: 16px;
    border: 1px solid #eee;
    background: #f9f9f9;
    resize: none;
    font-size: 16px;
    box-sizing: border-box;
    outline: none;
    font-family: inherit;
}}
textarea:focus {{ border-color: #000; background: #fff; }}

/* The WhatsApp Button */
button {{
    margin-top: 18px;
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 16px;
    background: #25D366; /* WhatsApp Green */
    color: white;
    font-size: 17px;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
    transition: transform 0.1s;
}}
button:active {{ transform: scale(0.98); }}

</style>
</head>
<body>

<div class="lang-toggle" onclick="toggleLang()">AR / EN</div>

<div class="card" id="app" data-lang="en">
{{content}}
</div>

<script>
function toggleLang() {{
    const app = document.getElementById('app');
    const newLang = app.getAttribute('data-lang') === 'en' ? 'ar' : 'en';
    app.setAttribute('data-lang', newLang);
    document.documentElement.lang = newLang;
    document.dir = newLang === 'en' ? 'ltr' : 'rtl';
    updateText();
}}

function updateText() {{
    const lang = document.getElementById('app').getAttribute('data-lang');
    document.querySelectorAll('[data-en]').forEach(el => {{
        el.innerText = el.getAttribute(lang === 'en' ? 'data-en' : 'data-ar');
    }});
}}
updateText();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def rate_page():
    content = f"""
    <h1 data-en="How was {BUSINESS_NAME_EN}?" data-ar="كيف كانت تجربتك في {BUSINESS_NAME_AR}?"></h1>
    <p data-en="Tap to rate" data-ar="اضغط للتقييم"></p>

    <form action="/process" method="post" id="ratingForm">
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
def process_rating(stars: int = Form(...)):
    if stars >= 4:
        return RedirectResponse(GOOGLE_MAPS_LINK, status_code=303)
    return RedirectResponse("/feedback", status_code=303)


@app.get("/feedback", response_class=HTMLResponse)
def feedback_page():
    content = """
    <h1 data-en="We are sorry 😞" data-ar="نأسف لسماع ذلك 😞"></h1>
    <p data-en="Please tell the manager directly" data-ar="يرجى إخبار المدير مباشرة"></p>

    <form action="/submit" method="post">
        <textarea name="complaint" rows="5" placeholder="..."></textarea>
        <button data-en="Continue to Chat ➜" data-ar="المتابعة للمحادثة ➜"></button>
    </form>
    """
    return HTMLResponse(HTML_BASE.replace("{content}", content))


@app.post("/submit")
def submit_feedback(complaint: str = Form(...)):
    # 1. Format the message for WhatsApp
    formatted_text = f"🚨 *Customer Feedback*\n\n{complaint}"

    # 2. Encode it for the URL (spaces become %20, etc.)
    encoded_text = urllib.parse.quote(formatted_text)

    # 3. Create the direct link
    whatsapp_link = f"https://wa.me/{OWNER_PHONE}?text={encoded_text}"

    # 4. Redirect the user to WhatsApp
    return RedirectResponse(whatsapp_link, status_code=303)


if __name__ == "__main__":
    import uvicorn


    uvicorn.run(app, host="0.0.0.0", port=8000)
