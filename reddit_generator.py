"""
Reddit Post Generator for Investleey + ZeusVisions
Generates ready-to-copy Reddit posts with screenshots.
Run via GitHub Actions — outputs everything to the console.
You copy and paste manually to Reddit.
"""
import os, random, subprocess, base64, requests, json
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
MODE       = os.environ.get("MODE", "stocks")
API_URL    = os.environ.get("STOCK_API_URL", "https://stockvision-production-ae61.up.railway.app") if MODE=="stocks" else os.environ.get("CRYPTO_API_URL", "https://cryptovision-production-ca20.up.railway.app")
API_TOKEN  = os.environ.get("STOCK_API_TOKEN", "") if MODE=="stocks" else os.environ.get("CRYPTO_API_TOKEN", "")
IMGBB_KEY  = os.environ.get("IMGBB_API_KEY", "72e357126560d58d7ae925855456fd50")
SITE_URL   = "https://investleey.com" if MODE=="stocks" else "https://zeusvisions.com"
SITE_NAME  = "Investleey" if MODE=="stocks" else "ZeusVisions"
SYMBOL     = os.environ.get("SYMBOL", "")  # optional override

STOCK_WATCHLIST  = ["NVDA","AAPL","TSLA","MSFT","GOOGL","META","AMZN","AMD","SPY","QQQ"]
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
WATCHLIST        = STOCK_WATCHLIST if MODE=="stocks" else CRYPTO_WATCHLIST


# ── GET FORECAST ──────────────────────────────────────────
def get_forecast(symbol, interval="1h"):
    print(f"📡 Fetching forecast: {symbol} {interval}...")
    try:
        r = requests.post(
            f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": interval},
            headers={"x-api-token": API_TOKEN},
            timeout=120
        )
        if r.status_code == 200:
            return r.json()
        print(f"API error: {r.status_code}")
    except Exception as e:
        print(f"Forecast error: {e}")
    return None


# ── GET SIGNAL ────────────────────────────────────────────
def get_signal(data):
    fma7 = data.get("forecast_ma7", [])
    fma3 = data.get("forecast_ma3", [])
    if fma7 and len(fma7) >= 5 and fma3 and len(fma3) >= 5:
        if fma7[0] < fma7[4] and fma3[0] < fma3[4]: return "BULLISH", "📈"
        elif fma7[0] > fma7[4] and fma3[0] > fma3[4]: return "BEARISH", "📉"
    return "NEUTRAL", "➡️"


# ── TAKE SCREENSHOT ───────────────────────────────────────
def take_screenshot(symbol):
    print(f"📸 Taking screenshot of {symbol}...")
    js_code = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const symbol = process.argv[2];
  const site   = process.argv[3];
  const browser = await chromium.launch();
  const page    = await browser.newPage();
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
  await page.waitForTimeout(4000);
  try {
    const el = await page.$('#tv-chart');
    if (el) { await el.screenshot({ path: '/tmp/reddit_chart.png' }); }
    else { await page.screenshot({ path: '/tmp/reddit_chart.png', clip: { x: 220, y: 80, width: 860, height: 540 } }); }
  } catch(e) { await page.screenshot({ path: '/tmp/reddit_chart.png' }); }
  await browser.close();
  console.log('Screenshot done!');
})();
"""
    with open('/tmp/reddit_screenshot.js', 'w') as f:
        f.write(js_code)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ['node', '/tmp/reddit_screenshot.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'}
    )
    if result.stdout: print(result.stdout.strip())
    if os.path.exists('/tmp/reddit_chart.png'):
        print("✅ Screenshot saved!")
        return '/tmp/reddit_chart.png'
    print("❌ Screenshot failed")
    return None


# ── UPLOAD TO IMGBB ───────────────────────────────────────
def upload_to_imgbb(image_path):
    print("⬆️  Uploading screenshot to imgbb...")
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        r = requests.post("https://api.imgbb.com/1/upload",
            data={"key": IMGBB_KEY, "image": b64}, timeout=30)
        if r.status_code == 200:
            data = r.json()["data"]
            print(f"✅ Uploaded: {data['url']}")
            return data['url'], data.get('display_url', data['url'])
    except Exception as e:
        print(f"imgbb error: {e}")
    return None, None


# ── GENERATE POSTS ────────────────────────────────────────
def generate_posts(data, symbol, signal, signal_emoji, image_url):
    last_close = data.get("last_close", 0)
    acc_ma7    = data.get("accuracy_ma7", 0)
    acc_ma25   = data.get("accuracy_ma25", 0)
    acc_ma3    = data.get("accuracy_ma3", 0)
    f_ma7      = data.get("forecast_ma7", [])
    f_ma3      = data.get("forecast_ma3", [])
    target_7d  = f_ma7[6]  if len(f_ma7)  > 6  else last_close
    target_30d = f_ma7[29] if len(f_ma7)  > 29 else last_close
    pct_7      = ((target_7d - last_close) / last_close * 100) if last_close else 0
    pct_30     = ((target_30d - last_close) / last_close * 100) if last_close else 0
    pct_7_str  = f"+{pct_7:.1f}%" if pct_7 >= 0 else f"{pct_7:.1f}%"
    pct_30_str = f"+{pct_30:.1f}%" if pct_30 >= 0 else f"{pct_30:.1f}%"
    now        = datetime.now(timezone.utc)
    date_str   = now.strftime("%B %d, %Y")
    display    = symbol.replace("USDT", "/USDT") if MODE == "crypto" else symbol
    asset_type = "crypto" if MODE == "crypto" else "stock"
    img_line   = f"\n\n[📊 Chart Screenshot]({image_url})\n" if image_url else ""

    posts = []

    # ── POST 1: r/SideProject or r/IMadeThis ─────────────
    posts.append({
        "subreddit": "r/SideProject  OR  r/IMadeThis",
        "title": f"I built a free AI {asset_type} forecasting tool while working my 9-to-5 — {display} is showing {signal} today",
        "body": f"""Hey everyone! Been quietly working on this side project for a few months and finally feel like it's good enough to share.

I built **{SITE_NAME}** — a free AI tool that gives BULLISH/BEARISH/NEUTRAL signals for {'500+ US stocks & ETFs' if MODE=='stocks' else '500+ crypto pairs'}.{img_line}

**Today's {display} signal ({date_str}):**
- Current Price: ${last_close:,.2f}
- Signal: {signal_emoji} **{signal}**
- 7-Day Target: ${target_7d:,.2f} ({pct_7_str})
- 30-Day Target: ${target_30d:,.2f} ({pct_30_str})
- AI Accuracy: {acc_ma7:.1f}% (MA-7) | {acc_ma25:.1f}% (MA-25)

The AI runs multiple moving average models and generates a consensus signal with a confidence score. Built the backend in FastAPI, deployed on Railway.

**Try it free:** {SITE_URL}
*(3-day full trial, no credit card needed)*

Would genuinely love feedback from anyone here who trades — what would make this more useful for your workflow?"""
    })

    # ── POST 2: r/algotrading ─────────────────────────────
    posts.append({
        "subreddit": "r/algotrading",
        "title": f"Built a multi-model MA consensus forecasting tool — {display} showing {signal} {signal_emoji} | {date_str}",
        "body": f"""Been building this for a while and wanted to get the algotrading community's thoughts on the approach.

**The method:**
The tool runs MA-3, MA-7, MA-25 and VWAP models simultaneously on OHLCV data, then generates a consensus signal based on whether the majority of models agree on direction.{img_line}

**Today's {display} output:**
- Price: ${last_close:,.2f}
- Consensus Signal: {signal_emoji} **{signal}**
- MA-3 Accuracy: {acc_ma3:.1f}% | MA-7: {acc_ma7:.1f}% | MA-25: {acc_ma25:.1f}%
- 7D Target: ${target_7d:,.2f} ({pct_7_str})

Works on 1m, 5m, 15m, 1H, 4H, 1D timeframes.

Code is Python/FastAPI backend with a JS frontend. Live at {SITE_URL} if you want to test it.

Curious what people here think — is the consensus approach reasonable or am I missing something fundamental?"""
    })

    # ── POST 3: r/stocks or r/CryptoCurrency ─────────────
    if signal == "BULLISH":
        title3 = f"{display} — AI showing {signal_emoji} BULLISH signal, 7-day target ${target_7d:,.2f} ({pct_7_str}) | {date_str}"
    elif signal == "BEARISH":
        title3 = f"{display} — AI showing {signal_emoji} BEARISH signal, 7-day target ${target_7d:,.2f} ({pct_7_str}) | {date_str}"
    else:
        title3 = f"{display} — AI showing {signal_emoji} NEUTRAL, consolidating around ${last_close:,.2f} | {date_str}"

    posts.append({
        "subreddit": "r/stocks  OR  r/CryptoCurrency  OR  r/Daytrading",
        "title": title3,
        "body": f"""Been tracking {display} with an AI forecasting tool I built. Here's today's output:{img_line}

**{display} — {date_str}**
- Current: ${last_close:,.2f}
- Signal: {signal_emoji} **{signal}**
- 7-Day Target: ${target_7d:,.2f} ({pct_7_str})
- 30-Day Target: ${target_30d:,.2f} ({pct_30_str})
- Backtested Accuracy: {acc_ma7:.1f}%

What's your take on {display} right now? Does this align with your analysis?

*(Tool is free at {SITE_URL} if anyone wants to run their own signals — not financial advice)*"""
    })

    return posts


# ── PRINT OUTPUT ──────────────────────────────────────────
def print_output(posts, image_url, image_path):
    sep = "=" * 70

    print(f"\n{sep}")
    print("🎉  REDDIT POST GENERATOR — COPY & PASTE BELOW")
    print(sep)

    if image_url:
        print(f"\n📸 SCREENSHOT URL (use this as image when posting):")
        print(f"   {image_url}")
        print(f"\n   ➡️  When posting to Reddit:")
        print(f"       1. Click 'Images & Video' tab")
        print(f"       2. Upload the screenshot file directly")
        print(f"          OR paste the URL above as a link post")

    for i, post in enumerate(posts, 1):
        print(f"\n{sep}")
        print(f"📝  POST OPTION {i} — Best for: {post['subreddit']}")
        print(sep)
        print(f"\n🏷️  TITLE (copy this):")
        print(f"{'─'*50}")
        print(post['title'])
        print(f"{'─'*50}")
        print(f"\n📄  BODY (copy this):")
        print(f"{'─'*50}")
        print(post['body'])
        print(f"{'─'*50}")

    print(f"\n{sep}")
    print("📌  POSTING TIPS:")
    print(sep)
    print("""
1. r/SideProject & r/IMadeThis — BEST for low karma accounts ✅
   → These communities love solo builders, very welcoming
   → Post Option 1 works great here

2. r/algotrading — Good but needs some karma
   → Very technical community, Post Option 2 is perfect
   → Comment on other posts first to build karma

3. r/stocks / r/CryptoCurrency — Needs more karma (50+)
   → Use Post Option 3 once you have more karma
   → Always add "not financial advice" disclaimer

4. IMPORTANT RULES:
   → Don't post same content twice in one week
   → Always engage with comments after posting
   → Don't just drop link and leave — Reddit hates that
   → Read each subreddit's rules before posting
""")
    print(sep)


# ── SAVE SCREENSHOT AS ARTIFACT ───────────────────────────
def save_artifact(image_path):
    """Copy screenshot to output dir for GitHub Actions artifact"""
    if image_path and os.path.exists(image_path):
        import shutil
        os.makedirs('reddit_output', exist_ok=True)
        dest = f"reddit_output/chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        shutil.copy(image_path, dest)
        print(f"\n💾 Screenshot saved as artifact: {dest}")


# ── MAIN ──────────────────────────────────────────────────
def main():
    print("🚀 Reddit Post Generator Starting...")
    print(f"   Mode: {MODE.upper()} | Site: {SITE_URL}")

    # Pick symbol
    if SYMBOL:
        symbol = SYMBOL.upper()
    else:
        weights = [3, 3, 2, 2, 1, 1, 1, 1, 1, 1][:len(WATCHLIST)]
        symbol  = random.choices(WATCHLIST, weights=weights, k=1)[0]
    print(f"   Symbol: {symbol}")

    # Get forecast
    data = get_forecast(symbol, interval="1h")
    if not data:
        fallback = "NVDA" if MODE == "stocks" else "BTCUSDT"
        print(f"   Trying fallback: {fallback}")
        data = get_forecast(fallback, interval="1h")
        symbol = fallback
    if not data:
        print("❌ Could not get forecast data")
        return

    signal, signal_emoji = get_signal(data)
    print(f"   Signal: {signal_emoji} {signal}")

    # Take screenshot
    image_path = take_screenshot(symbol)
    image_url  = None
    if image_path:
        image_url, _ = upload_to_imgbb(image_path)
        save_artifact(image_path)

    # Generate posts
    posts = generate_posts(data, symbol, signal, signal_emoji, image_url)

    # Print everything
    print_output(posts, image_url, image_path)


if __name__ == "__main__":
    main()
