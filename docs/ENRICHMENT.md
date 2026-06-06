# Enrichment & Record Schema

Each line of `indexes/dfars_sections_enriched.jsonl` is one `SectionRecord`
(`src/models.py`). This is the unit of retrieval and the unit of context.

## Fields and provenance

| Field | Type | Source | Authority |
| --- | --- | --- | --- |
| `section_id` | str | ingestion (heading regex) | identifier |
| `title` | str | ingestion | identifier |
| `part` | str? | derived from `section_id` prefix | — |
| `subpart` | str? | (reserved) | — |
| `page_start` / `page_end` | int | ingestion (page range) | citation |
| `original_text` | str | ingestion (verbatim PDF text) | **authoritative** |
| `summary` | str | **LLM** (Ollama, JSON) | orientation only |
| `key_topics` | str[] | **LLM** + regex patterns, merged | retrieval only |
| `applies_when` | str[] | rule-based (applicability sentences) | retrieval/orientation |
| `required_actions` | str[] | rule-based (contracting-action sentences) | retrieval/orientation |
| `obligations` | str[] | rule-based (`extract_obligations.py`) | retrieval/orientation |
| `exceptions` | str[] | rule-based (exception sentences) | retrieval/orientation |
| `cross_references` | str[] | rule-based (`extract_cross_references.py`) | navigation |
| `contracting_officer_notes` | str[] | rule-based (derived flags) | orientation |

**Authority rule:** only `original_text` (with `section_id` + page range)
grounds an answer. Every other field is a retrieval/orientation aid and must not
be cited as the regulation.

## LLM-generated fields

`summarize_sections.py::summarize_section_llm` prompts a local Ollama model
(`OLLAMA_LLM_MODEL`, default `gemma4:e4b`) for strict JSON:

```json
{ "summary": "2-4 sentences ...", "key_topics": ["lowercase phrase", ...] }
```

- Temperature 0, `format: json`, source capped at 8,000 chars.
- On HTTP error, timeout, or invalid JSON the section falls back to a
  deterministic truncation summary (`original_text[:500]`); the build never
  crashes.
- LLM `key_topics` are merged with the controlled regex topics in
  `enrich_sections.py::_merge_key_topics` (dedup, lowercased, capped at 10).

Current full build: 1,444 sections, 0% fallback, `key_topics` on 100% of
records (avg ~4.8).

## Rebuilding

```bash
# default sequential LLM build
PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections

# concurrent + skip tiny sections (match server OLLAMA_NUM_PARALLEL)
OLLAMA_NUM_PARALLEL=4 PYTHONPATH=. dfars-env/bin/python \
  -m src.preprocessing.enrich_sections --workers 4 --llm-min-chars 200

# deterministic only (no Ollama)
PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections --no-llm
```

Flags: `--input`, `--output`, `--limit N`, `--no-llm`, `--workers N`,
`--llm-min-chars N`. Output is written in input order and flushed per line, so a
long run is inspectable while it proceeds.

## How metadata is used downstream

- **Retrieval** (`keyword_search.py`): metadata is weighted ~3× over source text
  in the BM25 search string, and exact key-topic phrase matches get a boost, so
  the right sections surface even when the question doesn't quote the text.
- **Context** (`build_context.py`): non-empty `key_topics`, `applies_when`,
  `required_actions`, `exceptions`, and `cross_references` are included as
  labeled lines alongside the (budget-trimmed) `original_text`, helping the model
  orient before reading the source.

## Schema note

`context/schemas/section_metadata.schema.json` predates the current model and is
missing `applies_when`, `required_actions`, and `contracting_officer_notes`.
`src/models.py` is the source of truth. When you next touch the schema, sync it
to the model and update tests in the same change.
