"""
Pinterest Auto-Poster for ZEUSVision & Investleey
Posts chart screenshots as Pinterest pins
"""
import os, requests, random, subprocess, json
from datetime import datetime, timezone

MODE = os.environ.get("POST_MODE", "stocks")
PINTEREST_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_BOARD_ID = os.environ.get("PINTEREST_BOARD_ID", "")

if MODE == "crypto":
    API_URL   = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN = "mycryptovision2025"
    SITE_URL  = "https://zeusvisions.com"
    WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT"]
    WEIGHTS   = [4,3,3,2,2,1,1,1]
else:
    API_URL   = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN = "mystockvision2025"
    SITE_URL  = "https://investleey.com"
    WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","SPY","QQQ"]
    WEIGHTS   = [3,3,3,3,2,2,2,2,1,1]

def get_forecast(symbol):
    try:
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": "1d"},
            headers={"x-api-token": API_TOKEN},
            timeout=120)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Forecast error: {e}")
    return None

def take_screenshot(symbol):
    js = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 800 });
  await page.goto(process.argv[3], { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  const input = await page.$('#pair-input');
  if (input) { await input.fill(''); await input.type(process.argv[2]); }
  const btn = await page.$('.run-btn');
  if (btn) await btn.click();
  try {
    await page.waitForFunction(() => {
      const o = document.getElementById('chart-overlay');
      return o && o.classList.contains('hidden');
    }, { timeout: 60000 });
  } catch(e) {}
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/pin_chart.png', clip: { x: 0, y: 0, width: 1200, height: 800 } });
  await browser.close();
  console.log('Done!');
})();
"""
    with open('/tmp/pin_ss.js', 'w') as f: f.write(js)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(['node', '/tmp/pin_ss.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir, env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})
    print("Screenshot:", result.stdout.strip())
    if os.path.exists('/tmp/pin_chart.png'):
        return '/tmp/pin_chart.png'
    return None

def post_to_pinterest(title, description, link, image_path):
    if not PINTEREST_TOKEN or not PINTEREST_BOARD_ID:
        print("Pinterest credentials missing!")
        return False
    
    # Upload image first
    upload_url = "https://api.pinterest.com/v5/media"
    headers = {"Authorization": f"Bearer {PINTEREST_TOKEN}"}
    
    with open(image_path, 'rb') as img:
        r = requests.post(upload_url, headers=headers,
            files={"file": ("chart.png", img, "image/png")})
    
    if r.status_code not in [200, 201]:
        print(f"Image upload error: {r.text[:200]}")
        return False
    
    media_id = r.json().get("media_id")
    
    # Create pin
    pin_url = "https://api.pinterest.com/v5/pins"
    pin_data = {
        "board_id": PINTEREST_BOARD_ID,
        "title": title,
        "description": description,
        "link": link,
        "media_source": {"source_type": "media_id", "media_id": media_id}
    }
    
    r2 = requests.post(pin_url, headers={**headers, "Content-Type": "application/json"},
        json=pin_data)
    
    if r2.status_code in [200, 201]:
        print(f"✅ Posted to Pinterest!")
        return True
    print(f"❌ Pinterest error: {r2.text[:200]}")
    return False

def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")
    
    data = get_forecast(symbol)
    if not data:
        print("No forecast data")
        return
    
    last_close = data.get("last_close", 0)
    f_ma7 = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)
    is_bullish = (f_ma7[0] if f_ma7 else last_close) > last_close
    signal = "BULLISH 📈" if is_bullish else "BEARISH 📉"
    pct_7 = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0

    if MODE == "crypto":
        display = symbol.replace("USDT", "")
        title = f"{display} AI Forecast: {signal} | Free Crypto Analysis"
        desc = (f"{display} price prediction using advanced AI analysis.\n\n"
                f"Current: ${last_close:,.2f} | 7-Day Target: {'+' if pct_7>=0 else ''}{pct_7:.1f}%\n"
                f"Signal: {signal}\n\n"
                f"Get free AI forecasts for 500+ crypto pairs at {SITE_URL}\n"
                f"15-day free trial, no credit card needed!\n\n"
                f"#Crypto #Bitcoin #AITrading #CryptoForecast #ZEUSVision")
    else:
        title = f"{symbol} AI Stock Forecast: {signal} | Free Analysis"
        desc = (f"{symbol} stock price prediction using advanced AI analysis.\n\n"
                f"Current: ${last_close:,.2f} | 7-Day Target: {'+' if pct_7>=0 else ''}{pct_7:.1f}%\n"
                f"Signal: {signal}\n\n"
                f"Get free AI forecasts for 500+ US stocks at {SITE_URL}\n"
                f"15-day free trial, no credit card needed!\n\n"
                f"#Stocks #Investing #AITrading #StockForecast #Investleey")

    image_path = take_screenshot(symbol)
    if image_path:
        post_to_pinterest(title, desc, SITE_URL, image_path)
    else:
        print("No screenshot, skipping")

if __name__ == "__main__":
    main()
