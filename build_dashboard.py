#!/usr/bin/env python3
"""
Daily Market Rundown — Dashboard Builder
Usage: python3 build_dashboard.py rundown_YYYY-MM-DD.md
Converts a daily markdown briefing into market_rundown.html,
prepending the new entry so the most recent rundown is always at the top.
"""

import sys
import os
import re
from datetime import datetime
import markdown

# Always write output relative to this script's location (the repo root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(SCRIPT_DIR, "market_rundown.html")
PLACEHOLDER = "<!-- RUNDOWNS_PLACEHOLDER -->"
DARK_THEME_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
    font-size: 14px;
    line-height: 1.6;
}

header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 16px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
}

header h1 {
    font-size: 18px;
    font-weight: 600;
    color: #58a6ff;
    letter-spacing: 0.5px;
}

#last-updated {
    font-size: 12px;
    color: #8b949e;
}

#rundowns {
    max-width: 1100px;
    margin: 32px auto;
    padding: 0 24px;
}

.rundown-entry {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-bottom: 40px;
    overflow: hidden;
}

.entry-header {
    background: #1c2128;
    padding: 14px 24px;
    border-bottom: 1px solid #30363d;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.entry-date {
    font-size: 16px;
    font-weight: 600;
    color: #58a6ff;
}

.entry-meta {
    font-size: 12px;
    color: #8b949e;
}

.entry-body {
    padding: 0 24px 24px;
}

details {
    border-bottom: 1px solid #21262d;
    padding: 0;
}

details:last-child {
    border-bottom: none;
}

summary {
    padding: 14px 0;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    color: #c9d1d9;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 8px;
    user-select: none;
}

summary::-webkit-details-marker { display: none; }

summary::before {
    content: '▶';
    font-size: 10px;
    color: #58a6ff;
    transition: transform 0.2s;
    display: inline-block;
    width: 14px;
}

details[open] summary::before {
    transform: rotate(90deg);
}

.section-content {
    padding: 4px 0 16px 22px;
    color: #c9d1d9;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 13px;
}

th {
    background: #1c2128;
    color: #8b949e;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid #30363d;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}

td {
    padding: 8px 12px;
    border: 1px solid #21262d;
    vertical-align: top;
}

tr:nth-child(even) td {
    background: #1c2128;
}

/* Stock cards */
.stocks-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;
    margin-top: 8px;
}

.stock-card {
    background: #1c2128;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 14px 16px;
}

.stock-card .ticker-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}

.stock-card .ticker {
    font-size: 16px;
    font-weight: 700;
    color: #58a6ff;
    letter-spacing: 0.5px;
}

.stock-card .watchlist-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #2d2a00;
    color: #d29922;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid #5a4a00;
}

.stock-card .catalyst {
    font-size: 11px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
    margin-bottom: 8px;
    line-height: 1.4;
}

.stock-card .setup {
    font-size: 13px;
    color: #c9d1d9;
    line-height: 1.55;
}

.stock-card .setup a {
    color: #58a6ff;
    font-style: italic;
}

/* Analyst ratings */
.rating-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

.rating-upgrade { background: #1a4731; color: #3fb950; }
.rating-downgrade { background: #4a1a1a; color: #f85149; }
.rating-initiate { background: #1a3a5c; color: #58a6ff; }
.rating-hold { background: #2d2a1a; color: #d29922; }

/* Inline elements */
strong { color: #e6edf3; }
em { color: #8b949e; font-style: normal; font-size: 12px; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
p { margin: 6px 0; }
ul { padding-left: 20px; margin: 6px 0; }
li { margin: 4px 0; }
code { background: #1c2128; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #f0883e; }

/* Badges */
.badge-up { color: #3fb950; font-weight: 600; }
.badge-down { color: #f85149; font-weight: 600; }
.badge-flat { color: #d29922; font-weight: 600; }

/* Warning banner */
.warning-banner {
    background: #2d1f00;
    border: 1px solid #d29922;
    border-radius: 6px;
    padding: 10px 16px;
    margin: 16px 0;
    color: #d29922;
    font-size: 13px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
"""

SECTION_ICONS = {
    "Macro Overview": "🌐",
    "Economic Calendar": "📅",
    "Earnings Reports": "📊",
    "Analyst Ratings": "🎯",
    "Stocks in Play": "⚡",
    "Market Themes": "🔍",
}

SHELL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Market Rundown</title>
<style>
{css}
</style>
</head>
<body>
<header>
  <h1>📈 Daily Market Rundown</h1>
  <span id="last-updated">Last updated: {timestamp}</span>
</header>
<div id="rundowns">
{placeholder}
</div>
</body>
</html>
"""


def parse_sections(md_text):
    """Split markdown into title block + named sections."""
    lines = md_text.strip().split("\n")
    title = ""
    meta = ""
    sections = []
    current_section = None
    current_lines = []

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("*Generated:"):
            meta = line.strip("*").strip()
        elif re.match(r"^## \d+\.", line):
            if current_section is not None:
                sections.append((current_section, "\n".join(current_lines)))
            current_section = re.sub(r"^## \d+\.\s*", "", line).strip()
            current_lines = []
        elif line.strip() == "---":
            continue
        else:
            if current_section is not None:
                current_lines.append(line)

    if current_section is not None:
        sections.append((current_section, "\n".join(current_lines)))

    return title, meta, sections


def md_to_html(text):
    """Convert markdown text to HTML."""
    return markdown.markdown(
        text,
        extensions=["tables", "nl2br"],
    )


def build_stocks_section(md_text):
    """Render Stocks in Play as cards matching the target design."""
    # Split at the non-watchlist divider if present
    parts = re.split(r"\*\*Non-Watchlist Movers:\*\*", md_text, maxsplit=1)
    table_part = parts[0]
    extra_part = parts[1] if len(parts) > 1 else ""

    # Parse markdown table rows
    rows = []
    for line in table_part.split("\n"):
        if line.startswith("|") and "---" not in line and "Ticker" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                rows.append(cells)

    cards_html = '<div class="stocks-grid">'
    for row in rows:
        raw_ticker  = re.sub(r"\*\*(.+?)\*\*", r"\1", row[0]).strip()
        catalyst    = re.sub(r"\*\*(.+?)\*\*", r"\1", row[1]).strip() if len(row) > 1 else ""
        setup       = re.sub(r"\*\*(.+?)\*\*", r"\1", row[2]).strip() if len(row) > 2 else ""

        # Detect watchlist flag (⭐ WATCHLIST in ticker cell)
        is_watchlist = "WATCHLIST" in raw_ticker.upper() or "⭐" in raw_ticker
        ticker = re.sub(r"[⭐\s]*WATCHLIST", "", raw_ticker, flags=re.IGNORECASE).strip()

        watchlist_html = (
            '<span class="watchlist-badge">⭐ WATCHLIST</span>'
            if is_watchlist else ""
        )

        # Convert *via Source* style citations in setup to italic links
        setup_html = re.sub(
            r"\*via ([^*]+)\*",
            r"<em>via \1</em>",
            setup
        )

        cards_html += f"""
        <div class="stock-card">
          <div class="ticker-row">
            <span class="ticker">{ticker}</span>
            {watchlist_html}
          </div>
          <div class="catalyst">{catalyst}</div>
          <div class="setup">{setup_html}</div>
        </div>"""
    cards_html += "</div>"

    if extra_part.strip():
        cards_html += '<p style="margin-top:14px;font-weight:600;color:#8b949e;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Other Movers</p>'
        cards_html += md_to_html(extra_part.strip())

    return cards_html


def build_ratings_section(md_text):
    """Render Analyst Ratings table with colored badges."""
    html = md_to_html(md_text)
    # Inject badge classes based on action keywords
    html = re.sub(r"<td>Downgrade</td>", '<td><span class="rating-badge rating-downgrade">Downgrade</span></td>', html)
    html = re.sub(r"<td>Initiate Buy</td>", '<td><span class="rating-badge rating-initiate">Initiate Buy</span></td>', html)
    html = re.sub(r"<td>Upgrade</td>", '<td><span class="rating-badge rating-upgrade">Upgrade</span></td>', html)
    html = re.sub(r"<td>Hold</td>", '<td><span class="rating-badge rating-hold">Hold</span></td>', html)
    return html


def build_entry_html(md_file):
    """Build a full rundown entry HTML block from a markdown file."""
    with open(md_file, "r") as f:
        md_text = f.read()

    title, meta, sections = parse_sections(md_text)

    # Extract date from title or filename
    date_match = re.search(r"(\w+ \d+, \d{4})", title)
    display_date = date_match.group(1) if date_match else title

    # data-date from filename
    fname = os.path.basename(md_file)
    data_date_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    data_date = data_date_match.group(1) if data_date_match else "unknown"

    sections_html = ""
    for section_name, section_md in sections:
        icon = SECTION_ICONS.get(section_name, "•")

        if "Stocks in Play" in section_name:
            content_html = build_stocks_section(section_md)
        elif "Analyst Ratings" in section_name:
            content_html = build_ratings_section(section_md)
        else:
            content_html = md_to_html(section_md)

        # Default open for top 3 sections
        open_attr = "open" if section_name in ["Macro Overview", "Stocks in Play", "Analyst Ratings"] else ""

        sections_html += f"""
  <details {open_attr}>
    <summary>{icon} {section_name}</summary>
    <div class="section-content">
      {content_html}
    </div>
  </details>"""

    entry = f"""<section class="rundown-entry" data-date="{data_date}">
  <div class="entry-header">
    <span class="entry-date">📅 {display_date}</span>
    <span class="entry-meta">{meta}</span>
  </div>
  <div class="entry-body">
    {sections_html}
  </div>
</section>"""

    return entry


def build_or_update_dashboard(md_file):
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p CT")
    new_entry = build_entry_html(md_file)

    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r") as f:
            existing = f.read()

        # Update timestamp
        existing = re.sub(
            r'Last updated:.*?</span>',
            f'Last updated: {timestamp}</span>',
            existing
        )

        # Prepend new entry before the placeholder comment (or first existing entry)
        if PLACEHOLDER in existing:
            updated = existing.replace(PLACEHOLDER, new_entry + "\n" + PLACEHOLDER)
        else:
            updated = existing.replace('<div id="rundowns">', f'<div id="rundowns">\n{new_entry}')

        with open(DASHBOARD_FILE, "w") as f:
            f.write(updated)
        print(f"✅ Updated {DASHBOARD_FILE} — prepended entry for {md_file}")
    else:
        # First run — create the shell
        html = SHELL_TEMPLATE.format(
            css=DARK_THEME_CSS,
            timestamp=timestamp,
            placeholder=new_entry + "\n" + PLACEHOLDER,
        )
        with open(DASHBOARD_FILE, "w") as f:
            f.write(html)
        print(f"✅ Created {DASHBOARD_FILE} with entry for {md_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 build_dashboard.py rundown_YYYY-MM-DD.md")
        sys.exit(1)

    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found")
        sys.exit(1)

    build_or_update_dashboard(md_file)
