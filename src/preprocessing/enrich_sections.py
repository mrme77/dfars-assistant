"""Enrich DFARS section records for retrieval and contracting workflows."""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.models import SectionRecord
from src.preprocessing.extract_cross_references import extract_cross_references
from src.preprocessing.extract_obligations import extract_obligation_sentences
from src.preprocessing.ollama_llm import OllamaLLMClient
from src.preprocessing.summarize_sections import summarize_section, summarize_section_llm
from src.retrieval.section_store import load_sections

KEY_TOPIC_PATTERNS: dict[str, re.Pattern[str]] = {
    "cybersecurity": re.compile(r"\b(cyber|cybersecurity|incident|information system)\b", re.I),
    "covered defense information": re.compile(r"\bcovered defense information\b", re.I),
    "commercial acquisition": re.compile(r"\bcommercial (product|service|item)\b", re.I),
    "subcontractors": re.compile(r"\b(subcontractor|flow down|flowdown)\b", re.I),
    "data rights": re.compile(r"\b(data rights|technical data|computer software)\b", re.I),
    "foreign acquisition": re.compile(r"\b(foreign|domestic|country|trade agreements)\b", re.I),
    "solicitation provisions": re.compile(r"\b(solicitation|provision|contract clause)\b", re.I),
}


def enrich_section(
    section: SectionRecord,
    llm_client: OllamaLLMClient | None = None,
    llm_min_chars: int = 0,
) -> SectionRecord:
    """Add retrieval and workflow metadata to a section.

    Args:
        section: Source section record.
        llm_client: Optional Ollama client for LLM summaries and topics.
            When omitted, a deterministic truncation summary is used.
        llm_min_chars: Skip the LLM (use truncation) when the original text is
            shorter than this many characters. Short sections gain little from
            summarization and skipping them speeds up large runs.

    Returns:
        Enriched section record.
    """
    enriched = section.model_copy(deep=True)
    if llm_client is not None and len(enriched.original_text) >= llm_min_chars:
        summarize_section_llm(enriched, llm_client)
    else:
        summarize_section(enriched)
    enriched.cross_references = _without_self_reference(
        enriched.section_id,
        extract_cross_references(enriched.original_text),
    )
    enriched.key_topics = _merge_key_topics(
        enriched.key_topics,
        _extract_key_topics(enriched.original_text),
    )
    enriched.obligations = extract_obligation_sentences(enriched.original_text)[:8]
    enriched.applies_when = _extract_applicability_statements(enriched.original_text)[:6]
    enriched.required_actions = _extract_required_actions(enriched.original_text)[:6]
    enriched.exceptions = _extract_exception_statements(enriched.original_text)[:6]
    enriched.contracting_officer_notes = _build_contracting_officer_notes(enriched)
    return enriched


def enrich_index(
    input_path: Path,
    output_path: Path,
    limit: int | None = None,
    use_llm: bool = True,
    workers: int = 1,
    llm_min_chars: int = 0,
) -> int:
    """Enrich a section JSONL index and write a new JSONL file.

    Records are always written in input order. When ``workers > 1`` the LLM
    calls run concurrently against Ollama (set ``OLLAMA_NUM_PARALLEL`` on the
    server to match), which is the main lever for speeding up large runs.

    Args:
        input_path: Source section index path.
        output_path: Destination enriched index path.
        limit: Optional maximum section count for pilot runs.
        use_llm: Whether to use Ollama for summaries and key topics.
        workers: Number of concurrent enrichment workers.
        llm_min_chars: Skip the LLM for sections shorter than this length.

    Returns:
        Number of records written.
    """
    sections = load_sections(input_path)
    if limit is not None:
        sections = sections[:limit]

    llm_client = OllamaLLMClient() if use_llm else None
    total = len(sections)

    def _work(section: SectionRecord) -> SectionRecord:
        return enrich_section(
            section,
            llm_client=llm_client,
            llm_min_chars=llm_min_chars,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        results = (
            map(_work, sections)
            if workers <= 1
            else ThreadPoolExecutor(max_workers=workers).map(_work, sections)
        )
        for position, enriched in enumerate(results, start=1):
            output_file.write(json.dumps(enriched.model_dump(), ensure_ascii=False) + "\n")
            output_file.flush()
            if use_llm and (position % 25 == 0 or position == total):
                print(f"Enriched {position}/{total} sections", flush=True)
    return total


def _merge_key_topics(primary: list[str], secondary: list[str]) -> list[str]:
    """Merge topic lists, preserving order and dropping duplicates."""
    seen: set[str] = set()
    merged: list[str] = []
    for topic in [*primary, *secondary]:
        normalized = topic.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            merged.append(normalized)
    return merged[:10]


def _extract_key_topics(text: str) -> list[str]:
    """Extract controlled key topics from section text."""
    return [
        topic
        for topic, pattern in KEY_TOPIC_PATTERNS.items()
        if pattern.search(text)
    ]


def _extract_applicability_statements(text: str) -> list[str]:
    """Extract sentences that look like applicability or usage conditions."""
    candidates = _sentence_candidates(text)
    markers = ("applies", "apply", "use ", "include ", "insert ", "prescribed", "when ")
    return [
        sentence
        for sentence in candidates
        if any(marker in sentence.lower() for marker in markers)
    ]


def _extract_required_actions(text: str) -> list[str]:
    """Extract sentences that look like contracting actions."""
    candidates = _sentence_candidates(text)
    markers = ("contracting officer shall", "shall include", "shall insert", "use the clause")
    return [
        sentence
        for sentence in candidates
        if any(marker in sentence.lower() for marker in markers)
    ]


def _extract_exception_statements(text: str) -> list[str]:
    """Extract sentences that look like exceptions or exclusions."""
    candidates = _sentence_candidates(text)
    markers = ("except", "exception", "does not apply", "do not use", "unless")
    return [
        sentence
        for sentence in candidates
        if any(marker in sentence.lower() for marker in markers)
    ]


def _sentence_candidates(text: str) -> list[str]:
    """Split normalized text into reasonably sized sentence candidates."""
    normalized = " ".join(text.split())
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", normalized)
        if 20 <= len(sentence.strip()) <= 700
    ]


def _without_self_reference(section_id: str, references: list[str]) -> list[str]:
    """Remove a section's own identifier from cross-references."""
    return [reference for reference in references if reference != section_id]


def _build_contracting_officer_notes(section: SectionRecord) -> list[str]:
    """Build concise notes useful for contracting officer retrieval."""
    notes: list[str] = []
    if section.part == "252":
        notes.append("Clause text; check the prescribing DFARS section before use.")
    if "solicitation provisions" in section.key_topics:
        notes.append("Likely relevant to clause/provision selection questions.")
    if section.applies_when:
        notes.append("Contains applicability or usage language.")
    if section.exceptions:
        notes.append("Contains exception or exclusion language.")
    return notes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich DFARS section metadata.")
    parser.add_argument(
        "--input",
        default="indexes/dfars_sections.jsonl",
        help="Source section JSONL index.",
    )
    parser.add_argument(
        "--output",
        default="indexes/dfars_sections_enriched.jsonl",
        help="Destination enriched JSONL index.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional pilot record count.")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Ollama summaries and use deterministic truncation only.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Concurrent enrichment workers (match OLLAMA_NUM_PARALLEL on the server).",
    )
    parser.add_argument(
        "--llm-min-chars",
        type=int,
        default=0,
        help="Skip the LLM for sections shorter than this (truncation summary instead).",
    )
    args = parser.parse_args()

    count = enrich_index(
        Path(args.input),
        Path(args.output),
        limit=args.limit,
        use_llm=not args.no_llm,
        workers=args.workers,
        llm_min_chars=args.llm_min_chars,
    )
    print(f"Wrote {count} enriched DFARS sections.")

