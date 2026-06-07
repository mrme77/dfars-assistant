# DFARS Context Assistant

Ask cited questions over the DFARS regulation. The 1,466-page PDF is
preprocessed **once, locally** into a structured, searchable index of
section-level records. At query time the app retrieves only the most relevant
sections and sends those — not the whole document — to the model.

The original regulatory text remains the authoritative source for every answer;
the enriched metadata exists to help retrieval find the right sections and help
the model orient itself.

## Why this is more reliable than a generic chatbot

- Answers are grounded in indexed DFARS source text, with section + page citations.
- Retrieval is controlled: exact clause lookup plus metadata-enhanced BM25.
- Expensive work (extraction, LLM enrichment, indexing) is done offline, so the
  hosted app stays lightweight.

## Architecture at a glance

```text
Data/DFARS.pdf
  -> src/ingestion/extract_pdf.py        # PDF -> page text
  -> src/ingestion/detect_sections.py    # page text -> section records
  -> indexes/dfars_sections.jsonl        # base index (id, title, pages, text)
  -> src/preprocessing/enrich_sections.py# + LLM summaries, topics, obligations...
  -> indexes/dfars_sections_enriched.jsonl  # deployed index
  -> src/retrieval/*                     # exact lookup + BM25 (+ optional vectors)
  -> src/generation/build_context.py     # compact, budgeted context package
  -> app/streamlit_app.py / app.py       # UI + OpenRouter answer
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full data flow and
[docs/ENRICHMENT.md](docs/ENRICHMENT.md) for the metadata schema.

## The deployed index

`indexes/dfars_sections_enriched.jsonl` (~6.7 MB, 1,444 sections) is the only
artifact the hosted app needs. Each record is a `SectionRecord`
(`src/models.py`):

```text
section_id        title           part / subpart
page_start        page_end        original_text   (authoritative source)
summary           key_topics      applies_when    required_actions
obligations       exceptions      cross_references contracting_officer_notes
```

`summary` and `key_topics` are produced by a local LLM (Ollama); the remaining
fields are deterministic rule-based extractions. See enrichment details below.

## Hosted retrieval mode (Hugging Face Spaces)

The Space uses the same RAG shape as local, **without Ollama or Chroma**:

```text
user question
  -> exact section lookup        (252.204-7012 -> that record, score boosted)
  -> BM25 over enriched metadata + original section text
  -> top SectionRecords (deduped, ranked)
  -> budgeted context package (metadata + trimmed original_text)
  -> OpenRouter answer with citations
```

Hosted dependencies are the five packages in `requirements.txt`. Set
`OPENROUTER_API_KEY` in the Space secrets. Entry point:

```bash
streamlit run app.py
```

## Local development

```bash
uv venv dfars-env
source dfars-env/bin/activate
uv pip install -r requirements-local.txt   # adds pymupdf, chroma, sentence-transformers, keyring
cp .env.example .env                        # set OPENROUTER_API_KEY (or keychain fields)
dfars-env/bin/python -m streamlit run app/streamlit_app.py
```

Optional local semantic search (needs Ollama + Chroma):

```bash
DFARS_ENABLE_VECTOR_SEARCH=true dfars-env/bin/python -m streamlit run app/streamlit_app.py
```

## Rebuilding the enriched index

Summaries and key topics come from a local Ollama model
(`OLLAMA_LLM_MODEL`, default `gemma4:e4b`). Build offline, then commit the
resulting JSONL for hosting:

```bash
# full run (1,444 sections)
PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections \
  --input indexes/dfars_sections.jsonl \
  --output indexes/dfars_sections_enriched.jsonl

# faster: run LLM calls concurrently and skip tiny sections
OLLAMA_NUM_PARALLEL=4 PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections \
  --workers 4 --llm-min-chars 200

# no LLM (deterministic truncation summaries only)
PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections --no-llm

# pilot a handful of sections to a throwaway file
PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections \
  --limit 5 --output indexes/pilot.jsonl
```

Notes:

- If the LLM call fails or returns invalid JSON, the section falls back to a
  deterministic truncation summary — the build never crashes.
- Records are always written in input order, flushed per line, so a long run is
  inspectable as it goes.
- `--workers N` should match `OLLAMA_NUM_PARALLEL` on the Ollama server.

## Configuration

OpenRouter (answer generation):

```text
OPENROUTER_API_KEY=...                     # or leave empty to use macOS Keychain:
OPENROUTER_KEYCHAIN_SERVICE=openrouter
OPENROUTER_KEYCHAIN_ACCOUNT=OPENROUTER_API_KEY
```

Ollama (offline enrichment / optional local vectors):

```text
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_LLM_MODEL=gemma4:e4b
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

The answer model is `google/gemini-2.5-flash-lite-preview-09-2025`
(`src/generation/answer.py`).

## Authentication (optional)

A single shared login gates the app **only when `DFARS_AUTH_PASSWORD_HASH` is
set** (a bcrypt hash). Unset → the app runs open, which is convenient locally.

Generate a hash without exposing the plaintext, then store the printed values:

```bash
dfars-env/bin/python -m app.auth
```

```text
DFARS_AUTH_USERNAME=dfars
DFARS_AUTH_PASSWORD_HASH=$2b$12$...        # bcrypt hash, never the plaintext
```

- **Local:** put both lines in `.env` (git-ignored); `load_dotenv()` reads them.
- **Hugging Face:** set both as Space **Secrets** (`.env` is not deployed).

Login does a constant-time username check plus `bcrypt.checkpw`, returns a
generic error, and applies a short lockout after repeated failures. Sessions are
held in `st.session_state`, so a hard refresh requires signing in again.

## Testing

```bash
dfars-env/bin/python -m pytest -q
```

## Context engineering

The project is organized around four moves; see
[context/README.md](context/README.md):

- **Write** — durable section records, summaries, obligations, cross-references.
- **Select** — retrieve the smallest relevant set of sections per question.
- **Compress** — summaries for orientation, original text only where needed,
  under an explicit character budget.
- **Isolate** — keep instructions, source text, retrieval metadata, and the
  user question in separate, labeled blocks.
