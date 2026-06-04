"""
ZEUSVision Facebook Auto-Poster
Posts AI crypto forecasts to Facebook page every 4 hours
"""
import os, requests, random
from datetime import datetime, timezone

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


def get_forecast(symbol):
    print(f"Fetching {symbol}...")
    try:
        r = requests.post(
            f"{CRYPTO_API_URL}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": CRYPTO_TOKEN, "Content-Type": "application/json"},
            timeout=120
        )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"Error: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

def pct(current, future):
    if not future or current == 0: return 0.0
    return ((future - current) / current) * 100

def arrow(val): return "📈" if val >= 0 else "📉"
def fmt(val): return f"{'+' if val>=0 else ''}{val:.2f}%"

def format_post(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    now = datetime.now(timezone.utc)
    f_ma7  = data.get("forecast_ma7",   [last_close]*60)
    f_ma3  = data.get("forecast_ma3",   [last_close]*60)
    f_ma25 = data.get("forecast_ma25",  [last_close]*60)
    f_vwap = data.get("forecast_vwap600",[last_close]*60)

    ma3_7   = f_ma3[6]   if len(f_ma3)  >6  else last_close
    ma7_7   = f_ma7[6]   if len(f_ma7)  >6  else last_close
    ma7_30  = f_ma7[29]  if len(f_ma7)  >29 else last_close
    ma25_30 = f_ma25[29] if len(f_ma25) >29 else last_close
    vwap_7  = f_vwap[6]  if len(f_vwap) >6  else last_close

    signal_name, signal_emoji, signal_arrow = get_signal(data, interval)
    outlook = f"{signal_name} {signal_emoji}"
    p = f"${last_close:,.2f}" if last_close>=1 else f"${last_close:.6f}"
    display = symbol.replace("USDT","/USDT")

    return f"""📊 {display} AI FORECAST — {now.strftime('%A, %B %d %Y')}
🕐 {now.strftime('%I:%M %p UTC')}

💰 Current Price: {p}
📌 Outlook: {outlook}

━━━━━━━━━━━━━━━━━━━━
🤖 ZEUS-AI FORECAST LINES
━━━━━━━━━━━━━━━━━━━━
⚡ Short-Term (MA-3)
  7-Day: ${ma3_7:,.4f}  {arrow(pct(last_close,ma3_7))} {fmt(pct(last_close,ma3_7))}
  Accuracy: {data.get('accuracy_ma3',0):.1f}%

📈 Mid-Term (MA-7)
  7-Day:  ${ma7_7:,.4f}  {arrow(pct(last_close,ma7_7))} {fmt(pct(last_close,ma7_7))}
  30-Day: ${ma7_30:,.4f}  {arrow(pct(last_close,ma7_30))} {fmt(pct(last_close,ma7_30))}
  Accuracy: {data.get('accuracy_ma7',0):.1f}%

📊 Long-Term (MA-25)
  30-Day: ${ma25_30:,.4f}  {arrow(pct(last_close,ma25_30))} {fmt(pct(last_close,ma25_30))}
  Accuracy: {data.get('accuracy_ma25',0):.1f}%

💹 VWAP Trend
  7-Day: ${vwap_7:,.4f}  {arrow(pct(last_close,vwap_7))} {fmt(pct(last_close,vwap_7))}
  Accuracy: {data.get('accuracy_vwap600',0):.1f}%

━━━━━━━━━━━━━━━━━━━━
🌐 Full forecast at zeusvisions.com
📱 Sign up FREE — 500+ crypto pairs
━━━━━━━━━━━━━━━━━━━━
#ZEUSVision #CryptoForecast #{symbol.replace('USDT','')} #AITrading #Crypto #Bitcoin #CryptoMarket"""

def post_to_facebook(message):
    url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed"
    r = requests.post(url, data={"message": message, "access_token": FB_TOKEN}, timeout=30)
    print(f"FB Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ Posted! ID: {r.json().get('id','')}")
        return True
    print(f"❌ Error: {r.text}")
    return False

def main():
    import os as _os
    _mode = _os.environ.get("MODE", _os.environ.get("POST_MODE", "crypto"))
    _api_url = _os.environ.get("CRYPTO_API_URL", "") if _mode=="crypto" else _os.environ.get("STOCK_API_URL", "")
    _api_token = _os.environ.get("CRYPTO_API_TOKEN", "") if _mode=="crypto" else _os.environ.get("STOCK_API_TOKEN", "")
    global MODE, API_URL, API_TOKEN, WATCHLIST, SITE_URL, SITE_NAME
    MODE = _mode
    API_URL = _api_url
    API_TOKEN = _api_token
    WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"] if MODE=="crypto" else ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    SITE_URL = "https://zeusvisions.com" if MODE=="crypto" else "https://investleey.com"
    SITE_NAME = "ZeusVisions" if MODE=="crypto" else "Investleey" 
    weights = [max(1, 3-i//3) for i in range(len(WATCHLIST))]
    symbol = random.choices(WATCHLIST, weights=weights, k=1)[0]
    print(f"Selected: {symbol}")
    data = get_forecast(symbol) or get_forecast("BTCUSDT")
    if not data:
        print("❌ No forecast available.")
        return
    message = format_post(data, symbol, interval="1h")
    print(message[:300])
    post_to_facebook(message)

if __name__ == "__main__":
    main()

# ── WATCHLIST ─────────────────────────────────────────────
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST        = CRYPTO_WATCHLIST if MODE == "crypto" else STOCK_WATCHLIST
WEIGHTS          = [3,3,2,2,2,1,1,1,1,1] if len(WATCHLIST)==10 else [3,3,3,2,2,2,1,1,1,1,1,1]
SITE_URL         = "https://zeusvisions.com" if MODE == "crypto" else "https://investleey.com"
SITE_NAME        = "ZeusVisions" if MODE == "crypto" else "Investleey"
