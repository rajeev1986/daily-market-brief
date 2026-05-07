"""
Daily Market Rundown — GitHub Actions Pipeline Script

Runs the full pipeline:
  1. Research  — 3 combined web searches via OpenAI gpt-4o + web_search_preview
  2. Markdown  — gpt-4o synthesizes research into rundown_YYYY-MM-DD.md
  3. HTML      — build_dashboard.py converts markdown → market_rundown.html
  4. Archive   — build_dashboard.py writes archive/YYYY-MM-DD.html + index

Git commit + push is handled by the workflow YAML.

Cost optimisations:
  - 3 combined searches instead of 8 serial ones  (saves ~5 API calls/day)
  - Economic Calendar is a static MarketWatch link (no search needed)
  - Secondary Names / Week Ahead disabled by default (uncomment to re-enable)
  - Weekend + duplicate-run guards prevent accidental double billing
  - All HTML generation delegated to build_dashboard.py (no LLM for HTML)
"""

from __future__ import annotations

import os
import re
import sys
import logging
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("rundown")

# ── Constants ─────────────────────────────────────────────────────────────────
REPO_DIR    = Path(__file__).parent.parent.parent   # daily-market-brief/
MAX_ENTRIES = 7
CT          = ZoneInfo("America/Chicago")

# Models
SEARCH_MODEL    = "gpt-4o-mini"    # web_search_preview tool
SYNTHESIS_MODEL = "gpt-4o-mini"    # markdown generation

WATCHLIST = [
    "WDC", "MU", "LITE", "CIEN", "TSLA", "COHR", "CRDO", "PLTR", "TER",
    "LRCX", "GLW", "AAOI", "VRT", "TSM", "CLS", "GOOGL", "STX", "SNDK",
    "UNH", "NBIS", "AVGO", "NVDA", "AMD", "HOOD", "NFLX", "VIX",
    "META", "MSFT", "AMZN", "GLD", "SPY",
]

WARNING_BANNER = (
    "⚠️ **Incomplete — fewer than 3 data sources returned results.** "
    "Some sections below may be missing or incomplete.\n\n"
)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — RESEARCH  (3 combined searches)
# ═══════════════════════════════════════════════════════════════════════════════

def search(client: OpenAI, prompt: str) -> str:
    """Single web search via OpenAI Responses API."""
    try:
        response = client.responses.create(
            model=SEARCH_MODEL,
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text") and block.text:
                        return block.text
        log.warning("Search returned no text content — response structure may have changed")
    except Exception as exc:
        log.warning("Search failed: %s", exc)
    return ""


def research(client: OpenAI, today: date) -> dict[str, str]:
    """
    Run 3 combined searches to cover all research categories.
    Economic Calendar is skipped — rendered as a static MarketWatch link.
    """
    date_str = today.strftime("%B %d, %Y")
    wl       = ", ".join(WATCHLIST)
    results  = {}

    # Approved sources used across all searches
    SOURCES_MACRO    = "Reuters, Bloomberg, CNBC, MarketWatch, Financial Times, Yahoo Finance, Barron's, The Wall Street Journal, PBS NewsHour, Axios"
    SOURCES_EARNINGS = "Reuters, CNBC, MarketWatch, Yahoo Finance, The Wall Street Journal, Barron's, Axios"
    SOURCES_RATINGS  = "Reuters, Bloomberg, CNBC, MarketWatch, Yahoo Finance, The Wall Street Journal, Barron's"
    SOURCES_STOCKS   = "Reuters, CNBC, MarketWatch, Yahoo Finance, Financial Times, Barron's, Axios"

    # ── Search 1: Macro + Watchlist scan ─────────────────────────────────────
    log.info("Search 1/3 — macro + watchlist")
    results["macro"] = search(client,
        f"Today is {date_str}. Cover two things:\n\n"
        "1) PRE-MARKET MACRO: Find the CURRENT pre-market levels for S&P 500 futures, "
        "Nasdaq-100 futures, and Dow Jones futures (actual numeric values and % change). "
        "Also cover: global market moves (Asia close, Europe open), Fed commentary, "
        "geopolitical events, currency moves (USD, JPY, EUR), WTI crude price, "
        "Brent crude price, gold spot price. "
        f"Sources: {SOURCES_MACRO}.\n\n"
        f"2) WATCHLIST SCAN: check each of these tickers for earnings, analyst rating changes, "
        f"significant news catalysts, or unusual pre-market price action today: {wl}. "
        "Only report tickers with something actionable — skip the rest silently. "
        f"Sources: {SOURCES_STOCKS}.\n\n"
        "Summarize each part clearly. For index levels use the ACTUAL current numbers. "
        "Cite each fact with the source name and URL in this format: [Source Name](url)"
    )

    # ── Search 2: Earnings + Analyst Ratings ─────────────────────────────────
    log.info("Search 2/3 — earnings + analyst ratings")
    results["earnings_ratings"] = search(client,
        f"Today is {date_str}. Cover two things:\n\n"
        f"1) EARNINGS: companies reporting today (pre-market and after-hours). "
        f"Watchlist tickers first: {wl}. "
        "For each already-reported name: ticker, EPS actual vs estimate, revenue actual vs estimate, "
        "% stock reaction, one-sentence takeaway. "
        "For names reporting today: ticker, time (PM/AH), EPS estimate, revenue estimate, key focus. "
        f"Sources: {SOURCES_EARNINGS}.\n\n"
        f"2) ANALYST RATINGS: today's upgrades, downgrades, initiations, and price target changes. "
        f"Watchlist tickers first: {wl}. "
        "For each: ticker, firm, action (UPGRADE/DOWNGRADE/INITIATE/PT RAISE/PT CUT), "
        "new rating, new price target if available, one-sentence thesis. "
        f"Sources: {SOURCES_RATINGS}.\n\n"
        "Cite each fact with source name and URL: [Source Name](url)"
    )

    # ── Search 3: Stocks in Play + Market Themes ─────────────────────────────
    log.info("Search 3/3 — stocks in play + market themes")
    results["stocks_themes"] = search(client,
        f"Today is {date_str}. Cover two things:\n\n"
        f"1) STOCKS IN PLAY: most active pre-market movers and stocks with significant "
        f"news catalysts today. Watchlist tickers first: {wl}. "
        "For each: ticker, catalyst (one phrase), why it could move today (one sentence), "
        "whether it is a watchlist name. "
        f"Sources: {SOURCES_STOCKS}.\n\n"
        "2) MARKET THEMES: 4-5 dominant sector narratives, ETF flows, and macro themes "
        "driving today's action. Include a Key Risks & Conflicting Signals table at the end "
        "with columns: Risk | Signal/Trigger | Implication. "
        f"Sources: {SOURCES_MACRO}.\n\n"
        "Cite each fact with source name and URL: [Source Name](url)"
    )

    # Optional: uncomment to re-enable Secondary Names + Week Ahead
    # log.info("Search 4/4 — secondary names + week ahead")
    # results["secondary_week"] = search(client,
    #     f"Today is {date_str}. Cover two things:\n\n"
    #     "1) SECONDARY NAMES: stocks with fresh news today that are notable but lower priority. "
    #     "Include: ticker, brief catalyst, one sentence note. "
    #     "Sources: Benzinga, Yahoo Finance, MarketWatch.\n\n"
    #     "2) WEEK AHEAD: key events for the rest of this week and next week — earnings (with dates), "
    #     "economic data releases, Fed events, major geopolitical or policy events. "
    #     "Format as a list by date. "
    #     "Sources: Earnings Whispers, Investing.com calendar, Federal Reserve, CNBC.\n\n"
    #     "Cite sources inline for both."
    # )

    for name, val in results.items():
        if not val:
            log.warning("Empty result for search: %s", name)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — GENERATE MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════════

def generate_markdown(client: OpenAI, research_data: dict[str, str], today: date) -> str:
    """Synthesize research into a structured markdown briefing."""
    date_str = today.strftime("%A, %B %d, %Y")

    usable  = sum(1 for v in research_data.values() if v and len(v.strip()) > 50)
    warning = WARNING_BANNER if usable < 2 else ""

    sections = "\n\n".join(
        f"=== {k.upper()} ===\n{v.strip() or '[No data available]'}"
        for k, v in research_data.items()
    )

    prompt = f"""Today is {date_str}.

Using the research notes below, write today's Daily Market Rundown in markdown.

OUTPUT EXACTLY these 7 sections in this order (use ## headings with numbers):

---

## 1. Macro Overview
Open with a key-levels table using ACTUAL current values from the research (not placeholders):
| Index / Asset | Level | Change | Note |
Include rows for: S&P 500 Futures, Nasdaq-100 Futures, Dow Futures, WTI Crude, Brent Crude, Gold, USD/JPY
Use real numbers from the research. If a value is unavailable write "N/A".
Then 2-3 prose paragraphs covering the main overnight narrative, geopolitical context, and Fed posture.
Cite sources as clickable markdown links: [Source Name](https://url.com)

## 2. Economic Calendar
Write exactly this line and nothing else:
[📅 MarketWatch Economic Calendar](https://www.marketwatch.com/economy-politics/calendar)

## 3. Earnings Reports
### Already Reported
One entry per ticker in this format:
**TICKER** ⭐ (if watchlist) — EPS $X.XX vs $X.XX est. Revenue $XB vs $XB est. Stock +/-X%. One-sentence takeaway. [Source Name](url)

### Reporting Today
One bullet per ticker:
- **TICKER** (Company name) — EPS est. $X.XX, Rev est. $XB. Key focus: one sentence. [Source Name](url)

### Other Majors This Week
Brief prose for notable non-watchlist names.

## 4. Analyst Ratings
### Watchlist Names
| Ticker | Firm | Action | New Rating | PT | Setup Note |

### Other Notable
| Ticker | Firm | Action | Rating | Note |

Use UPGRADE / DOWNGRADE / INITIATE / PT RAISE / PT CUT as action labels.

## 5. Stocks in Play
One entry per stock in this EXACT format (no table — use bold ticker + two lines):

**TICKER** ⭐ Watchlist (include ⭐ Watchlist only if it is a watchlist name)
Catalyst type — one-sentence description of the catalyst.
Why it moves today — one sentence on the specific intraday setup. [Source Name](url)

Watchlist names first. Order by expected volatility (highest first).

## 6. Market Themes
4-5 named themes. Each: **Bold Theme Title.** 2-3 sentence explanation. [Source Name](url)

At the end, add a Key Risks & Conflicting Signals table:
**Key Risks & Conflicting Signals**
| Risk | Signal / Trigger | Implication |

## 7. Secondary Names
| Ticker | Catalyst | Brief |

---

RULES:
- Use ACTUAL values from the research — never use placeholder values like $735 or TBD
- All source citations MUST be markdown links: [Source Name](https://actual-url.com)
- Do NOT use *via Source* italic format — always use [Source Name](url) hyperlinks
- Summarize — do not paste research verbatim
- If a section has no data, write "Nothing notable today."
- Do not add any text before ## 1. Macro Overview
- Do not add any sections beyond the 7 listed above

--- RESEARCH NOTES ---
{sections}
"""

    log.info("Generating markdown with %s...", SYNTHESIS_MODEL)
    try:
        response = client.chat.completions.create(
            model=SYNTHESIS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional pre-market research analyst. "
                        "Synthesize raw research into a clean, structured daily market briefing. "
                        "Be concise, factual, and scannable. Cite sources inline with real URLs. "
                        "Never fabricate data or invent sources."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4500,
        )
    except Exception as exc:
        log.error("Markdown generation API call failed: %s", exc)
        raise

    content = response.choices[0].message.content or ""
    if len(content.strip()) < 100:
        log.error("Generated markdown is too short (%d chars) — aborting", len(content.strip()))
        raise ValueError("LLM returned empty or near-empty markdown")

    header  = f"# Daily Market Rundown — {date_str}\n\n"
    return header + warning + content


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — HTML GENERATION  (delegated to build_dashboard.py)
# ═══════════════════════════════════════════════════════════════════════════════

def build_html(md_path: Path) -> None:
    """
    Delegate all HTML generation to build_dashboard.py.
    This guarantees the pipeline always uses the same template as local builds.
    """
    sys.path.insert(0, str(REPO_DIR))
    from build_dashboard import build_or_update  # type: ignore
    build_or_update(str(md_path))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        log.error("OPENAI_API_KEY is not set.")
        sys.exit(1)

    # ── Determine run date ────────────────────────────────────────────────────
    run_date_str = os.environ.get("RUN_DATE", "").strip()
    if run_date_str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", run_date_str):
            log.error("Invalid RUN_DATE format '%s' — expected YYYY-MM-DD", run_date_str)
            sys.exit(1)
        try:
            today = date.fromisoformat(run_date_str)
        except ValueError:
            log.error("Invalid RUN_DATE value: %s", run_date_str)
            sys.exit(1)
    else:
        today = datetime.now(CT).date()

    iso_date = today.isoformat()

    log.info("=" * 60)
    log.info("Daily Market Rundown pipeline — %s", iso_date)
    log.info("Models: search=%s  synthesis=%s", SEARCH_MODEL, SYNTHESIS_MODEL)
    log.info("=" * 60)

    # ── Guard: skip weekends ──────────────────────────────────────────────────
    if today.weekday() >= 5:
        log.info("Today is a weekend (%s). Skipping.", today.strftime("%A"))
        sys.exit(0)

    # ── Guard: skip if rundown already exists ─────────────────────────────────
    # Set FORCE_RERUN=1 in the workflow env to bypass this guard (e.g. for reruns)
    md_path = REPO_DIR / f"rundown_{iso_date}.md"
    if md_path.exists() and not os.environ.get("FORCE_RERUN"):
        log.info("Rundown for %s already exists — skipping to avoid duplicate billing.", iso_date)
        log.info("Set FORCE_RERUN=1 to override this guard.")
        sys.exit(0)

    client = OpenAI(api_key=api_key)

    # ── 1. Research ───────────────────────────────────────────────────────────
    research_data = research(client, today)
    usable = sum(1 for v in research_data.values() if v and len(v.strip()) > 50)
    log.info("Usable search results: %d / %d", usable, len(research_data))

    if usable == 0:
        log.error("All searches failed — no data returned. Aborting.")
        sys.exit(1)
    if usable < len(research_data):
        log.warning("%d of %d searches returned no data — briefing may be incomplete",
                    len(research_data) - usable, len(research_data))

    # ── 2. Generate markdown ──────────────────────────────────────────────────
    try:
        markdown = generate_markdown(client, research_data, today)
    except Exception as exc:
        log.error("Failed to generate markdown: %s", exc)
        sys.exit(1)

    # ── 3. Save markdown ──────────────────────────────────────────────────────
    try:
        md_path.write_text(markdown, encoding="utf-8")
        log.info("Saved %s", md_path.name)
    except OSError as exc:
        log.error("Failed to write %s: %s", md_path, exc)
        sys.exit(1)

    # ── 4. Build HTML (dashboard + archive) via build_dashboard.py ───────────
    try:
        build_html(md_path)
    except Exception as exc:
        log.error("HTML build failed: %s", exc)
        # Don't exit — markdown was saved successfully, HTML can be rebuilt manually
        log.error("Markdown saved at %s — re-run: python build_dashboard.py %s", md_path.name, md_path.name)

    log.info("=" * 60)
    log.info("Pipeline complete — %s", iso_date)
    log.info("Live: https://rajeev1986.github.io/daily-market-brief/market_rundown.html")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
