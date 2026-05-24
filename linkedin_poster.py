"""
ZEUSVision + Investleey LinkedIn Auto-Poster
Posts AI forecast updates to LinkedIn Company Pages
"""
import os, requests, random, json, webbrowser
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
MODE = os.environ.get("POST_MODE", "stocks")

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
def format_post(data, symbol):
    last_close = data.get("last_close", 0)
    f_ma7      = data.get("forecast_ma7", [last_close]*60)
    acc_ma7    = data.get("accuracy_ma7", 0)
    acc_ma25   = data.get("accuracy_ma25", 0)

    ma7_1h     = f_ma7[0] if f_ma7 else last_close
    is_bullish = ma7_1h > last_close
    signal     = "BULLISH 📈" if is_bullish else "BEARISH 📉"
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
def upload_image_to_linkedin(image_path):
    """Upload image to LinkedIn and return asset URN"""
    person_urn = get_person_urn() or f"urn:li:person:me"
    org_urn = person_urn

    # Step 1: Register upload
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": org_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    r = requests.post(register_url, headers=HEADERS, json=register_body)
    if r.status_code != 200:
        print(f"Register upload error: {r.text[:200]}")
        return None

    upload_data = r.json()
    upload_url  = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset       = upload_data["value"]["asset"]

    # Step 2: Upload the image
    with open(image_path, "rb") as img:
        upload_headers = {"Authorization": f"Bearer {LI_ACCESS_TOKEN}"}
        r2 = requests.put(upload_url, headers=upload_headers, data=img)

    if r2.status_code in [200, 201]:
        print(f"Image uploaded! Asset: {asset}")
        return asset
    print(f"Image upload failed: {r2.status_code}")
    return None

# ── POST TO LINKEDIN ──────────────────────────────────────
def get_person_urn():
    """Get the member URN from the access token"""
    headers = {"Authorization": f"Bearer {LI_ACCESS_TOKEN}"}
    
    # Try /v2/userinfo (OpenID Connect)
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    print(f"userinfo status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        sub = data.get("sub", "")
        if sub:
            return f"urn:li:person:{sub}"
    
    # Try /v2/me
    r2 = requests.get("https://api.linkedin.com/v2/me",
        headers={**headers, "X-Restli-Protocol-Version": "2.0.0"})
    print(f"me status: {r2.status_code}, body: {r2.text[:200]}")
    if r2.status_code == 200:
        pid = r2.json().get("id", "")
        if pid:
            return f"urn:li:person:{pid}"
    
    # Try /v2/me with linkedin_id field
    r3 = requests.get("https://api.linkedin.com/v2/me?projection=(id)",
        headers={**headers, "X-Restli-Protocol-Version": "2.0.0"})
    print(f"me projection status: {r3.status_code}, body: {r3.text[:200]}")
    if r3.status_code == 200:
        pid = r3.json().get("id", "")
        if pid:
            return f"urn:li:person:{pid}"
    
    return None


def post_to_linkedin(text, image_path=None):
    person_urn = get_person_urn()
    if not person_urn:
        print("❌ Could not get person URN")
        return False
    print(f"Posting as: {person_urn}")
    author_urn = person_urn
    url = "https://api.linkedin.com/v2/ugcPosts"

    if image_path:
        asset = upload_image_to_linkedin(image_path)
        if asset:
            body = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "IMAGE",
                        "media": [{
                            "status": "READY",
                            "description": {"text": "ZEUS-AI Forecast Chart"},
                            "media": asset,
                            "title": {"text": "AI Forecast"}
                        }]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
        else:
            image_path = None

    if not image_path:
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }

    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code in [200, 201]:
        print(f"✅ Posted to LinkedIn!")
        return True
    print(f"❌ LinkedIn error {r.status_code}: {r.text[:300]}")
    return False

# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    import subprocess, os as _os
    js_code = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const symbol = process.argv[2];
  const site = process.argv[3];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.addInitScript(() => {
    localStorage.setItem('zeus_token', 'dev');
    localStorage.setItem('zeus_plan', 'pro');
  });
  await page.goto(site, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  const input = await page.$('#pair-input');
  if (input) { await input.fill(''); await input.type(symbol); }
  const btn = await page.$('.run-btn');
  if (btn) await btn.click();
  try {
    await page.waitForFunction(() => {
      const o = document.getElementById('chart-overlay');
      return o && o.classList.contains('hidden');
    }, { timeout: 60000 });
  } catch(e) { console.log('Timeout'); }
  await page.waitForTimeout(3000);
  try {
    const el = await page.$('#tv-chart');
    if (el) { await el.screenshot({ path: '/tmp/li_chart.png' }); }
    else { await page.screenshot({ path: '/tmp/li_chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } }); }
  } catch(e) { await page.screenshot({ path: '/tmp/li_chart.png' }); }
  await browser.close();
  console.log('Done!');
})();
"""
    with open('/tmp/li_screenshot.js', 'w') as jf:
        jf.write(js_code)

    project_dir = _os.path.dirname(_os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/li_screenshot.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**_os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})

    print("Screenshot:", result.stdout.strip())
    if _os.path.exists('/tmp/li_chart.png'):
        return '/tmp/li_chart.png'
    return None

# ── MAIN ──────────────────────────────────────────────────
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

    text = format_post(data, symbol)
    print(f"Post preview:\n{text[:150]}...")

    image_path = take_screenshot(symbol)
    post_to_linkedin(text, image_path)

if __name__ == "__main__":
    main()
