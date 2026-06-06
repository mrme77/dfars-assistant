# context/ — Context Engineering Assets

This directory holds the **durable, version-controlled context** the assistant
relies on, kept separate from code and from runtime data. The goal is a clean
separation of concerns so each piece of context can be reasoned about, reviewed,
and reused independently.

## Layout

```text
context/
  system/      # standing instructions and policies (the assistant's "rules")
    assistant_rules.md     behavior + grounding rules
    citation_policy.md     how every grounded answer must cite sources
    legal_disclaimer.md    scope limits (no legal advice / final determinations)
  schemas/     # contracts for structured data
    section_metadata.schema.json   shape of a DFARS section record
    answer.schema.json             shape of a structured answer
  workflows/   # step-by-step procedures for recurring question types
    answer_dfars_question.md
    check_clause_applicability.md
    compare_sections.md
```

## The four moves

The whole system is organized around four context-engineering moves. Each maps
to concrete parts of the repo:

- **Write** — produce durable, reusable context once. The offline pipeline
  writes section records, LLM summaries, topics, obligations, and
  cross-references into `indexes/dfars_sections_enriched.jsonl`. The assets in
  this directory are also "written" context: rules, schemas, workflows.

- **Select** — pull only the smallest relevant slice per question. Retrieval
  (`src/retrieval/`) selects a handful of sections via exact lookup + BM25, not
  the whole document.

- **Compress** — fit the selection into a tight budget. `build_context.py`
  leads with summaries and metadata for orientation and includes
  budget-trimmed `original_text` only where needed
  (`DEFAULT_CONTEXT_CHAR_BUDGET`).

- **Isolate** — keep context types in separate, labeled blocks so they don't
  bleed into each other: system rules vs. retrieval metadata vs. verbatim source
  text vs. the user question. The context package and this directory both
  enforce that separation.

## Authority

Across all of these, **`original_text` (with section id + page range) is the
only authority for an answer.** Summaries, topics, and notes orient retrieval
and the model; they are never cited as the regulation. See
[../docs/ENRICHMENT.md](../docs/ENRICHMENT.md).
