"""Visual theme and reusable UI fragments for the DFARS assistant."""

from __future__ import annotations

import html

from src.models import RetrievedSection

#: Global stylesheet. Defines design tokens in :root and restyles Streamlit
#: defaults for a professional, document-forward look.
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');

:root {
  --navy-900: #0b1f3a;
  --navy-700: #13315c;
  --navy-600: #1c4587;
  --accent:   #2563eb;
  --accent-soft: #e8f0fe;
  --ink:      #1a2433;
  --muted:    #5b6675;
  --line:     #e4e8ee;
  --surface:  #ffffff;
  --canvas:   #f4f6fa;
  --good:     #0f766e;
  --radius:   14px;
  --shadow:   0 1px 2px rgba(16,24,40,.04), 0 8px 24px rgba(16,24,40,.06);
}

html, body, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
.stApp { background: var(--canvas); }
.block-container { padding-top: 2.2rem; max-width: 980px; }

/* Hero header */
.dfars-hero {
  background: linear-gradient(135deg, var(--navy-900) 0%, var(--navy-600) 100%);
  border-radius: var(--radius);
  padding: 1.6rem 1.8rem;
  color: #fff;
  box-shadow: var(--shadow);
  margin-bottom: 1.4rem;
}
.dfars-hero .eyebrow {
  font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
  color: #9db8e6; font-weight: 600; margin-bottom: .35rem;
}
.dfars-hero h1 {
  font-size: 1.7rem; font-weight: 700; margin: 0; line-height: 1.15; color:#fff;
}
.dfars-hero p { margin: .5rem 0 0; color: #c8d6ee; font-size: .95rem; max-width: 60ch; }

/* Section labels */
.dfars-label {
  font-size: .74rem; letter-spacing: .1em; text-transform: uppercase;
  color: var(--muted); font-weight: 600; margin: 1.4rem 0 .6rem;
}

/* Answer card */
.dfars-answer {
  background: var(--surface); border: 1px solid var(--line);
  border-left: 4px solid var(--accent);
  border-radius: var(--radius); padding: 1.3rem 1.5rem;
  box-shadow: var(--shadow);
  font-family: 'Source Serif 4', Georgia, serif; font-size: 1.02rem; line-height: 1.6;
  color: var(--ink);
}
.dfars-answer p:first-child { margin-top: 0; }

/* Badges / pills */
.dfars-badges { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; margin-bottom: .25rem; }
.pill {
  display: inline-flex; align-items: center; gap: .3rem;
  font-size: .76rem; font-weight: 600; padding: .18rem .55rem; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); background: #fafbfc;
}
.pill.id { background: var(--navy-700); color:#fff; border-color: var(--navy-700); letter-spacing:.02em; }
.pill.method-exact { background:#ecfdf5; color: var(--good); border-color:#bbf7d0; }
.pill.method-bm25 { background: var(--accent-soft); color: var(--navy-600); border-color:#cfe0fb; }
.pill.method-vector { background:#f5f3ff; color:#6d28d9; border-color:#e9d5ff; }
.pill.pages { background:#fff; }
.topic {
  display:inline-block; font-size:.74rem; color: var(--navy-600);
  background: var(--accent-soft); border:1px solid #d7e4fb;
  padding:.12rem .5rem; border-radius:6px; margin:.15rem .25rem .15rem 0;
}
.sec-title { font-size:1.02rem; font-weight:600; color: var(--ink); margin:.35rem 0 .15rem; }

/* Buttons */
.stButton > button {
  background: var(--accent); color:#fff; border:0; border-radius:10px;
  padding:.55rem 1.4rem; font-weight:600; font-size:.95rem;
  box-shadow: 0 1px 2px rgba(37,99,235,.3); transition: filter .15s ease;
}
.stButton > button:hover { filter: brightness(1.07); color:#fff; }
.stButton > button:disabled { background:#aebfd6; box-shadow:none; }

/* Inputs */
.stTextArea textarea {
  border-radius: 12px !important; border:1px solid var(--line) !important;
  font-size: 1rem !important; background: var(--surface) !important;
}
.stTextArea textarea:focus { border-color: var(--accent) !important; box-shadow:0 0 0 3px var(--accent-soft) !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--surface); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] .dfars-brand { font-weight:700; color:var(--navy-700); font-size:1.05rem; }

/* Disclaimer */
.dfars-footer {
  margin-top: 2rem; padding-top: 1rem; border-top:1px solid var(--line);
  color: var(--muted); font-size:.8rem; line-height:1.5;
}
#MainMenu, footer { visibility: hidden; }
</style>
"""


def hero() -> str:
    """Return the hero header HTML."""
    return (
        '<div class="dfars-hero">'
        '<div class="eyebrow">Defense Federal Acquisition Regulation Supplement</div>'
        "<h1>DFARS Context Assistant</h1>"
        "<p>Cited answers grounded in indexed DFARS sections. Ask about a clause, "
        "an applicability condition, or a definition.</p>"
        "</div>"
    )


def section_header(result: RetrievedSection) -> str:
    """Return the badge + title HTML for a retrieved section."""
    section = result.section
    method = html.escape(result.retrieval_method)
    badges = (
        '<div class="dfars-badges">'
        f'<span class="pill id">DFARS {html.escape(section.section_id)}</span>'
        f'<span class="pill pages">pp. {section.page_start}–{section.page_end}</span>'
        f'<span class="pill method-{method}">{method}</span>'
        f'<span class="pill">score {result.score:,.0f}</span>'
        "</div>"
    )
    title = f'<div class="sec-title">{html.escape(section.title)}</div>'
    topics = ""
    if section.key_topics:
        chips = "".join(
            f'<span class="topic">{html.escape(topic)}</span>'
            for topic in section.key_topics[:6]
        )
        topics = f"<div>{chips}</div>"
    return badges + title + topics


def label(text: str) -> str:
    """Return a small uppercase section label."""
    return f'<div class="dfars-label">{html.escape(text)}</div>'


def disclaimer() -> str:
    """Return the footer disclaimer HTML."""
    return (
        '<div class="dfars-footer">'
        "<strong>Not legal advice.</strong> This assistant retrieves and summarizes "
        "DFARS source text to support research. Answers may be incomplete or out of "
        "date. Verify against the current regulation and consult counsel before relying "
        "on any determination."
        "</div>"
    )
