"""
YouTube Shorts Script Generator for ZEUSVision & Investleey
Generates 60-second scripts to record and post as YouTube Shorts
Run: python youtube_shorts.py
"""
import os, requests, random
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
MODE              = os.environ.get("MODE", "crypto")
API_URL           = os.environ.get("CRYPTO_API_URL", os.environ.get("STOCK_API_URL", ""))
API_TOKEN         = os.environ.get("CRYPTO_API_TOKEN", os.environ.get("STOCK_API_TOKEN", ""))
YT_CLIENT_ID      = os.environ.get("YOUTUBE_CLIENT_ID", "")
YT_CLIENT_SECRET  = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YT_REFRESH_TOKEN  = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")


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


def get_forecast(symbol, api_url, token):
    try:
        r = requests.post(f"{api_url}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": token},
            timeout=60)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

def generate_script(symbol, data, mode, interval="1h"):
    last_close = data.get("last_close", 0)
    f_ma7 = data.get("forecast_ma7", [last_close]*60)
    acc = data.get("accuracy_ma7", 0)
    is_bullish = (f_ma7[0] if f_ma7 else last_close) > last_close
    _sn, _se, _sa = get_signal(data, interval)
    signal = _sn
    pct_7 = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target = f_ma7[6] if len(f_ma7)>6 else last_close
    pct_sign = "+" if pct_7 >= 0 else ""

    if mode == "crypto":
        display = symbol.replace("USDT", "")
        site = CRYPTO_SITE
        asset_type = "crypto"
        hashtags = f"#Crypto #Bitcoin #{display} #CryptoTrading #AITrading #CryptoPrediction #BTC"
    else:
        display = symbol
        site = STOCK_SITE
        asset_type = "stock"
        hashtags = f"#Stocks #StockMarket #{symbol} #Investing #AITrading #StockPrediction #WallStreet"

    emoji = "📈" if is_bullish else "📉"

    script = f"""
{'='*65}
🎬 YOUTUBE SHORT #{display} — {datetime.now().strftime('%B %d, %Y')}
{'='*65}

📌 TITLE:
"{display} AI Forecast: {signal} {emoji} | {pct_sign}{pct_7:.1f}% in 7 Days?"

📌 THUMBNAIL TEXT:
"{display} {signal} {emoji}"
"{pct_sign}{pct_7:.1f}% TARGET"
"AI PREDICTS"

{'='*65}
🎙️ SCRIPT (read this while screen recording your site):
{'='*65}

[0-3 sec] HOOK — Say this while showing {display} chart:
"Is {display} going {'up' if is_bullish else 'down'}? Our AI just gave a {signal} signal!"

[3-8 sec] CURRENT PRICE — Show the chart:
"Right now {display} is trading at ${last_close:,.2f}."

[8-20 sec] AI SIGNAL — Show the forecast lines on chart:
"Our AI analyzed the last {'500+' if mode=='crypto' else '500+'} candles and generated this forecast.
The system is showing a {signal} signal with {acc:.0f}% accuracy.
The 7-day price target is ${target:,.2f} — that's {pct_sign}{pct_7:.1f}% from here."

[20-35 sec] HOW IT WORKS — Show the accuracy scores:
"This isn't just a random guess. The AI evaluates multiple 
price patterns simultaneously and gives you a confidence score.
{acc:.0f}% accuracy means it's been right {acc:.0f} out of 100 times historically."

[35-50 sec] CTA — Show the website:
"You can run this analysis yourself for FREE.
Go to {site} — it covers {'500+ crypto pairs' if mode=='crypto' else '500+ US stocks and ETFs'}.
Just type any {'symbol' if mode=='stock' else 'pair'}, click ZEUS-AI, and get your forecast instantly.
There's a 15-day free trial, no credit card needed."

[50-60 sec] CLOSE — Back to chart:
"Will {display} hit ${target:,.2f}? 
Follow for daily AI forecasts and comment your prediction below!
Link in bio → {site}"

{'='*65}
📌 DESCRIPTION (paste in YouTube):
{'='*65}
{display} AI price forecast using advanced machine learning analysis.

Current Price: ${last_close:,.2f}
AI Signal: {signal} {emoji}  
7-Day Target: ${target:,.2f} ({pct_sign}{pct_7:.1f}%)
Confidence: {acc:.0f}%

Get FREE AI forecasts for {'500+ crypto pairs' if mode=='crypto' else '500+ US stocks'} at:
👉 {site}
✅ 15-day free trial
✅ No credit card needed
✅ BULLISH/BEARISH signals

⚠️ Not financial advice. Always do your own research.

{hashtags}
{'='*65}
📌 RECORDING TIPS:
{'='*65}
1. Screen record your browser showing {site}
2. Run forecast for {symbol} while recording
3. Zoom in on the chart and accuracy scores
4. Use your phone camera on the screen or screen recorder
5. Add background music (YouTube Audio Library - free)
6. Post between 7-9 AM or 6-8 PM your local time
7. Use ALL the hashtags in description
{'='*65}
"""
    return script

def main():
    print("=" * 65)
    print("🎬 YOUTUBE SHORTS SCRIPT GENERATOR")
    print("ZEUSVision & Investleey — Drive Viral Traffic")
    print("=" * 65)
    print()

    # Generate 2 crypto + 2 stock scripts
    crypto_picks = random.sample(CRYPTO_SYMBOLS, 2)
    stock_picks  = random.sample(STOCK_SYMBOLS, 2)

    print("🔮 CRYPTO SHORTS (for ZEUSVision channel)")
    print("-" * 65)
    for sym in crypto_picks:
        print(f"\nFetching forecast for {sym}...")
        data = get_forecast(sym, CRYPTO_API, CRYPTO_TOKEN)
        if not data:
            print(f"  Could not fetch {sym}")
            continue
        print(generate_script(sym, data, "crypto"))

    print("\n💹 STOCK SHORTS (for Investleey channel)")
    print("-" * 65)
    for sym in stock_picks:
        print(f"\nFetching forecast for {sym}...")
        data = get_forecast(sym, STOCK_API, STOCK_TOKEN)
        if not data:
            print(f"  Could not fetch {sym}")
            continue
        print(generate_script(sym, data, "stock"))

    print()
    print("=" * 65)
    print("🚀 YOUR YOUTUBE SHORTS STRATEGY:")
    print("=" * 65)
    print("""
📅 POSTING SCHEDULE:
   • Post 1-2 Shorts per day (morning + evening)
   • Best times: 7-9 AM and 6-8 PM Philippines time
   • Weekdays perform better for stocks
   • Weekends good for crypto

📱 HOW TO RECORD (no face needed!):
   1. Open zeusvisions.com or investleey.com
   2. Run a forecast for today's symbol
   3. Screen record while narrating the script
   4. Edit in CapCut (free app) - add captions
   5. Upload as YouTube Short (vertical 9:16)

🎯 CHANNEL SETUP:
   • Create 2 channels: "ZEUS Vision AI" + "Investleey"  
   • Channel description: AI-powered forecasting
   • Link both sites in channel bio
   • Pin a comment with site link on every video

💡 VIRAL TIPS:
   • First 3 seconds must be a HOOK
   • Always ask viewers to comment their prediction
   • Reply to every comment (boosts algorithm)
   • Cross-post Shorts to Instagram Reels + TikTok
   • Use trending audio from YouTube library
""")
    print("=" * 65)

if __name__ == "__main__":
    main()
