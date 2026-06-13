"""
Reddit Post Generator for Investleey + ZeusVisions
Generates human-sounding Reddit posts with screenshots.
"""
import os, random, subprocess, base64, requests
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────
MODE       = os.environ.get("MODE", "stocks")
API_URL    = os.environ.get("STOCK_API_URL", "https://stockvision-production-ae61.up.railway.app") if MODE=="stocks" else os.environ.get("CRYPTO_API_URL", "https://cryptovision-production-ca20.up.railway.app")
API_TOKEN  = os.environ.get("STOCK_API_TOKEN", "") if MODE=="stocks" else os.environ.get("CRYPTO_API_TOKEN", "")
IMGBB_KEY  = os.environ.get("IMGBB_API_KEY", "72e357126560d58d7ae925855456fd50")
SITE_URL   = "https://investleey.com" if MODE=="stocks" else "https://zeusvisions.com"
SITE_NAME  = "Investleey" if MODE=="stocks" else "ZeusVisions"
SYMBOL     = os.environ.get("SYMBOL", "")

STOCK_WATCHLIST  = ["NVDA","AAPL","TSLA","MSFT","GOOGL","META","AMZN","AMD","SPY","QQQ"]
CRYPTO_WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
WATCHLIST        = STOCK_WATCHLIST if MODE=="stocks" else CRYPTO_WATCHLIST


def get_forecast(symbol, interval="1h"):
    print(f"Fetching {symbol}...")
    try:
        r = requests.post(f"{API_URL}/forecast",
            json={"symbol": symbol, "interval": interval},
            headers={"x-api-token": API_TOKEN}, timeout=120)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error: {e}")
    return None


def get_signal(data):
    fma7 = data.get("forecast_ma7", [])
    fma3 = data.get("forecast_ma3", [])
    if fma7 and len(fma7)>=5 and fma3 and len(fma3)>=5:
        if fma7[0]<fma7[4] and fma3[0]<fma3[4]: return "BULLISH","📈"
        elif fma7[0]>fma7[4] and fma3[0]>fma3[4]: return "BEARISH","📉"
    return "NEUTRAL","➡️"


def take_screenshot(symbol):
    print(f"Taking screenshot...")
    js = """
const { chromium } = require('/home/runner/work/investleey-autoposter/investleey-autoposter/node_modules/playwright');
(async () => {
  const symbol = process.argv[2], site = process.argv[3];
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
  } catch(e) {}
  await page.waitForTimeout(4000);
  try {
    const el = await page.$('#tv-chart');
    if (el) await el.screenshot({ path: '/tmp/reddit_chart.png' });
    else await page.screenshot({ path: '/tmp/reddit_chart.png', clip: { x:220, y:80, width:860, height:540 } });
  } catch(e) { await page.screenshot({ path: '/tmp/reddit_chart.png' }); }
  await browser.close();
})();
"""
    with open('/tmp/ss.js','w') as f: f.write(js)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(['node','/tmp/ss.js', symbol, SITE_URL],
        capture_output=True, text=True, timeout=120,
        cwd=project_dir,
        env={**os.environ, 'NODE_PATH': f'{project_dir}/node_modules'})
    if os.path.exists('/tmp/reddit_chart.png'):
        print("Screenshot done!")
        return '/tmp/reddit_chart.png'
    return None


def upload_imgbb(path):
    try:
        with open(path,"rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        r = requests.post("https://api.imgbb.com/1/upload",
            data={"key": IMGBB_KEY, "image": b64}, timeout=30)
        if r.status_code == 200:
            url = r.json()["data"]["url"]
            print(f"Uploaded: {url}")
            return url
    except Exception as e:
        print(f"Upload error: {e}")
    return None


def generate_posts(data, symbol, signal, emoji, image_url):
    price   = data.get("last_close", 0)
    acc7    = data.get("accuracy_ma7", 0)
    acc25   = data.get("accuracy_ma25", 0)
    fma7    = data.get("forecast_ma7", [])
    t7      = fma7[6]  if len(fma7)>6  else price
    t30     = fma7[29] if len(fma7)>29 else price
    pct7    = ((t7-price)/price*100) if price else 0
    pct30   = ((t30-price)/price*100) if price else 0
    p7s     = f"+{pct7:.1f}%" if pct7>=0 else f"{pct7:.1f}%"
    p30s    = f"+{pct30:.1f}%" if pct30>=0 else f"{pct30:.1f}%"
    display = symbol.replace("USDT","/USDT") if MODE=="crypto" else symbol
    img     = f"\n\n[Chart]({image_url})\n" if image_url else ""
    dow     = datetime.now().strftime("%A")
    asset   = "crypto" if MODE=="crypto" else "stock"

    # ── Vary openers so posts don't look templated ────────
    openers_sideproject = [
        f"so i've been working on this thing for the past few months while doing my day job and i think it's finally at a point where i can share it",
        f"been lurking here forever, finally have something worth posting about",
        f"not sure if this belongs here but figured this community would appreciate it more than most",
        f"ok so this started as a weekend project and kind of got out of hand lol",
    ]

    openers_algo = [
        f"wanted to get some feedback on a forecasting approach i've been working on",
        f"been building this in my spare time, curious what people who actually know what they're doing think",
        f"throwing this out there for critique — be brutal, i can take it",
        f"built something i've been wanting for ages and figured someone here might find it interesting",
    ]

    openers_discuss = [
        f"been tracking {display} with a tool i built — sharing for anyone who's interested",
        f"my ai model is flagging {display} today, posting for discussion",
        f"ran my forecasting tool on {display} this morning, here's what came out",
        f"for what it's worth, here's what my model is showing on {display} right now",
    ]

    o1 = random.choice(openers_sideproject)
    o2 = random.choice(openers_algo)
    o3 = random.choice(openers_discuss)

    # ── Vary signal descriptions ──────────────────────────
    if signal == "BULLISH":
        signal_desc = [
            f"it's calling {display} bullish right now",
            f"model is leaning bullish on {display}",
            f"pointing up on {display} — make of that what you will",
        ]
    elif signal == "BEARISH":
        signal_desc = [
            f"it's flagging {display} as bearish",
            f"model is bearish on {display} currently",
            f"not looking great for {display} according to the model",
        ]
    else:
        signal_desc = [
            f"showing neutral on {display} — basically saying wait and see",
            f"{display} is consolidating according to the model",
            f"model can't make up its mind on {display} lol",
        ]
    sdesc = random.choice(signal_desc)

    posts = []

    # ── POST 1: r/SideProject / r/IMadeThis ──────────────
    posts.append({
        "subreddit": "r/SideProject  or  r/IMadeThis  ← BEST for low karma!",
        "title": random.choice([
            f"built a free ai {asset} forecasting tool in my spare time — {sdesc}",
            f"side project update: my ai {asset} tool {sdesc} ({display} today)",
            f"spent way too many weekends on this — free ai {asset} forecaster, {sdesc}",
        ]),
        "body": f"""{o1}

i built {SITE_NAME}, a free tool that gives bull/bear signals for {'500+ stocks' if MODE=='stocks' else '500+ crypto pairs'}. it uses multiple moving average models and spits out a consensus signal with a confidence score.{img}

here's what it's showing on {display} right now:
price: ${price:,.2f}
signal: {emoji} {signal.lower()} 
7 day target: ${t7:,.2f} ({p7s})
30 day target: ${t30:,.2f} ({p30s})
accuracy on backtesting: {acc7:.0f}% (ma7) / {acc25:.0f}% (ma25)

it's free to try — 3 days unlimited, no credit card or anything: {SITE_URL}

honestly just want to know if this is actually useful or if i'm the only one who would use something like this lol. what would you change?"""
    })

    # ── POST 2: r/algotrading ────────────────────────────
    posts.append({
        "subreddit": "r/algotrading",
        "title": random.choice([
            f"consensus MA forecasting on {display} — {signal.lower()} signal, feedback welcome",
            f"my multi-model MA tool is showing {signal.lower()} on {display} — is this approach sound?",
            f"built a MA consensus model, curious what algotraders think of the output on {display}",
        ]),
        "body": f"""{o2}

the basic idea: run MA-3, MA-7, MA-25 and VWAP forecasts in parallel, then check if 3 out of 4 agree on direction. if they do, it's a signal. if not, neutral.{img}

{display} right now:
${price:,.2f} current
{emoji} {signal.lower()} signal  
7d: ${t7:,.2f} ({p7s})
MA7 backtest accuracy: {acc7:.1f}%
MA25 backtest accuracy: {acc25:.1f}%

works across 1m to 1d timeframes. built in fastapi, live at {SITE_URL} if you want to poke at it

main thing i'm not sure about: is consensus across MAs actually meaningful or am i just averaging noise? curious what people here think"""
    })

    # ── POST 3: r/stocks / r/CryptoCurrency ──────────────
    if signal == "BULLISH":
        t3 = random.choice([
            f"{display} looking bullish according to my model — anyone else seeing this?",
            f"my ai is saying {display} is a buy right now — thoughts?",
            f"{display} — model flagging bullish {dow}, 7d target {p7s}",
        ])
    elif signal == "BEARISH":
        t3 = random.choice([
            f"{display} bearish signal on my model today — anyone else cautious?",
            f"my tool is flagging {display} as bearish — curious if others agree",
            f"{display} — model showing bearish {dow}, 7d target {p7s}",
        ])
    else:
        t3 = random.choice([
            f"{display} neutral/consolidating on my model — waiting for a clearer signal",
            f"my ai can't decide on {display} today lol — neutral signal",
            f"{display} — model showing neutral {dow}, range bound",
        ])

    posts.append({
        "subreddit": f"r/{'stocks' if MODE=='stocks' else 'CryptoCurrency'}  or  r/Daytrading",
        "title": t3,
        "body": f"""{o3}{img}

{display} — {datetime.now().strftime("%b %d")}:
${price:,.2f}
{emoji} {signal.lower()}
7d target: ${t7:,.2f} ({p7s})

what are you guys seeing on {display}? curious if this lines up with anyone else's analysis

*(running this through a tool i built — {SITE_URL} if curious, it's free. not financial advice obviously)*"""
    })

    return posts


def print_output(posts, image_url):
    sep = "="*65
    print(f"\n{sep}")
    print("✅  REDDIT POSTS READY — COPY AND PASTE")
    print(sep)

    if image_url:
        print(f"\n📸  SCREENSHOT LINK:")
        print(f"    {image_url}")
        print(f"    Download from artifacts below OR use this link in your post")

    for i, post in enumerate(posts, 1):
        print(f"\n{sep}")
        print(f"OPTION {i}   {post['subreddit']}")
        print(sep)
        print(f"\nTITLE:\n{post['title']}")
        print(f"\nBODY:\n{post['body']}")

    print(f"\n{sep}")
    print("TIPS FOR LOW KARMA ACCOUNTS:")
    print(sep)
    print("""
Start with r/SideProject or r/IMadeThis (Option 1)
  These accept ANY karma level and love builders

After posting, stick around and reply to comments
  Don't just post and disappear — Reddit hates that

Wait 2-3 days between posts on different subreddits
  Don't post all 3 on the same day

Tweak the post slightly before each one
  Change a few words so it doesn't look copy-pasted

r/algotrading and r/stocks need ~50 karma first
  Comment on other posts this week to build it up
""")
    print(sep)


def save_artifact(path):
    if path and os.path.exists(path):
        import shutil
        os.makedirs('reddit_output', exist_ok=True)
        dest = f"reddit_output/chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        shutil.copy(path, dest)
        print(f"Screenshot artifact: {dest}")


def main():
    print(f"Mode: {MODE} | Site: {SITE_URL}")
    symbol = SYMBOL.upper() if SYMBOL else random.choices(
        WATCHLIST, weights=[3,3,2,2,1,1,1,1,1,1][:len(WATCHLIST)], k=1)[0]
    print(f"Symbol: {symbol}")

    data = get_forecast(symbol)
    if not data:
        fb = "NVDA" if MODE=="stocks" else "BTCUSDT"
        data = get_forecast(fb)
        symbol = fb
    if not data:
        print("No forecast data")
        return

    signal, emoji = get_signal(data)
    print(f"Signal: {emoji} {signal}")

    image_path = take_screenshot(symbol)
    image_url  = upload_imgbb(image_path) if image_path else None
    save_artifact(image_path)

    posts = generate_posts(data, symbol, signal, emoji, image_url)
    print_output(posts, image_url)


if __name__ == "__main__":
    main()
