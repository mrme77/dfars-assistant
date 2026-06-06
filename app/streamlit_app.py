"""Streamlit interface for the DFARS context assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from src.generation.answer import DEFAULT_OPENROUTER_MODEL, answer_with_openrouter
from src.generation.build_context import build_context_package
from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.section_store import load_sections

ENRICHED_INDEX_PATH = Path("indexes/dfars_sections_enriched.jsonl")
BASE_INDEX_PATH = Path("indexes/dfars_sections.jsonl")


@st.cache_resource
def load_searcher() -> HybridSearcher:
    """Load and cache the DFARS searcher."""
    sections = load_sections(_index_path())
    return HybridSearcher(sections, use_vector=_vector_search_enabled())


def main() -> None:
    """Render the Streamlit app."""
    load_dotenv()
    st.set_page_config(page_title="DFARS Context Assistant", layout="wide")
    st.title("DFARS Context Assistant")
    st.caption(
        "DFARS assistant: metadata-enhanced retrieval over indexed sections "
        "with OpenRouter answers."
    )

    if not _index_path().exists():
        st.error(
            "Section index is missing. Expected "
            "`indexes/dfars_sections_enriched.jsonl` or `indexes/dfars_sections.jsonl`."
        )
        return

    searcher = load_searcher()
    question = st.text_area(
        "Question",
        placeholder="Ask about a DFARS section or clause, such as 252.204-7012.",
    )
    result_limit = st.slider("Sections to retrieve", min_value=1, max_value=12, value=6)

    answer_enabled = st.toggle("Generate answer with OpenRouter", value=True)

    if st.button("Ask", disabled=not question.strip()):
        results = searcher.search(question, limit=result_limit)
        if not results:
            st.warning("No relevant DFARS sections were found.")
            return

        context_package = build_context_package(question, results)

        if answer_enabled:
            st.subheader("Answer")
            with st.spinner("Generating answer from retrieved DFARS sections..."):
                try:
                    st.markdown(answer_with_openrouter(context_package))
                except RuntimeError as exc:
                    st.error(str(exc))
                    st.info(
                        "Set OPENROUTER_API_KEY in `.env`. "
                        f"The default model is `{DEFAULT_OPENROUTER_MODEL}`."
                    )

        st.subheader("Retrieved Sections")
        for result in results:
            section = result.section
            with st.expander(
                f"DFARS {section.section_id}: {section.title} "
                f"(pages {section.page_start}-{section.page_end})"
            ):
                st.caption(f"Retrieval: {result.retrieval_method} | Score: {result.score:.2f}")
                st.text(section.original_text[:5000])

        st.subheader("Context Package Preview")
        st.text_area(
            "Context sent to the answer model",
            value=context_package,
            height=420,
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
