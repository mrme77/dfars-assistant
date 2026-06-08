# CLAUDE.md — DFARS Context Assistant

Project-level guidance for Claude. Global user instructions still apply; this
file adds project specifics.

## What this project is

A DFARS question-answering assistant built as a **RAG over a controlled index**.
The DFARS PDF (`Data/DFARS.pdf`, ~1,466 pages) is preprocessed offline into
section-level records (`indexes/dfars_sections_enriched.jsonl`, 1,444 sections).
At query time the app retrieves the most relevant sections and sends only those
to an LLM, which answers with section + page citations.

**Core principle:** `original_text` is the authority for every answer. Enriched
metadata (summary, key_topics, etc.) exists to improve retrieval and orient the
model — it never overrides or substitutes for the source text.

## Pipeline (offline → hosted)

```
extract_pdf.py -> detect_sections.py -> dfars_sections.jsonl
  -> enrich_sections.py -> dfars_sections_enriched.jsonl   # deployed artifact
  -> retrieval (exact + BM25, optional vectors) -> build_context.py -> answer.py
```

Offline (local, `requirements-local.txt`): extraction, LLM enrichment via
Ollama, optional Chroma vector index.
Hosted (Hugging Face, `requirements.txt`): load JSONL, BM25 + exact lookup,
OpenRouter answer. No Ollama/Chroma/torch on the Space.

## Key files

| File | Role |
| --- | --- |
| `src/models.py` | `SectionRecord`, `RetrievedSection`, `PageText` (pydantic) |
| `src/ingestion/detect_sections.py` | regex heading detection -> section records |
| `src/preprocessing/enrich_sections.py` | LLM + rule-based metadata; CLI to rebuild index |
| `src/preprocessing/summarize_sections.py` | LLM summary + topics, truncation fallback |
| `src/preprocessing/ollama_llm.py` | local Ollama JSON client |
| `src/retrieval/hybrid_search.py` | exact-id lookup + BM25 (+ optional vector) |
| `src/retrieval/keyword_search.py` | BM25 with metadata boosting |
| `src/generation/build_context.py` | budgeted, labeled context package |
| `src/generation/answer.py` | OpenRouter call + system prompt |
| `app/streamlit_app.py`, `app.py` | UI; `app.py` is the HF entry point |
| `app/theme.py` | dark "defense terminal" CSS + UI fragments (hero, cards, help) |
| `app/auth.py` | optional shared login (bcrypt); active iff `DFARS_AUTH_PASSWORD_HASH` set |

## Conventions specific to this repo

- **Run modules with `PYTHONPATH=.`** and the venv python:
  `PYTHONPATH=. dfars-env/bin/python -m src.preprocessing.enrich_sections`.
- Imports are absolute from `src.` (e.g. `from src.models import SectionRecord`).
- Vector search is **lazy-imported** in `hybrid_search.py` so the hosted BM25
  path never pulls in Chroma/Ollama. Keep it that way.
- The enriched index is loaded once via `@st.cache_resource`.
- Enrichment must **never crash the build**: LLM failures fall back to
  deterministic truncation. Preserve this.
- Records are written in input order, flushed per line.

## Common tasks

```bash
# tests
dfars-env/bin/python -m pytest -q

# rebuild enriched index (LLM, concurrent)
OLLAMA_NUM_PARALLEL=4 PYTHONPATH=. dfars-env/bin/python \
  -m src.preprocessing.enrich_sections --workers 4 --llm-min-chars 200

# run app locally
dfars-env/bin/python -m streamlit run app/streamlit_app.py

# generate an auth hash (prints DFARS_AUTH_* lines; plaintext never stored)
dfars-env/bin/python -m app.auth
```

## Deployment

Two git remotes hold the same code:

- `dfars-assistant` → GitHub (github.com/mrme77/dfars-assistant) — source of truth.
- `hf` → Hugging Face Space (huggingface.co/spaces/mrme77/dfars-assistant) — runs
  the app as a **Docker** Space (HF dropped the native Streamlit SDK).

**Dual-branch quirk:** GitHub `main` has a clean README; HF **requires** a YAML
frontmatter block in `README.md` (`sdk: docker`, `app_port: 7860`) or the Space
fails with `CONFIG_ERROR`. That frontmatter lives only on the **`hf-deploy`**
branch, which is pushed to HF `main`. So:

```bash
git push dfars-assistant main                 # GitHub (clean)
git checkout hf-deploy && git merge main && git push hf hf-deploy:main && git checkout main
```

`Dockerfile` runs Streamlit on port 7860. Runtime secrets (`OPENROUTER_API_KEY`,
`DFARS_AUTH_USERNAME`, `DFARS_AUTH_PASSWORD_HASH`) are set in the HF Space
**Secrets** UI, never committed. A GitHub Action could automate the sync later
(injecting frontmatter), which would retire the `hf-deploy` branch.

## Guardrails

- Do not send the full PDF or full index to the LLM — only retrieved sections,
  under the `build_context.py` character budget.
- Do not hardcode secrets. `OPENROUTER_API_KEY` via env/keychain; Ollama config
  via env.
- The assistant must not give legal advice or final contract determinations
  (`src/generation/answer.py` system prompt, `context/system/assistant_rules.md`).
- When changing `SectionRecord`, update the enrichment writer, `build_context.py`,
  `context/schemas/section_metadata.schema.json`, and tests together.
