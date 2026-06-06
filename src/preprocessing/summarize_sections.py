"""Generate retrieval-oriented summaries for DFARS section records."""

from src.models import SectionRecord
from src.preprocessing.ollama_llm import OllamaLLMClient

SUMMARY_SYSTEM_PROMPT = (
    "You are a DFARS regulatory analyst. You summarize defense acquisition "
    "regulation sections for a retrieval index. Be precise and factual. "
    "Never invent obligations not present in the source text."
)

MAX_SOURCE_CHARS = 8000


def summarize_section(section: SectionRecord) -> SectionRecord:
    """Create a deterministic fallback summary for a section.

    Used when no LLM client is available. Mutates and returns the section.

    Args:
        section: Source section record.

    Returns:
        Updated section record.
    """
    text = " ".join(section.original_text.split())
    section.summary = text[:500]
    return section


def summarize_section_llm(
    section: SectionRecord,
    client: OllamaLLMClient,
) -> SectionRecord:
    """Generate an LLM summary and key topics for a section.

    Falls back to a deterministic truncation summary if the model fails.
    Mutates and returns the section.

    Args:
        section: Source section record.
        client: Ollama LLM client.

    Returns:
        Updated section record with `summary` and (when produced) `key_topics`.
    """
    source = " ".join(section.original_text.split())[:MAX_SOURCE_CHARS]
    prompt = _build_prompt(section.section_id, section.title, source)

    try:
        result = client.generate_json(prompt, system=SUMMARY_SYSTEM_PROMPT)
    except RuntimeError:
        return summarize_section(section)

    summary = result.get("summary")
    if isinstance(summary, str) and summary.strip():
        section.summary = summary.strip()[:1000]
    else:
        summarize_section(section)

    topics = result.get("key_topics")
    if isinstance(topics, list):
        section.key_topics = [
            str(topic).strip().lower()
            for topic in topics
            if str(topic).strip()
        ][:8]

    return section


def _build_prompt(section_id: str, title: str, source: str) -> str:
    """Build the summarization prompt for one section."""
    return (
        f"Summarize this DFARS section for a search index.\n\n"
        f"Section: {section_id}\n"
        f"Title: {title}\n\n"
        f"Source text:\n{source}\n\n"
        "Return a JSON object with exactly these keys:\n"
        '- "summary": 2-4 sentences describing what this section governs, who it '
        "applies to, and the core obligation or rule. Plain English.\n"
        '- "key_topics": 3-6 short lowercase topic phrases for retrieval '
        '(e.g. "cybersecurity", "subcontractor flowdown", "data rights").\n'
        "Use only information present in the source text."
    )
