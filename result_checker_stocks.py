"""
Investleey - Daily Stock Result Checker
Tracks ALL stocks the user has forecasted
Posts daily win/loss results to social platforms
"""
import os, requests, json
from datetime import datetime, timezone

API_URL    = os.environ.get("STOCK_API_URL", "")
API_TOKEN  = os.environ.get("STOCK_API_TOKEN", "")
FB_TOKEN   = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "103114287835428")
TG_BOT     = os.environ.get("TELEGRAM_BOT_TOKEN_STOCKS", "")
TG_CHAN    = os.environ.get("TELEGRAM_STOCK_CHANNEL", "")
DC_BOT     = os.environ.get("DISCORD_BOT_TOKEN", "")
DC_CHAN    = os.environ.get("DISCORD_STOCK_CHANNEL", "")

# Top 5 stocks to always track
DEFAULT_PAIRS = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"]
RECORD_FILE   = "/tmp/inv_forecasts.json"

def get_forecast(symbol):
    try:
        r = requests.post(
            f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1d"},
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
    try:
        with open(RECORD_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_today(forecasts):
    with open(RECORD_FILE, "w") as f:
        json.dump(forecasts, f)

def check_result(signal, entry, current):
    diff = ((current - entry) / entry) * 100
    if signal == "BULLISH":
        return "✅ CORRECT" if diff > 0.1 else ("❌ WRONG" if diff < -0.1 else "➖ NEUTRAL")
    elif signal == "BEARISH":
        return "✅ CORRECT" if diff < -0.1 else ("❌ WRONG" if diff > 0.1 else "➖ NEUTRAL")
    return "➖ NEUTRAL"

def post_all(message):
    # Facebook
    if FB_TOKEN:
        try:
            r = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
                data={"message": message, "access_token": FB_TOKEN}, timeout=30
            )
            print(f"{'✅' if 'id' in r.json() else '❌'} Facebook")
        except Exception as e: print(f"❌ FB: {e}")

    # Telegram
    if TG_BOT and TG_CHAN:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
                data={"chat_id": TG_CHAN, "text": message}, timeout=30
            )
            print(f"{'✅' if r.status_code==200 else '❌'} Telegram")
        except Exception as e: print(f"❌ TG: {e}")

    # Discord
    if DC_BOT and DC_CHAN:
        try:
            r = requests.post(
                f"https://discord.com/api/v10/channels/{DC_CHAN}/messages",
                headers={"Authorization": f"Bot {DC_BOT}", "Content-Type": "application/json"},
                json={"content": message}, timeout=30
            )
            print(f"{'✅' if r.status_code in [200,201] else '❌'} Discord")
        except Exception as e: print(f"❌ DC: {e}")

def main():
    now = datetime.now(timezone.utc)
    print(f"Investleey Result Checker: {now.strftime('%Y-%m-%d %H:%M UTC')}")

    yesterday = load_yesterday()
    # Always track default pairs + any previously tracked stocks
    all_pairs = list(set(DEFAULT_PAIRS + list(yesterday.keys())))

    today_forecasts = {}
    results = []
    wins = losses = 0

    for symbol in all_pairs:
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

        if symbol in yesterday:
            prev = yesterday[symbol]
            entry = prev.get("price", current_price)
            prev_signal = prev.get("signal", "NEUTRAL")
            result = check_result(prev_signal, entry, current_price)
            pct = ((current_price - entry) / entry) * 100
            results.append({
                "symbol": symbol,
                "signal": prev_signal,
                "entry": entry,
                "current": current_price,
                "pct": pct,
                "result": result
            })
            if "✅" in result: wins += 1
            elif "❌" in result: losses += 1

    save_today(today_forecasts)

    if not results:
        print("First run — forecasts saved for tomorrow's comparison.")
        return

    total = wins + losses
    win_rate = round((wins / total * 100) if total > 0 else 0)
    date_str = now.strftime("%b %d, %Y")

    lines = [f"📊 INVESTLEEY AI TRACK RECORD — {date_str}"]
    lines.append(f"🎯 Win Rate: {wins}/{total} = {win_rate}%")
    lines.append("━" * 30)

    for r in results:
        if '➖' in r['result']: continue
        sig_e = "📈" if r['signal']=='BULLISH' else "📉"
        pct_str = f"+{r['pct']:.2f}%" if r['pct'] >= 0 else f"{r['pct']:.2f}%"
        lines.append(f"{r['result']} {r['symbol']} | {r['signal']} {sig_e} | {pct_str}")

    lines.append("━" * 30)
    lines.append("📌 Today's Signals:")
    for sym, d in list(today_forecasts.items())[:5]:
        sig_e = "📈" if d['signal']=='BULLISH' else ("📉" if d['signal']=='BEARISH' else "●")
        lines.append(f"  {sym}: {d['signal']} {sig_e}")

    lines.append("")
    lines.append("⚡ Get FREE AI stock forecasts at investleey.com")
    lines.append("#Investleey #StockAI #AITrading #StockMarket #Investing")

    message = "\n".join(lines)
    print("\n--- PREVIEW ---")
    print(message)
    print("--- END ---\n")

    post_all(message)
    print(f"\n✅ Done! {wins}W/{losses}L = {win_rate}% win rate")

if __name__ == "__main__":
    main()
