"""
Daily Market Rundown — GitHub Actions Pipeline Script

Runs the full pipeline:
  1. Research (OpenAI web_search tool, 8 categories)
  2. Generate markdown briefing
  3. Save rundown_YYYY-MM-DD.md
  4. Update market_rundown.html (prepend + trim to 7 days)
  5. Write archive/YYYY-MM-DD.html
  6. Update archive/index.html

Git commit + push is handled by the workflow YAML (step 6).
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

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("rundown")

# ── Constants ─────────────────────────────────────────────────────────────
REPO_DIR   = Path(__file__).parent.parent.parent  # daily-market-brief/
MAX_ENTRIES = 7
CT = ZoneInfo("America/Chicago")

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


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — RESEARCH
# ═══════════════════════════════════════════════════════════════════════════

def search(client: OpenAI, prompt: str) -> str:
    """Call OpenAI Responses API with web_search_preview tool."""
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        return block.text
    except Exception as exc:
        log.warning("Search failed: %s", exc)
    return ""


def research(client: OpenAI, today: date) -> dict[str, str]:
    """Run research using 4 combined searches instead of 8 serial ones."""
    date_str = today.strftime("%B %d, %Y")
    wl       = ", ".join(WATCHLIST)
    results  = {}

    # ── Combined search 1: Macro + Economic Calendar ──────────────────
    log.info("Researching: macro + economic_calendar")
    text = search(client,
        f"Today is {date_str}. Search for two things:\n"
        "1) Pre-market macro conditions: overnight futures (S&P 500, Nasdaq, Dow), "
        "global market moves (Asia, Europe), Fed commentary, geopolitical events, "
        "currency moves (USD, JPY, EUR), oil and gold prices. "
        "Sources: Reuters, Bloomberg, CNBC, MarketWatch, Yahoo Finance.\n"
        "2) Today's U.S. economic data releases and Fed speaker events: "
        "event name, time ET, consensus estimate, prior value. "
        "Sources: Investing.com, ForexFactory, BLS.gov, Federal Reserve. "
        "If no major releases today, state that clearly.\n"
        "Summarize each part in 4-6 bullet points. Cite sources inline."
    )
    results["macro"] = text
    results["economic_calendar"] = text  # same search, split by LLM at synthesis

    # ── Combined search 2: Earnings + Analyst Ratings ─────────────────
    log.info("Researching: earnings + analyst_ratings")
    text = search(client,
        f"Today is {date_str}. Search for two things:\n"
        f"1) Companies reporting earnings today (pre-market and after-hours). "
        f"Watchlist tickers first: {wl}. "
        "For each: ticker, EPS actual vs estimate, revenue actual vs estimate, stock reaction. "
        "Sources: Earnings Whispers, Yahoo Finance, MarketWatch, CNBC.\n"
        f"2) Today's analyst upgrades, downgrades, initiations, and price target changes. "
        f"Watchlist first: {wl}. "
        "For each: ticker, firm, action, new rating, price target, one-sentence thesis. "
        "Sources: Benzinga, MarketBeat, TheStreet, Tipranks, CNBC.\n"
        "Cite sources inline for both."
    )
    results["earnings"] = text
    results["analyst_ratings"] = text  # same search, split by LLM at synthesis

    # ── Combined search 3: Stocks in Play + Market Themes ─────────────
    log.info("Researching: stocks_in_play + market_themes")
    text = search(client,
        f"Today is {date_str}. Search for two things:\n"
        f"1) Most active pre-market movers and stocks with significant news catalysts. "
        f"Watchlist first: {wl}. "
        "For each: ticker, % move pre-market, catalyst, one sentence on why it could move. "
        "Sources: Benzinga, Finviz, MarketBeat, Yahoo Finance, CNBC pre-market movers.\n"
        "2) Dominant sector narratives, ETF flows, and broader market themes driving today's action. "
        "What sectors are leading/lagging? 3-4 key themes. "
        "Sources: ETF.com, Sector SPDRs, Yahoo Finance, MarketWatch, Seeking Alpha.\n"
        "Cite sources inline for both."
    )
    results["stocks_in_play"] = text
    results["market_themes"] = text  # same search, split by LLM at synthesis

    # ── Combined search 4: Secondary Names + Week Ahead ───────────────
    log.info("Researching: secondary_names + week_ahead")
    text = search(client,
        f"Today is {date_str}. Search for two things:\n"
        "1) Stocks with fresh news today that are notable but lower priority movers. "
        "Include: ticker, brief catalyst, one sentence note. "
        "Sources: Benzinga, Yahoo Finance, MarketWatch.\n"
        "2) Key events for the rest of this week and next week: earnings (with dates), "
        "economic data releases, Fed events, major geopolitical or policy events. "
        "Format as a list by date. "
        "Sources: Earnings Whispers, Investing.com calendar, Federal Reserve, CNBC.\n"
        "Cite sources inline for both."
    )
    results["secondary_names"] = text
    results["week_ahead"] = text  # same search, split by LLM at synthesis

    # Log any empty results
    for name, val in results.items():
        if not val:
            log.warning("No data returned for: %s", name)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — GENERATE MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════

def generate_markdown(client: OpenAI, research_data: dict[str, str], today: date) -> str:
    """Synthesize research into a structured markdown briefing."""
    date_str = today.strftime("%A, %B %d, %Y")

    usable = sum(1 for v in research_data.values() if v and len(v.strip()) > 50)
    warning = WARNING_BANNER if usable < 3 else ""

    sections = "\n\n".join(
        f"=== {k.upper().replace('_', ' ')} ===\n{v.strip() or '[No data available]'}"
        for k, v in research_data.items()
    )

    prompt = f"""Today is {date_str}.

Using the research notes below, write today's Daily Market Rundown in markdown.

REQUIRED SECTIONS (in this exact order, use ## headings):

## 1. Macro Overview
Key overnight and pre-market macro developments. 4-6 bullet points.

## 2. Economic Calendar
Today's scheduled data releases and Fed events. Markdown table:
| Event | Time (ET) | Expected | Prior | Notes |

## 3. Earnings Reports
Notable results. Markdown table: | Ticker | Result | vs. Estimate | Reaction |
Flag watchlist names with ⭐.

## 4. Analyst Ratings
Today's upgrades/downgrades/initiations. Watchlist names first.
Table: | Ticker | Firm | Action | Rating | Price Target | Note |

## 5. Stocks in Play
Primary movers with clear catalysts. Watchlist names first.
Table or list: Ticker | Catalyst | Why it could move today

## 6. Market Themes
3-4 dominant sector narratives or macro themes.

## 7. Secondary Names
Bullet list of stocks with fresh news but lower priority.

## 8. Week Ahead
Key events for the rest of the week.
Table: | Date | Event/Ticker | Notes |

RULES:
- Summarize — do not paste research verbatim
- Cite each major data point inline: *via Source*
- If a section has no data, write "Nothing notable today."
- Do not add any text before ## 1. Macro Overview

--- RESEARCH NOTES ---
{sections}
"""

    log.info("Generating markdown briefing...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional pre-market research analyst. "
                    "Synthesize raw research into a clean, structured daily market briefing. "
                    "Be concise, factual, and scannable. Cite sources inline. Never fabricate data."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content or ""
    header  = f"# Daily Market Rundown — {date_str}\n\n"
    return header + warning + content


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — CONVERT MARKDOWN → HTML ENTRY
# ═══════════════════════════════════════════════════════════════════════════

def markdown_to_html_entry(client: OpenAI, markdown: str, today: date) -> str:
    """Convert markdown briefing to an HTML entry block using local Python converter."""
    import sys
    sys.path.insert(0, str(REPO_DIR))
    from build_dashboard import build_entry_html
    import tempfile, os

    iso_date     = today.isoformat()
    display_date = today.strftime("%A, %B %d, %Y")
    now_et       = datetime.now(ZoneInfo("America/New_York"))
    timestamp_et = now_et.strftime("%-I:%M %p ET")

    # Write markdown to a temp file so build_entry_html can read it
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f"_{iso_date}.md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(markdown)
        tmp_path = tmp.name

    try:
        log.info("Converting markdown to HTML entry (local converter)...")
        html = build_entry_html(tmp_path)
    finally:
        os.unlink(tmp_path)

    return html


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — UPDATE market_rundown.html
# ═══════════════════════════════════════════════════════════════════════════

def update_main_html(html_entry: str, iso_date: str, timestamp_ct: str) -> None:
    """Prepend new entry to market_rundown.html and trim to MAX_ENTRIES."""
    path    = REPO_DIR / "market_rundown.html"
    content = path.read_text(encoding="utf-8")

    # Update last-updated timestamp
    content = re.sub(
        r'(<span id="last-updated">)[^<]*(</span>)',
        rf'\g<1>Last updated: {timestamp_ct}\g<2>',
        content,
    )

    # Prepend new entry
    marker    = '<div id="rundowns">'
    new_block = (
        f'\n\n      <!-- ═══════════════════════════════════════════════════════════ -->\n'
        f'      <!-- ENTRY: {iso_date}                                           -->\n'
        f'      <!-- ═══════════════════════════════════════════════════════════ -->\n'
        f'      {html_entry}\n'
    )
    content = content.replace(marker, marker + new_block, 1)

    # Trim to MAX_ENTRIES
    content = trim_entries(content)

    path.write_text(content, encoding="utf-8")
    log.info("Updated market_rundown.html")


def trim_entries(content: str) -> str:
    """Remove entries beyond MAX_ENTRIES from market_rundown.html."""
    marker_re = re.compile(
        r'<!-- ═+.*?ENTRY: \d{4}-\d{2}-\d{2}.*?-->', re.DOTALL
    )
    markers = list(marker_re.finditer(content))
    if len(markers) <= MAX_ENTRIES:
        return content

    cutoff_pos       = markers[MAX_ENTRIES].start()
    tail             = content[cutoff_pos:]
    last_section_end = tail.rfind("</section>")
    if last_section_end != -1:
        content = content[:cutoff_pos] + content[cutoff_pos + last_section_end + len("</section>"):]
    return content


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — WRITE archive/YYYY-MM-DD.html
# ═══════════════════════════════════════════════════════════════════════════

ARCHIVE_FOOTER = """
  <footer id="page-footer">
    <p class="footer-disclaimer">
      <strong>⚠️ For market research and informational purposes only.</strong>
      This briefing does not constitute financial advice, investment recommendations, or an offer to buy or sell any security.
      All content is aggregated from publicly available sources and is provided as-is without warranty of accuracy or completeness.
      Past market performance is not indicative of future results. Always conduct your own due diligence and consult a qualified
      financial advisor before making any investment decisions.
    </p>
    <p class="footer-copy">© 2026 Rajeev Piyare &nbsp;·&nbsp; Daily Market Rundown &nbsp;·&nbsp; All rights reserved.</p>
  </footer>"""

ARCHIVE_CSS = """
    :root {
      --bg:#0d0f14; --surface:#161a22; --surface-alt:#1e2330; --border:#2a2f3d;
      --accent:#4f8ef7; --accent-dim:#2d5299; --green:#3ecf6e; --red:#f75f5f;
      --yellow:#f7c948; --text:#e2e6f0; --text-muted:#7a8299; --radius:8px;
      --font:'Segoe UI',system-ui,-apple-system,sans-serif;
      --mono:'Cascadia Code','Fira Code','Consolas',monospace;
    }
    body { background:var(--bg); color:var(--text); font-family:var(--font); font-size:15px; line-height:1.6; padding:0 0 60px; }
    a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
    #page-header { background:var(--surface); border-bottom:1px solid var(--border); padding:16px 32px; display:flex; align-items:center; gap:16px; position:sticky; top:0; z-index:100; }
    #page-header h1 { font-size:1.1rem; font-weight:700; }
    .nav-links { display:flex; gap:12px; margin-left:auto; font-size:0.82rem; font-family:var(--mono); }
    .nav-links a { background:var(--surface-alt); border:1px solid var(--border); border-radius:5px; padding:5px 12px; }
    .nav-links a:hover { background:var(--border); text-decoration:none; }
    #main { max-width:960px; margin:0 auto; padding:32px 24px; }
    .rundown-entry { margin-bottom:40px; border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; }
    .rundown-entry-header { background:var(--surface-alt); padding:14px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:12px; }
    .rundown-entry-header h2 { font-size:1.05rem; font-weight:600; color:var(--accent); font-family:var(--mono); }
    .rundown-entry-header .entry-meta { font-size:0.78rem; color:var(--text-muted); }
    details { border-bottom:1px solid var(--border); } details:last-child { border-bottom:none; }
    summary { padding:12px 20px; cursor:pointer; font-weight:600; font-size:0.88rem; letter-spacing:0.04em; text-transform:uppercase; color:var(--text-muted); background:var(--surface); list-style:none; display:flex; align-items:center; gap:8px; user-select:none; transition:background 0.15s,color 0.15s; }
    summary::-webkit-details-marker { display:none; }
    summary::before { content:'▶'; font-size:0.65rem; color:var(--accent-dim); transition:transform 0.2s; flex-shrink:0; }
    details[open]>summary::before { transform:rotate(90deg); }
    details[open]>summary { color:var(--text); background:var(--surface-alt); } summary:hover { background:var(--surface-alt); color:var(--text); }
    .section-body { padding:16px 20px; background:var(--surface); }
    .section-body p { margin-bottom:10px; } .section-body p:last-child { margin-bottom:0; }
    .section-body ul { padding-left:18px; margin-bottom:10px; } .section-body li { margin-bottom:6px; }
    .stock-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; padding:16px 20px; background:var(--surface); }
    .stock-card { background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; }
    .stock-card .ticker { font-family:var(--mono); font-size:1rem; font-weight:700; color:var(--accent); margin-bottom:4px; }
    .stock-card .catalyst { font-size:0.78rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }
    .stock-card .note { font-size:0.85rem; color:var(--text); line-height:1.5; }
    .badge { display:inline-block; font-size:0.7rem; font-family:var(--mono); padding:2px 7px; border-radius:4px; font-weight:600; margin-left:6px; vertical-align:middle; }
    .badge-up { background:#1a3d2b; color:var(--green); } .badge-down { background:#3d1a1a; color:var(--red); } .badge-watch { background:#3d3010; color:var(--yellow); }
    .ratings-table, .calendar-table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    .ratings-table th, .calendar-table th { text-align:left; padding:8px 12px; background:var(--surface-alt); color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; border-bottom:1px solid var(--border); }
    .ratings-table td, .calendar-table td { padding:8px 12px; border-bottom:1px solid var(--border); vertical-align:top; }
    .ratings-table tr:last-child td, .calendar-table tr:last-child td { border-bottom:none; }
    .ratings-table tr:hover td, .calendar-table tr:hover td { background:var(--surface-alt); }
    .ticker-cell { font-family:var(--mono); font-weight:700; color:var(--accent); }
    .warning-banner { background:#3d2e00; border:1px solid #7a5c00; border-radius:var(--radius); padding:10px 16px; margin:12px 20px; font-size:0.88rem; color:var(--yellow); }
    #page-footer { border-top:1px solid var(--border); background:var(--surface); padding:24px 32px; margin-top:40px; text-align:center; }
    #page-footer .footer-disclaimer { font-size:0.78rem; color:var(--text-muted); max-width:720px; margin:0 auto 10px; line-height:1.6; }
    #page-footer .footer-disclaimer strong { color:var(--yellow); }
    #page-footer .footer-copy { font-size:0.75rem; color:var(--text-muted); font-family:var(--mono); opacity:0.6; }
    #logo { display:flex; align-items:center; gap:10px; text-decoration:none; }
    #logo-text { display:flex; flex-direction:column; line-height:1.2; }
    #logo-text .logo-title { font-size:1rem; font-weight:700; color:var(--text); }
    #logo-text .logo-sub { font-size:0.65rem; color:var(--text-muted); font-family:var(--mono); letter-spacing:0.06em; text-transform:uppercase; }
    ::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:var(--bg); }
    ::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
    @media (max-width: 640px) {
      #page-header { padding:12px 16px; flex-wrap:wrap; gap:10px; }
      #logo { flex:1 1 100%; }
      #logo-text .logo-title { font-size:0.95rem; }
      #logo-text .logo-sub { display:none; }
      .nav-links { margin-left:0; width:100%; justify-content:flex-end; }
      #main { padding:16px 12px; }
      .rundown-entry-header { flex-direction:column; align-items:flex-start; gap:4px; padding:12px 14px; }
      .rundown-entry-header h2 { font-size:0.95rem; }
      summary { padding:11px 14px; font-size:0.82rem; }
      .section-body { padding:14px 14px; font-size:0.88rem; overflow-x:auto; -webkit-overflow-scrolling:touch; }
      .ratings-table, .calendar-table { font-size:0.78rem; min-width:480px; }
      .ratings-table th, .ratings-table td, .calendar-table th, .calendar-table td { padding:6px 8px; }
      .stock-grid { grid-template-columns:1fr; padding:12px 14px; gap:10px; }
      .badge { font-size:0.65rem; padding:2px 5px; }
      .rundown-entry { margin-bottom:24px; }
      #page-footer { padding:20px 16px; }
      #page-footer .footer-disclaimer { font-size:0.73rem; }
      #page-footer .footer-copy { font-size:0.7rem; }
    }
    @media (min-width:641px) and (max-width:900px) {
      #page-header { padding:16px 20px; }
      #main { padding:24px 16px; }
      .stock-grid { grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); }
      .section-body { overflow-x:auto; -webkit-overflow-scrolling:touch; }
    }"""


def write_archive_page(html_entry: str, iso_date: str, display_date: str) -> None:
    """Write a standalone archive page for this day."""
    archive_dir = REPO_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)

    logo_svg = """<svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="18" cy="18" r="17" fill="#1e2330" stroke="#2a2f3d" stroke-width="1.5"/>
        <rect x="8"  y="20" width="4" height="8"  rx="1" fill="#f75f5f"/>
        <line x1="10" y1="18" x2="10" y2="20" stroke="#f75f5f" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="10" y1="28" x2="10" y2="30" stroke="#f75f5f" stroke-width="1.5" stroke-linecap="round"/>
        <rect x="16" y="14" width="4" height="10" rx="1" fill="#3ecf6e"/>
        <line x1="18" y1="11" x2="18" y2="14" stroke="#3ecf6e" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="18" y1="24" x2="18" y2="27" stroke="#3ecf6e" stroke-width="1.5" stroke-linecap="round"/>
        <rect x="24" y="11" width="4" height="12" rx="1" fill="#3ecf6e"/>
        <line x1="26" y1="8"  x2="26" y2="11" stroke="#3ecf6e" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="26" y1="23" x2="26" y2="26" stroke="#3ecf6e" stroke-width="1.5" stroke-linecap="round"/>
        <polyline points="10,24 18,17 26,13" stroke="#4f8ef7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.7"/>
      </svg>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Market Rundown — {display_date}</title>
  <style>
{ARCHIVE_CSS}
  </style>
</head>
<body>
  <header id="page-header">
    <a href="../market_rundown.html" id="logo">
      {logo_svg}
      <div id="logo-text">
        <span class="logo-title">Market Rundown</span>
        <span class="logo-sub">Daily Pre-Market Brief</span>
      </div>
    </a>
    <nav class="nav-links">
      <a href="index.html">📁 All Archives</a>
      <a href="../market_rundown.html">⬅ Latest</a>
    </nav>
  </header>
  <main id="main">
    {html_entry}
  </main>
  <footer id="page-footer">
    <p class="footer-disclaimer">
      <strong>⚠️ For market research and informational purposes only.</strong>
      This briefing does not constitute financial advice, investment recommendations, or an offer to buy or sell any security.
      All content is aggregated from publicly available sources and is provided as-is without warranty of accuracy or completeness.
      Past market performance is not indicative of future results. Always conduct your own due diligence and consult a qualified
      financial advisor before making any investment decisions.
    </p>
    <p class="footer-copy">© 2026 Rajeev Piyare &nbsp;·&nbsp; Daily Market Rundown &nbsp;·&nbsp; All rights reserved.</p>
  </footer>
</body>
</html>"""

    (archive_dir / f"{iso_date}.html").write_text(page, encoding="utf-8")
    log.info("Wrote archive/%s.html", iso_date)


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6 — UPDATE archive/index.html
# ═══════════════════════════════════════════════════════════════════════════

def update_archive_index(iso_date: str, markdown: str) -> None:
    """Prepend a new row to archive/index.html."""
    index_path = REPO_DIR / "archive" / "index.html"
    if not index_path.exists():
        log.warning("archive/index.html not found — skipping index update")
        return

    today      = date.fromisoformat(iso_date)
    dow        = today.strftime("%A")
    year       = iso_date[:4]
    month_name = today.strftime("%B")
    headline   = _extract_headline(markdown)

    content = index_path.read_text(encoding="utf-8")

    new_row = (
        f'\n          <li class="entry-item">\n'
        f'            <span class="entry-date">{iso_date}</span>\n'
        f'            <span class="entry-dow">{dow}</span>\n'
        f'            <a class="entry-link" href="{iso_date}.html">{headline}</a>\n'
        f'            <span class="entry-badge">Pre-Market</span>\n'
        f'          </li>'
    )

    # Try to insert into existing month section
    month_re = re.compile(
        rf'(<div class="month-label">{month_name}</div>\s*<ul class="entry-list">)',
        re.DOTALL,
    )
    m = month_re.search(content)
    if m:
        content = content[: m.end()] + new_row + content[m.end() :]
    else:
        # Create new month block inside existing year group
        year_re = re.compile(rf'(<div class="year-label">{year}</div>)', re.DOTALL)
        ym = year_re.search(content)
        new_month = (
            f'\n\n      <div class="month-group">\n'
            f'        <div class="month-label">{month_name}</div>\n'
            f'        <ul class="entry-list">{new_row}\n\n        </ul>\n'
            f'      </div>'
        )
        if ym:
            content = content[: ym.end()] + new_month + content[ym.end() :]
        else:
            # New year entirely
            new_year = (
                f'\n    <div class="year-group">\n'
                f'      <div class="year-label">{year}</div>'
                f'{new_month}\n'
                f'    </div>\n'
            )
            content = content.replace("  </main>", new_year + "  </main>", 1)

    index_path.write_text(content, encoding="utf-8")
    log.info("Updated archive/index.html")


def _extract_headline(markdown: str) -> str:
    """Pull a one-line headline from the markdown for the archive index."""
    for line in markdown.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if len(line) > 30 and not line.startswith("#"):
            return (line[:120] + "…") if len(line) > 120 else line
    return "Daily Market Rundown"


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        log.error("OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    # Determine run date
    run_date_str = os.environ.get("RUN_DATE", "")
    if run_date_str:
        try:
            today = date.fromisoformat(run_date_str)
        except ValueError:
            log.error("Invalid RUN_DATE: %s", run_date_str)
            sys.exit(1)
    else:
        today = datetime.now(CT).date()

    iso_date     = today.isoformat()
    display_date = today.strftime("%A, %B %d, %Y")
    now_ct       = datetime.now(CT)
    timestamp_ct = now_ct.strftime("%A, %B %d, %Y — %-I:%M %p CT")

    log.info("=" * 60)
    log.info("Daily Market Rundown pipeline — %s", iso_date)
    log.info("=" * 60)

    # ── Guard: skip weekends ──────────────────────────────────────────
    if today.weekday() >= 5:  # 5=Saturday, 6=Sunday
        log.info("Today is a weekend (%s). Skipping run.", today.strftime("%A"))
        sys.exit(0)

    # ── Guard: skip if today's rundown already exists ─────────────────
    md_path = REPO_DIR / f"rundown_{iso_date}.md"
    if md_path.exists():
        log.info("Rundown for %s already exists (%s). Skipping to avoid duplicate billing.",
                 iso_date, md_path.name)
        sys.exit(0)

    client = OpenAI(api_key=api_key)

    # ── 1. Research ───────────────────────────────────────────────────
    research_data = research(client, today)
    usable = sum(1 for v in research_data.values() if v and len(v.strip()) > 50)
    log.info("Usable research categories: %d / %d", usable, len(research_data))

    if usable == 0:
        log.error("No research data returned. Aborting to avoid empty rundown.")
        sys.exit(1)

    # ── 2. Generate markdown ──────────────────────────────────────────
    markdown = generate_markdown(client, research_data, today)

    # ── 3. Save markdown ──────────────────────────────────────────────
    md_path.write_text(markdown, encoding="utf-8")
    log.info("Saved %s", md_path.name)

    # ── 4. Convert to HTML entry ──────────────────────────────────────
    html_entry = markdown_to_html_entry(client, markdown, today)

    # ── 5. Update market_rundown.html ─────────────────────────────────
    update_main_html(html_entry, iso_date, timestamp_ct)

    # ── 6. Write archive page ─────────────────────────────────────────
    write_archive_page(html_entry, iso_date, display_date)

    # ── 7. Update archive index ───────────────────────────────────────
    update_archive_index(iso_date, markdown)

    log.info("=" * 60)
    log.info("Pipeline complete for %s", iso_date)
    log.info("Live at: https://rajeev1986.github.io/daily-market-brief/market_rundown.html")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
