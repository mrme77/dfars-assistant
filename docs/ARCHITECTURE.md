# Architecture

The system has two halves: an **offline preprocessing pipeline** (run locally,
ahead of time) and an **online retrieval/answer path** (lightweight, hosted).
The boundary between them is a single artifact:
`indexes/dfars_sections_enriched.jsonl`.

## Data flow

```text
                         OFFLINE (local, requirements-local.txt)
 Data/DFARS.pdf
     │  src/ingestion/extract_pdf.py        (PyMuPDF: page -> PageText)
     ▼
 page text
     │  src/ingestion/detect_sections.py    (regex heading -> SectionRecord)
     ▼
 indexes/dfars_sections.jsonl               base records: id, title, pages, text
     │  src/preprocessing/enrich_sections.py
     │    ├─ summarize_sections.py  -> LLM summary + key_topics (Ollama)
     │    ├─ extract_obligations.py -> obligations
     │    ├─ extract_cross_references.py -> cross_references
     │    └─ rule-based applies_when / required_actions / exceptions / notes
     ▼
 indexes/dfars_sections_enriched.jsonl      ◀── DEPLOYED ARTIFACT
─────────────────────────────────────────────────────────────────────────────
                         ONLINE (hosted, requirements.txt)
 user question
     │  src/retrieval/section_store.py       load_sections() -> [SectionRecord]
     │  src/retrieval/hybrid_search.py
     │    ├─ exact id lookup  (SECTION_ID_PATTERN, score 1e6)
     │    ├─ keyword_search.py BM25 over metadata-weighted text
     │    └─ vector_search.py (optional, local only, lazy-imported)
     │  src/retrieval/rerank.py              dedupe_results() by best score
     ▼
 top-N RetrievedSection
     │  src/generation/build_context.py      labeled, char-budgeted package
     ▼
 context package
     │  src/generation/answer.py             OpenRouter chat completion
     ▼
 cited answer  ──►  app/streamlit_app.py
```

## Components

### Ingestion (`src/ingestion/`)

- `extract_pdf.py` — PyMuPDF extracts each page to a `PageText(page_number, text)`.
- `detect_sections.py` — `SECTION_HEADING_PATTERN` matches DFARS headings
  (`NNN.NNNN`, `NNN.NNN-NNNN`, `NNN.NNN`). Lines accumulate under the current
  heading until the next one; `build_sections` emits `SectionRecord`s with page
  ranges and `original_text`. `part` is derived from the id prefix.

### Preprocessing / enrichment (`src/preprocessing/`)

Adds metadata to each record. Two kinds of fields:

- **LLM-generated** (`summarize_sections.py` + `ollama_llm.py`): `summary`
  (2–4 sentences) and `key_topics`. Uses a local Ollama model
  (`OLLAMA_LLM_MODEL`, default `gemma4:e4b`) returning strict JSON. On any
  failure it falls back to a deterministic truncation summary.
- **Rule-based**: `obligations`, `cross_references`, `applies_when`,
  `required_actions`, `exceptions`, `contracting_officer_notes` — regex/sentence
  heuristics over `original_text`. LLM and regex topics are merged.

`enrich_index()` supports `--workers` (concurrent LLM calls),
`--llm-min-chars` (skip tiny sections), `--limit` (pilot), and `--no-llm`.

### Retrieval (`src/retrieval/`)

- `section_store.py` — loads/validates JSONL into `SectionRecord`s and provides
  exact `section_id` lookup (case-insensitive; one id may map to several records).
- `keyword_search.py` — `BM25Okapi` over a search string that repeats metadata
  (id, title, summary, topics, applies_when, required_actions, cross_references,
  notes) three times plus the first 4,000 chars of `original_text`, so metadata
  matches dominate. `_metadata_boost` adds deterministic bumps for token overlap
  and exact key-topic phrase matches.
- `hybrid_search.py` — unions exact + BM25 (+ optional vectors). Exact matches
  get score `1e6` so an explicitly named clause always surfaces. Pure-id queries
  skip semantic search.
- `rerank.py` — `dedupe_results` keeps the best-scoring instance per section and
  truncates to `limit`.
- `vector_search.py` / `build_vector_index.py` / `ollama_embeddings.py` —
  optional local semantic search via Chroma + Ollama embeddings. Lazy-imported
  so the hosted path never loads them.

### Generation (`src/generation/`)

- `build_context.py` — formats each retrieved section as a labeled block
  (section, title, pages, summary, then non-empty metadata, then trimmed
  `original_text`). Total source text is capped at `DEFAULT_CONTEXT_CHAR_BUDGET`
  (28,000), split evenly across sections, so one large section cannot blow the
  context window.
- `answer.py` — posts the package to OpenRouter
  (`google/gemini-2.5-flash-lite-preview-09-2025`) with a system prompt that
  forces source-grounded, cited answers and forbids legal determinations. Key is
  read from env or macOS Keychain.

### App (`app/`)

- `streamlit_app.py` — loads the index (prefers enriched), runs search, builds
  the context package, optionally calls OpenRouter, and shows answer, retrieved
  sections, and a context preview.
- `app.py` (repo root) — Hugging Face Spaces entry point that imports and runs
  `streamlit_app.main`.

## Hosted vs local

| Concern | Local | Hosted (HF Space) |
| --- | --- | --- |
| Deps | `requirements-local.txt` | `requirements.txt` (5 pkgs) |
| Retrieval | exact + BM25 (+ optional vectors) | exact + BM25 |
| Embeddings/LLM enrichment | Ollama | not used |
| Answer model | OpenRouter | OpenRouter |
| Index | rebuilt locally | committed JSONL |
