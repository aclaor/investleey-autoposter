"""
ZEUSVision + Investleey Screenshot Auto-Poster
Takes actual screenshot of the website chart and posts to Facebook
"""
import os, requests, random, io, subprocess, sys, time
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
FB_TOKEN   = os.environ["FB_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID = "103114287835428"
MODE = os.environ.get("POST_MODE", "stocks")

if MODE == "crypto":
    SITE_URL  = "https://zeusvisions.com"
    BRAND_URL = "zeusvisions.com"
    WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
                 "DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
    WEIGHTS   = [4,3,3,2,2,1,1,1,1,1]
    API_URL   = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN = "mycryptovision2025"
else:
    SITE_URL  = "https://investleey.com"
    BRAND_URL = "investleey.com"
    WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","GOOGL",
                 "META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    WEIGHTS   = [3,3,3,3,2,2,2,2,1,1,1,1]
    API_URL   = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN = "mystockvision2025"

# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    print(f"Taking screenshot of {symbol} chart...")
    
    site = SITE_URL
    
    # Write JS file separately to avoid f-string issues
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
  if (input) {
    await input.fill('');
    await input.type(symbol);
  }
  const btn = await page.$('.run-btn');
  if (btn) await btn.click();
  console.log('Clicked forecast button, waiting...');
  try {
    await page.waitForFunction(() => {
      const overlay = document.getElementById('chart-overlay');
      return overlay && overlay.classList.contains('hidden');
    }, { timeout: 60000 });
    console.log('Forecast complete!');
  } catch(e) {
    console.log('Timeout, proceeding anyway');
  }
  await page.waitForTimeout(3000);
  try {
    const chartEl = await page.$('#tv-chart');
    if (chartEl) {
      await chartEl.screenshot({ path: '/tmp/chart.png' });
      console.log('Chart screenshot taken');
    } else {
      await page.screenshot({ path: '/tmp/chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } });
      console.log('Fallback screenshot taken');
    }
  } catch(e) {
    console.log('Error:', e.message);
    await page.screenshot({ path: '/tmp/chart.png' });
  }
  await browser.close();
  console.log('Done!');
})();
"""
    with open('/tmp/screenshot.js', 'w') as jf:
        jf.write(js_code)
    

    import os as _os
    project_dir = _os.path.dirname(_os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/screenshot.js', symbol, site],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**_os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr[:500])
    print("Return code:", result.returncode)
    if result.returncode != 0:
        return None
    
    try:
        with open('/tmp/chart.png', 'rb') as f:
            return io.BytesIO(f.read())
    except:
        return None

# ── FETCH FORECAST DATA FOR CAPTION ──────────────────────
def get_forecast(symbol):
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

# ── FORMAT CAPTION ────────────────────────────────────────
def format_caption(data, symbol):
    if not data:
        return f"📊 {symbol} AI Forecast\n🌐 {BRAND_URL}\n#AITrading #ZEUSVision"
    
    last_close = data.get("last_close", 0)
    f_ma7  = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)
    acc_ma3 = data.get("accuracy_ma3", 0)
    acc_ma25 = data.get("accuracy_ma25", 0)
    pct = ((f_ma7[6] - last_close) / last_close * 100) if last_close else 0
    pct30 = ((f_ma7[29] - last_close) / last_close * 100) if last_close and len(f_ma7)>29 else 0
    outlook = "BULLISH" if pct >= 0.5 else "BEARISH" if pct <= -0.5 else "NEUTRAL"
    o_emoji = "🟢" if pct >= 0.5 else "🔴" if pct <= -0.5 else "⚪"

    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
        tags = f"#{symbol.replace('USDT','')} #Crypto #Bitcoin #CryptoTrading #CryptoForecast"
        site = "zeusvisions.com"
    else:
        display = symbol
        tags = f"#{symbol} #Stocks #WallStreet #Investing #StockForecast"
        site = "investleey.com"

    return f"""📊 {display} — ZEUS-AI Forecast
💰 Current Price: ${last_close:,.2f}
{o_emoji} Outlook: {outlook}

🎯 7-Day Target:  ${f_ma7[6]:,.2f} ({'+' if pct>=0 else ''}{pct:.1f}%)
🎯 30-Day Target: ${f_ma7[29] if len(f_ma7)>29 else last_close:,.2f} ({'+' if pct30>=0 else ''}{pct30:.1f}%)

🤖 AI Accuracy Scores:
  MA-3:  {acc_ma3:.1f}%
  MA-7:  {acc_ma7:.1f}%
  MA-25: {acc_ma25:.1f}%

🌐 Get full forecast at {site}
📱 Sign up FREE — 500+ {'crypto pairs' if MODE=='crypto' else 'US stocks & ETFs'}

#AITrading #ZEUSVision #Investleey {tags}"""

# ── POST TO FACEBOOK ──────────────────────────────────────
def post_image_to_facebook(image_bytes, caption):
    try:
        url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
        image_bytes.seek(0)
        r = requests.post(url,
            files={'source': ('chart.png', image_bytes, 'image/png')},
            data={'caption': caption, 'access_token': FB_TOKEN},
            timeout=60)
        print(f"FB Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Posted! ID: {r.json().get('id','')}")
            return True
        print(f"FB Error: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")

    # Take screenshot of actual website chart
    chart = take_screenshot(symbol)
    
    # Get forecast data for caption
    data = get_forecast(symbol)
    caption = format_caption(data, symbol)
    print(f"\nCaption preview:\n{caption[:300]}\n")

    if chart:
        post_image_to_facebook(chart, caption)
    else:
        print("Screenshot failed - skipping post")

if __name__ == "__main__":
    main()
