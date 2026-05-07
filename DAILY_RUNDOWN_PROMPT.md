# Daily Market Rundown — Manual Fallback Guide

> This file is a **manual fallback** for days when the automated GitHub Actions pipeline fails.
> Under normal operation, everything runs automatically — no action needed.

---

## Automated Pipeline (Normal Operation)

**Schedule:** Monday–Friday at 8:00 AM CT (13:00 UTC)
**Monitor:** https://github.com/rajeev1986/daily-market-brief/actions
**Live dashboard:** https://rajeev1986.github.io/daily-market-brief/market_rundown.html
**Archive:** https://rajeev1986.github.io/daily-market-brief/archive/index.html

**To trigger manually from GitHub:**
1. Go to https://github.com/rajeev1986/daily-market-brief/actions
2. Click **Daily Market Rundown** → **Run workflow**
3. Leave date blank for today, or enter `YYYY-MM-DD` for a specific date
4. Set `force_rerun` to `1` if today's rundown already exists and you want to regenerate it

---

## Manual Fallback — Run Locally

If the automated pipeline fails, run it locally:

```bash
# Install dependencies (one-time)
pip install openai==2.33.0 markdown==3.7

# Set your API key
export OPENAI_API_KEY=sk-...

# Run the pipeline for today
python .github/scripts/run_pipeline.py

# Or for a specific date
RUN_DATE=2026-05-07 python .github/scripts/run_pipeline.py

# Force regenerate even if today's file exists
FORCE_RERUN=1 python .github/scripts/run_pipeline.py
```

Then commit and push:
```bash
git add market_rundown.html rundown_YYYY-MM-DD.md archive/YYYY-MM-DD.html archive/index.html
git commit -m "Daily rundown YYYY-MM-DD"
git push origin main
```

---

## Manual Fallback — Write Rundown Yourself + Build HTML

If you want to write the markdown manually and just build the HTML:

```bash
# After writing rundown_YYYY-MM-DD.md manually:
python build_dashboard.py rundown_YYYY-MM-DD.md

# Then commit and push as above
```

---

## Watchlist

`WDC, MU, LITE, CIEN, TSLA, COHR, CRDO, PLTR, TER, LRCX, GLW, AAOI, VRT, TSM, CLS, GOOGL, STX, SNDK, UNH, NBIS, AVGO, NVDA, AMD, HOOD, NFLX, VIX, META, MSFT, AMZN, GLD, SPY`

---

## Approved Sources

Reuters, Bloomberg, CNBC, MarketWatch, Financial Times, Yahoo Finance, Barron's, The Wall Street Journal, PBS NewsHour, Axios

---

## File Structure

```
daily-market-brief/
├── .github/
│   ├── workflows/
│   │   ├── daily_rundown.yml   ← Main pipeline (Mon–Fri 8 AM CT)
│   │   └── keepalive.yml       ← Prevents GitHub schedule throttling (runs Sundays)
│   └── scripts/
│       └── run_pipeline.py     ← Full pipeline: research → markdown → HTML → push
├── build_dashboard.py          ← Local script: markdown → HTML only (no API calls)
├── market_rundown.html         ← Live dashboard (last 7 days)
├── archive/
│   ├── index.html              ← Browsable archive index
│   └── YYYY-MM-DD.html         ← Permanent standalone page per day
├── rundown_YYYY-MM-DD.md       ← Source markdown per day
└── DAILY_RUNDOWN_PROMPT.md     ← This file
```
