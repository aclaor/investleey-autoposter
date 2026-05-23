"""
YouTube Shorts Auto-Poster for ZEUSVision & Investleey
Generates forecast video and uploads to YouTube automatically
Run: python youtube_poster.py
"""
import os, requests, random, json, time, subprocess
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
MODE = os.environ.get("POST_MODE", "stocks")
YT_CLIENT_ID     = os.environ.get("YOUTUBE_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

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

# ── GET YOUTUBE ACCESS TOKEN ──────────────────────────────
def get_access_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    })
    if r.status_code == 200:
        return r.json().get("access_token")
    print(f"Token error: {r.text[:200]}")
    return None

# ── GET FORECAST ──────────────────────────────────────────
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

# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    try:
        subprocess.run(["pip", "install", "playwright", "-q"], capture_output=True)
        subprocess.run(["playwright", "install", "chromium", "--with-deps"], capture_output=True)
    except: pass

    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({{ width: 1080, height: 1920 }});
  await page.goto('{SITE_URL}', {{ waitUntil: 'networkidle', timeout: 30000 }});
  await page.waitForTimeout(2000);
  const input = await page.$('#pair-input');
  if (input) {{ await input.fill(''); await input.type('{symbol}'); }}
  const btn = await page.$('.run-btn');
  if (btn) await btn.click();
  try {{
    await page.waitForFunction(() => {{
      const o = document.getElementById('chart-overlay');
      return o && o.classList.contains('hidden');
    }}, {{ timeout: 60000 }});
  }} catch(e) {{}}
  await page.waitForTimeout(3000);
  await page.screenshot({{ path: '/tmp/yt_chart.png' }});
  await browser.close();
  console.log('Screenshot done!');
}})();
"""
    with open('/tmp/yt_ss.js', 'w') as f:
        f.write(js)
    
    result = subprocess.run(['node', '/tmp/yt_ss.js'],
        capture_output=True, text=True, timeout=120)
    print("Screenshot:", result.stdout.strip() or result.stderr.strip())
    
    if os.path.exists('/tmp/yt_chart.png'):
        return '/tmp/yt_chart.png'
    return None

# ── CREATE VIDEO FROM SCREENSHOT ─────────────────────────
def create_video(image_path, symbol, signal, price, target, pct, acc):
    try:
        subprocess.run(["apt-get", "install", "-y", "-q", "ffmpeg"], capture_output=True)
    except: pass

    output = '/tmp/yt_short.mp4'
    emoji = "📈" if signal == "BULLISH" else "📉"
    pct_sign = "+" if pct >= 0 else ""

    # Create 30-second video from screenshot with text overlay
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', image_path,
        '-vf', (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"drawtext=text='{symbol} AI FORECAST':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=100:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=black@0.5:boxborderw=10,"
            f"drawtext=text='{signal} {emoji}':fontsize=80:fontcolor={'00ff88' if signal=='BULLISH' else 'ff4455'}:x=(w-text_w)/2:y=200:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=black@0.5:boxborderw=10,"
            f"drawtext=text='7-Day Target\\: \\${target:.2f} ({pct_sign}{pct:.1f}%)':fontsize=50:fontcolor=yellow:x=(w-text_w)/2:y=320:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=black@0.5:boxborderw=10,"
            f"drawtext=text='AI Confidence\\: {acc:.0f}%':fontsize=45:fontcolor=cyan:x=(w-text_w)/2:y=420:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=black@0.5:boxborderw=10,"
            f"drawtext=text='Try FREE at {SITE_URL}':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=1750:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=black@0.7:boxborderw=10"
        ),
        '-t', '30',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if os.path.exists(output):
        print(f"Video created: {output}")
        return output
    print(f"FFmpeg error: {result.stderr[-300:]}")
    return None

# ── UPLOAD TO YOUTUBE ─────────────────────────────────────
def upload_to_youtube(video_path, title, description, tags):
    access_token = get_access_token()
    if not access_token:
        print("No access token!")
        return False

    # Step 1: Initialize upload
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(os.path.getsize(video_path))
    }

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags[:10],
            "categoryId": "25"  # News & Politics
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    init_r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers=headers,
        json=metadata
    )

    if init_r.status_code != 200:
        print(f"Init error: {init_r.text[:200]}")
        return False

    upload_url = init_r.headers.get("Location")
    if not upload_url:
        print("No upload URL!")
        return False

    # Step 2: Upload video
    with open(video_path, 'rb') as f:
        video_data = f.read()

    upload_r = requests.put(
        upload_url,
        headers={"Content-Type": "video/mp4"},
        data=video_data
    )

    if upload_r.status_code in [200, 201]:
        video_id = upload_r.json().get("id")
        print(f"✅ Uploaded! https://youtube.com/shorts/{video_id}")
        return True

    print(f"Upload error: {upload_r.text[:200]}")
    return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        print("YouTube credentials not set!")
        return

    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")

    data = get_forecast(symbol)
    if not data:
        print("No forecast data")
        return

    last_close = data.get("last_close", 0)
    f_ma7 = data.get("forecast_ma7", [last_close]*60)
    acc = data.get("accuracy_ma7", 0)
    is_bullish = (f_ma7[0] if f_ma7 else last_close) > last_close
    signal = "BULLISH" if is_bullish else "BEARISH"
    pct = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target = f_ma7[6] if len(f_ma7)>6 else last_close
    pct_sign = "+" if pct >= 0 else ""
    emoji = "📈" if is_bullish else "📉"

    if MODE == "crypto":
        display = symbol.replace("USDT", "")
        title = f"{display} Price Prediction: {signal} {emoji} | AI Forecast {pct_sign}{pct:.1f}% #Shorts"
        tags = [display, "Bitcoin", "Crypto", "CryptoForecast", "AITrading", "CryptoPrediction", "Shorts", "BTC"]
    else:
        display = symbol
        title = f"{display} Stock Forecast: {signal} {emoji} | AI Predicts {pct_sign}{pct:.1f}% #Shorts"
        tags = [symbol, "Stocks", "StockMarket", "AITrading", "StockForecast", "Investing", "Shorts", "WallStreet"]

    description = f"""{display} AI price forecast — {signal} signal {emoji}

Current Price: ${last_close:,.2f}
7-Day Target: ${target:,.2f} ({pct_sign}{pct:.1f}%)
AI Confidence: {acc:.0f}%

Get FREE AI forecasts for {'500+ crypto pairs' if MODE=='crypto' else '500+ US stocks'} 👇
🔗 {SITE_URL}
✅ 15-day free trial — no credit card needed!

⚠️ Not financial advice. Always do your own research.

{'#Crypto #Bitcoin #AITrading #CryptoForecast #CryptoPrediction #BTC #ETH #Shorts' if MODE=='crypto' else '#Stocks #Investing #AITrading #StockForecast #WallStreet #NVDA #AAPL #Shorts'}"""

    print(f"Signal: {signal} | Target: ${target:,.2f} ({pct_sign}{pct:.1f}%)")
    print("Taking screenshot...")
    image = take_screenshot(symbol)

    if not image:
        print("Screenshot failed — creating simple image...")
        # Create simple colored image as fallback
        subprocess.run(['convert', '-size', '1080x1920', 'xc:#060810',
            '-fill', '#00ff88' if is_bullish else '#ff4455',
            '-font', 'DejaVu-Sans-Bold', '-pointsize', '80',
            '-gravity', 'Center', '-annotate', '0',
            f'{display}\n{signal} {emoji}\nTarget: {pct_sign}{pct:.1f}%\n{SITE_URL}',
            '/tmp/yt_chart.png'], capture_output=True)
        if os.path.exists('/tmp/yt_chart.png'):
            image = '/tmp/yt_chart.png'

    if not image:
        print("No image — skipping")
        return

    print("Creating video...")
    video = create_video(image, display, signal, last_close, target, pct, acc)

    if not video:
        print("Video creation failed")
        return

    print(f"Uploading to YouTube...")
    upload_to_youtube(video, title, description, tags)

if __name__ == "__main__":
    main()
