"""
ZEUSVision + Investleey LinkedIn Auto-Poster
Posts AI forecast updates to LinkedIn Company Pages
"""
import os, requests, random, json, webbrowser
from datetime import datetime, timezone

def get_signal(data, interval="1h"):
    """
    New signal logic:
    - 1h and above: MA7 + MA3 (first vs 5th value, both must agree)
    - 15m and below: VWAP200/Pink (first vs 5th value)
    """
    short_intervals = ["1m", "5m", "15m"]
    is_short = interval in short_intervals
    last_close = data.get("last_close", 0)

    if is_short:
        # 15m and below: use forecast_vwap200 (Pink VWAP-200)
        fv200 = data.get("forecast_vwap200", [])
        if fv200 and len(fv200) >= 5:
            first = fv200[0]
            fifth = fv200[4]
            threshold = (last_close or first) * 0.0005
            if abs(fifth - first) <= threshold:
                return "NEUTRAL", "⚪", "●"
            elif first < fifth:
                return "BULLISH", "🟢", "📈"
            else:
                return "BEARISH", "🔴", "📉"
    else:
        # 1h and above: MA7 AND MA3 must agree
        fma7 = data.get("forecast_ma7", [])
        fma3 = data.get("forecast_ma3", [])
        if fma7 and len(fma7) >= 5 and fma3 and len(fma3) >= 5:
            ma7_bull = fma7[0] < fma7[4]
            ma7_bear = fma7[0] > fma7[4]
            ma3_bull = fma3[0] < fma3[4]
            ma3_bear = fma3[0] > fma3[4]
            if ma7_bull and ma3_bull:
                return "BULLISH", "🟢", "📈"
            elif ma7_bear and ma3_bear:
                return "BEARISH", "🔴", "📉"
            else:
                return "NEUTRAL", "⚪", "●"
    return "NEUTRAL", "⚪", "●"



# ── CONFIG ────────────────────────────────────────────────
MODE = os.environ.get("POST_MODE", "stocks")
LI_PERSON_ID = os.environ.get("LI_PERSON_ID", "")  # Global - works across all modes

if MODE == "crypto":
    LI_CLIENT_ID     = os.environ["LI_CLIENT_ID_CRYPTO"]
    LI_CLIENT_SECRET = os.environ["LI_CLIENT_SECRET_CRYPTO"]
    LI_ACCESS_TOKEN  = os.environ["LI_ACCESS_TOKEN_CRYPTO"]
    LI_ORG_ID        = os.environ["LI_ORG_ID_CRYPTO"]
    API_URL          = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN        = "mycryptovision2025"
    SITE_URL         = "https://zeusvisions.com"
    WATCHLIST        = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
                        "DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
    WEIGHTS          = [4,3,3,2,2,1,1,1,1,1]
else:
    LI_CLIENT_ID     = os.environ["LI_CLIENT_ID_STOCKS"]
    LI_CLIENT_SECRET = os.environ["LI_CLIENT_SECRET_STOCKS"]
    LI_ACCESS_TOKEN  = os.environ["LI_ACCESS_TOKEN_STOCKS"]
    LI_ORG_ID        = os.environ["LI_ORG_ID_STOCKS"]
    API_URL          = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN        = "mystockvision2025"
    SITE_URL         = "https://investleey.com"
    WATCHLIST        = ["AAPL","MSFT","NVDA","TSLA","GOOGL",
                        "META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    WEIGHTS          = [3,3,3,3,2,2,2,2,1,1,1,1]

HEADERS = {
    "Authorization": f"Bearer {LI_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0"
}

# ── FETCH FORECAST ────────────────────────────────────────
def get_forecast(symbol):
    print(f"Fetching {symbol}...")
    try:
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1d"},
            headers={"x-api-token": API_TOKEN, "Content-Type": "application/json"},
            timeout=120)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Forecast error: {e}")
    return None

# ── FORMAT POST ───────────────────────────────────────────
def format_post(data, symbol, interval="1d"):
    last_close = data.get("last_close", 0)
    f_ma7      = data.get("forecast_ma7", [last_close]*60)
    acc_ma7    = data.get("accuracy_ma7", 0)
    acc_ma25   = data.get("accuracy_ma25", 0)

    ma7_1h     = f_ma7[0] if f_ma7 else last_close
    signal_name, signal_emoji, signal_arrow = get_signal(data, interval)
    is_bullish = signal_name == "BULLISH"
    signal     = f"{signal_name} {signal_arrow}"
    pct_7      = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target_7   = f_ma7[6] if len(f_ma7)>6 else last_close
    pct_sign   = "+" if pct_7 >= 0 else ""

    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
        tags = "#Crypto #Bitcoin #CryptoTrading #AITrading #BlockChain #Web3"
        cta = f"🚀 Try ZEUS-AI free at {SITE_URL} — 500+ crypto pairs, 15-day free trial"
    else:
        display = symbol
        tags = "#Stocks #Investing #WallStreet #StockMarket #Finance #AITrading"
        cta = f"🚀 Try ZEUS-AI free at {SITE_URL} — 500+ US stocks & ETFs, 15-day free trial"

    now = datetime.now(timezone.utc).strftime('%B %d, %Y')

    text = f"""⚡ ZEUS-AI Forecast Update — {display} | {now}

Our proprietary AI just analyzed {display} and here's what it sees:

📊 Current Price: ${last_close:,.2f}
🎯 Signal: {signal}
📈 7-Day Target: ${target_7:,.2f} ({pct_sign}{pct_7:.1f}%)
🤖 AI Accuracy: {acc_ma7:.1f}% (MA-7) | {acc_ma25:.1f}% (MA-25)

Our deep learning models are trained on millions of candlesticks to detect price patterns invisible to the human eye.

{cta}

{tags}"""

    return text

# ── UPLOAD IMAGE ──────────────────────────────────────────
def get_person_urn():
    """Get person URN from env or LinkedIn API"""
    if LI_PERSON_ID:
        print(f"Using person ID: {LI_PERSON_ID[:4]}*** (urn:li:person:{LI_PERSON_ID})")
        return f"urn:li:person:{LI_PERSON_ID}"
    # Fallback: try userinfo endpoint
    headers = {"Authorization": f"Bearer {LI_ACCESS_TOKEN}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    if r.status_code == 200:
        sub = r.json().get("sub", "")
        if sub: return f"urn:li:person:{sub}"
    return None

def upload_image_to_linkedin(image_path):
    """Upload image to LinkedIn using newer Images API"""
    person_urn = get_person_urn()
    if not person_urn:
        return None

    headers = {
        "Authorization": f"Bearer {LI_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Step 1: Register upload (v2 assets API - no versioning needed)
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    r1 = requests.post(register_url,
        headers={"Authorization": f"Bearer {LI_ACCESS_TOKEN}",
                 "Content-Type": "application/json",
                 "X-Restli-Protocol-Version": "2.0.0"},
        json=register_body)
    if r1.status_code not in [200, 201]:
        print(f"Image register failed: {r1.status_code} {r1.text[:200]}")
        return None

    value = r1.json().get("value", {})
    upload_url = value.get("uploadMechanism", {}).get(
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")
    asset = value.get("asset")

    if not upload_url or not asset:
        print(f"No upload URL or asset: {value}")
        return None

    # Step 2: Upload image bytes
    with open(image_path, "rb") as f:
        img_data = f.read()

    r2 = requests.put(upload_url, data=img_data,
        headers={"Authorization": f"Bearer {LI_ACCESS_TOKEN}",
                 "Content-Type": "image/png"})

    if r2.status_code in [200, 201]:
        print(f"Image uploaded! Asset: {asset}")
        return asset
    else:
        print(f"Image upload failed: {r2.status_code} {r2.text[:200]}")
        return None


def post_to_linkedin(text, image_path=None):
    person_urn = get_person_urn()
    if not person_urn:
        print("❌ Could not get person URN")
        return False
    print(f"Posting as: {person_urn}")

    headers = {
        "Authorization": f"Bearer {LI_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Try ugcPosts first
    if image_path:
        asset = upload_image_to_linkedin(image_path)
    else:
        asset = None

    # Build body for ugcPosts
    if asset:
        media = [{
            "status": "READY",
            "description": {"text": "ZEUS-AI Forecast"},
            "media": asset,
            "title": {"text": "AI Forecast"}
        }]
        share_category = "IMAGE"
    else:
        media = []
        share_category = "NONE"

    body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text[:3000]},
                "shareMediaCategory": share_category,
                "media": media
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    r = requests.post("https://api.linkedin.com/v2/ugcPosts",
        headers=headers, json=body)

    if r.status_code in [200, 201]:
        print(f"✅ Posted to LinkedIn!")
        return True

    print(f"ugcPosts failed {r.status_code}: {r.text[:200]}")

    # Fallback: try /v2/shares API
    share_body = {
        "content": {"contentEntities": [], "title": text[:200]},
        "distribution": {"linkedInDistributionTarget": {}},
        "owner": person_urn,
        "text": {"text": text[:3000]},
        "subject": "AI Forecast"
    }
    r2 = requests.post("https://api.linkedin.com/v2/shares",
        headers=headers, json=share_body)

    if r2.status_code in [200, 201]:
        print(f"✅ Posted via shares API!")
        return True

    print(f"shares API also failed {r2.status_code}: {r2.text[:200]}")
    return False


def take_screenshot(symbol):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # LinkedIn optimal image size: 1200x627
            page = browser.new_page(viewport={"width": 1200, "height": 627})
            page.goto(SITE_URL, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            # Hide non-chart elements for clean look
            page.evaluate("""() => {
                const hide = [
                    '.ob-panel', '.right-panel', '#bottom-section',
                    '.ticker-bar', '.topbar', '.pair-header',
                    '.trades-panel', '#crypto-market-overview',
                    '#faq-section', '.bottom-bar', '#signup-popup',
                    '.chart-signup-banner', '#chart-signup-banner',
                    '.pricing-modal', '.modal-overlay'
                ];
                hide.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.style.display='none');
                });
                // Make chart fill the screen
                const layout = document.querySelector('.main-layout');
                if(layout) layout.style.gridTemplateColumns = '1fr';
                const chart = document.querySelector('.chart-area');
                if(chart) { chart.style.height = '550px'; chart.style.minHeight = '550px'; }
                const panel = document.querySelector('.chart-panel');
                if(panel) panel.style.height = '627px';
            }""")
            inp = page.query_selector('#pair-input')
            if inp:
                inp.fill('')
                inp.type(symbol)
            btn = page.query_selector('.run-btn')
            if btn:
                btn.click()
            try:
                page.wait_for_function(
                    "() => { const o = document.getElementById('chart-overlay'); return o && o.classList.contains('hidden'); }",
                    timeout=60000
                )
            except: pass
            page.wait_for_timeout(4000)
            path = '/tmp/li_chart.png'
            page.screenshot(path=path, clip={"x": 0, "y": 0, "width": 1200, "height": 627})
            browser.close()
            print(f"Screenshot saved!")
            return path
    except Exception as e:
        print(f"Screenshot error: {e}")
    return None


def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")

    data = get_forecast(symbol)
    if not data:
        backup = "BTCUSDT" if MODE == "crypto" else "AAPL"
        data = get_forecast(backup)
        symbol = backup
    if not data:
        print("No data")
        return

    text = format_post(data, symbol, interval="1d")
    print(f"Post preview:\n{text[:150]}...")

    image_path = take_screenshot(symbol)
    post_to_linkedin(text, image_path)

if __name__ == "__main__":
    main()
