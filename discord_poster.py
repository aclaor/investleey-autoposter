"""
ZEUSVision + Investleey Discord Auto-Poster
Posts AI forecast charts to Discord channels
"""
import os, requests, random, subprocess
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
import os as _os
MODE      = _os.environ.get("MODE", _os.environ.get("POST_MODE", "crypto"))
API_URL   = _os.environ.get("CRYPTO_API_URL", "") if MODE=="crypto" else _os.environ.get("STOCK_API_URL", "")
API_TOKEN = _os.environ.get("CRYPTO_API_TOKEN", "") if MODE=="crypto" else _os.environ.get("STOCK_API_TOKEN", "")
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST = CRYPTO_WATCHLIST if MODE=="crypto" else STOCK_WATCHLIST
WEIGHTS   = [3,3,2,2,2,1,1,1,1,1] if len(WATCHLIST)==10 else [3,3,3,2,2,2,1,1,1,1,1,1]
SITE_URL  = "https://zeusvisions.com" if MODE=="crypto" else "https://investleey.com"
SITE_NAME = "ZeusVisions" if MODE=="crypto" else "Investleey"


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
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1h"},
            headers={"x-api-token": API_TOKEN, "Content-Type": "application/json"},
            timeout=120)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Forecast error: {e}")
    return None

# ── FORMAT MESSAGE ────────────────────────────────────────
def format_message(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    f_ma7      = data.get("forecast_ma7", [last_close]*60)
    acc_ma7    = data.get("accuracy_ma7", 0)
    acc_ma25   = data.get("accuracy_ma25", 0)

    ma7_1h     = f_ma7[0] if f_ma7 else last_close
    signal_name, signal_emoji, signal_arrow = get_signal(data, interval)
    is_bullish = signal_name == "BULLISH"
    signal     = f"{signal_emoji} {signal_name}"
    arrow      = signal_arrow
    color      = 0x0ecb81 if is_bullish else (0xf6465d if signal_name == "BEARISH" else 0x607a99)

    pct_7    = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target_7 = f_ma7[6] if len(f_ma7)>6 else last_close
    pct_sign = "+" if pct_7 >= 0 else ""

    if MODE == "crypto":
        display   = symbol.replace("USDT", "/USDT")
        asset_type = "crypto pairs"
        footer    = "ZEUSVision AI • zeusvisions.com"
    else:
        display   = symbol
        asset_type = "US stocks & ETFs"
        footer    = "Investleey • investleey.com"

    now = datetime.now(timezone.utc).strftime('%b %d, %Y %H:%M UTC')

    # Discord embed
    embed = {
        "title": f"{arrow} {display} — ZEUS-AI Forecast",
        "color": color,
        "fields": [
            {"name": "💰 Current Price", "value": f"`${last_close:,.2f}`", "inline": True},
            {"name": "📊 Signal", "value": f"**{signal}**", "inline": True},
            {"name": "🎯 7-Day Target", "value": f"`${target_7:,.2f}` ({pct_sign}{pct_7:.1f}%)", "inline": True},
            {"name": "🤖 AI Accuracy", "value": f"MA-7: `{acc_ma7:.1f}%` | MA-25: `{acc_ma25:.1f}%`", "inline": False},
        ],
        "description": f"🌐 **[Get full forecast at {SITE_URL}]({SITE_URL})**\n📱 Free 15-day trial — 500+ {asset_type}",
        "footer": {"text": footer},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return embed

# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    js_code = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const symbol = process.argv[2];
  const site = process.argv[3];
  const browser = await chromium.launch();
  const page = await browser.newPage();
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
    if (el) { await el.screenshot({ path: '/tmp/dc_chart.png' }); }
    else { await page.screenshot({ path: '/tmp/dc_chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } }); }
  } catch(e) { await page.screenshot({ path: '/tmp/dc_chart.png' }); }
  await browser.close();
  console.log('Screenshot done!');
})();
"""
    with open('/tmp/dc_screenshot.js', 'w') as jf:
        jf.write(js_code)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/dc_screenshot.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})

    print("Screenshot:", result.stdout.strip())
    if os.path.exists('/tmp/dc_chart.png'):
        return '/tmp/dc_chart.png'
    return None

# ── POST TO DISCORD ───────────────────────────────────────
def post_to_discord(embed, image_path=None):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    if image_path:
        with open(image_path, 'rb') as img:
            r = requests.post(url,
                headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                data={"payload_json": __import__('json').dumps({"embeds": [embed]})},
                files={"file": ("chart.png", img, "image/png")},
                timeout=30)
    else:
        r = requests.post(url,
            headers=HEADERS,
            json={"embeds": [embed]},
            timeout=30)

    if r.status_code in [200, 201]:
        print(f"✅ Posted to Discord channel {CHANNEL_ID}!")
        return True
    print(f"❌ Discord error {r.status_code}: {r.text[:300]}")
    return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol} | Channel: {CHANNEL_ID}")

    data = get_forecast(symbol)
    if not data:
        backup = "BTCUSDT" if MODE == "crypto" else "AAPL"
        data = get_forecast(backup)
        symbol = backup
    if not data:
        print("No forecast data")
        return

    embed = format_message(data, symbol, interval="1h")
    print(f"Signal: {embed['fields'][1]['value']}")

    image_path = take_screenshot(symbol)
    post_to_discord(embed, image_path)

if __name__ == "__main__":
    main()

# ── WATCHLIST ─────────────────────────────────────────────
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST        = CRYPTO_WATCHLIST if MODE == "crypto" else STOCK_WATCHLIST
WEIGHTS          = [3,3,2,2,2,1,1,1,1,1] if len(WATCHLIST)==10 else [3,3,3,2,2,2,1,1,1,1,1,1]
SITE_URL         = "https://zeusvisions.com" if MODE == "crypto" else "https://investleey.com"
SITE_NAME        = "ZeusVisions" if MODE == "crypto" else "Investleey"
