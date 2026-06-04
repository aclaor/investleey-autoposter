"""
Investleey Instagram Auto-Poster
Generates forecast image and posts to @investleey_ai every 4 hours
"""
import os, requests, random, json, base64
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import io

# ── FULL CONFIG ───────────────────────────────────────────
import os as _os
MODE              = _os.environ.get("MODE", _os.environ.get("POST_MODE", "crypto"))
API_URL           = _os.environ.get("CRYPTO_API_URL", "") if MODE=="crypto" else _os.environ.get("STOCK_API_URL", "")
API_TOKEN         = _os.environ.get("CRYPTO_API_TOKEN", "") if MODE=="crypto" else _os.environ.get("STOCK_API_TOKEN", "")
FB_TOKEN          = _os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID        = _os.environ.get("FB_PAGE_ID", "103114287835428")
IG_USER_ID        = _os.environ.get("IG_USER_ID", "17841436490185424")
IMGBB_KEY         = _os.environ.get("IMGBB_API_KEY", "72e357126560d58d7ae925855456fd50")
DISCORD_BOT_TOKEN = _os.environ.get("DISCORD_BOT_TOKEN", "")
CHANNEL_ID        = _os.environ.get("DISCORD_CRYPTO_CHANNEL", "") if MODE=="crypto" else _os.environ.get("DISCORD_STOCK_CHANNEL", "")
HEADERS           = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
TG_BOT_TOKEN      = _os.environ.get("TELEGRAM_BOT_TOKEN_CRYPTO", "") if MODE=="crypto" else _os.environ.get("TELEGRAM_BOT_TOKEN_STOCKS", "")
TG_CHANNEL        = _os.environ.get("TELEGRAM_CRYPTO_CHANNEL", "") if MODE=="crypto" else _os.environ.get("TELEGRAM_STOCK_CHANNEL", "")
LI_TOKEN          = _os.environ.get("LI_ACCESS_TOKEN_CRYPTO", "") if MODE=="crypto" else _os.environ.get("LI_ACCESS_TOKEN_STOCKS", "")
LI_ORG_ID         = _os.environ.get("LI_ORG_ID_CRYPTO", "117744639") if MODE=="crypto" else _os.environ.get("LI_ORG_ID_STOCKS", "117924319")
LI_PERSON_ID      = _os.environ.get("LI_PERSON_ID", "")
YT_CLIENT_ID      = _os.environ.get("YOUTUBE_CLIENT_ID", "")
YT_CLIENT_SECRET  = _os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YT_REFRESH_TOKEN  = _os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
CRYPTO_WATCHLIST  = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","DOTUSDT"]
STOCK_WATCHLIST   = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","AMD","NFLX","JPM","SPY","QQQ"]
WATCHLIST         = CRYPTO_WATCHLIST if MODE=="crypto" else STOCK_WATCHLIST
WEIGHTS           = [3,3,2,2,2,1,1,1,1,1] if len(WATCHLIST)==10 else [3,3,3,2,2,2,1,1,1,1,1,1]
SITE_URL          = "https://zeusvisions.com" if MODE=="crypto" else "https://investleey.com"
SITE_NAME         = "ZeusVisions" if MODE=="crypto" else "Investleey"

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



def get_forecast(symbol, interval="1h"):
    print(f"Fetching forecast for {symbol}...")
    r = requests.post(
        f"{API_URL}/forecast",
        json={"symbol": symbol, "interval": interval},
        headers={"x-api-token": API_TOKEN},
        timeout=120
    )
    if r.status_code == 200:
        return r.json()
    print(f"Error: {r.status_code} {r.text[:200]}")
    return None

# ── GENERATE IMAGE ────────────────────────────────────────
def generate_image(data, symbol, interval="1h"):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color="#060810")
    draw = ImageDraw.Draw(img)

    # Try to load fonts, fall back to default
    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 72)
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 44)
        font_sm    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
        font_xs    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 26)
    except:
        font_big = font_med = font_sm = font_xs = ImageFont.load_default()

    # Colors
    GREEN  = "#0ecb81"
    RED    = "#f6465d"
    YELLOW = "#f0b90b"
    CYAN   = "#00ffff"
    GRAY   = "#607a99"
    WHITE  = "#d0e0f0"
    DARK   = "#0b0f1a"
    BORDER = "#1e2a40"

    # Background gradient effect
    for i in range(H):
        alpha = int(i / H * 20)
        draw.line([(0, i), (W, i)], fill=f"#{alpha:02x}{alpha+5:02x}{alpha+20:02x}")

    # Top border line
    draw.rectangle([0, 0, W, 6], fill=CYAN)

    # Logo area
    draw.rectangle([30, 20, 330, 70], fill=DARK, outline=BORDER, width=2)
    draw.text((45, 28), "INVESTLEEY", font=font_xs, fill=CYAN)

    # Date/time
    now = datetime.now(timezone.utc)
    dt_str = now.strftime("%b %d, %Y  %H:%M UTC")
    draw.text((W-350, 28), dt_str, font=font_xs, fill=GRAY)

    # Symbol
    draw.text((W//2, 130), symbol, font=font_big, fill=WHITE, anchor="mm")

    # Current price
    last_close = data.get("last_close", 0)
    price_str = f"${last_close:,.2f}"
    draw.text((W//2, 220), price_str, font=font_med, fill=YELLOW, anchor="mm")

    # Signal
    fc200 = data.get("forecast_vwap200", [])
    signal = "NEUTRAL ●"
    sig_color = GRAY
    if fc200 and len(fc200) >= 3:
        first, last = fc200[0], fc200[-1]
        threshold = (last_close or first) * 0.001
        interval = "1h"
        _sn, _se, _sa = get_signal(data, interval)
        signal = _sn + " " + _sa
        sig_color = GREEN if _sn == "BULLISH" else (RED if _sn == "BEARISH" else GRAY)

    # Signal box
    draw.rounded_rectangle([W//2-180, 255, W//2+180, 315], radius=12, fill=DARK, outline=sig_color, width=3)
    draw.text((W//2, 285), signal, font=font_sm, fill=sig_color, anchor="mm")

    # Divider
    draw.line([(60, 340), (W-60, 340)], fill=BORDER, width=2)

    # Forecast targets
    f_ma7  = data.get("forecast_ma7", [])
    f_ma25 = data.get("forecast_ma25", [])
    acc_ma7  = data.get("accuracy_ma7", 0)
    acc_ma25 = data.get("accuracy_ma25", 0)

    def pct(current, future):
        if not future or current == 0: return 0.0
        return ((future - current) / current) * 100

    def fmt_pct(val):
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.2f}%"

    def pct_color(val):
        return GREEN if val >= 0 else RED

    y = 370
    rows = []
    if f_ma7:
        t7  = f_ma7[6]  if len(f_ma7) > 6  else last_close
        t30 = f_ma7[29] if len(f_ma7) > 29 else last_close
        rows.append(("7-Day Target",  f"${t7:,.2f}",  fmt_pct(pct(last_close, t7)),  pct(last_close, t7)))
        rows.append(("30-Day Target", f"${t30:,.2f}", fmt_pct(pct(last_close, t30)), pct(last_close, t30)))
    if f_ma25:
        t25 = f_ma25[29] if len(f_ma25) > 29 else last_close
        rows.append(("MA-25 Target",  f"${t25:,.2f}", fmt_pct(pct(last_close, t25)), pct(last_close, t25)))

    for label, price, chg, chg_val in rows:
        draw.rectangle([60, y, W-60, y+70], fill=DARK, outline=BORDER, width=1)
        draw.text((90, y+18), label, font=font_xs, fill=GRAY)
        draw.text((W//2, y+18), price, font=font_xs, fill=WHITE, anchor="lm")
        draw.text((W-90, y+18), chg, font=font_xs, fill=pct_color(chg_val), anchor="rm")
        y += 80

    # Accuracy
    draw.line([(60, y+10), (W-60, y+10)], fill=BORDER, width=2)
    y += 30
    draw.text((W//2, y), f"AI Accuracy: {acc_ma7:.1f}%", font=font_sm, fill=GREEN, anchor="mm")
    y += 55

    # CTA box
    draw.rounded_rectangle([60, y, W-60, y+110], radius=16,
                            fill="#0ecb8120", outline=GREEN, width=3)
    draw.text((W//2, y+28), "🚀 FREE AI Stock Forecasts", font=font_sm, fill=GREEN, anchor="mm")
    draw.text((W//2, y+68), "investleey.com", font=font_med, fill=CYAN, anchor="mm")

    # Bottom border
    draw.rectangle([0, H-6, W, H], fill=YELLOW)

    # Save to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.getvalue()

# ── UPLOAD TO IMGBB ───────────────────────────────────────
def upload_image(image_bytes):
    print("Uploading image to imgbb...")
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_KEY, "image": b64},
        timeout=30
    )
    if r.status_code == 200:
        url = r.json()["data"]["url"]
        print(f"✅ Image uploaded: {url}")
        return url
    print(f"❌ imgbb error: {r.status_code} {r.text[:200]}")
    return None

# ── POST TO INSTAGRAM ─────────────────────────────────────
def post_to_instagram(image_url, caption):
    print("Posting to Instagram...")

    # Step 1: Create media container
    r1 = requests.post(
        f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": FB_TOKEN
        },
        timeout=30
    )
    if r1.status_code != 200:
        print(f"❌ Container error: {r1.status_code} {r1.text[:200]}")
        return False

    container_id = r1.json().get("id")
    print(f"✅ Container created: {container_id}")

    # Step 2: Publish
    import time
    time.sleep(3)
    r2 = requests.post(
        f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": FB_TOKEN
        },
        timeout=30
    )
    if r2.status_code == 200:
        post_id = r2.json().get("id")
        print(f"✅ Posted to Instagram! Post ID: {post_id}")
        return True

    print(f"❌ Publish error: {r2.status_code} {r2.text[:200]}")
    return False

# ── FORMAT CAPTION ────────────────────────────────────────
def format_caption(data, symbol, interval="1h"):
    last_close = data.get("last_close", 0)
    signal_name, signal_emoji, signal_arrow = get_signal(data, "1h")
    signal = f"{signal_name} {signal_arrow}"

    acc = data.get("accuracy_ma7", 0)
    now = datetime.now(timezone.utc)

    return f"""📊 {symbol} AI Forecast — {now.strftime("%b %d, %Y")}

💰 Price: ${last_close:,.2f}
📌 Signal: {signal}
🎯 Accuracy: {acc:.1f}%

🤖 Powered by ZEUS-AI — Our proprietary AI analyzes price action, volume, and trend data to generate forecasts.

🚀 Get FREE AI forecasts for 500+ stocks at investleey.com

#Investleey #StockForecast #{symbol} #AITrading #StockMarket #Investing #WallStreet #StockAnalysis #TradingSignals #AIStock"""

# ── MAIN ──────────────────────────────────────────────────
def main():
    weights = [max(1, 3-i//3) for i in range(len(WATCHLIST))]
    symbol = random.choices(WATCHLIST, weights=weights, k=1)[0]
    print(f"Selected: {symbol}")

    data = get_forecast(symbol)
    if not data:
        symbol = "AAPL"
        data = get_forecast(symbol)
    if not data:
        print("❌ Could not get forecast. Exiting.")
        return

    # Generate image
    image_bytes = generate_image(data, symbol, interval="1h")
    print(f"✅ Image generated ({len(image_bytes):,} bytes)")

    # Upload to imgbb
    image_url = upload_image(image_bytes)
    if not image_url:
        print("❌ Failed to upload image.")
        return

    # Format caption
    caption = format_caption(data, symbol, interval="1h")
    print("\n--- CAPTION PREVIEW ---")
    print(caption)
    print("--- END ---\n")

    # Post to Instagram
    success = post_to_instagram(image_url, caption)
    if success:
        print(f"✅ Successfully posted {symbol} forecast to Instagram!")
    else:
        print("❌ Failed to post to Instagram.")

if __name__ == "__main__":
    main()
