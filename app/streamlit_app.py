"""Streamlit interface for the DFARS context assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from app import auth, theme
from src.generation.answer import DEFAULT_OPENROUTER_MODEL, answer_with_openrouter
from src.generation.build_context import build_context_package
from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.section_store import load_sections

ENRICHED_INDEX_PATH = Path("indexes/dfars_sections_enriched.jsonl")
BASE_INDEX_PATH = Path("indexes/dfars_sections.jsonl")

EXAMPLE_QUESTIONS = [
    ("252.204-7012 safeguarding", "What does DFARS 252.204-7012 require for safeguarding covered defense information?"),
    ("Cyber incident reporting", "When must a contracting officer include the cyber incident reporting clause?"),
    ("Commercial item rules", "How does DFARS treat commercial item acquisitions?"),
]


@st.cache_resource
def load_searcher() -> HybridSearcher:
    """Load and cache the DFARS searcher."""
    sections = load_sections(_index_path())
    return HybridSearcher(sections, use_vector=_vector_search_enabled())


def main() -> None:
    """Render the Streamlit app."""
    load_dotenv()
    st.set_page_config(
        page_title="DFARS Context Assistant",
        page_icon="⚖️",
        layout="centered",
    )
    st.markdown(theme.BASE_CSS, unsafe_allow_html=True)
    st.markdown(theme.hero(), unsafe_allow_html=True)

    auth.require_login()  # halts here until signed in (when auth is configured)

    if not _index_path().exists():
        st.error(
            "Section index is missing. Expected "
            "`indexes/dfars_sections_enriched.jsonl` or `indexes/dfars_sections.jsonl`."
        )
        return

    searcher = load_searcher()
    result_limit, answer_enabled = _render_sidebar()

    with st.popover("❔ How to use this assistant", use_container_width=False):
        st.markdown(theme.help_markdown())

    question = st.text_area(
        "Question",
        key="question",
        height=120,
        label_visibility="collapsed",
        placeholder="Ask about a DFARS section or clause, e.g. 252.204-7012 …",
        help=(
            "Naming a clause id (e.g. 252.204-7012) triggers exact lookup; "
            "plain-language questions use metadata-enhanced keyword search."
        ),
    )
    ask = st.button(
        "Search DFARS",
        type="primary",
        use_container_width=True,
        disabled=not question.strip(),
    )
    _render_examples()

    if ask and question.strip():
        _run_query(searcher, question.strip(), result_limit, answer_enabled)

    st.markdown(theme.disclaimer(), unsafe_allow_html=True)


def _render_sidebar() -> tuple[int, bool]:
    """Render sidebar settings and return (result_limit, answer_enabled)."""
    with st.sidebar:
        st.markdown('<div class="dfars-brand">⚖️ DFARS Assistant</div>', unsafe_allow_html=True)
        st.caption("Metadata-enhanced retrieval over indexed DFARS sections.")
        st.divider()

        st.subheader("Retrieval")
        result_limit = st.slider(
            "Sections to retrieve",
            1,
            12,
            6,
            help=(
                "How many DFARS sections to pull into context. Higher = broader "
                "coverage but more tokens and possible noise; lower = tighter, "
                "faster, cheaper. 4–6 suits most questions."
            ),
        )
        answer_enabled = st.toggle(
            "Generate cited answer",
            value=True,
            help=(
                "On: send retrieved sections to the model for a cited answer "
                "(needs OPENROUTER_API_KEY). Off: show retrieved sections only — "
                "no model call, no cost."
            ),
        )

        st.divider()
        with st.expander("About"):
            st.markdown(
                "Answers are grounded in indexed DFARS source text. The original "
                "regulation remains authoritative; summaries and topics only aid "
                "retrieval.\n\n"
                f"**Answer model:** `{DEFAULT_OPENROUTER_MODEL}`  \n"
                f"**Sections indexed:** {len(load_searcher().store.sections):,}"
            )

        if auth.auth_enabled():
            st.divider()
            auth.sign_out_button()
    return result_limit, answer_enabled


def _use_example(question: str) -> None:
    """Callback: load an example into the question box before the widget rebuilds."""
    st.session_state["question"] = question


def _render_examples() -> None:
    """Render clickable example questions."""
    st.markdown(theme.label("Try an example"), unsafe_allow_html=True)
    st.markdown('<div class="dfars-examples">', unsafe_allow_html=True)
    columns = st.columns(len(EXAMPLE_QUESTIONS))
    for column, (short_label, full_question) in zip(columns, EXAMPLE_QUESTIONS, strict=False):
        column.button(
            short_label,
            key=f"ex-{short_label}",
            on_click=_use_example,
            args=(full_question,),
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _run_query(
    searcher: HybridSearcher,
    question: str,
    result_limit: int,
    answer_enabled: bool,
) -> None:
    """Execute retrieval, answer generation, and render results."""
    results = searcher.search(question, limit=result_limit)
    if not results:
        st.warning("No relevant DFARS sections were found. Try rephrasing or a section id.")
        return

    context_package = build_context_package(question, results)

    if answer_enabled:
        st.markdown(theme.label("Answer"), unsafe_allow_html=True)
        with st.spinner("Generating cited answer from retrieved DFARS sections…"):
            try:
                answer = answer_with_openrouter(context_package)
            except RuntimeError as exc:
                st.error(str(exc))
                st.info(
                    "Set `OPENROUTER_API_KEY` in the environment. "
                    f"Default model: `{DEFAULT_OPENROUTER_MODEL}`."
                )
            else:
                with st.container(border=True):
                    st.markdown(theme.eyebrow("◆ Answer"), unsafe_allow_html=True)
                    st.markdown(answer)

    st.markdown(theme.label(f"Retrieved sections ({len(results)})"), unsafe_allow_html=True)
    for result in results:
        with st.container(border=True):
            st.markdown(theme.section_header(result), unsafe_allow_html=True)
            if result.section.summary:
                st.caption(result.section.summary)
            with st.expander("Source text"):
                st.text(result.section.original_text[:5000])

    with st.expander("Context package sent to the model"):
        st.text_area(
            "Context",
            value=context_package,
            height=360,
            label_visibility="collapsed",
        )


def _index_path() -> Path:
    """Return the best available section index path."""
    if ENRICHED_INDEX_PATH.exists():
        return ENRICHED_INDEX_PATH
    return BASE_INDEX_PATH


def _vector_search_enabled() -> bool:
    """Return whether vector search should be enabled for this process."""
    return os.getenv("DFARS_ENABLE_VECTOR_SEARCH", "").lower() in {"1", "true", "yes"}


if __name__ == "__main__":
    main()
