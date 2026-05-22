"""
ZEUSVision + Investleey Discord Auto-Poster
Posts AI forecast charts to Discord channels
"""
import os, requests, random, subprocess
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
MODE = os.environ.get("POST_MODE", "stocks")

if MODE == "crypto":
    CHANNEL_ID = os.environ.get("DISCORD_CRYPTO_CHANNEL", "1507191849494908978")
    API_URL    = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN  = "mycryptovision2025"
    SITE_URL   = "https://zeusvisions.com"
    WATCHLIST  = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
                  "DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
    WEIGHTS    = [4,3,3,2,2,1,1,1,1,1]
else:
    CHANNEL_ID = os.environ.get("DISCORD_STOCK_CHANNEL", "1507191734340419605")
    API_URL    = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN  = "mystockvision2025"
    SITE_URL   = "https://investleey.com"
    WATCHLIST  = ["AAPL","MSFT","NVDA","TSLA","GOOGL",
                  "META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    WEIGHTS    = [3,3,3,3,2,2,2,2,1,1,1,1]

HEADERS = {
    "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
    "Content-Type": "application/json"
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

# ── FORMAT MESSAGE ────────────────────────────────────────
def format_message(data, symbol):
    last_close = data.get("last_close", 0)
    f_ma7      = data.get("forecast_ma7", [last_close]*60)
    acc_ma7    = data.get("accuracy_ma7", 0)
    acc_ma25   = data.get("accuracy_ma25", 0)

    ma7_1h     = f_ma7[0] if f_ma7 else last_close
    is_bullish = ma7_1h > last_close
    signal     = "🟢 BULLISH" if is_bullish else "🔴 BEARISH"
    arrow      = "📈" if is_bullish else "📉"
    color      = 0x0ecb81 if is_bullish else 0xf6465d

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

    embed = format_message(data, symbol)
    print(f"Signal: {embed['fields'][1]['value']}")

    image_path = take_screenshot(symbol)
    post_to_discord(embed, image_path)

if __name__ == "__main__":
    main()
