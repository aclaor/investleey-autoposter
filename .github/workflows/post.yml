name: Investleey FB Auto-Post

on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:         # Allow manual trigger

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests pillow
      - name: Run auto-poster
        env:
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          STOCK_API_URL: ${{ secrets.STOCK_API_URL }}
          STOCK_API_TOKEN: ${{ secrets.STOCK_API_TOKEN }}
        run: python poster.py
