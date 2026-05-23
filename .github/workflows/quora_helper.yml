name: Daily Quora Answer Generator

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  generate-answers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Generate Quora answers
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python quora_helper.py
