"""
Investleey + ZEUSVision Image Auto-Poster
Generates chart images and posts to Instagram + X
"""
import os, requests, random, io, json
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── CONFIG ────────────────────────────────────────────────
FB_TOKEN       = os.environ["FB_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID     = "103114287835428"
IG_ACCOUNT_ID  = os.environ.get("IG_ACCOUNT_ID", "")  # Instagram Business Account ID
X_API_KEY      = os.environ.get("X_API_KEY", "")
X_API_SECRET   = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET= os.environ.get("X_ACCESS_SECRET", "")

MODE = os.environ.get("POST_MODE", "stocks")  # stocks or crypto

if MODE == "crypto":
    API_URL   = "https://cryptovision-production-ca20.up.railway.app"
    API_TOKEN = "mycryptovision2025"
    SITE_URL  = "zeusvisions.com"
    WATCHLIST = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
                 "DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
    WEIGHTS   = [4,3,3,2,2,1,1,1,1,1]
else:
    API_URL   = "https://stockvision-production-ae61.up.railway.app"
    API_TOKEN = "mystockvision2025"
    SITE_URL  = "investleey.com"
    WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","GOOGL",
                 "META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
    WEIGHTS   = [3,3,3,3,2,2,2,2,1,1,1,1]

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
        print(f"Error: {r.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

# ── GENERATE CHART IMAGE ──────────────────────────────────
def generate_chart(data, symbol):
    last_close = data.get("last_close", 0)
    f_ma3  = data.get("forecast_ma3",  [last_close]*60)
    f_ma7  = data.get("forecast_ma7",  [last_close]*60)
    f_ma25 = data.get("forecast_ma25", [last_close]*60)
    f_vwap = data.get("forecast_vwap600", [last_close]*60)
    acc_ma3  = data.get("accuracy_ma3",  0)
    acc_ma7  = data.get("accuracy_ma7",  0)
    acc_ma25 = data.get("accuracy_ma25", 0)

    # Only show 30 days of forecast
    days = min(30, len(f_ma7))
    x = list(range(days))

    # Display symbol
    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
    else:
        display = symbol

    # Dark theme chart
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#0b0f1a')
    ax.set_facecolor('#131926')

    # Current price line
    ax.axhline(y=last_close, color='#607a99', linewidth=1, linestyle='--', alpha=0.5, label=f'Current: ${last_close:,.2f}')

    # Forecast lines
    ax.plot(x, f_ma3[:days],  color='#00d4ff', linewidth=2,   linestyle='--', label=f'MA-3  ({acc_ma3:.0f}%)')
    ax.plot(x, f_ma7[:days],  color='#0ecb81', linewidth=2.5, linestyle='-',  label=f'MA-7  ({acc_ma7:.0f}%)')
    ax.plot(x, f_ma25[:days], color='#f0b90b', linewidth=2,   linestyle='-',  label=f'MA-25 ({acc_ma25:.0f}%)')
    ax.plot(x, f_vwap[:days], color='#f6465d', linewidth=1.5, linestyle=':',  label=f'VWAP')

    # Fill between MA7 and current
    ax.fill_between(x, last_close, f_ma7[:days],
                    alpha=0.1,
                    color='#0ecb81' if f_ma7[days-1] >= last_close else '#f6465d')

    # End point dots
    ax.scatter([days-1], [f_ma7[days-1]],  color='#0ecb81', s=80, zorder=5)
    ax.scatter([days-1], [f_ma25[days-1]], color='#f0b90b', s=80, zorder=5)

    # Styling
    ax.tick_params(colors='#607a99', labelsize=9)
    ax.spines['bottom'].set_color('#1e2a40')
    ax.spines['top'].set_color('#1e2a40')
    ax.spines['left'].set_color('#1e2a40')
    ax.spines['right'].set_color('#1e2a40')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
    ax.set_xlabel('Days', color='#607a99', fontsize=9)
    ax.set_ylabel('Price (USD)', color='#607a99', fontsize=9)

    # Legend
    legend = ax.legend(loc='upper left', facecolor='#0b0f1a',
                       edgecolor='#1e2a40', labelcolor='#d0e0f0', fontsize=9)

    # Outlook
    pct_change = ((f_ma7[days-1] - last_close) / last_close) * 100
    outlook = "BULLISH 🟢" if pct_change >= 0.5 else "BEARISH 🔴" if pct_change <= -0.5 else "NEUTRAL ⚪"

    # Title
    fig.suptitle(f'{display} — 30-Day AI Forecast', color='#d0e0f0',
                 fontsize=16, fontweight='bold', y=0.98)

    # Subtitle info
    now = datetime.now(timezone.utc).strftime('%B %d, %Y')
    ax.set_title(f'Price: ${last_close:,.2f}  |  Outlook: {outlook}  |  {now}',
                 color='#607a99', fontsize=10, pad=10)

    # Watermark
    fig.text(0.99, 0.01, f'🌐 {SITE_URL}', ha='right', va='bottom',
             color='#344a66', fontsize=9, style='italic')

    # Grid
    ax.grid(color='#1e2a40', linewidth=0.5, alpha=0.7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#0b0f1a', edgecolor='none')
    buf.seek(0)
    plt.close()
    print(f"✅ Chart generated!")
    return buf

# ── POST IMAGE TO FACEBOOK ───────────────────────────────
def post_image_to_facebook(image_bytes, caption):
    try:
        # Upload photo to Facebook page
        url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
        image_bytes.seek(0)
        r = requests.post(url, files={'source': ('chart.png', image_bytes, 'image/png')},
            data={'caption': caption, 'access_token': FB_TOKEN}, timeout=60)
        print(f"FB Image Status: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ Image posted to Facebook! ID: {r.json().get('id','')}")
            return True
        print(f"❌ FB Image Error: {r.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return False

# ── POST TO INSTAGRAM ─────────────────────────────────────
def post_to_instagram(image_bytes, caption):
    if not IG_ACCOUNT_ID:
        print("⚠️ No Instagram Account ID set")
        return False
    try:
        # Step 1: Upload image as container
        upload_url = f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/media"
        # Need to host image publicly first - upload to Facebook
        files = {'file': ('chart.png', image_bytes, 'image/png')}
        r1 = requests.post(upload_url, data={
            'caption': caption,
            'access_token': FB_TOKEN,
            'image_url': ''  # Needs public URL
        })
        print(f"Instagram upload: {r1.status_code}")

        # Step 2: Publish container
        if r1.status_code == 200:
            container_id = r1.json().get('id')
            r2 = requests.post(
                f"https://graph.facebook.com/v21.0/{IG_ACCOUNT_ID}/media_publish",
                data={'creation_id': container_id, 'access_token': FB_TOKEN}
            )
            if r2.status_code == 200:
                print(f"✅ Posted to Instagram! ID: {r2.json().get('id')}")
                return True
        print(f"❌ Instagram error: {r1.text}")
    except Exception as e:
        print(f"❌ Instagram exception: {e}")
    return False

# ── POST TO X (TWITTER) ───────────────────────────────────
def post_to_x(image_bytes, text):
    if not X_API_KEY:
        print("⚠️ No X API credentials set")
        return False
    try:
        import tweepy
        # Text-only tweet (free tier)
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )
        r = client.create_tweet(text=text[:280])
        print(f"✅ Posted to X! ID: {r.data['id']}")
        return True
    except Exception as e:
        print(f"❌ X error: {e}")
    return False

# ── FORMAT CAPTIONS ───────────────────────────────────────
def format_caption(data, symbol):
    last_close = data.get("last_close", 0)
    f_ma7  = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)
    pct = ((f_ma7[6] - last_close) / last_close * 100) if last_close else 0
    outlook = "BULLISH 🟢" if pct >= 0.5 else "BEARISH 🔴" if pct <= -0.5 else "NEUTRAL ⚪"

    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
        tag = f"#{symbol.replace('USDT','')} #Crypto #Bitcoin #CryptoTrading"
        site = "zeusvisions.com"
    else:
        display = symbol
        tag = f"#{symbol} #Stocks #WallStreet #Investing"
        site = "investleey.com"

    caption = f"""📊 {display} AI Forecast
💰 Current: ${last_close:,.2f}
📌 Outlook: {outlook}
🎯 7-Day Target: ${f_ma7[6]:,.2f} ({'+' if pct>=0 else ''}{pct:.1f}%)
🤖 AI Accuracy: {acc_ma7:.1f}%

🌐 Full forecast at {site}
📱 Sign up FREE — 500+ {'crypto pairs' if MODE=='crypto' else 'stocks & ETFs'}

#AITrading #ZEUSVision {tag}"""
    return caption

# ── MAIN ──────────────────────────────────────────────────
def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Selected: {symbol}")

    data = get_forecast(symbol)
    if not data:
        backup = "BTCUSDT" if MODE == "crypto" else "AAPL"
        data = get_forecast(backup)
        symbol = backup
    if not data:
        print("❌ No data available")
        return

    # Generate chart
    chart = generate_chart(data, symbol)
    caption = format_caption(data, symbol)

    print(f"\nCaption preview:\n{caption[:200]}\n")

    # Post image to Facebook page
    chart.seek(0)
    post_image_to_facebook(chart, caption)

    # Post to Instagram (requires app review approval)
    # chart.seek(0)
    # post_to_instagram(chart, caption)

    # X posting disabled - requires paid plan ($100/month)
    # Uncomment when ready to upgrade
    # chart.seek(0)
    # post_to_x(chart, caption[:280])
    print("ℹ️ X posting skipped - upgrade to X Basic to enable")

if __name__ == "__main__":
    main()
