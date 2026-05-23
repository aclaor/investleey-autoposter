"""
TradingView Idea Generator for ZEUSVision & Investleey
Generates compelling trading ideas to post on TradingView.com
Run: python tradingview_helper.py
"""
import os, requests, random
from datetime import datetime, timezone

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CRYPTO_SITE   = "https://zeusvisions.com"
STOCK_SITE    = "https://investleey.com"

# ── CRYPTO SYMBOLS TO FEATURE ─────────────────────────────
CRYPTO_SYMBOLS = [
    ("BTCUSDT", "Bitcoin", "BINANCE"),
    ("ETHUSDT", "Ethereum", "BINANCE"),
    ("SOLUSDT", "Solana", "BINANCE"),
    ("BNBUSDT", "BNB", "BINANCE"),
    ("XRPUSDT", "XRP", "BINANCE"),
    ("ADAUSDT", "Cardano", "BINANCE"),
    ("DOGEUSDT", "Dogecoin", "BINANCE"),
    ("AVAXUSDT", "Avalanche", "BINANCE"),
    ("LINKUSDT", "Chainlink", "BINANCE"),
    ("DOTUSDT", "Polkadot", "BINANCE"),
]

# ── STOCK SYMBOLS TO FEATURE ──────────────────────────────
STOCK_SYMBOLS = [
    ("AAPL", "Apple", "NASDAQ"),
    ("MSFT", "Microsoft", "NASDAQ"),
    ("NVDA", "NVIDIA", "NASDAQ"),
    ("TSLA", "Tesla", "NASDAQ"),
    ("GOOGL", "Alphabet", "NASDAQ"),
    ("META", "Meta", "NASDAQ"),
    ("AMZN", "Amazon", "NASDAQ"),
    ("AMD", "AMD", "NASDAQ"),
    ("SPY", "S&P 500 ETF", "AMEX"),
    ("QQQ", "Nasdaq ETF", "NASDAQ"),
]

# ── FETCH LIVE FORECAST ───────────────────────────────────
def get_forecast(symbol, api_url, api_token, interval="1d"):
    try:
        r = requests.post(f"{api_url}/forecast",
            json={"symbol": symbol, "interval": interval},
            headers={"x-api-token": api_token, "Content-Type": "application/json"},
            timeout=60)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Forecast error: {e}")
    return None

# ── GENERATE IDEA TEXT ────────────────────────────────────
def generate_idea(symbol, name, exchange, data, site, mode):
    last_close = data.get("last_close", 0)
    f_ma7 = data.get("forecast_ma7", [last_close]*60)
    acc_ma7 = data.get("accuracy_ma7", 0)

    ma7_1h = f_ma7[0] if f_ma7 else last_close
    is_bullish = ma7_1h > last_close
    signal = "BULLISH" if is_bullish else "BEARISH"
    arrow = "📈" if is_bullish else "📉"

    pct_7 = ((f_ma7[6] - last_close) / last_close * 100) if last_close and len(f_ma7)>6 else 0
    target_7 = f_ma7[6] if len(f_ma7)>6 else last_close
    pct_sign = "+" if pct_7 >= 0 else ""

    asset_type = "crypto" if mode == "crypto" else "stock"

    # TradingView idea title (max 80 chars)
    title = f"{symbol} — AI Forecast: {signal} {arrow} | {pct_sign}{pct_7:.1f}% Target"

    # TradingView idea body
    body = f"""{arrow} {name} ({symbol}) — ZEUS-AI Forecast

Current Price: ${last_close:,.2f}
Signal: {signal}
7-Day Target: ${target_7:,.2f} ({pct_sign}{pct_7:.1f}%)
AI Confidence: {acc_ma7:.1f}%

Our proprietary AI has analyzed {symbol} across multiple timeframes and models to generate this forecast. The system evaluates price patterns, momentum, and volume to produce a consensus signal.

This is {"a bullish" if is_bullish else "a bearish"} setup based on current market conditions. {"Price momentum appears to be building upward." if is_bullish else "Price momentum suggests downward pressure."}

🔮 Want to see the full AI forecast chart?
Get your free 15-day trial at {site}
→ 500+ {asset_type}s covered
→ Multiple AI models
→ No credit card needed

━━━━━━━━━━━━━━━━━━━━
⚠️ This is not financial advice. Always do your own research before making any trading decisions. Past performance does not guarantee future results.
━━━━━━━━━━━━━━━━━━━━"""

    # Tags for TradingView
    if mode == "crypto":
        tags = f"{symbol.replace('USDT','')} Bitcoin Crypto AI MachineLearning Forecast {signal}"
    else:
        tags = f"{symbol} Stocks AI MachineLearning Forecast WallStreet {signal}"

    return title, body, tags, exchange

# ── MAIN ──────────────────────────────────────────────────
def main():
    CRYPTO_API = "https://cryptovision-production-ca20.up.railway.app"
    STOCK_API  = "https://stockvision-production-ae61.up.railway.app"
    CRYPTO_TOKEN = "mycryptovision2025"
    STOCK_TOKEN  = "mystockvision2025"

    print("=" * 65)
    print("📊 TRADINGVIEW IDEA GENERATOR")
    print("ZEUSVision & Investleey — Drive Trading Community Traffic")
    print("=" * 65)
    print()

    # Pick 2 crypto + 2 stock symbols
    crypto_picks = random.sample(CRYPTO_SYMBOLS, 2)
    stock_picks  = random.sample(STOCK_SYMBOLS, 2)

    print("🔮 CRYPTO IDEAS (post on TradingView for zeusvisions.com)")
    print("-" * 65)
    for sym, name, exchange in crypto_picks:
        print(f"\nFetching AI forecast for {sym}...")
        data = get_forecast(sym, CRYPTO_API, CRYPTO_TOKEN, "1d")
        if not data:
            print(f"  ⚠️  Could not fetch {sym}, skipping...")
            continue

        title, body, tags, exch = generate_idea(sym, name, exchange, data, CRYPTO_SITE, "crypto")

        print(f"\n{'='*65}")
        print(f"📌 TITLE (copy this):")
        print(f"   {title}")
        print(f"\n📝 BODY (copy this):")
        print("-" * 40)
        print(body)
        print("-" * 40)
        print(f"\n🏷️  TAGS: {tags}")
        print(f"📈 CHART: {exch}:{sym}")
        print(f"\n✅ HOW TO POST:")
        print(f"   1. Go to tradingview.com → 'Publish' → 'Publish idea'")
        print(f"   2. Open {exch}:{sym} chart first")
        print(f"   3. Paste title and body above")
        print(f"   4. Add tags: {tags[:50]}")
        print(f"   5. Set as 'Educational' or 'Analysis'")

    print()
    print("=" * 65)
    print("💹 STOCK IDEAS (post on TradingView for investleey.com)")
    print("-" * 65)
    for sym, name, exchange in stock_picks:
        print(f"\nFetching AI forecast for {sym}...")
        data = get_forecast(sym, STOCK_API, STOCK_TOKEN, "1d")
        if not data:
            print(f"  ⚠️  Could not fetch {sym}, skipping...")
            continue

        title, body, tags, exch = generate_idea(sym, name, exchange, data, STOCK_SITE, "stock")

        print(f"\n{'='*65}")
        print(f"📌 TITLE (copy this):")
        print(f"   {title}")
        print(f"\n📝 BODY (copy this):")
        print("-" * 40)
        print(body)
        print("-" * 40)
        print(f"\n🏷️  TAGS: {tags}")
        print(f"📈 CHART: {exch}:{sym}")
        print(f"\n✅ HOW TO POST:")
        print(f"   1. Go to tradingview.com → 'Publish' → 'Publish idea'")
        print(f"   2. Open {exch}:{sym} chart first")
        print(f"   3. Paste title and body above")
        print(f"   4. Add tags: {tags[:50]}")

    print()
    print("=" * 65)
    print("💡 TIPS FOR MORE VIEWS ON TRADINGVIEW:")
    print("   • Post 1-2 ideas per day for best reach")
    print("   • Always attach a chart screenshot")
    print("   • Use popular symbols (BTC, ETH, AAPL, NVDA)")
    print("   • Post when market opens (9:30 AM EST stocks)")
    print("   • Engage with comments to boost visibility")
    print("   • Follow other analysts to get followers back")
    print("=" * 65)

if __name__ == "__main__":
    main()
