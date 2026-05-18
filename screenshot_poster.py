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
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({{ width: 1280, height: 720 }});
  
  // Set auth token in localStorage before loading
  await page.addInitScript(() => {{
    localStorage.setItem('zeus_token', 'dev');
    localStorage.setItem('zeus_plan', 'pro');
  }});
  
  // Go to site
  await page.goto('{SITE_URL}', {{ waitUntil: 'networkidle', timeout: 30000 }});
  await page.waitForTimeout(3000);
  
  // Set symbol in input
  const input = await page.$('#pair-input');
  if (input) {{
    await input.fill('');
    await input.type('{symbol}');
  }}
  
  // Click ZEUS-AI button
  const btn = await page.$('.run-btn');
  if (btn) await btn.click();
  
  // Wait for chart to load
  await page.waitForTimeout(8000);
  
  // Screenshot just the chart area
  const chartEl = await page.$('#chart-container') || await page.$('.chart-wrap') || await page.$('#chart');
  if (chartEl) {{
    await chartEl.screenshot({{ path: '/tmp/chart.png' }});
  }} else {{
    // Full page screenshot
    await page.screenshot({{ path: '/tmp/chart.png', clip: {{ x: 220, y: 130, width: 900, height: 500 }} }});
  }}
  
  await browser.close();
  console.log('Screenshot saved!');
}})();
"""
    with open('/tmp/screenshot.js', 'w') as f:
        f.write(script)
    
    # Run from project dir where playwright is installed
    import os
    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(['node', '/tmp/screenshot.js'], 
                          capture_output=True, text=True, timeout=90,
                          cwd=project_dir,
                          env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})
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
