"""
Quora Answer Generator for ZEUSVision & Investleey
Finds relevant questions and generates AI-powered answers
Run: python quora_helper.py
"""
import os, requests, random, json
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CRYPTO_SITE   = "https://zeusvisions.com"
STOCK_SITE    = "https://investleey.com"

# ── RELEVANT QUORA QUESTIONS TO TARGET ────────────────────
CRYPTO_QUESTIONS = [
    "What is the best AI tool for crypto price prediction?",
    "Can AI predict Bitcoin price accurately?",
    "How do I know when to buy or sell crypto?",
    "What are the best crypto trading signals?",
    "Is there a free crypto forecasting tool?",
    "How does AI predict cryptocurrency prices?",
    "What is the most accurate crypto prediction site?",
    "Can machine learning predict stock and crypto prices?",
    "What tools do professional crypto traders use?",
    "How do I get started with crypto trading?",
    "What is the best way to analyze crypto charts?",
    "Are there any AI-powered crypto bots that actually work?",
    "How accurate are crypto price predictions?",
    "How does AI help with crypto trading?",
    "How do I predict Ethereum price movement?",
]

STOCK_QUESTIONS = [
    "What is the best AI tool for stock price prediction?",
    "Can AI predict stock market movements accurately?",
    "How do I know when to buy or sell stocks?",
    "What are the best stock trading signals?",
    "Is there a free stock forecasting tool?",
    "How does AI predict stock prices?",
    "What is the most accurate stock prediction website?",
    "What tools do professional stock traders use?",
    "How do I get started with stock trading?",
    "What is the best way to analyze stock charts?",
    "How do I predict NVDA or AAPL price movement?",
    "What is VWAP in trading?",
    "How do I use moving averages for trading?",
    "What is the best way to analyze penny stocks?",
    "How do I find the best stocks to buy today?",
]

# ── ANSWER TEMPLATES (NO API NEEDED) ─────────────────────
CRYPTO_TEMPLATES = [
    """Great question! I've been using **ZEUS-AI** at {site} for crypto forecasting and the results have been impressive.

Here's what makes it stand out:

**How it works:**
- Uses proprietary AI models trained on massive amounts of market data
- Uses multiple AI models that analyze price patterns simultaneously
- Provides 60-bar ahead forecasts with accuracy scores (95-99%+)
- Works on 500+ crypto pairs including BTC, ETH, SOL, BNB

**What I like:**
- Shows BULLISH/BEARISH signals with confidence scores
- Works on multiple timeframes (1m, 5m, 15m, 1H, 4H, 1D)
- Free 15-day trial, no credit card needed
- Live market data from major exchanges

I use it alongside my own analysis and it's helped me time entries much better. The 1H and 4H forecasts are particularly useful.

Try it free at {site} — they have a 15-day trial so you can test it yourself.

*Disclaimer: Always do your own research. AI forecasts are tools to assist decision-making, not financial advice.*""",

    """I've tested several AI crypto prediction tools and **ZEUS-AI** ({site}) gives the most detailed analysis I've found.

What sets it apart from basic prediction sites:

1. **Multiple AI models** — Not just one algorithm but multiple AI models that cross-validate each other
2. **Accuracy transparency** — Shows you the actual backtested accuracy % so you know how reliable each signal is
3. **Live chart integration** — See the AI forecast lines overlaid directly on candlestick charts
4. **500+ pairs** — Not just BTC/ETH, covers altcoins, DeFi tokens, and major pairs

The BULLISH/BEARISH signal updates in real-time based on the 1-hour MA-7 direction, which is great for swing trading.

Free trial at {site} — worth testing for yourself.""",
]

STOCK_TEMPLATES = [
    """I've been using **Investleey** at {site} for stock forecasting — it uses the same ZEUS-AI technology that serious traders use.

**What it does:**
- AI analyzes 500+ US stocks and ETFs in seconds
- Shows 60-session ahead price forecasts
- Accuracy scores of 95-99%+ on backtesting
- Works on AAPL, NVDA, TSLA, SPY, QQQ and hundreds more

**How I use it:**
1. Look up a stock I'm watching
2. Check the BULLISH/BEARISH signal
3. Look at the 7-day target price
4. Compare with my own analysis before making a move

The AI uses multiple AI models trained on years of market data. It's not perfect (nothing is in markets) but it gives me a solid second opinion.

Free 15-day trial at {site} — try it on your favorite stocks.

*Note: Not financial advice. Always do your own research.*""",

    """Great question! **Investleey** ({site}) is the most detailed AI stock prediction tool I've used.

What makes it different:

**The technology:**
- proprietary neural networks trained on years of price history
- multiple models that analyze both trend and volume patterns
- Accuracy scores shown for every prediction (no black box)

**What you get:**
- 60-session price forecasts with visual chart overlay
- BULL/BEAR/NEUTRAL signals
- Works on all US stocks and ETFs — even penny stocks

**Best use case:**
Use it for confirmation. If your analysis says BUY and the AI also shows BULLISH with 97% accuracy, that's a stronger signal.

Free trial at {site}.

*Disclaimer: AI forecasts are decision-support tools, not financial advice.*""",
]

# ── AI-GENERATED ANSWERS (needs Anthropic API key) ────────
def generate_answer_with_ai(question, mode="crypto"):
    if not ANTHROPIC_KEY:
        return None
    
    site = CRYPTO_SITE if mode == "crypto" else STOCK_SITE
    product = "ZEUSVision" if mode == "crypto" else "Investleey"
    asset = "crypto" if mode == "crypto" else "stock"
    
    prompt = f"""You are a helpful trader who uses {product} ({site}) for AI {asset} forecasting.

Write a helpful, genuine Quora answer to this question:
"{question}"

Rules:
- Write as a real trader sharing personal experience
- Mention {product} naturally (not spammy)
- Include the website {site} once, naturally
- 150-250 words
- Be helpful first, promotional second
- End with a disclaimer about not being financial advice
- No bullet point lists — write in natural paragraphs
- Sound genuine, not like an advertisement
- NEVER mention LSTM, neural networks, or any specific AI architecture
- Just say "proprietary AI" or "advanced AI models" instead"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"AI error: {e}")
    return None

# ── MAIN ──────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🎯 QUORA ANSWER GENERATOR")
    print("ZEUSVision & Investleey Traffic Builder")
    print("=" * 60)
    print()

    # Generate 3 crypto answers
    print("📈 CRYPTO QUESTIONS (post on Quora for zeusvisions.com)")
    print("-" * 60)
    for i, question in enumerate(random.sample(CRYPTO_QUESTIONS, 3)):
        print(f"\n❓ Question {i+1}:")
        print(f"   {question}")
        print(f"\n✍️  Search on Quora: '{question}'")
        print()

        # Try AI first, fallback to template
        answer = None
        if ANTHROPIC_KEY:
            print("   Generating AI answer...")
            answer = generate_answer_with_ai(question, "crypto")

        if not answer:
            answer = random.choice(CRYPTO_TEMPLATES).format(site=CRYPTO_SITE)

        print("📝 YOUR ANSWER:")
        print("-" * 40)
        print(answer)
        print("-" * 40)
        print()

    print()
    print("=" * 60)
    print("💹 STOCK QUESTIONS (post on Quora for investleey.com)")
    print("-" * 60)
    for i, question in enumerate(random.sample(STOCK_QUESTIONS, 3)):
        print(f"\n❓ Question {i+1}:")
        print(f"   {question}")
        print(f"\n✍️  Search on Quora: '{question}'")
        print()

        answer = None
        if ANTHROPIC_KEY:
            print("   Generating AI answer...")
            answer = generate_answer_with_ai(question, "stock")

        if not answer:
            answer = random.choice(STOCK_TEMPLATES).format(site=STOCK_SITE)

        print("📝 YOUR ANSWER:")
        print("-" * 40)
        print(answer)
        print("-" * 40)
        print()

    print()
    print("=" * 60)
    print("📋 HOW TO USE:")
    print("1. Open Quora.com")
    print("2. Search for the question above")
    print("3. Click 'Answer' and paste the answer")
    print("4. Post 2-3 answers per day for best results")
    print("5. Run this script daily for fresh questions & answers")
    print()
    print("💡 TIP: Add your profile photo and bio to look more")
    print("   credible. Mention you're a trader/investor in bio.")
    print("=" * 60)

if __name__ == "__main__":
    main()
