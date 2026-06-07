"""
Investleey + ZeusVisions Facebook Auto-Poster
Posts AI forecast charts WITH screenshots to Facebook page
Uses same screenshot logic as discord_poster.py
"""
import os, requests, random, base64, json, subprocess
from datetime import datetime, timezone

import os as _os
MODE       = _os.environ.get("MODE", _os.environ.get("POST_MODE", "stocks"))
API_URL    = _os.environ.get("CRYPTO_API_URL", "") if MODE=="crypto" else _os.environ.get("STOCK_API_URL", "")
API_TOKEN  = _os.environ.get("CRYPTO_API_TOKEN", "") if MODE=="crypto" else _os.environ.get("STOCK_API_TOKEN", "")
FB_TOKEN   = _os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = _os.environ.get("FB_PAGE_ID", "103114287835428")
IMGBB_KEY  = _os.environ.get("IMGBB_API_KEY", "72e357126560d58d7ae925855456fd50")

CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST  = CRYPTO_WATCHLIST if MODE=="crypto" else STOCK_WATCHLIST
WEIGHTS    = [3,3,2,2,2,1,1,1,1,1] if len(WATCHLIST)==10 else [3,3,3,2,2,2,1,1,1,1,1,1]
SITE_URL   = "https://zeusvisions.com" if MODE=="crypto" else "https://investleey.com"
SITE_NAME  = "ZeusVisions" if MODE=="crypto" else "Investleey"


def get_signal(data, interval="1h"):
    short_intervals = ["1m", "5m", "15m"]
    is_short = interval in short_intervals
    last_close = data.get("last_close", 0)
    if is_short:
        fv200 = data.get("forecast_vwap200", [])
        if fv200 and len(fv200) >= 5:
            first, fifth = fv200[0], fv200[4]
            threshold = (last_close or first) * 0.0005
            if abs(fifth - first) <= threshold: return "NEUTRAL", "⚪", "●"
            elif first < fifth: return "BULLISH", "🟢", "📈"
            else: return "BEARISH", "🔴", "📉"
    else:
        fma7 = data.get("forecast_ma7", [])
        fma3 = data.get("forecast_ma3", [])
        if fma7 and len(fma7) >= 5 and fma3 and len(fma3) >= 5:
            if fma7[0] < fma7[4] and fma3[0] < fma3[4]: return "BULLISH", "🟢", "📈"
            elif fma7[0] > fma7[4] and fma3[0] > fma3[4]: return "BEARISH", "🔴", "📉"
            else: return "NEUTRAL", "⚪", "●"
    return "NEUTRAL", "⚪", "●"


def get_forecast(symbol, interval="1h"):
    print(f"Fetching forecast for {symbol} {interval}...")
    try:
        api_base = API_URL or ("https://cryptovision-production-ca20.up.railway.app" if MODE=="crypto" else "https://stockvision-production-ae61.up.railway.app")
        r = requests.post(
            f"{api_base}/forecast",
            json={"symbol": symbol, "interval": interval},
            headers={"x-api-token": API_TOKEN},
            timeout=120
        )
        if r.status_code == 200:
            return r.json()
        print(f"Error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"Forecast error: {e}")
    return None


def format_post(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    now        = datetime.now(timezone.utc)
    day        = now.strftime("%A, %B %d %Y")
    time_str   = now.strftime("%I:%M %p UTC")

    f_ma7   = data.get("forecast_ma7",   [])
    f_ma3   = data.get("forecast_ma3",   [])
    f_ma25  = data.get("forecast_ma25",  [])
    f_vwap  = data.get("forecast_vwap600", [])

    def pct(current, future):
        if not future or current == 0: return 0.0
        return ((future - current) / current) * 100

    def fmt(val):
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.2f}%"

    ma7_7d   = f_ma7[6]   if len(f_ma7)   > 6  else last_close
    ma7_30d  = f_ma7[29]  if len(f_ma7)   > 29 else last_close
    ma3_7d   = f_ma3[6]   if len(f_ma3)   > 6  else last_close
    ma25_30d = f_ma25[29] if len(f_ma25)  > 29 else last_close
    vwap_7d  = f_vwap[6]  if len(f_vwap)  > 6  else last_close

    acc_ma7  = data.get("accuracy_ma7",   0)
    acc_ma3  = data.get("accuracy_ma3",   0)
    acc_ma25 = data.get("accuracy_ma25",  0)
    acc_vwap = data.get("accuracy_vwap600", 0)

    signal_name, signal_emoji, signal_arrow = get_signal(data, interval)
    outlook   = f"{signal_name} {signal_emoji}"
    display   = symbol.replace("USDT", "/USDT") if MODE=="crypto" else symbol
    asset_type = "crypto pairs" if MODE=="crypto" else "US stocks & ETFs"

    post = f"""{signal_arrow} {display} AI FORECAST — {day}
🕐 Generated at {time_str}

💰 Current Price: ${last_close:,.2f}
📌 Outlook: {outlook}

━━━━━━━━━━━━━━━━━━━━
🤖 ZEUS-AI FORECAST LINES
━━━━━━━━━━━━━━━━━━━━

⚡ Short-Term (MA-3)
  7-Day Target:  ${ma3_7d:,.2f}   {fmt(pct(last_close,ma3_7d))}
  Accuracy: {acc_ma3:.1f}%

📈 Mid-Term (MA-7)
  7-Day Target:  ${ma7_7d:,.2f}   {fmt(pct(last_close,ma7_7d))}
  30-Day Target: ${ma7_30d:,.2f}   {fmt(pct(last_close,ma7_30d))}
  Accuracy: {acc_ma7:.1f}%

📊 Long-Term (MA-25)
  30-Day Target: ${ma25_30d:,.2f}   {fmt(pct(last_close,ma25_30d))}
  Accuracy: {acc_ma25:.1f}%

💹 VWAP Trend
  7-Day Target:  ${vwap_7d:,.2f}   {fmt(pct(last_close,vwap_7d))}
  Accuracy: {acc_vwap:.1f}%

━━━━━━━━━━━━━━━━━━━━
🌐 Get full AI forecast at {SITE_URL}
📱 Sign up FREE — 500+ {asset_type}
━━━━━━━━━━━━━━━━━━━━
#{SITE_NAME} #StockForecast #{symbol.replace('/','').replace('-','')} #AITrading #StockMarket #Investing #WallStreet #StockAnalysis"""

    return post


# ── TAKE SCREENSHOT — exact same logic as discord_poster.py ──
def take_screenshot(symbol):
    # Identical JS to discord_poster.py — captures #tv-chart for clean look
    js_code = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const symbol = process.argv[2];
  const site   = process.argv[3];
  const browser = await chromium.launch();
  const page    = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 720 });
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
  } catch(e) { console.log('Timeout waiting for chart'); }
  await page.waitForTimeout(3000);
  try {
    const el = await page.$('#tv-chart');
    if (el) { await el.screenshot({ path: '/tmp/fb_chart.png' }); }
    else { await page.screenshot({ path: '/tmp/fb_chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } }); }
  } catch(e) { await page.screenshot({ path: '/tmp/fb_chart.png' }); }
  await browser.close();
  console.log('Screenshot done!');
})();
"""
    with open('/tmp/fb_screenshot.js', 'w') as jf:
        jf.write(js_code)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/fb_screenshot.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'}
    )
    print("Screenshot:", result.stdout.strip())
    if result.stderr: print("Stderr:", result.stderr.strip()[:200])
    if os.path.exists('/tmp/fb_chart.png'):
        print("✅ Screenshot saved!")
        return '/tmp/fb_chart.png'
    print("❌ Screenshot not found")
    return None


# ── UPLOAD TO IMGBB ───────────────────────────────────────
def upload_to_imgbb(image_path):
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        r = requests.post("https://api.imgbb.com/1/upload",
            data={"key": IMGBB_KEY, "image": b64}, timeout=30)
        if r.status_code == 200:
            url = r.json()["data"]["url"]
            print(f"✅ Uploaded to imgbb: {url}")
            return url
        print(f"imgbb error: {r.status_code}")
    except Exception as e:
        print(f"imgbb error: {e}")
    return None


# ── POST TO FACEBOOK WITH PHOTO ───────────────────────────
def post_to_facebook_with_photo(message, image_url):
    endpoints = [
        f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
        f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos",
        f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos",
    ]
    for url in endpoints:
        try:
            r = requests.post(url, data={
                "url": image_url,
                "caption": message,
                "access_token": FB_TOKEN
            }, timeout=30)
            print(f"Tried {url}: {r.status_code}")
            if r.status_code == 200:
                post_id = r.json().get("id", "")
                print(f"✅ Posted with photo! Post ID: {post_id}")
                return True
        except Exception as e:
            print(f"Error: {e}")
    return False


def post_to_facebook_text_only(message):
    endpoints = [
        f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
        f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed",
    ]
    for url in endpoints:
        try:
            r = requests.post(url, data={
                "message": message,
                "access_token": FB_TOKEN
            }, timeout=30)
            print(f"Tried {url}: {r.status_code}")
            if r.status_code == 200:
                print(f"✅ Posted text-only!")
                return True
        except Exception as e:
            print(f"Error: {e}")
    return False


# ── MAIN ──────────────────────────────────────────────────
def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")

    data = get_forecast(symbol, interval="1h")
    if not data:
        fallback = "BTCUSDT" if MODE=="crypto" else "AAPL"
        print(f"Trying fallback: {fallback}")
        data = get_forecast(fallback, interval="1h")
        symbol = fallback
    if not data:
        print("❌ No forecast data. Exiting.")
        return

    message = format_post(data, symbol, interval="1h")
    print("\n--- POST PREVIEW ---")
    print(message[:300])
    print("--- END PREVIEW ---\n")

    # Screenshot → imgbb → Facebook with photo
    image_path = take_screenshot(symbol)
    if image_path:
        image_url = upload_to_imgbb(image_path)
        if image_url:
            success = post_to_facebook_with_photo(message, image_url)
            if success:
                print(f"✅ Posted {symbol} with screenshot to Facebook!")
                return
        print("imgbb upload failed, trying text-only...")

    # Fallback: text only
    success = post_to_facebook_text_only(message)
    if success:
        print(f"✅ Posted {symbol} text-only to Facebook!")
    else:
        print("❌ Failed to post to Facebook.")


if __name__ == "__main__":
    main()
