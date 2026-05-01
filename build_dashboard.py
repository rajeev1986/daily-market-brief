#!/usr/bin/env python3
"""
Daily Market Rundown — Dashboard Builder
Usage: python3 build_dashboard.py rundown_YYYY-MM-DD.md
Converts a daily markdown briefing into market_rundown.html,
prepending the new entry so the most recent rundown is always at the top.
Keeps the last 7 days of entries; removes the oldest when over the limit.
"""

import sys
import os
import re
from datetime import datetime
import markdown as md_lib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(SCRIPT_DIR, "market_rundown.html")
MAX_ENTRIES = 7
PLACEHOLDER = "<!-- RUNDOWNS_PLACEHOLDER -->"

# ── CSS (matches sample_market_rundown.html design) ──────────────────────────
CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d0f14; --surface: #161a23; --surface2: #1e2330; --border: #2a3044;
      --accent: #4a9eff; --accent-dim: #1e3a5f; --green: #34d399; --red: #f87171;
      --yellow: #fbbf24; --text: #e2e8f0; --text-muted: #7a8499; --text-dim: #4a5568;
      --radius: 8px; --font: 'Segoe UI', system-ui, -apple-system, sans-serif;
      --font-mono: 'Cascadia Code', 'Fira Code', 'Courier New', monospace;
    }
    html { font-size: 15px; }
    body { background: var(--bg); color: var(--text); font-family: var(--font); line-height: 1.6; min-height: 100vh; padding: 0 0 4rem; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.25rem 2rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; position: sticky; top: 0; z-index: 100; }
    header .brand { display: flex; align-items: center; gap: 1rem; text-decoration: none; }
    header .brand .logo-text { display: flex; flex-direction: column; line-height: 1.2; }
    header .brand .logo-title { font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
    header .brand .logo-sub { font-size: 0.68rem; color: var(--text-muted); font-family: var(--font-mono); letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.1rem; }
    #last-updated { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono); background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.3rem 0.75rem; white-space: nowrap; }
    main { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem 0; }
    .rundown-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 1.5rem; overflow: hidden; }
    .rundown-card .card-header { display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); background: var(--surface2); }
    .rundown-card .card-date { font-size: 0.95rem; font-weight: 600; color: var(--accent); letter-spacing: -0.01em; }
    .rundown-card .card-badge { font-size: 0.72rem; font-family: var(--font-mono); background: var(--accent-dim); color: var(--accent); border-radius: 4px; padding: 0.15rem 0.5rem; font-weight: 600; letter-spacing: 0.04em; }
    details { border-bottom: 1px solid var(--border); }
    details:last-child { border-bottom: none; }
    summary { display: flex; align-items: center; gap: 0.6rem; padding: 0.85rem 1.25rem; cursor: pointer; user-select: none; font-weight: 600; font-size: 0.875rem; color: var(--text); letter-spacing: 0.02em; text-transform: uppercase; list-style: none; transition: background 0.15s; }
    summary::-webkit-details-marker { display: none; }
    summary:hover { background: var(--surface2); }
    summary::after { content: '›'; margin-left: auto; font-size: 1.1rem; color: var(--text-dim); transition: transform 0.2s; display: inline-block; }
    details[open] summary::after { transform: rotate(90deg); }
    .section-icon { font-size: 1rem; opacity: 0.85; }
    .section-body { padding: 1rem 1.25rem 1.25rem; }
    .stocks-table { width: 100%; border-collapse: collapse; font-size: 0.835rem; }
    .stocks-table thead tr { border-bottom: 1px solid var(--border); }
    .stocks-table th { text-align: left; padding: 0.4rem 0.75rem; font-size: 0.7rem; color: var(--text-muted); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
    .stocks-table td { padding: 0.55rem 0.75rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .stocks-table tbody tr:last-child td { border-bottom: none; }
    .stocks-table tbody tr:hover { background: var(--surface2); }
    .ticker { font-weight: 700; color: var(--accent); letter-spacing: 0.04em; }
    .up { color: var(--green); } .down { color: var(--red); } .flat { color: var(--text-muted); }
    .pill { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
    .pill.up { background: rgba(52,211,153,0.12); color: var(--green); }
    .pill.down { background: rgba(248,113,113,0.12); color: var(--red); }
    .pill.flat { background: var(--surface2); color: var(--text-muted); }
    .prose { font-size: 0.88rem; color: var(--text); line-height: 1.75; }
    .prose p + p { margin-top: 0.65rem; }
    .prose strong { color: var(--text); font-weight: 600; }
    .levels-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .level-item { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.65rem 0.85rem; }
    .level-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; margin-bottom: 0.2rem; }
    .level-value { font-family: var(--font-mono); font-size: 0.95rem; font-weight: 700; }
    .level-note { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.15rem; }
    .stocks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(285px, 1fr)); gap: 0.75rem; }
    .stock-card { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem; }
    .stock-card .card-ticker { font-family: var(--font-mono); font-size: 1rem; font-weight: 700; color: var(--accent); margin-bottom: 0.25rem; }
    .stock-card .card-catalyst { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.35rem; font-weight: 600; }
    .stock-card .card-note { font-size: 0.83rem; line-height: 1.6; }
    .watchlist-badge { font-size: 0.68rem; color: var(--accent); font-family: var(--font-mono); font-weight: 700; letter-spacing: 0.03em; }
    .pill-action-up { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: rgba(52,211,153,0.12); color: var(--green); }
    .pill-action-down { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: rgba(248,113,113,0.12); color: var(--red); }
    .pill-action-flat { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: var(--surface2); color: var(--text-muted); }
    .warning-banner { background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.3); border-radius: var(--radius); padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: var(--yellow); }
    footer { border-top: 1px solid var(--border); background: var(--surface); margin-top: 2.5rem; padding: 1.5rem 2rem; text-align: center; }
    .footer-disclaimer { font-size: 0.78rem; color: var(--text-muted); max-width: 720px; margin: 0 auto 0.5rem; line-height: 1.7; }
    .footer-disclaimer strong { color: var(--yellow); }
    .footer-copy { font-size: 0.72rem; color: var(--text-dim); font-family: var(--font-mono); }
    @media (max-width: 600px) {
      header { padding: 1rem; flex-wrap: wrap; }
      main { padding: 1rem 0.75rem 0; }
      .stocks-table { font-size: 0.77rem; }
      .stocks-table th, .stocks-table td { padding: 0.45rem 0.4rem; }
      .stocks-grid { grid-template-columns: 1fr; }
    }
"""

# ── HTML shell ────────────────────────────────────────────────────────────────
SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Daily Market Rundown</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <a class="brand" href="#">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="24" cy="24" r="23" fill="#1e2330" stroke="#2a3044" stroke-width="1.5"/>
        <!-- Red candle -->
        <rect x="10" y="27" width="6" height="10" rx="1" fill="#f87171"/>
        <line x1="13" y1="24" x2="13" y2="27" stroke="#f87171" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="13" y1="37" x2="13" y2="40" stroke="#f87171" stroke-width="1.5" stroke-linecap="round"/>
        <!-- Green candle (middle) -->
        <rect x="21" y="18" width="6" height="13" rx="1" fill="#34d399"/>
        <line x1="24" y1="14" x2="24" y2="18" stroke="#34d399" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="24" y1="31" x2="24" y2="35" stroke="#34d399" stroke-width="1.5" stroke-linecap="round"/>
        <!-- Green candle (right) -->
        <rect x="32" y="13" width="6" height="16" rx="1" fill="#34d399"/>
        <line x1="35" y1="9"  x2="35" y2="13" stroke="#34d399" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="35" y1="29" x2="35" y2="33" stroke="#34d399" stroke-width="1.5" stroke-linecap="round"/>
        <!-- Trend line -->
        <polyline points="13,32 24,23 35,18" stroke="#4a9eff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.8"/>
      </svg>
      <div class="logo-text">
        <span class="logo-title">Market Rundown</span>
        <span class="logo-sub">Daily Pre-Market Brief</span>
      </div>
    </a>
    <div id="last-updated">{timestamp}</div>
  </header>
  <main>
    <div id="rundowns">
{placeholder}
    </div>
    <footer>
      <p class="footer-disclaimer">
        <strong>⚠️ For market research and informational purposes only.</strong>
        This briefing does not constitute financial advice, investment recommendations, or an offer to buy or sell any security.
        All content is aggregated from publicly available sources and is provided as-is without warranty of accuracy or completeness.
        Past market performance is not indicative of future results. Always conduct your own due diligence and consult a qualified
        financial advisor before making any investment decisions.
      </p>
      <p class="footer-copy">Daily Market Rundown &nbsp;·&nbsp; Generated automatically from public sources</p>
    </footer>
  </main>
</body>
</html>"""

# ── Section config ────────────────────────────────────────────────────────────
SECTION_ICONS = {
    "Macro Overview":      "🌐",
    "Economic Calendar":   "📅",
    "Earnings Reports":    "📣",
    "Analyst Ratings":     "🏷️",
    "Stocks in Play":      "🎯",
    "Market Themes":       "🧭",
    "Secondary Names":     "📋",
    "Week Ahead":          "🗓️",
}

OPEN_BY_DEFAULT = {"Macro Overview", "Stocks in Play"}





# ── Markdown helpers ──────────────────────────────────────────────────────────

def to_html(text: str) -> str:
    """Convert markdown to HTML with table + nl2br support."""
    return md_lib.markdown(text.strip(), extensions=["tables", "nl2br"])


# ── Section parsers ───────────────────────────────────────────────────────────

def build_macro_section(md_text: str) -> str:
    """Parse the key-levels table (if present) into .levels-grid tiles, then prose."""
    lines = md_text.strip().split("\n")
    table_lines, prose_lines = [], []
    in_table = False

    for line in lines:
        if line.startswith("|") and not in_table:
            in_table = True
        if in_table and line.startswith("|"):
            table_lines.append(line)
        elif in_table and not line.startswith("|"):
            in_table = False
            prose_lines.append(line)
        else:
            prose_lines.append(line)

    html = ""

    # Parse key-levels table into tiles
    if table_lines:
        rows = []
        for line in table_lines:
            if "---" in line or re.match(r"\|\s*Index\s*\|", line, re.I):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0]:
                rows.append(cells)

        if rows:
            html += '<div class="levels-grid">\n'
            for row in rows:
                label = row[0]
                value = row[1] if len(row) > 1 else "—"
                note  = row[2] if len(row) > 2 else ""
                # Detect direction for color
                val_class = ""
                if any(c in value for c in ["+", "↑"]):
                    val_class = " up"
                elif any(c in value for c in ["−", "-", "↓"]) and value not in ["—", "-"]:
                    val_class = " down"
                html += (
                    f'  <div class="level-item">\n'
                    f'    <div class="level-label">{label}</div>\n'
                    f'    <div class="level-value{val_class}">{value}</div>\n'
                    f'    <div class="level-note">{note}</div>\n'
                    f'  </div>\n'
                )
            html += '</div>\n'

    # Remaining prose
    prose_md = "\n".join(prose_lines).strip()
    if prose_md:
        html += f'<div class="prose">{to_html(prose_md)}</div>'

    return html


def build_calendar_section(md_text: str) -> str:
    """Economic Calendar: just render the MarketWatch link."""
    # If the section only contains a link, render it cleanly
    if "marketwatch.com/economy-politics/calendar" in md_text:
        return (
            '<div class="prose">'
            '<p>View the full economic calendar for the week on MarketWatch:</p>'
            '<p><a href="https://www.marketwatch.com/economy-politics/calendar" '
            'target="_blank" rel="noopener">�� MarketWatch Economic Calendar →</a></p>'
            '</div>'
        )
    # Fallback: render as prose
    return f'<div class="prose">{to_html(md_text)}</div>'


def build_stocks_section(md_text: str) -> str:
    """Render Stocks in Play as a card grid."""
    # Split on bold ticker lines: **TICKER** or **TICKER** ⭐
    entries = re.split(r'\n(?=\*\*[A-Z/]+)', md_text.strip())
    if len(entries) <= 1:
        # Fallback: plain prose
        return f'<div class="prose">{to_html(md_text)}</div>'

    html = '<div class="stocks-grid">\n'
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        lines = entry.split("\n")
        header = lines[0]

        # Extract ticker
        ticker_match = re.match(r'\*{0,2}([A-Z][A-Z0-9 /&.-]+?)\*{0,2}(?:\s|$)', header)
        ticker = ticker_match.group(1).strip() if ticker_match else re.sub(r'\*+', '', header.split()[0])

        is_watchlist = "⭐" in header or "Watchlist" in header

        # Remaining lines: first non-empty = catalyst, rest = note
        body_lines = [l.strip() for l in lines[1:] if l.strip()]
        catalyst = body_lines[0] if body_lines else ""
        note_lines = body_lines[1:] if len(body_lines) > 1 else []
        note = " ".join(note_lines)

        # Detect border color from catalyst/note keywords
        border_color = "var(--accent)"
        lower = (catalyst + note).lower()
        if any(w in lower for w in ["gap down", "miss", "slashed", "downgrade", "risk", "selloff"]):
            border_color = "var(--red)"
        elif any(w in lower for w in ["beat", "surge", "upgrade", "record", "buyback", "raised guidance"]):
            border_color = "var(--green)"
        elif any(w in lower for w in ["reports", "pending", "earnings", "setup"]):
            border_color = "var(--yellow)"

        watchlist_badge = (
            ' <span class="watchlist-badge">⚠ WATCHLIST</span>' if is_watchlist else ""
        )

        # Convert note markdown links
        note_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', note)
        catalyst_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', catalyst)

        html += (
            f'  <div class="stock-card" style="border-left: 3px solid {border_color};">\n'
            f'    <div class="card-ticker">{ticker}{watchlist_badge}</div>\n'
            f'    <div class="card-catalyst">{catalyst_html}</div>\n'
            f'    <div class="card-note">{note_html}</div>\n'
            f'  </div>\n'
        )
    html += '</div>'
    return html


def build_earnings_section(md_text: str) -> str:
    """Render Earnings with highlighted result cards for reported names and
    a stocks-table for upcoming names."""
    html = ""
    lines = md_text.strip().split("\n")
    current_sub = ""
    current_block = []

    def flush_block(sub, block):
        out = ""
        block_md = "\n".join(block).strip()
        if not block_md:
            return out

        if "Already Reported" in sub:
            # Each bold ticker entry becomes a highlighted result card
            entries = re.split(r'\n(?=\*\*[A-Z])', block_md)
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue
                border = "var(--accent)"
                low = entry.lower()
                if any(w in low for w in ["−9", "−17", "−2%", "miss", "slashed", "selloff", "gap down"]):
                    border = "var(--red)"
                elif any(w in low for w in ["+", "beat", "record", "surge", "raised", "buyback"]):
                    border = "var(--green)"
                elif any(w in low for w in ["mixed", "guidance", "recovering"]):
                    border = "var(--yellow)"
                entry_html = to_html(entry)
                out += (
                    f'<div style="background:var(--surface2);border:1px solid var(--border);'
                    f'border-left:3px solid {border};border-radius:var(--radius);'
                    f'padding:0.85rem 1rem;margin-bottom:0.75rem;">'
                    f'<div class="prose">{entry_html}</div></div>\n'
                )

        elif "Reporting Today" in sub or "Reporting This Week" in sub:
            # Parse bullet list entries into result cards with ticker pill + move badge
            bullet_entries = re.findall(r'^[-*]\s+(.+)$', block_md, re.MULTILINE)
            if bullet_entries:
                out += '<div style="display:flex;flex-direction:column;gap:0.6rem;">\n'
                for item in bullet_entries:
                    # Extract ticker
                    ticker_m = re.match(r'\*\*([A-Z][A-Z0-9 /&]+?)\*\*(?:\s*\([^)]+\))?', item)
                    ticker = ticker_m.group(1).strip() if ticker_m else ""

                    # Extract move/reaction — prioritize "Stock X%" pattern, then standalone
                    move_m = re.search(r'[Ss]tock\s+([\+\−\-][0-9][^\s,\.]+)', item)
                    if not move_m:
                        move_m = re.search(r'(?<!\w)([\+\−\-][0-9][0-9\.\-–]+%)', item)
                    move = move_m.group(1).strip() if move_m else ""

                    # Direction — check stock move first, then keywords
                    if move:
                        is_down = move.startswith("−") or move.startswith("-")
                        is_up = not is_down
                    else:
                        is_down = any(w in item.lower() for w in ["slash", "miss", "gap down", "plummet"])
                        is_up = any(w in item.lower() for w in ["beat", "soar", "surge", "raised guidance", "record"])
                    border = "var(--green)" if is_up else ("var(--red)" if is_down else "var(--yellow)")
                    move_class = "up" if is_up else ("down" if is_down else "flat")

                    # Body text — strip the leading **TICKER** / **TICKER** / **TICKER2** part
                    body = re.sub(r'^(?:\*\*[A-Z][A-Z0-9 /&]+\*\*\s*[/]?\s*)+(?:\([^)]+\))?\s*[—\-]\s*', '', item)
                    body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', body)
                    body = re.sub(r'\*via ([^*]+)\*', r'<em>via \1</em>', body)

                    watchlist_tickers = {"WDC","MU","LITE","CIEN","TSLA","COHR","CRDO","PLTR","TER",
                                         "LRCX","GLW","AAOI","VRT","TSM","CLS","GOOGL","STX","SNDK",
                                         "UNH","NBIS","AVGO","NVDA","AMD","HOOD","NFLX","MSFT",
                                         "AMZN","GLD","SPY","META","AAPL","ROKU"}
                    wl_badge = (
                        ' <span style="font-size:0.68rem;color:var(--accent);font-family:var(--font-mono);'
                        'font-weight:700;letter-spacing:0.03em;">⚠ WATCHLIST</span>'
                        if ticker in watchlist_tickers else ""
                    )
                    move_badge = (
                        f' <span class="pill {move_class}">{move}</span>' if move else ""
                    )

                    out += (
                        f'<div style="background:var(--surface2);border:1px solid var(--border);'
                        f'border-left:3px solid {border};border-radius:var(--radius);padding:0.75rem 1rem;">\n'
                        f'  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;flex-wrap:wrap;">\n'
                        f'    <span class="ticker">{ticker}</span>{move_badge}{wl_badge}\n'
                        f'  </div>\n'
                        f'  <p style="font-size:0.83rem;line-height:1.6;">{body}</p>\n'
                        f'</div>\n'
                    )
                out += '</div>\n'
            else:
                # Fallback: table or prose
                out = to_html(block_md).replace("<table>", '<table class="stocks-table" style="margin-bottom:1.1rem;">')
                out = re.sub(r'<th>', '<th style="text-align:left">', out)
                out = re.sub(r'<td>', '<td style="text-align:left">', out)

        else:
            # Generic sub-section: tables and prose
            out = to_html(block_md).replace("<table>", '<table class="stocks-table" style="margin-bottom:1.1rem;">')
            out = re.sub(r'<th>', '<th style="text-align:left">', out)
            out = re.sub(r'<td>', '<td style="text-align:left">', out)
            out = re.sub(r'<strong>([A-Z]{1,5})</strong>', r'<span class="ticker">\1</span>', out)
        return out

    sub_pattern = re.compile(r'^###\s+(.+)$')
    for line in lines:
        m = sub_pattern.match(line)
        if m:
            html += flush_block(current_sub, current_block)
            current_sub = m.group(1)
            label = current_sub.replace("---", "—")
            html += (
                f'<p style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;'
                f'letter-spacing:0.06em;font-weight:600;margin-bottom:0.65rem;margin-top:0.9rem;">'
                f'{label}</p>\n'
            )
            current_block = []
        else:
            current_block.append(line)

    html += flush_block(current_sub, current_block)
    return html


def build_ratings_section(md_text: str) -> str:
    """Render Analyst Ratings with proper ticker spans, pill classes, and left-aligned columns."""
    html = to_html(md_text)

    # Sub-section headers: ### → small-caps label
    html = re.sub(
        r'<h3>(.+?)</h3>',
        r'<p style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;'
        r'letter-spacing:0.06em;font-weight:600;margin-bottom:0.65rem;margin-top:0.9rem;">\1</p>',
        html
    )

    # Apply stocks-table class and left-align all columns
    html = html.replace("<table>", '<table class="stocks-table" style="margin-bottom:1.1rem;">')
    html = re.sub(r'<th>', '<th style="text-align:left">', html)
    html = re.sub(r'<td>', '<td style="text-align:left">', html)

    # Ticker cells: bold ticker text → span.ticker
    html = re.sub(r'<td style="text-align:left"><strong>([A-Z]{1,6}(?:\s[A-Z]{1,6})?)</strong>',
                  r'<td style="text-align:left"><span class="ticker">\1</span>', html)

    # Action pills — use .pill.up / .pill.down to match sample exactly
    pill_map = {
        "UPGRADE":    '<span class="pill up">UPGRADE</span>',
        "INITIATE":   '<span class="pill up">INITIATE</span>',
        "PT RAISE":   '<span class="pill up">PT RAISE</span>',
        "STRONG BUY": '<span class="pill up">STRONG BUY</span>',
        "DOWNGRADE":  '<span class="pill down">DOWNGRADE</span>',
        "PT CUT":     '<span class="pill down">PT CUT</span>',
        "HOLD":       '<span class="pill flat">HOLD</span>',
        "NEUTRAL":    '<span class="pill flat">NEUTRAL</span>',
    }
    for action, pill_html in pill_map.items():
        html = html.replace(f'>{action}<', f'>{pill_html}<')

    return html


def build_themes_section(md_text: str) -> str:
    """Render Market Themes as prose paragraphs. Key Risks table gets its own block."""
    # Split off Key Risks table if present
    risks_split = re.split(r'\*\*Key Risks.*?\*\*', md_text, maxsplit=1)
    themes_md = risks_split[0].strip()
    risks_md = risks_split[1].strip() if len(risks_split) > 1 else ""

    # Escape literal asterisks in company names
    themes_md = re.sub(r'(?<=[A-Za-z])\*(?=[A-Za-z])', r'\\*', themes_md)

    themes_html = f'<div class="prose">{to_html(themes_md)}</div>'

    if risks_md:
        risks_html = to_html(risks_md)
        risks_html = risks_html.replace(
            "<table>",
            '<table class="stocks-table" style="font-family:var(--font);font-size:0.845rem;">'
        )
        risks_html = re.sub(r'<th>', '<th style="text-align:left">', risks_html)
        risks_html = re.sub(r'<td>', '<td style="text-align:left">', risks_html)
        # Color implication cells
        risks_html = re.sub(
            r'(<td style="text-align:left">)(Oil spike|Broader|Watch SNAP|Any negative)',
            r'<td style="text-align:left;color:var(--red)">\2',
            risks_html
        )
        themes_html += (
            '\n<details style="margin-top:0.75rem;border:1px solid var(--border);border-radius:var(--radius);">'
            '\n  <summary style="padding:0.75rem 1rem;"><span class="section-icon">⚠️</span> Key Risks &amp; Conflicting Signals</summary>'
            f'\n  <div class="section-body">{risks_html}</div>'
            '\n</details>'
        )

    return themes_html


def build_generic_section(md_text: str) -> str:
    """Default: convert markdown to HTML, wrap tables in stocks-table class."""
    # Escape literal asterisks in company names like E*TRADE before markdown parsing
    md_text = re.sub(r'(?<=[A-Za-z])\*(?=[A-Za-z])', r'\\*', md_text)
    html = to_html(md_text)
    html = html.replace("<table>", '<table class="stocks-table">')
    return html


# ── Section dispatcher ────────────────────────────────────────────────────────

def build_section_content(name: str, md_text: str) -> str:
    if "Macro" in name:
        return build_macro_section(md_text)
    if "Calendar" in name:
        return build_calendar_section(md_text)
    if "Earnings" in name:
        return build_earnings_section(md_text)
    if "Analyst" in name or "Ratings" in name:
        return build_ratings_section(md_text)
    if "Stocks in Play" in name:
        return build_stocks_section(md_text)
    if "Themes" in name:
        return build_themes_section(md_text)
    return build_generic_section(md_text)


# ── Markdown parser ───────────────────────────────────────────────────────────

def parse_rundown(md_text: str):
    """Return (title, sections) where sections = list of (name, body_md)."""
    lines = md_text.strip().split("\n")
    title = ""
    sections = []
    current_name = None
    current_lines = []

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        elif re.match(r"^## \d+\.", line):
            if current_name is not None:
                sections.append((current_name, "\n".join(current_lines)))
            current_name = re.sub(r"^## \d+\.\s*", "", line).strip()
            current_lines = []
        elif line.strip() == "---":
            continue
        else:
            if current_name is not None:
                current_lines.append(line)

    if current_name is not None:
        sections.append((current_name, "\n".join(current_lines)))

    return title, sections


# ── Entry builder ─────────────────────────────────────────────────────────────

def build_entry(md_file: str) -> str:
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    title, sections = parse_rundown(md_text)

    # Extract display date from title
    date_match = re.search(r"(\w+day,\s+\w+ \d+,\s+\d{4})", title)
    display_date = date_match.group(1) if date_match else title

    # Extract ISO date from filename
    fname = os.path.basename(md_file)
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    iso_date = iso_match.group(1) if iso_match else "unknown"

    # Day of week for badge
    try:
        from datetime import date as dt_date
        d = dt_date.fromisoformat(iso_date)
        dow = d.strftime("%A").upper()
    except Exception:
        dow = "WEEKDAY"

    sections_html = ""
    for name, body in sections:
        icon = SECTION_ICONS.get(name, "•")
        open_attr = " open" if name in OPEN_BY_DEFAULT else ""
        content = build_section_content(name, body)
        sections_html += (
            f'\n        <details{open_attr}>\n'
            f'          <summary><span class="section-icon">{icon}</span> {name}</summary>\n'
            f'          <div class="section-body">{content}</div>\n'
            f'        </details>'
        )

    return (
        f'\n      <!-- ══════════════════════════════════════════════════════════════\n'
        f'           ENTRY: {iso_date}\n'
        f'           ══════════════════════════════════════════════════════════════ -->\n'
        f'      <section class="rundown-card" data-date="{iso_date}">\n'
        f'        <div class="card-header">\n'
        f'          <span class="card-date">{display_date}</span>\n'
        f'          <span class="card-badge">PRE-MARKET · {dow}</span>\n'
        f'        </div>'
        f'{sections_html}\n'
        f'      </section>'
    )


# ── Trim to MAX_ENTRIES ───────────────────────────────────────────────────────

def trim_entries(html: str) -> str:
    """Remove oldest entries beyond MAX_ENTRIES."""
    pattern = re.compile(r'<!--\s*═+.*?ENTRY:\s*\d{4}-\d{2}-\d{2}.*?-->', re.DOTALL)
    markers = list(pattern.finditer(html))
    if len(markers) <= MAX_ENTRIES:
        return html
    cutoff = markers[MAX_ENTRIES].start()
    # Find the closing </section> after the last entry to keep
    tail = html[cutoff:]
    last_close = tail.rfind("</section>")
    if last_close != -1:
        html = html[:cutoff] + html[cutoff + last_close + len("</section>"):]
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def build_or_update(md_file: str):
    timestamp = datetime.now().strftime("%b %d, %Y · %I:%M %p CT")
    new_entry = build_entry(md_file)

    # Collect existing entries from the current dashboard (if any), excluding
    # the one we're about to add (avoid duplicates on re-run).
    existing_entries = ""
    new_iso = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(md_file))
    new_date = new_iso.group(1) if new_iso else ""

    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            old_html = f.read()

        # Extract all existing <section> blocks, skip the one matching today's date
        section_pattern = re.compile(
            r'<!--\s*═+.*?ENTRY:\s*(\d{4}-\d{2}-\d{2}).*?-->.*?</section>',
            re.DOTALL
        )
        kept = []
        for m in section_pattern.finditer(old_html):
            if m.group(1) != new_date:
                kept.append(m.group(0))

        # Enforce MAX_ENTRIES (new entry counts as 1)
        kept = kept[:MAX_ENTRIES - 1]
        existing_entries = "\n".join(kept)

    combined = new_entry + ("\n" + existing_entries if existing_entries else "")

    html = SHELL.format(
        css=CSS,
        timestamp=timestamp,
        placeholder=combined + "\n      " + PLACEHOLDER
    )

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Built {DASHBOARD_FILE} — {os.path.basename(md_file)} at top")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 build_dashboard.py rundown_YYYY-MM-DD.md")
        sys.exit(1)
    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        # Try relative to script dir
        md_file = os.path.join(SCRIPT_DIR, md_file)
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found")
        sys.exit(1)
    build_or_update(md_file)
