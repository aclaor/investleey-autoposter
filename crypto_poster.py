"""
Investleey Facebook Auto-Poster
Posts AI stock forecasts to Facebook page every 4 hours
"""
import os, requests, random, json
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
FB_TOKEN   = os.environ["FB_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") or "103114287835428"  # caishenshop
API_URL    = os.environ.get("CRYPTO_API_URL") or "https://cryptovision-production-ca20.up.railway.app"
API_TOKEN  = os.environ.get("CRYPTO_API_TOKEN") or "mycryptovision2025"
if not API_TOKEN or API_TOKEN == "***":
    API_TOKEN = "mycryptovision2025"
print(f"Using API_URL: {API_URL}")
print(f"FB_PAGE_ID: {os.environ.get(chr(70)+chr(66)+chr(95)+chr(80)+chr(65)+chr(71)+chr(69)+chr(95)+chr(73)+chr(68), chr(78)+chr(79)+chr(84)+chr(32)+chr(83)+chr(69)+chr(84))}")

# Most active stocks to rotate through
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
    "MATICUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "NEARUSDT",
    "INJUSDT", "ARBUSDT", "OPUSDT", "APTUSDT", "SUIUSDT",
]

# ── FETCH FORECAST ────────────────────────────────────────
def get_forecast(symbol, interval="1d"):
    print(f"Fetching forecast for {symbol} {interval}...")
    r = requests.post(
        "https://stockvision-production-ae61.up.railway.app/forecast",
        json={"symbol": symbol, "interval": interval},
        headers={"x-api-token": API_TOKEN},
        timeout=120
    )
    if r.status_code == 200:
        return r.json()
    print(f"Error: {r.status_code} {r.text[:200]}")
    return None

# ── FORMAT POST ───────────────────────────────────────────
def format_post(data, symbol):
    last_close = data.get("last_close", 0)
    plan       = data.get("plan", "pro")
    now        = datetime.now(timezone.utc)
    day        = now.strftime("%A, %B %d %Y")
    time_str   = now.strftime("%I:%M %p UTC")

    # Get forecast lines
    f_ma7   = data.get("forecast_ma7",   [])
    f_ma3   = data.get("forecast_ma3",   [])
    f_ma25  = data.get("forecast_ma25",  [])
    f_vwap  = data.get("forecast_vwap600", [])

    def pct(current, future):
        if not future or current == 0:
            return 0.0
        return ((future - current) / current) * 100

    def arrow(val):
        return "📈" if val >= 0 else "📉"

    def fmt(val):
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.2f}%"

    # Calculate 7-day and 30-day projections
    ma7_7d   = f_ma7[6]   if len(f_ma7)   > 6  else last_close
    ma7_30d  = f_ma7[29]  if len(f_ma7)   > 29 else last_close
    ma3_7d   = f_ma3[6]   if len(f_ma3)   > 6  else last_close
    ma25_30d = f_ma25[29] if len(f_ma25)  > 29 else last_close
    vwap_7d  = f_vwap[6]  if len(f_vwap)  > 6  else last_close

    # Accuracy scores
    acc_ma7  = data.get("accuracy_ma7",   0)
    acc_ma3  = data.get("accuracy_ma3",   0)
    acc_ma25 = data.get("accuracy_ma25",  0)
    acc_vwap = data.get("accuracy_vwap600", 0)

    # Overall direction
    avg_pct = pct(last_close, ma7_7d)
    outlook = "BULLISH 🟢" if avg_pct >= 0.5 else "BEARISH 🔴" if avg_pct <= -0.5 else "NEUTRAL ⚪"

    # Format price based on value
    if last_close >= 1000:
        price_str = f"${last_close:,.2f}"
    elif last_close >= 1:
        price_str = f"${last_close:,.4f}"
    else:
        price_str = f"${last_close:.6f}"
    
    # Clean symbol display
    display_sym = symbol.replace("USDT", "/USDT")
    
    post = f"""📊 {display_sym} AI FORECAST — {day}
🕐 Generated at {time_str}

💰 Current Price: {price_str}
📌 Outlook: {outlook}

━━━━━━━━━━━━━━━━━━━━
🤖 ZEUS-AI FORECAST LINES
━━━━━━━━━━━━━━━━━━━━

⚡ Short-Term (MA-3)
  7-Day Target:  ${ma3_7d:,.2f}  {arrow(pct(last_close,ma3_7d))} {fmt(pct(last_close,ma3_7d))}
  Accuracy: {acc_ma3:.1f}%

📈 Mid-Term (MA-7)
  7-Day Target:  ${ma7_7d:,.2f}  {arrow(pct(last_close,ma7_7d))} {fmt(pct(last_close,ma7_7d))}
  30-Day Target: ${ma7_30d:,.2f}  {arrow(pct(last_close,ma7_30d))} {fmt(pct(last_close,ma7_30d))}
  Accuracy: {acc_ma7:.1f}%

📊 Long-Term (MA-25)
  30-Day Target: ${ma25_30d:,.2f}  {arrow(pct(last_close,ma25_30d))} {fmt(pct(last_close,ma25_30d))}
  Accuracy: {acc_ma25:.1f}%

💹 VWAP Trend
  7-Day Target:  ${vwap_7d:,.2f}  {arrow(pct(last_close,vwap_7d))} {fmt(pct(last_close,vwap_7d))}
  Accuracy: {acc_vwap:.1f}%

━━━━━━━━━━━━━━━━━━━━
🌐 Get full AI forecast at zeusvisions.com
📱 Sign up FREE — 500+ crypto pairs
━━━━━━━━━━━━━━━━━━━━
#ZEUSVision #CryptoForecast #{symbol} #AITrading #CryptoMarket #Crypto #Bitcoin #CryptoTrading"""

    return post

# ── POST TO FACEBOOK ──────────────────────────────────────
def post_to_facebook(message):
    # Try multiple endpoints for New Pages Experience compatibility
    endpoints = [
        f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
        f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed",
        f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed",
        f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed",
    ]
    for url in endpoints:
        r = requests.post(url, data={
            "message": message,
            "access_token": FB_TOKEN
        }, timeout=30)
        print(f"Tried {url}: {r.status_code}")
        if r.status_code == 200:
            post_id = r.json().get("id", "")
            print(f"✅ Posted to Facebook! Post ID: {post_id}")
            return True
        elif "New Pages Experience" not in r.text and r.status_code != 403:
            print(f"❌ Facebook error: {r.status_code} {r.text}")
            return False
    print(f"❌ All endpoints failed. Last error: {r.text}")
    return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    # Pick a random stock, weighted toward high-volume ones
    weights = [4,3,3,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    symbol = random.choices(WATCHLIST, weights=weights, k=1)[0]
    print(f"Selected: {symbol}")

    # Get forecast
    data = get_forecast(symbol, interval="1d")
    if not data:
        # Try fallback symbol
        symbol = "AAPL"
        data = get_forecast(symbol, interval="1d")
    if not data:
        print("❌ Could not get forecast. Exiting.")
        return

    # Format and post
    message = format_post(data, symbol)
    print("\n--- POST PREVIEW ---")
    print(message)
    print("--- END PREVIEW ---\n")

    success = post_to_facebook(message)
    if success:
        print(f"✅ Successfully posted {symbol} forecast to Facebook!")
    else:
        print("❌ Failed to post to Facebook.")

if __name__ == "__main__":
    main()
