name: Discord Auto-Post

on:
  schedule:
    - cron: '15 * * * *'  # Every hour at :15
  workflow_dispatch:

jobs:
  post-stocks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Post stocks to Discord
        env:
          MODE: stocks
          POST_MODE: stocks
          STOCK_API_URL: ${{ secrets.STOCK_API_URL }}
          STOCK_API_TOKEN: ${{ secrets.STOCK_API_TOKEN }}
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          DISCORD_STOCK_CHANNEL: ${{ secrets.DISCORD_STOCK_CHANNEL }}
        run: python discord_poster.py

  post-crypto:
    runs-on: ubuntu-latest
    needs: post-stocks
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Post crypto to Discord
        env:
          MODE: crypto
          POST_MODE: crypto
          CRYPTO_API_URL: ${{ secrets.CRYPTO_API_URL }}
          CRYPTO_API_TOKEN: ${{ secrets.CRYPTO_API_TOKEN }}
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          DISCORD_CRYPTO_CHANNEL: ${{ secrets.DISCORD_CRYPTO_CHANNEL }}
        run: python discord_poster.py
