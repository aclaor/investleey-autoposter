"""
ZEUSVision Facebook Auto-Poster
Posts AI crypto forecasts to Facebook page every 4 hours with screenshot
"""
import os, requests, random, base64
from datetime import datetime, timezone
import os as _os

MODE       = _os.environ.get("MODE", _os.environ.get("POST_MODE", "crypto"))
API_URL    = _os.environ.get("CRYPTO_API_URL", "") if MODE=="crypto" else _os.environ.get("STOCK_API_URL", "")
API_TOKEN  = _os.environ.get("CRYPTO_API_TOKEN", "") if MODE=="crypto" else _os.environ.get("STOCK_API_TOKEN", "")
FB_TOKEN   = _os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = _os.environ.get("FB_PAGE_ID", "103114287835428")
IMGBB_KEY  = _os.environ.get("IMGBB_API_KEY", "72e357126560d58d7ae925855456fd50")
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST  = CRYPTO_WATCHLIST if MODE=="crypto" else STOCK_WATCHLIST
WEIGHTS    = [max(1, 3-i//3) for i in range(len(WATCHLIST))]
SITE_URL   = "https://zeusvisions.com" if MODE=="crypto" else "https://investleey.com"
SITE_NAME  = "ZeusVisions" if MODE=="crypto" else "Investleey"

def get_signal(data, interval="1h"):
    last_close = data.get("last_close", 0)
    if interval in ["1m","5m","15m"]:
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

def get_forecast(symbol):
    print(f"Fetching {symbol}...")
    try:
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": API_TOKEN, "Content-Type": "application/json"},
            timeout=120)
        if r.status_code == 200: return r.json()
        print(f"Error: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

def pct(c, f): return ((f-c)/c)*100 if f and c else 0.0
def arrow(v): return "📈" if v >= 0 else "📉"
def fmt(v): return f"{'+' if v>=0 else ''}{v:.2f}%"

def format_post(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    now = datetime.now(timezone.utc)
    f_ma7  = data.get("forecast_ma7",  [last_close]*60)
    f_ma3  = data.get("forecast_ma3",  [last_close]*60)
    f_ma25 = data.get("forecast_ma25", [last_close]*60)
    f_vwap = data.get("forecast_vwap600",[last_close]*60)
    ma3_7   = f_ma3[6]   if len(f_ma3)>6   else last_close
    ma7_7   = f_ma7[6]   if len(f_ma7)>6   else last_close
    ma7_30  = f_ma7[29]  if len(f_ma7)>29  else last_close
    ma25_30 = f_ma25[29] if len(f_ma25)>29 else last_close
    vwap_7  = f_vwap[6]  if len(f_vwap)>6  else last_close
    signal_name, signal_emoji, _ = get_signal(data, interval)
    outlook = f"{signal_name} {signal_emoji}"
    p = f"${last_close:,.2f}" if last_close>=1 else f"${last_close:.6f}"
    display = symbol.replace("USDT","/USDT") if MODE=="crypto" else symbol
    site = "zeusvisions.com" if MODE=="crypto" else "investleey.com"
    tags = "#ZEUSVision #CryptoForecast #AITrading #Crypto #Bitcoin" if MODE=="crypto" else "#Investleey #StockForecast #AITrading #Stocks"
    return f"""📊 {display} AI FORECAST — {now.strftime('%A, %B %d %Y')}
🕐 {now.strftime('%I:%M %p UTC')}
💰 Current Price: {p}
📌 Outlook: {outlook}
━━━━━━━━━━━━━━━━━━━━
🤖 ZEUS-AI FORECAST LINES
━━━━━━━━━━━━━━━━━━━━
⚡ Short-Term (MA-3): ${ma3_7:,.4f} {arrow(pct(last_close,ma3_7))} {fmt(pct(last_close,ma3_7))} | Acc: {data.get("accuracy_ma3",0):.1f}%
📈 Mid-Term (MA-7):  ${ma7_7:,.4f} {arrow(pct(last_close,ma7_7))} {fmt(pct(last_close,ma7_7))} | Acc: {data.get("accuracy_ma7",0):.1f}%
📊 Long-Term (MA-25): ${ma25_30:,.4f} {arrow(pct(last_close,ma25_30))} {fmt(pct(last_close,ma25_30))} | Acc: {data.get("accuracy_ma25",0):.1f}%
━━━━━━━━━━━━━━━━━━━━
🌐 Full forecast at {site}
📱 Sign up FREE — 500+ {"crypto pairs" if MODE=="crypto" else "US stocks & ETFs"}
━━━━━━━━━━━━━━━━━━━━
{tags} #{symbol.replace("USDT","")}"""

def take_screenshot(symbol):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(SITE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            page.evaluate("""() => {
                [".ticker-bar","#bottom-section","#faq-section",".bottom-bar",
                 ".pricing-modal",".modal-overlay","#signup-popup",
                 ".trades-panel",".ob-panel","#crypto-market-overview"].forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.style.display="none");
                });
            }""")
            inp = page.query_selector("#pair-input")
            if inp: inp.fill(""); inp.type(symbol)
            btn = page.query_selector(".run-btn")
            if btn: btn.click()
            try:
                page.wait_for_function(
                    "() => { const o = document.getElementById('chart-overlay'); return o && o.classList.contains('hidden'); }",
                    timeout=90000)
            except: pass
            page.wait_for_timeout(4000)
            path = "/tmp/fb_chart.png"
            chart = page.query_selector(".chart-panel")
            if chart: chart.screenshot(path=path)
            else:
                left = page.query_selector(".left-panel")
                if left: left.screenshot(path=path)
                else: page.screenshot(path=path)
            browser.close()
            print("✅ Screenshot saved!")
            return path
    except Exception as e:
        print(f"Screenshot error: {e}")
    return None

def upload_to_imgbb(image_path):
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        r = requests.post("https://api.imgbb.com/1/upload",
            data={"key": IMGBB_KEY, "image": b64}, timeout=30)
        if r.status_code == 200:
            url = r.json()["data"]["url"]
            print(f"✅ Uploaded: {url}")
            return url
    except Exception as e:
        print(f"imgbb error: {e}")
    return None

def post_to_facebook(message, image_url=None):
    if image_url:
        r = requests.post(f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
            data={"url": image_url, "caption": message, "access_token": FB_TOKEN}, timeout=30)
    else:
        r = requests.post(f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
            data={"message": message, "access_token": FB_TOKEN}, timeout=30)
    if r.status_code == 200:
        print(f"✅ Posted! ID: {r.json().get('id','')}")
        return True
    print(f"❌ Error: {r.text[:200]}")
    return False

def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Selected: {symbol}")
    data = get_forecast(symbol) or get_forecast("BTCUSDT" if MODE=="crypto" else "AAPL")
    if not data:
        print("❌ No forecast available.")
        return
    message = format_post(data, symbol, interval="1h")
    print(message[:300])
    image_path = take_screenshot(symbol)
    image_url = upload_to_imgbb(image_path) if image_path else None
    post_to_facebook(message, image_url)

if __name__ == "__main__":
    main()
