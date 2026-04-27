# Daily Market Rundown — Agent Prompts

Each prompt below is a standalone instruction for an AI agent. Run them in order.
Prompts 0–1 are one-time setup. Prompts 2–3 run daily. Prompt 4 is fully automated via GitHub Actions.

---

## Prompt 0 — One-Time Infrastructure Setup

This prompt documents the full infrastructure that was set up once and does not need to be repeated.

### 0.1 — GitHub Pages Repository

A public GitHub repository named **`daily-market-brief`** was created under the account **`rajeev1986`**.

- GitHub Pages is enabled on the `main` branch, root folder (`/`)
- The live dashboard is accessible at:
  **https://rajeev1986.github.io/daily-market-brief/market_rundown.html**
- The archive index is at:
  **https://rajeev1986.github.io/daily-market-brief/archive/index.html**
- Individual daily archive pages are at:
  **https://rajeev1986.github.io/daily-market-brief/archive/YYYY-MM-DD.html**

### 0.2 — Repository File Structure

```
daily-market-brief/
├── .github/
│   ├── workflows/
│   │   └── daily_rundown.yml       ← GitHub Actions schedule + pipeline trigger
│   └── scripts/
│       └── run_pipeline.py         ← Full pipeline: research → markdown → HTML → git push
├── market_rundown.html             ← Live dashboard (last 7 days, newest on top)
├── archive/
│   ├── index.html                  ← Browsable archive of all past rundowns
│   └── YYYY-MM-DD.html             ← One standalone page per day (permanent)
└── rundown_YYYY-MM-DD.md           ← Source markdown for each day (git history)
```

### 0.3 — GitHub Actions Automation

The pipeline runs entirely on GitHub's servers via **GitHub Actions** — no local machine, no scheduler, no login required.

**Schedule:** Monday–Friday at 13:00 UTC (= 8:00 AM CT in summer / 7:00 AM CT in winter)

**Workflow file:** `.github/workflows/daily_rundown.yml`
**Pipeline script:** `.github/scripts/run_pipeline.py`

**Dependencies (installed automatically by the workflow):**
- `openai==1.30.0` — research (web_search tool) + markdown generation + HTML conversion
- `jinja2==3.1.4` — templating

**Required GitHub secret (one-time setup):**
1. Go to: **https://github.com/rajeev1986/daily-market-brief/settings/secrets/actions**
2. Click **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Value: your OpenAI API key (`sk-...`)

> OpenAI API access is pay-as-you-go (not a subscription). Each daily run costs ~$0.10–$0.25.
> Sign up at **https://platform.openai.com** — separate from ChatGPT.

### 0.4 — How the Pipeline Works (End-to-End)

Every weekday at 8 AM CT, GitHub Actions runs this sequence:

```
1. Checkout repo (daily-market-brief)

2. run_pipeline.py:
   a. Research    → 8 web searches via OpenAI web_search tool
                    (macro, calendar, earnings, ratings, stocks, themes, secondary, week ahead)
   b. Markdown    → LLM synthesizes research into structured rundown_YYYY-MM-DD.md
   c. HTML entry  → LLM converts markdown to HTML entry block
   d. Dashboard   → prepend entry to market_rundown.html (trim to last 7 days)
   e. Archive     → write archive/YYYY-MM-DD.html (permanent standalone page)
   f. Index       → prepend row to archive/index.html

3. git commit + push → GitHub Pages auto-deploys in ~30 seconds
```

**Error handling:**
- Zero usable research categories → pipeline exits with error, nothing published
- Fewer than 3 categories → publishes with ⚠️ warning banner at top of entry
- Any failure → GitHub Actions marks the run as failed + sends email notification to your GitHub account

### 0.5 — Manual Run (any time)

To trigger the pipeline immediately without waiting for the schedule:

1. Go to: **https://github.com/rajeev1986/daily-market-brief/actions**
2. Click **Daily Market Rundown** in the left sidebar
3. Click **Run workflow** → optionally enter a specific date → **Run workflow**

To run for a specific past date, enter it in the `date_override` field (format: `YYYY-MM-DD`).

### 0.6 — Monitoring

- **Run history:** https://github.com/rajeev1986/daily-market-brief/actions
- **Live page:** https://rajeev1986.github.io/daily-market-brief/market_rundown.html
- **Archive:** https://rajeev1986.github.io/daily-market-brief/archive/index.html
- **Failure alerts:** GitHub sends an email to your account when a workflow run fails

---

## Prompt 1 — First-Time Setup: Create the HTML Dashboard Shell

> ✅ **Already completed.** `market_rundown.html` and the archive structure were created and pushed to GitHub Pages.
> Only run this prompt again if you need to rebuild the dashboard from scratch.

Create a single self-contained HTML file named `market_rundown.html` in the `daily-market-brief/` repo directory.

This file will serve as the daily market briefing dashboard. On first creation it should contain:
- A page title: "Daily Market Rundown"
- A dark theme stylesheet (embedded, no external dependencies)
- A header with the title, a placeholder for the last-updated timestamp, and an **Archive** link pointing to `archive/index.html`
- An empty `<div id="rundowns">` container where daily briefing entries will be prepended on each run
- Collapsible section support using plain HTML `<details>` and `<summary>` tags — no JavaScript frameworks
- A clean, minimal layout optimized for quick scanning before the market open
- High contrast text, clearly separated sections, and a visually distinct card or table layout for stocks

Also create:
- `archive/index.html` — browsable archive index (year/month grouped, newest first)
- `archive/.gitkeep` — so the folder is tracked by git

Commit and push to `main`. GitHub Pages will serve the file at:
`https://rajeev1986.github.io/daily-market-brief/market_rundown.html`

---

## Prompt 2 — Generate Today's Daily Market Rundown

Today's date is: **{TODAY'S DATE}**
Current time: **{CURRENT TIME} ET**

You are a pre-market research assistant. Your job is to research current market conditions using live web sources and produce a structured daily briefing.

### Step 1 — Research

Work through each category below in order. For each category, search the listed sources and extract the most relevant, actionable information published today or late yesterday.

---

**Watchlist Priority**

Always check these tickers first. For each one, look for: earnings reports, analyst rating changes, significant news catalysts,
unusual pre-market price action, or options activity. Only include a ticker if something notable is found today — skip it silently if nothing is actionable.

Watchlist: `WDC, MU, LITE, CIEN, TSLA, COHR, CRDO, PLTR, TER, LRCX, GLW, AAOI, VRT, TSM, CLS, GOOGL, STX, SNDK, UNH, NBIS, AVGO, NVDA, AMD, HOOD, NFLX, VIX, META, MSFT, AMZN, GLD, SPY`

After covering the watchlist, expand to other high-potential names from the broader market.

---

**Macro & Overnight**
- Search for: overnight futures activity, global market moves, Fed commentary, geopolitical events, currency moves
- Sources: Reuters, Bloomberg, CNBC, MarketWatch, Financial Times, Yahoo Finance, Barron's, The Wall Street Journal

**Economic Calendar**
- Search for: today's scheduled data releases (CPI, PPI, jobs, PMI, retail sales, etc.) and any Fed speaker events
- Sources: Investing.com economic calendar, ForexFactory, BLS.gov, Federal Reserve website

**Earnings**
- Search for: companies reporting earnings today (pre-market and after-hours) and any notable results already released
- Sources: Earnings Whispers, EarningsHub, SeekingAlpha, Yahoo Finance earnings calendar, MarketWatch earnings calendar, Nasdaq earnings calendar

**Analyst Ratings**
- Search for: today's analyst upgrades, downgrades, initiations, and rating changes
- For each, capture: ticker, analyst firm, new rating, price target (if available), and a one-sentence note on trade setup potential this week
- Prioritize watchlist tickers and high-conviction firms
- Sources: Benzinga analyst ratings, MarketBeat, TheStreet, Tipranks, Nasdaq analyst activity

**Stocks in Play**
- Search for: most active pre-market movers, stocks with significant news catalysts, unusual options activity
- Prioritize names with the highest likelihood of meaningful intraday volatility
- Sources: Benzinga, Finviz, MarketBeat, Yahoo Finance, MarketWatch, Barchart, StockAnalysis

**Market Themes**
- Search for: dominant sector narratives, ETF flows, and broader market themes driving today's action
- Sources: ETF.com, Sector SPDRs, Yahoo Finance, MarketWatch, Seeking Alpha

---

**Research Rules:**
- Use only information published today or late yesterday
- Cross-reference at least two sources for any major claim
- If a source is unavailable, note it and move on
- Flag conflicting signals across sources (e.g., one source bullish, another cautious on the same name)

---

### Step 2 — Generate the Briefing

Using the research above, produce today's Daily Market Rundown as a markdown briefing with the following sections in this order:

1. **Macro Overview** — key overnight and pre-market macro developments
2. **Economic Calendar** — today's scheduled data releases and Fed events, with expected vs. prior values where available
3. **Earnings Reports** — notable pre-market and after-hours results with market reactions; flag any watchlist names
4. **Analyst Ratings** — today's upgrades, downgrades, and initiations; watchlist names first, then others
5. **Stocks in Play** — primary names with clear catalysts; for each include ticker, catalyst, and one sentence on why it could move today; watchlist names first
6. **Market Themes** — broader narratives driving sector or index moves today
7. **Secondary Names** — stocks with fresh news but lower priority than Stocks in Play
8. **Week Ahead** — key events, earnings, and data releases for the rest of the week

**Output requirements:**
- Summarize — do not paste raw headlines or quote sources verbatim
- Cite the source for each major data point inline (e.g., *via Reuters*)
- Keep each section concise — the full briefing should be scannable in under 5 minutes
- Save the output as `rundown_YYYY-MM-DD.md` using today's date

---

## Prompt 3 — Update the HTML Dashboard

Read the markdown file `rundown_YYYY-MM-DD.md` generated in Prompt 2 (use today's date).

Convert it into an HTML entry and prepend it inside the `<div id="rundowns">` container in `market_rundown.html`.

Requirements:
- Each daily entry must be wrapped in a `<section>` tag with a `data-date` attribute (e.g., `data-date="2025-01-15"`)
- The entry date must be displayed as a visible heading at the top of the section
- Each briefing section (Macro Overview, Earnings, etc.) must use a `<details>` / `<summary>` collapsible block
- Stocks in Play entries must use a card or table layout, visually distinct from prose sections
- All source citations must be rendered as clickable `<a href>` links where a URL is available
- Update the last-updated timestamp in the page header to the current date and time ET
- New entries are prepended — most recent rundown appears at the top of the page
- `market_rundown.html` keeps only the **last 7 days** of entries — remove the oldest entry if there are more than 7
- Do not modify any existing entries already in the file (other than removing the oldest when over the 7-day limit)

Also:
- Write a standalone archive page at `archive/YYYY-MM-DD.html` containing the full entry for permanent access
- Prepend a new row to `archive/index.html` with the date, day of week, and a one-line headline summary

Then commit and push all changed files:
```bash
git add market_rundown.html rundown_YYYY-MM-DD.md archive/YYYY-MM-DD.html archive/index.html
git commit -m "Daily rundown YYYY-MM-DD"
git push origin main
```

GitHub Pages will auto-deploy within ~30 seconds. The updated dashboard will be live at:
**https://rajeev1986.github.io/daily-market-brief/market_rundown.html**

---

## Prompt 4 — Automated Daily Workflow

> ✅ **Fully automated via GitHub Actions.** No local setup required.
> See **Prompt 0** for full details.

**The only setup step remaining:** Add your OpenAI API key as a GitHub secret:
1. Go to: **https://github.com/rajeev1986/daily-market-brief/settings/secrets/actions**
2. New repository secret → Name: `OPENAI_API_KEY` → Value: `sk-...`

Once the secret is set, the pipeline runs automatically every weekday at 8 AM CT.
No MacBook required. No login required. Runs on GitHub's servers for free.
