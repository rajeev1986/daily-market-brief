# Daily Market Rundown — Agent Workflow

---

## HOW TO USE THIS FILE

- **Prompt 0** — One-time infrastructure reference. Already set up. Do not re-run.
- **Prompts 1–3** — Run these every weekday morning. They are the daily pipeline.
- **Prompt 4** — Fully automated via GitHub Actions. No manual action needed.

When running the daily pipeline, execute Prompts 1 → 2 → 3 in order without stopping for confirmation. Report only at the end.

---

## Prompt 0 — Infrastructure Reference (One-Time Setup — Already Done)

### Repository
- GitHub repo: `rajeev1986/daily-market-brief`
- GitHub Pages live at: **https://rajeev1986.github.io/daily-market-brief/market_rundown.html**
- Archive index: **https://rajeev1986.github.io/daily-market-brief/archive/index.html**
- Individual archive pages: **https://rajeev1986.github.io/daily-market-brief/archive/YYYY-MM-DD.html**

### File Structure
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
├── build_dashboard.py              ← Local convenience script (markdown → HTML)
├── DAILY_RUNDOWN_PROMPT.md         ← This file
└── rundown_YYYY-MM-DD.md           ← Source markdown for each day
```

### Automation
- **Schedule:** Monday–Friday at 13:00 UTC (= 8:00 AM CT)
- **Trigger manually:** https://github.com/rajeev1986/daily-market-brief/actions → Run workflow
- **Required secret:** `OPENAI_API_KEY` at https://github.com/rajeev1986/daily-market-brief/settings/secrets/actions
- **Cost:** ~$0.10–$0.25 per run (OpenAI pay-as-you-go)
- **Failure alerts:** GitHub emails your account on any workflow failure

---

## Prompt 1 — Research

> **Run this every weekday morning.**
> Today's date: use the current date from your environment.

Work through each category below in order. Search the listed sources and extract the most relevant, actionable information published today or late yesterday. Cross-reference at least two sources for any major claim. If a source is unavailable, note it and move on. Flag any conflicting signals across sources.

---

### 1A — Watchlist Scan (Run First)

Check every ticker below for: earnings reports, analyst rating changes, significant news catalysts, unusual pre-market price action, or options activity. Only flag a ticker if something actionable was found today — skip silently otherwise. After covering the watchlist, expand to other high-potential names from the broader market.

**Watchlist:**
`WDC, MU, LITE, CIEN, TSLA, COHR, CRDO, PLTR, TER, LRCX, GLW, AAOI, VRT, TSM, CLS, GOOGL, STX, SNDK, UNH, NBIS, AVGO, NVDA, AMD, HOOD, NFLX, VIX, MSFT, AMZN, GLD, SPY`

---

### 1B — Macro & Overnight

Search for: overnight futures (S&P 500, Nasdaq, Dow), global market moves (Asia, Europe), Fed commentary, geopolitical events, currency moves (USD, JPY, EUR), oil, gold.

Sources: Reuters, Bloomberg, CNBC, MarketWatch, Financial Times, Yahoo Finance, Barron's, The Wall Street Journal, PBS NewsHour, Axios

---

### 1C — Economic Calendar

Do not fetch or extract calendar data. Instead, render the Economic Calendar section in the HTML as a direct link to:
**https://www.marketwatch.com/economy-politics/calendar**

The section body should contain only this:
```html
<div class="section-body prose">
  <p>View the full economic calendar for the week on MarketWatch:</p>
  <p><a href="https://www.marketwatch.com/economy-politics/calendar" target="_blank" rel="noopener">📅 MarketWatch Economic Calendar →</a></p>
</div>
```

Skip this category entirely during research. Do not include it in the markdown briefing either.

---

### 1D — Earnings

Find: companies reporting today (pre-market and after-hours), notable results already released this week, and a full list of watchlist names reporting this week.

For each result: ticker, EPS actual vs. estimate, revenue actual vs. estimate, % after-hours move, one-sentence takeaway.

Sources: Earnings Whispers, EarningsHub, SeekingAlpha, Yahoo Finance earnings calendar, MarketWatch earnings calendar, Nasdaq earnings calendar, FactSet

---

### 1E — Analyst Ratings

Find today's upgrades, downgrades, initiations, and price target changes. Watchlist tickers first, then broader market.

For each: ticker, firm, action (UPGRADE / DOWNGRADE / INITIATE / PT RAISE / PT CUT), new rating, new price target (if available), one-sentence thesis.

Sources: Benzinga, MarketBeat, TheStreet, TipRanks, Nasdaq analyst activity, Zacks

---

### 1F — Stocks in Play & Options Activity

Find: most active pre-market movers, stocks with significant news catalysts, unusual options activity.

For unusual options: flag ticker, contract type (call/put), volume vs. average, strike, expiry, and whether flow was buy-side or sell-side.

Watchlist tickers first, then broader market.

Sources: Benzinga, Finviz, MarketBeat, Yahoo Finance, Barchart unusual options, Unusual Whales, StockAnalysis

---

### 1G — Market Themes & Sector Flows

Find: dominant sector narratives, ETF flows, rotation signals, crypto market conditions, and broader macro themes driving today's action.

Sources: ETF.com, Sector SPDRs, Yahoo Finance, MarketWatch, Seeking Alpha, iShares, AAII, Investing.com sector analysis

---

## Prompt 2 — Generate the Daily Rundown Markdown

> **Run immediately after Prompt 1.**

Using your research from Prompt 1, write today's Daily Market Rundown. Save it as:
`rundown_YYYY-MM-DD.md` (use today's actual date)

The file must contain exactly these 7 sections in this order:

---

```
# Daily Market Rundown — [Weekday, Month DD, YYYY]
*Pre-market briefing | Read time: ~4 min*

## 1. Macro Overview
Open with a key-levels grid showing: S&P 500, Nasdaq, Dow (closes + week-to-date
moves), VIX, WTI Crude, Brent Crude, Gold/GLD.
Then 2–3 prose paragraphs covering the main overnight narrative and top risks.

## 2. Economic Calendar
Do not write calendar content. Insert only this line:
  [📅 MarketWatch Economic Calendar](https://www.marketwatch.com/economy-politics/calendar)

## 3. Earnings Reports
Sub-section "Already Reported":
  Ticker | Result vs. Estimate | % AH Move | Takeaway
  Flag watchlist names with ⭐. Use border-left accent color in HTML:
  green = beat/gap up, red = miss/gap down, yellow = mixed.

Sub-section "Reporting This Week":
  Ticker | Date/Time | EPS Est. | Rev Est. | Key Focus
  Watchlist names first.

Sub-section "Other Majors This Week":
  Brief prose for notable non-watchlist names.

## 4. Analyst Ratings
Sub-section "Watchlist Names":
  Ticker | Firm | Action | New Rating | PT | Setup Note

Sub-section "Other Notable":
  Same table format.

Action labels: UPGRADE / DOWNGRADE / INITIATE / PT RAISE / PT CUT

## 5. Stocks in Play
One entry per stock. Format:
  **TICKER** ⭐ Watchlist (if applicable)
  Catalyst type — one-sentence description.
  Why it moves today — one sentence on the specific intraday setup.

Watchlist names first. Order by expected volatility (highest first).
Include unusual options activity names here if they are primary movers,
otherwise put them in Section 7.

## 6. Market Themes
4–6 named themes. Each: bold title + 2–3 sentence explanation + inline source citations.
Cover: sector rotation, AI/tech narrative, macro backdrop, geopolitical, crypto/commodity.

At the end of Section 6, add a "Key Risks & Conflicting Signals" table if any
conflicting signals were found during research:
| Risk | Signal / Trigger | Implication |

## 7. Secondary Names
Table: Ticker | Catalyst | Brief (one sentence)
Include:
- Non-watchlist names with fresh news not covered in Section 5
- Unusual options activity names (if not already in Section 5)
- Any names from research not yet captured above
```

---

**Output rules:**
- Summarize — do not paste raw headlines verbatim
- Cite each major data point inline: `(*via Reuters*)` or `[Source](https://url)`
- Use real hyperlinks where URLs are known
- Keep each section concise and scannable

---

### Gap Audit (Before Proceeding to Prompt 3)

Before writing any HTML, verify nothing was dropped:

1. Re-read your research notes from Prompt 1
2. Re-read the markdown you just wrote
3. Check for: watchlist tickers in research but absent from sections 5 or 7 · analyst ratings found but not included · options flow names not in section 7 · economic events missing from section 2 · market themes not captured in section 6 · conflicting signals with no home
4. Add any gaps to the markdown
5. Only proceed to Prompt 3 once satisfied nothing material was dropped

---

## Prompt 3 — Inject Into market_rundown.html

> **Run immediately after Prompt 2.**

Read the current `market_rundown.html`. Convert today's rundown into a fully-styled HTML entry and **prepend** it inside `<div id="rundowns">`.

---

### HTML Entry Structure

Each daily entry must use this exact outer structure:

```html
<!-- ══════════════════════════════════════════════════════════════
     ENTRY: YYYY-MM-DD
     ══════════════════════════════════════════════════════════════ -->
<section class="rundown-card" data-date="YYYY-MM-DD">

  <div class="card-header">
    <span class="card-date">[Full date, e.g. Monday, April 28, 2026]</span>
    <span class="card-badge">PRE-MARKET · [DAY OF WEEK]</span>
  </div>

  <!-- One <details> block per section -->
  <details open>
    <summary><span class="section-icon">[emoji]</span> [SECTION NAME IN CAPS]</summary>
    <div class="section-body"> ... </div>
  </details>

  <details>
    <summary>...</summary>
    <div class="section-body"> ... </div>
  </details>

</section>
```

---

### Section Rendering Rules

**MACRO OVERVIEW** — `<details open>`
- `.levels-grid` with `.level-item` tiles for: S&P 500, Nasdaq, Dow, VIX, WTI Crude, Brent Crude, GLD
- Apply `.up` / `.down` classes to `.level-value` and `.level-note` for color coding
- Follow with `.prose` paragraphs for the narrative

**ECONOMIC CALENDAR** — `<details>`
- Do not render any table or event data
- Section body contains only a direct link:
```html
<div class="section-body prose">
  <p>View the full economic calendar for the week on MarketWatch:</p>
  <p><a href="https://www.marketwatch.com/economy-politics/calendar" target="_blank" rel="noopener">📅 MarketWatch Economic Calendar →</a></p>
</div>
```

**EARNINGS REPORTS** — `<details>`
- "Already Reported" entries: highlighted card div with `border-left` accent
  - `var(--red)` = large miss / gap down
  - `var(--green)` = beat / gap up
  - `var(--yellow)` = mixed / guidance miss
- "Reporting This Week": `.stocks-table`
- Watchlist names get `⚠ WATCHLIST` badge: `<span style="font-size:0.68rem;color:var(--accent);margin-left:auto;font-family:var(--font-mono);font-weight:700;letter-spacing:0.03em;">⚠ WATCHLIST</span>`

**ANALYST RATINGS** — `<details>`
- Two `.stocks-table` blocks: "Watchlist Names" then "Other Notable"
- Action pills: `.pill.up` for UPGRADE / INITIATE / PT RAISE · `.pill.down` for DOWNGRADE / PT CUT

**STOCKS IN PLAY** — `<details open>`
- Card grid: `display:grid; grid-template-columns:repeat(auto-fill,minmax(285px,1fr)); gap:0.75rem`
- Each card: `background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:0.85rem 1rem`
- Border-left accent color:
  - `var(--red)` = gap risk / short catalyst
  - `var(--green)` = bullish catalyst
  - `var(--yellow)` = pending / earnings setup
  - `var(--accent)` = AI / momentum / neutral
- Card top row: `<span class="ticker">TICKER</span>` + direction pill + `⚠ WATCHLIST` badge (if applicable)
- Catalyst label: `font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em`
- Setup paragraph: `font-size:0.83rem; line-height:1.6`
- Watchlist cards first, then broader market cards

**KEY RISKS & CONFLICTING SIGNALS** (when present) — `<details>`
- `.stocks-table` with columns: Risk | Signal/Trigger | Implication
- Implication cell: `color:var(--red)` for high severity, `color:var(--yellow)` for medium
- Insert between Market Themes and Secondary Names

**MARKET THEMES** — `<details>`
- `.prose` paragraphs, one per theme
- Bold theme title + 2–3 sentences + inline source links

**SECONDARY NAMES** — `<details>`
- `.stocks-table` with Ticker | Catalyst | Brief columns
- Inline source links in the Brief column where available

---

### Page-Level Rules

- **PREPEND** the new entry — most recent date must be the first child inside `<div id="rundowns">`
- Do **NOT** modify any existing entries already in the file
- Remove the `.empty-state` placeholder if still present
- Update `#last-updated` to today's date + time ET: `Last updated: Mon DD, YYYY · HH:MM AM/PM ET`
- Keep only the **last 7 days** of entries — remove the oldest `<section>` if there are more than 7
- All source citations: `<a href="..." target="_blank" rel="noopener">Source</a>`
- Use existing CSS classes only — do **not** add new `<style>` blocks
- Section summary emojis: 🌐 Macro · 📅 Calendar · 📣 Earnings · 🏷️ Ratings · 🎯 Stocks in Play · 🧭 Themes · ⚠️ Risks · 📋 Secondary

---

### Final Verification Checklist

After writing the HTML, confirm all of the following before reporting done:

- [ ] New `<section data-date="YYYY-MM-DD">` is the **first** child inside `<div id="rundowns">`
- [ ] `#last-updated` reflects today's date and time ET
- [ ] Every HIGH-priority item from Prompt 1 appears somewhere in the HTML entry
- [ ] HTML file closes with `</body></html>` and is well-formed
- [ ] Entry count: `grep -c "data-date" market_rundown.html` equals expected number of days

---

### Deliverables

When the full pipeline completes, commit and push:

```bash
git add market_rundown.html rundown_YYYY-MM-DD.md archive/YYYY-MM-DD.html archive/index.html
git commit -m "Daily rundown YYYY-MM-DD"
git push origin main
```

Also write:
- `archive/YYYY-MM-DD.html` — standalone archive page for permanent access
- Prepend a new row to `archive/index.html` with: date, day of week, one-line headline summary

GitHub Pages auto-deploys within ~30 seconds.
**Live at: https://rajeev1986.github.io/daily-market-brief/market_rundown.html**

---

## Prompt 4 — Automated Daily Workflow (GitHub Actions — No Action Needed)

The pipeline runs automatically every weekday at 8:00 AM CT via GitHub Actions.

**Only remaining setup step:** Confirm `OPENAI_API_KEY` is set as a GitHub secret:
1. Go to: https://github.com/rajeev1986/daily-market-brief/settings/secrets/actions
2. New repository secret → Name: `OPENAI_API_KEY` → Value: `sk-...`

**Monitor runs:** https://github.com/rajeev1986/daily-market-brief/actions
