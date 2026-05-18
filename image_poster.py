"""
Investleey + ZEUSVision Image Auto-Poster
Generates candlestick chart images and posts to Facebook
"""
import os, requests, random, io
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── CONFIG ────────────────────────────────────────────────
FB_TOKEN   = os.environ["FB_PAGE_ACCESS_TOKEN"]
FB_PAGE_ID = "103114287835428"
MODE = os.environ.get("POST_MODE", "stocks")

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
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        print(f"Error: {r.text[:100]}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

# ── GENERATE CANDLESTICK CHART ────────────────────────────
def generate_chart(data, symbol):
    last_close = float(data.get("last_close", 0))
    candles    = data.get("candles", [])
    f_ma3  = data.get("forecast_ma3",     [last_close]*60)
    f_ma7  = data.get("forecast_ma7",     [last_close]*60)
    f_ma25 = data.get("forecast_ma25",    [last_close]*60)
    f_vwap = data.get("forecast_vwap600", [last_close]*60)
    acc_ma3  = data.get("accuracy_ma3",  0)
    acc_ma7  = data.get("accuracy_ma7",  0)
    acc_ma25 = data.get("accuracy_ma25", 0)

    display = symbol.replace("USDT", "/USDT") if MODE == "crypto" else symbol

    # Use last 100 candles
    hist = candles[-100:] if len(candles) >= 100 else candles
    n_hist = len(hist)
    n_fore = min(30, len(f_ma7))
    x_fore = list(range(n_hist, n_hist + n_fore))

    # Extract OHLC
    opens  = [float(c['o']) for c in hist]
    highs  = [float(c['h']) for c in hist]
    lows   = [float(c['l']) for c in hist]
    closes = [float(c['c']) for c in hist]

    # Price range for ylim
    all_prices = highs + lows + [v for v in f_ma7[:n_fore] if v]
    price_min = min(all_prices) * 0.995
    price_max = max(all_prices) * 1.005

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#0b0f1a')
    ax.set_facecolor('#131926')
    ax.set_ylim(price_min, price_max)
    ax.set_xlim(-1, n_hist + n_fore + 1)

    # ── Draw candlesticks ──
    for i in range(n_hist):
        o, h, l, cl = opens[i], highs[i], lows[i], closes[i]
        up = cl >= o
        color = '#0ecb81' if up else '#f6465d'
        # Wick
        ax.plot([i, i], [l, h], color=color, linewidth=0.8, zorder=2)
        # Body
        body_bot = min(o, cl)
        body_top = max(o, cl)
        body_h = max(body_top - body_bot, last_close * 0.0005)
        rect = plt.Rectangle((i - 0.35, body_bot), 0.7, body_h,
                              color=color, zorder=3)
        ax.add_patch(rect)

    # ── Divider ──
    ax.axvline(x=n_hist - 0.5, color='#344a66', linewidth=1.5,
               linestyle='--', alpha=0.9, zorder=4)
    ax.text(n_hist + 0.3, price_max * 0.999, 'AI FORECAST →',
            color='#344a66', fontsize=8, va='top', zorder=5,
            fontfamily='monospace')

    # ── Forecast lines ──
    ax.plot(x_fore, f_ma3[:n_fore],  color='#00d4ff', linewidth=1.8,
            linestyle='--', label=f'MA-3 ({acc_ma3:.0f}%)', zorder=4)
    ax.plot(x_fore, f_ma7[:n_fore],  color='#0ecb81', linewidth=2.5,
            linestyle='-',  label=f'MA-7 ({acc_ma7:.0f}%)', zorder=4)
    ax.plot(x_fore, f_ma25[:n_fore], color='#f0b90b', linewidth=2.0,
            linestyle='-',  label=f'MA-25 ({acc_ma25:.0f}%)', zorder=4)
    ax.plot(x_fore, f_vwap[:n_fore], color='#a855f7', linewidth=1.5,
            linestyle=':',  label='VWAP', zorder=4)

    # Fill forecast
    ax.fill_between(x_fore, last_close, f_ma7[:n_fore], alpha=0.08,
                    color='#0ecb81' if f_ma7[n_fore-1] >= last_close else '#f6465d')

    # End dots
    ax.scatter([x_fore[-1]], [f_ma7[n_fore-1]],  color='#0ecb81', s=80, zorder=6)
    ax.scatter([x_fore[-1]], [f_ma25[n_fore-1]], color='#f0b90b', s=80, zorder=6)

    # ── Styling ──
    ax.tick_params(colors='#607a99', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#1e2a40')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f'${v:,.2f}'))
    ax.set_xticks([])
    ax.grid(color='#1e2a40', linewidth=0.4, alpha=0.5, axis='y')
    ax.legend(loc='upper left', facecolor='#0b0f1a',
              edgecolor='#1e2a40', labelcolor='#d0e0f0', fontsize=9)

    # ── Title ──
    pct = ((f_ma7[n_fore-1] - last_close) / last_close) * 100
    outlook = "BULLISH" if pct >= 0.5 else "BEARISH" if pct <= -0.5 else "NEUTRAL"
    o_color = '#0ecb81' if pct >= 0.5 else '#f6465d' if pct <= -0.5 else '#607a99'
    now = datetime.now(timezone.utc).strftime('%b %d, %Y')

    fig.text(0.02, 0.97, f'{display}', ha='left', va='top',
             color='#d0e0f0', fontsize=18, fontweight='bold')
    fig.text(0.02, 0.91, f'${last_close:,.2f}', ha='left', va='top',
             color='#d0e0f0', fontsize=14)
    fig.text(0.98, 0.97, outlook, ha='right', va='top',
             color=o_color, fontsize=14, fontweight='bold')
    fig.text(0.02, 0.02, f'100 Candles + 30-Day Forecast  |  {now}',
             ha='left', va='bottom', color='#607a99', fontsize=8)
    fig.text(0.98, 0.02, SITE_URL, ha='right', va='bottom',
             color='#0ecb81', fontsize=9)

    plt.tight_layout(rect=[0, 0.04, 1, 0.89])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#0b0f1a', edgecolor='none')
    buf.seek(0)
    plt.close()
    print(f"Chart generated! Candles: {n_hist}, Forecast: {n_fore}")
    return buf

# ── POST IMAGE TO FACEBOOK ────────────────────────────────
def post_image_to_facebook(image_bytes, caption):
    try:
        url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
        image_bytes.seek(0)
        r = requests.post(url,
            files={'source': ('chart.png', image_bytes, 'image/png')},
            data={'caption': caption, 'access_token': FB_TOKEN}, timeout=60)
        print(f"FB Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Posted! ID: {r.json().get('id','')}")
            return True
        print(f"FB Error: {r.text}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

# ── FORMAT CAPTION ────────────────────────────────────────
def format_caption(data, symbol):
    last_close = data.get("last_close", 0)
    f_ma7  = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)
    pct = ((f_ma7[6] - last_close) / last_close * 100) if last_close else 0
    outlook = "BULLISH" if pct >= 0.5 else "BEARISH" if pct <= -0.5 else "NEUTRAL"

    if MODE == "crypto":
        display = symbol.replace("USDT", "/USDT")
        tag = f"#{symbol.replace('USDT','')} #Crypto #Bitcoin #CryptoTrading"
        site = "zeusvisions.com"
    else:
        display = symbol
        tag = f"#{symbol} #Stocks #WallStreet #Investing"
        site = "investleey.com"

    return f"""📊 {display} AI Forecast
💰 Current: ${last_close:,.2f}
📌 Outlook: {outlook}
🎯 7-Day Target: ${f_ma7[6]:,.2f} ({'+' if pct>=0 else ''}{pct:.1f}%)
🤖 AI Accuracy: {acc_ma7:.1f}%

🌐 Full forecast at {site}
📱 Sign up FREE — 500+ {'crypto pairs' if MODE=='crypto' else 'stocks & ETFs'}

#AITrading #ZEUSVision {tag}"""

# ── MAIN ──────────────────────────────────────────────────
def main():
    symbol = random.choices(WATCHLIST, weights=WEIGHTS, k=1)[0]
    print(f"Mode: {MODE} | Symbol: {symbol}")

    data = get_forecast(symbol)
    if not data:
        backup = "BTCUSDT" if MODE == "crypto" else "AAPL"
        data = get_forecast(backup)
        symbol = backup
    if not data:
        print("No data available")
        return

    chart   = generate_chart(data, symbol)
    caption = format_caption(data, symbol)
    print(caption[:200])
    post_image_to_facebook(chart, caption)

if __name__ == "__main__":
    main()
