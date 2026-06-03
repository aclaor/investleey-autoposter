"""
ZEUSVision + Investleey Telegram Auto-Poster
Posts AI forecast charts to Telegram channels
"""
import os, requests, random, time
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
if os.environ.get("POST_MODE", "stocks") == "crypto":
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN_CRYPTO"]
else:
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN_STOCKS"]
TELEGRAM_CRYPTO_CHANNEL = os.environ.get("TELEGRAM_CRYPTO_CHANNEL", "")  # e.g. @zeusvisions
TELEGRAM_STOCK_CHANNEL  = os.environ.get("TELEGRAM_STOCK_CHANNEL", "")   # e.g. @investleey

MODE = os.environ.get("POST_MODE", "stocks")

if MODE == "crypto":
    API_URL    = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN  = "mycryptovision2025"
    SITE_URL   = "https://zeusvisions.com"
    CHANNEL    = TELEGRAM_CRYPTO_CHANNEL
    WATCHLIST  = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
                  "DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
    WEIGHTS    = [4,3,3,2,2,1,1,1,1,1]
else:
    API_URL    = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN  = "mystockvision2025"
    SITE_URL   = "https://investleey.com"
    CHANNEL    = TELEGRAM_STOCK_CHANNEL
    WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL",
                  "META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    WEIGHTS    = [3,3,3,3,2,2,2,2,1,1,1,1]

# ── FETCH FORECAST ────────────────────────────────────────
def get_forecast(symbol):
    print(f"Fetching {symbol}...")
    try:
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": API_TOKEN, "Content-Type": "application/json"},
            timeout=120)
        if r.status_code == 200:
            return r.json()
        print(f"Error: {r.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

# ── FORMAT MESSAGE ────────────────────────────────────────
def escape_md(text):
    for c in ['-', '.', '!', '(', ')', '+', '=', '|', '{', '}', '#', '~', '>', '<']:
        text = text.replace(c, f'\\{c}')
    return text

def format_message(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    f_ma7  = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)

    ma7_1h = f_ma7[0] if f_ma7 else last_close
    signal_name, signal_emoji, signal_arrow = get_signal(data, interval)
    is_bullish = signal_name == "BULLISH"
    signal = f"{signal_emoji} {signal_name}"
    arrow = signal_arrow

    pct_7 = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target_7 = f_ma7[6] if len(f_ma7)>6 else last_close

    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
        asset_type = "crypto pairs"
        tags = "#Crypto #Bitcoin #CryptoTrading #AITrading #ZEUSVision"
    else:
        display = symbol
        asset_type = "US stocks and ETFs"
        tags = "#Stocks #WallStreet #Investing #AITrading #Investleey"

    pct_sign = "+" if pct_7 >= 0 else ""

    msg = (
        f"{arrow} <b>{display} — ZEUS-AI Forecast</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: <code>${last_close:,.2f}</code>\n"
        f"📊 Signal: <b>{signal}</b>\n"
        f"🎯 7-Day: <code>${target_7:,.2f}</code> ({pct_sign}{pct_7:.1f}%)\n"
        f"🤖 AI Accuracy: <code>{acc_ma7:.1f}%</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <a href=\"{SITE_URL}\">Get full forecast</a>\n"
        f"📱 Free 15-day trial — 500+ {asset_type}\n\n"
        f"{tags}"
    )
    return msg


# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    import subprocess, os as _os
    site = SITE_URL
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
    if (el) { await el.screenshot({ path: '/tmp/tg_chart.png' }); }
    else { await page.screenshot({ path: '/tmp/tg_chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } }); }
  } catch(e) { await page.screenshot({ path: '/tmp/tg_chart.png' }); }
  await browser.close();
  console.log('Done!');
})();
"""
    with open('/tmp/tg_screenshot.js', 'w') as jf:
        jf.write(js_code)

    project_dir = _os.path.dirname(_os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/tg_screenshot.js', symbol, site],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**_os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})

    print("Screenshot:", result.stdout.strip())
    if result.returncode != 0:
        print("Error:", result.stderr[:200])
        return None

    if _os.path.exists('/tmp/tg_chart.png'):
        return '/tmp/tg_chart.png'
    return None

# ── POST TO TELEGRAM ──────────────────────────────────────
def post_to_telegram(message, image_path=None):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    if image_path:
        # Post with photo
        url = f"{base_url}/sendPhoto"
        with open(image_path, 'rb') as img:
            r = requests.post(url, data={
                "chat_id": CHANNEL,
                "caption": message,
                "parse_mode": "HTML"
            }, files={"photo": img}, timeout=30)
    else:
        # Text only
        url = f"{base_url}/sendMessage"
        r = requests.post(url, json={
            "chat_id": CHANNEL,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }, timeout=30)

    if r.status_code == 200:
        print(f"✅ Posted to Telegram {CHANNEL}!")
        return True
    print(f"❌ Telegram error: {r.text[:200]}")
    return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    if not CHANNEL:
        print(f"No Telegram channel set for {MODE} mode")
        return

    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol} | Channel: {CHANNEL}")

    data = get_forecast(symbol)
    if not data:
        backup = "BTCUSDT" if MODE == "crypto" else "AAPL"
        data = get_forecast(backup)
        symbol = backup
    if not data:
        print("No data")
        return

    message = format_message(data, symbol)
    print(f"Message preview:\n{message[:100]}...")

    image_path = take_screenshot(symbol)
    print(f"Screenshot: {image_path}")

    post_to_telegram(message, image_path)

if __name__ == "__main__":
    main()
