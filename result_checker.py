"""
Zeus AI - Daily Result Checker
Runs daily, checks if yesterday's forecast was correct,
posts results to all social platforms
"""
import os, requests, json
from datetime import datetime, timezone, timedelta

API_URL   = os.environ.get("CRYPTO_API_URL", "")
API_TOKEN = os.environ.get("CRYPTO_API_TOKEN", "")
FB_TOKEN  = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "103114287835428")
TG_BOT    = os.environ.get("TELEGRAM_BOT_TOKEN_CRYPTO", "")
TG_CHAN   = os.environ.get("TELEGRAM_CRYPTO_CHANNEL", "")
DC_BOT    = os.environ.get("DISCORD_BOT_TOKEN", "")
DC_CHAN   = os.environ.get("DISCORD_CRYPTO_CHANNEL", "")

# Top 5 crypto pairs to track
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

def get_forecast(symbol):
    try:
        r = requests.post(
            f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": API_TOKEN},
            timeout=120
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Forecast error for {symbol}: {e}")
    return None

def get_signal(data):
    fma7 = data.get("forecast_ma7", [])
    fma3 = data.get("forecast_ma3", [])
    if fma7 and len(fma7) >= 5 and fma3 and len(fma3) >= 5:
        if fma7[0] < fma7[4] and fma3[0] < fma3[4]: return "BULLISH"
        elif fma7[0] > fma7[4] and fma3[0] > fma3[4]: return "BEARISH"
    return "NEUTRAL"

def load_yesterday():
    """Load yesterday's forecasts from file"""
    try:
        with open("/tmp/zeus_forecasts.json") as f:
            return json.load(f)
    except:
        return {}

def save_today(forecasts):
    """Save today's forecasts for tomorrow's comparison"""
    with open("/tmp/zeus_forecasts.json", "w") as f:
        json.dump(forecasts, f)

def check_result(signal, entry_price, current_price):
    """Check if forecast was correct"""
    diff = ((current_price - entry_price) / entry_price) * 100
    if signal == "BULLISH":
        return "✅ CORRECT" if diff > 0.1 else ("❌ WRONG" if diff < -0.1 else "➖ NEUTRAL")
    elif signal == "BEARISH":
        return "✅ CORRECT" if diff < -0.1 else ("❌ WRONG" if diff > 0.1 else "➖ NEUTRAL")
    return "➖ NEUTRAL"

def post_facebook(message):
    if not FB_TOKEN: return
    try:
        r = requests.post(
            f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
            data={"message": message, "access_token": FB_TOKEN},
            timeout=30
        )
        if "id" in r.json(): print("✅ Facebook posted!")
        else: print(f"❌ Facebook: {r.text[:100]}")
    except Exception as e:
        print(f"❌ Facebook error: {e}")

def post_telegram(message):
    if not TG_BOT or not TG_CHAN: return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
            data={"chat_id": TG_CHAN, "text": message},
            timeout=30
        )
        if r.status_code == 200: print("✅ Telegram posted!")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def post_discord(message):
    if not DC_BOT or not DC_CHAN: return
    try:
        r = requests.post(
            f"https://discord.com/api/v10/channels/{DC_CHAN}/messages",
            headers={"Authorization": f"Bot {DC_BOT}", "Content-Type": "application/json"},
            json={"content": message},
            timeout=30
        )
        if r.status_code in [200, 201]: print("✅ Discord posted!")
    except Exception as e:
        print(f"❌ Discord error: {e}")

def main():
    now = datetime.now(timezone.utc)
    print(f"Running result checker: {now.strftime('%Y-%m-%d %H:%M UTC')}")

    # Load yesterday's forecasts
    yesterday = load_yesterday()

    # Get today's forecasts and compare
    today_forecasts = {}
    results = []
    wins = 0
    total = 0

    for symbol in PAIRS:
        print(f"Checking {symbol}...")
        data = get_forecast(symbol)
        if not data:
            continue

        current_price = data.get("last_close", 0)
        signal = get_signal(data)
        today_forecasts[symbol] = {
            "price": current_price,
            "signal": signal,
            "time": now.isoformat()
        }

        # Compare with yesterday
        if symbol in yesterday:
            prev = yesterday[symbol]
            entry_price = prev.get("price", current_price)
            prev_signal = prev.get("signal", "NEUTRAL")
            result = check_result(prev_signal, entry_price, current_price)
            pct = ((current_price - entry_price) / entry_price) * 100

            results.append({
                "symbol": symbol,
                "signal": prev_signal,
                "entry": entry_price,
                "current": current_price,
                "pct": pct,
                "result": result
            })

            if "✅" in result: wins += 1
            if "➖" not in result: total += 1

    # Save today's forecasts
    save_today(today_forecasts)

    if not results:
        print("No previous forecasts to compare. First run — saving today's forecasts.")
        return

    # Build message
    win_rate = round((wins / total * 100) if total > 0 else 0)
    date_str = now.strftime("%b %d, %Y")

    lines = [f"🤖 ZEUS-AI DAILY TRACK RECORD — {date_str}"]
    lines.append(f"📊 Win Rate: {wins}/{total} = {win_rate}%")
    lines.append("━" * 30)

    for r in results:
        sig_emoji = "📈" if r["signal"] == "BULLISH" else ("📉" if r["signal"] == "BEARISH" else "●")
        pct_str = f"+{r['pct']:.2f}%" if r['pct'] >= 0 else f"{r['pct']:.2f}%"
        lines.append(f"{r['result']} {r['symbol'].replace('USDT','')} | {r['signal']} {sig_emoji} | {pct_str}")

    lines.append("━" * 30)
    lines.append(f"📌 Today's Signals:")
    for symbol, d in today_forecasts.items():
        sig_e = "📈" if d['signal']=='BULLISH' else ("📉" if d['signal']=='BEARISH' else "●")
        lines.append(f"  {symbol.replace('USDT','')}: {d['signal']} {sig_e}")

    lines.append("")
    lines.append("⚡ Get FREE AI forecasts at zeusvisions.com")
    lines.append("#ZEUSVision #CryptoAI #AITrading #Bitcoin #Crypto")

    message = "\n".join(lines)
    print("\n--- MESSAGE PREVIEW ---")
    print(message)
    print("--- END ---\n")

    # Post to all platforms
    post_facebook(message)
    post_telegram(message)
    post_discord(message)

    print(f"\n✅ Done! Win rate: {wins}/{total} = {win_rate}%")

if __name__ == "__main__":
    main()
