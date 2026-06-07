"""Dark "defense terminal" theme and reusable UI fragments.

Design direction: an institutional, document-forward console for defense
acquisition regulation. Near-black cool charcoal, signal-amber accent, and
IBM Plex (Sans + Mono) so clause identifiers read like precise codes.
"""

from __future__ import annotations

import html

from src.models import RetrievedSection

#: Global stylesheet. Pairs with .streamlit/config.toml (base="dark") so native
#: Streamlit widgets render dark; this refines structure, type, and accents.
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg:        #0a0d12;
  --surface:   #12161f;
  --surface-2: #1a2030;
  --line:      #283041;
  --line-soft: #1c2433;
  --ink:       #e9e6df;
  --muted:     #939cab;
  --faint:     #69727f;
  --amber:     #e0b341;
  --amber-dim: #b8881f;
  --amber-soft: rgba(224,179,65,.12);
  --teal:      #4cc4b0;
  --teal-soft: rgba(76,196,176,.12);
  --violet:    #a78bfa;
  --violet-soft: rgba(167,139,250,.12);
  --radius:    12px;
  --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, monospace;
  --sans: 'IBM Plex Sans', system-ui, sans-serif;
}

html, body, [class*="css"], .stApp { font-family: var(--sans); }
.stApp {
  background:
    radial-gradient(1100px 520px at 50% -8%, #141d2e 0%, rgba(20,29,46,0) 60%),
    var(--bg);
}
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 940px; }
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; height: 0; }
/* hide Streamlit's auto header anchor-link (chain) icons */
[data-testid="stHeaderActionElements"] { display: none !important; }
.stMarkdown a.anchor-link, h1 > a, h2 > a, h3 > a, h4 > a { display: none !important; }

/* ---- Hero ---- */
.dfars-hero {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background:
    linear-gradient(180deg, rgba(224,179,65,.05), rgba(224,179,65,0) 40%),
    var(--surface);
  padding: 1.7rem 1.8rem 1.5rem;
  overflow: hidden;
}
.dfars-hero::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 2px;
  background: linear-gradient(90deg, var(--amber-dim), var(--amber), transparent 70%);
}
.dfars-hero .eyebrow {
  font-family: var(--mono); font-size: .68rem; letter-spacing: .22em;
  text-transform: uppercase; color: var(--amber); font-weight: 500; margin-bottom: .6rem;
}
.dfars-hero h1 {
  font-size: 1.85rem; font-weight: 700; letter-spacing: -.01em;
  margin: 0; color: var(--ink); line-height: 1.1;
}

/* ---- Inline info tooltip (legal notice by the title) ---- */
.dfars-info {
  position: relative; display: inline-flex; align-items: center; justify-content: center;
  width: 1.15rem; height: 1.15rem; margin-left: .55rem; vertical-align: middle;
  font-family: var(--mono); font-size: .72rem; font-weight: 600; cursor: help;
  color: var(--amber); border: 1px solid rgba(224,179,65,.5); border-radius: 50%;
  background: var(--amber-soft); transition: background .15s ease;
}
.dfars-info:hover, .dfars-info:focus-visible { background: rgba(224,179,65,.22); outline: none; }
.dfars-tip {
  position: absolute; top: 150%; left: 0; z-index: 50; width: 290px;
  background: var(--surface-2); border: 1px solid var(--line);
  border-left: 3px solid var(--amber); border-radius: 9px; padding: .7rem .85rem;
  font-family: var(--sans); font-size: .76rem; font-weight: 400; line-height: 1.5;
  color: var(--muted); text-transform: none; letter-spacing: normal;
  box-shadow: 0 10px 30px rgba(0,0,0,.45);
  opacity: 0; visibility: hidden; transform: translateY(-4px); transition: all .16s ease;
}
.dfars-tip strong { color: var(--amber); font-weight: 600; }
.dfars-info:hover .dfars-tip, .dfars-info:focus-visible .dfars-tip {
  opacity: 1; visibility: visible; transform: translateY(0);
}
.dfars-hero p { margin: .6rem 0 0; color: var(--muted); font-size: .92rem; max-width: 62ch; }

/* ---- Eyebrow labels ---- */
.dfars-label {
  font-family: var(--mono); font-size: .68rem; letter-spacing: .18em;
  text-transform: uppercase; color: var(--faint); font-weight: 500;
  margin: 1.6rem 0 .7rem; display: flex; align-items: center; gap: .6rem;
}
.dfars-label::after { content: ""; flex: 1; height: 1px; background: var(--line-soft); }
.dfars-eyebrow {
  font-family: var(--mono); font-size: .68rem; letter-spacing: .2em;
  text-transform: uppercase; color: var(--amber); font-weight: 600; margin-bottom: .5rem;
}

/* ---- Cards (bordered containers) ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--radius) !important;
}
/* the answer card is the only bordered container holding an .dfars-eyebrow */
[data-testid="stVerticalBlockBorderWrapper"]:has(.dfars-eyebrow) {
  border-left: 3px solid var(--amber) !important;
  background: linear-gradient(180deg, rgba(224,179,65,.05), rgba(224,179,65,0) 30%), var(--surface) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.dfars-eyebrow) .stMarkdown {
  font-size: 1rem; line-height: 1.62; color: var(--ink);
}

/* ---- Badges ---- */
.dfars-badges { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; margin-bottom: .55rem; }
.pill {
  font-family: var(--mono); font-size: .72rem; font-weight: 500;
  padding: .2rem .55rem; border-radius: 6px;
  border: 1px solid var(--line); color: var(--muted); background: var(--surface-2);
  display: inline-flex; align-items: center; letter-spacing: .02em;
}
.pill.id {
  color: var(--amber); border-color: rgba(224,179,65,.4); background: var(--amber-soft);
  font-weight: 600;
}
.pill.method-exact  { color: var(--teal);   border-color: rgba(76,196,176,.4);  background: var(--teal-soft); }
.pill.method-bm25   { color: var(--amber);  border-color: rgba(224,179,65,.35); background: var(--amber-soft); }
.pill.method-vector { color: var(--violet); border-color: rgba(167,139,250,.4); background: var(--violet-soft); }
.pill.pages, .pill.score { color: var(--faint); }
.sec-title { font-size: 1.04rem; font-weight: 600; color: var(--ink); margin: .1rem 0 .5rem; letter-spacing: -.005em; }
.topics { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .1rem; }
.topic {
  font-family: var(--mono); font-size: .7rem; color: var(--muted);
  background: var(--surface-2); border: 1px solid var(--line-soft);
  padding: .12rem .45rem; border-radius: 5px;
}

/* ---- Buttons ---- */
.stButton > button {
  background: var(--amber); color: #1a1206; border: 0; border-radius: 9px;
  padding: .55rem 1.5rem; font-weight: 600; font-size: .92rem; font-family: var(--sans);
  transition: transform .12s ease, filter .12s ease;
}
.stButton > button:hover { filter: brightness(1.08); transform: translateY(-1px); color: #1a1206; }
.stButton > button:active { transform: translateY(0); }
.stButton > button:disabled { background: #2a313e; color: var(--faint); }
/* secondary (example) buttons */
.dfars-examples .stButton > button {
  background: var(--surface); color: var(--muted); border: 1px solid var(--line);
  font-family: var(--mono); font-size: .74rem; font-weight: 500; letter-spacing: .02em;
  padding: .45rem .7rem; width: 100%; text-align: left; line-height: 1.3;
}
.dfars-examples .stButton > button:hover {
  border-color: rgba(224,179,65,.5); color: var(--amber); background: var(--surface-2); transform: none;
}

/* ---- Help popover ---- */
[data-testid="stPopover"] > button {
  background: transparent; color: var(--muted); border: 1px dashed var(--line);
  border-radius: 9px; font-family: var(--mono); font-size: .76rem; font-weight: 500;
  letter-spacing: .02em; padding: .4rem .8rem; box-shadow: none;
}
[data-testid="stPopover"] > button:hover {
  border-color: rgba(224,179,65,.5); color: var(--amber); background: var(--surface-2);
  transform: none; filter: none;
}
[data-testid="stPopoverBody"] {
  background: var(--surface) !important; border: 1px solid var(--line) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stPopoverBody"] .stMarkdown { font-size: .86rem; line-height: 1.55; }

/* ---- Inputs ---- */
.stTextArea textarea {
  background: var(--surface) !important; color: var(--ink) !important;
  border: 1px solid var(--line) !important; border-radius: 11px !important;
  font-size: 1rem !important; font-family: var(--sans) !important;
}
.stTextArea textarea::placeholder { color: var(--faint) !important; }
/* hide the "Press ⌘+Enter to apply" helper under inputs */
[data-testid="InputInstructions"] { display: none !important; }
.stTextArea textarea:focus {
  border-color: var(--amber) !important; box-shadow: 0 0 0 3px var(--amber-soft) !important;
}

/* ---- Expanders ---- */
[data-testid="stExpander"] details {
  background: var(--surface) !important; border: 1px solid var(--line) !important;
  border-radius: 9px !important;
}
[data-testid="stExpander"] summary { color: var(--muted) !important; font-size: .85rem; }
[data-testid="stExpander"] summary:hover { color: var(--amber) !important; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] { background: #0c0f15; border-right: 1px solid var(--line-soft); }
section[data-testid="stSidebar"] .dfars-brand {
  font-family: var(--mono); font-weight: 600; color: var(--amber);
  font-size: .82rem; letter-spacing: .14em; text-transform: uppercase;
}

/* ---- Footer disclaimer ---- */
.dfars-footer {
  margin-top: 2.4rem; padding: 1rem 1.1rem; border-radius: 10px;
  border: 1px solid var(--line-soft); background: rgba(224,179,65,.04);
  color: var(--muted); font-size: .78rem; line-height: 1.55;
}
.dfars-footer strong { color: var(--amber); font-weight: 600; }
</style>
"""


def hero() -> str:
    """Return the hero header HTML, with a legal-notice tooltip by the title."""
    tip = (
        '<span class="dfars-info" tabindex="0" role="note" aria-label="Legal notice">i'
        '<span class="dfars-tip"><strong>Not legal advice.</strong> Retrieves and '
        "summarizes DFARS source text for research. Answers may be incomplete or out "
        "of date &mdash; verify against the current regulation and consult counsel "
        "before relying on any determination.</span></span>"
    )
    return (
        '<div class="dfars-hero">'
        '<div class="eyebrow">Defense Federal Acquisition Regulation Supplement</div>'
        f"<h1>DFARS Context Assistant{tip}</h1>"
        "<p>Cited answers grounded in indexed DFARS source text. Query a clause, an "
        "applicability condition, or a definition &mdash; retrieval returns the "
        "controlling sections, verbatim.</p>"
        "</div>"
    )


def eyebrow(text: str) -> str:
    """Return an amber monospace eyebrow (e.g. above the answer)."""
    return f'<div class="dfars-eyebrow">{html.escape(text)}</div>'


def section_header(result: RetrievedSection) -> str:
    """Return the badge + title + topics HTML for a retrieved section."""
    section = result.section
    method = html.escape(result.retrieval_method)
    badges = (
        '<div class="dfars-badges">'
        f'<span class="pill id">{html.escape(section.section_id)}</span>'
        f'<span class="pill pages">pp.&nbsp;{section.page_start}&ndash;{section.page_end}</span>'
        f'<span class="pill method-{method}">{method}</span>'
        f'<span class="pill score">score&nbsp;{result.score:,.0f}</span>'
        "</div>"
    )
    title = f'<div class="sec-title">{html.escape(section.title)}</div>'
    topics = ""
    if section.key_topics:
        chips = "".join(
            f'<span class="topic">{html.escape(topic)}</span>'
            for topic in section.key_topics[:6]
        )
        topics = f'<div class="topics">{chips}</div>'
    return badges + title + topics


def label(text: str) -> str:
    """Return a monospace section divider label."""
    return f'<div class="dfars-label">{html.escape(text)}</div>'


def help_markdown() -> str:
    """Return the 'how to use' guide shown in the help popover."""
    return (
        "**What this is.** A research assistant over the DFARS regulation. It "
        "retrieves the most relevant sections for your question and answers from "
        "their original text, with citations.\n\n"
        "**Ask about:**\n"
        "- **A specific clause or section** — e.g. `252.204-7012`. Naming an id "
        "pulls that exact record.\n"
        "- **Applicability** — *when* a clause or rule applies, and to whom.\n"
        "- **Definitions** — what a DFARS term means.\n"
        "- **Comparisons** — how two sections or clauses differ.\n"
        "- **General explanation** — a plain-English summary of a topic.\n\n"
        "**How it answers.** It selects the controlling sections, sends only those "
        "to the model, and cites the **section id + page range** for each claim. "
        "The original regulation text is the authority — summaries only help "
        "retrieval.\n\n"
        "**Examples:**\n"
        "- *What does DFARS 252.204-7012 require for safeguarding covered defense "
        "information?*\n"
        "- *When must a contracting officer include the cyber incident reporting "
        "clause?*\n"
        "- *How does DFARS treat commercial item acquisitions?*\n\n"
        "**Tips.** Use the sidebar to set how many sections to retrieve and to turn "
        "answer generation on/off. Every result is expandable to read the verbatim "
        "source text.\n\n"
        "_Not legal advice — verify against the current regulation._"
    )


def disclaimer() -> str:
    """Return the footer disclaimer HTML."""
    return (
        '<div class="dfars-footer">'
        "<strong>Not legal advice.</strong> This tool retrieves and summarizes DFARS "
        "source text for research. Answers may be incomplete or out of date. Verify "
        "against the current regulation and consult counsel before relying on any "
        "determination."
        "</div>"
    )
