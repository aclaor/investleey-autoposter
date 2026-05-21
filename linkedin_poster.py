name: LinkedIn Auto-Post

on:
  schedule:
    - cron: '0 2,6,10,14,18,22 * * *'  # Every 4 hours
  workflow_dispatch:

jobs:
  post-stocks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          pip install requests
          npm install playwright
          npx playwright install chromium --with-deps
      - name: Post stocks to LinkedIn
        env:
          LI_CLIENT_ID_STOCKS: ${{ secrets.LI_CLIENT_ID_STOCKS }}
          LI_CLIENT_SECRET_STOCKS: ${{ secrets.LI_CLIENT_SECRET_STOCKS }}
          LI_ACCESS_TOKEN_STOCKS: ${{ secrets.LI_ACCESS_TOKEN_STOCKS }}
          LI_ORG_ID_STOCKS: ${{ secrets.LI_ORG_ID_STOCKS }}
          POST_MODE: stocks
        run: python linkedin_poster.py

  post-crypto:
    runs-on: ubuntu-latest
    needs: post-stocks
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          pip install requests
          npm install playwright
          npx playwright install chromium --with-deps
      - name: Post crypto to LinkedIn
        env:
          LI_CLIENT_ID_CRYPTO: ${{ secrets.LI_CLIENT_ID_CRYPTO }}
          LI_CLIENT_SECRET_CRYPTO: ${{ secrets.LI_CLIENT_SECRET_CRYPTO }}
          LI_ACCESS_TOKEN_CRYPTO: ${{ secrets.LI_ACCESS_TOKEN_CRYPTO }}
          LI_ORG_ID_CRYPTO: ${{ secrets.LI_ORG_ID_CRYPTO }}
          POST_MODE: crypto
        run: python linkedin_poster.py
