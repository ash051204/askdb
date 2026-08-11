# AskDB

A natural language to SQL assistant over the Chinook Postgres database.

Status: in development

## Local setup notes

- PostgreSQL 16 (Homebrew) runs on port **5433**, not the default 5432,
  because PostgreSQL 17 already occupies 5432 on this machine.
- The Chinook Postgres script drops and recreates the `chinook` database itself.
- Table names are lowercase snake_case (`album`, `invoice_line`) — no
  identifier quoting needed in generated SQL.
- App connects as `chinook_readonly`, a SELECT-only role with a 10s
  statement timeout.
- Invoice dates span 2021-01-01 to 2025-12-22 (not the classic 2009-2013
  Chinook range). Eval questions must use years inside this window.
- All 3503 tracks have a genre_id, so track-genre joins drop no rows.
- Foreign keys are read from `pg_catalog`, not `information_schema`. The
  latter filters by privilege and returns nothing for the read-only app
  role, which silently produced a schema with no relationships.
- `validate_sql` splits on `;` naively, so a semicolon inside a string
  literal would be rejected. This is a false negative, never a false
  positive — the read-only role is the actual security guarantee.

## Smoke test (Phase 2, 10 questions)

10/10 on practice-set questions (easy/medium only). Observations:
- Prompt's date-range rule was ignored; model used EXTRACT(YEAR...) instead.
  Correct result, but non-sargable.
- Model omits ORDER BY when the question doesn't imply one — motivates the
  `order_matters` flag in the Phase 4 comparison function.
- pgvector's Homebrew bottle only ships extensions for PG17/PG18, so it was
  built from source (v0.8.0) against postgresql@16's pg_config.

## Retrieval quality (Phase 3)

Similarity scores cluster in a narrow band (0.43-0.78) against a ~0.47 baseline
for unrelated text, so ranking is weakly discriminative.

On "which artists sold the most tracks", the `artist` table ranks 7th of 11 —
k must reach 64% of the schema to retrieve a table the question names outright.
Longer descriptions (album, track) outrank shorter ones (artist) regardless of
relevance.

Root cause: embedding similarity matches on topic, while SQL generation needs
join reachability. A question requiring a 4-table join chain cannot be served
by top-k semantic retrieval unless k approaches full schema size.

Sharpening the `playlist` description moved it from rank 1 to rank 6 on the
artist question — wording measurably changes retrieval, but does not fix the
structural limitation.

## RAG vs. full-schema comparison (Phase 3)

12 questions, qwen2.5-coder:7b, temperature 0, retrieval at k=6 of 11 tables.

| Mode | Executed successfully | Avg prompt |
|---|---|---|
| Full schema | 12/12 | 3,231 chars |
| Retrieval (k=6) | 11/12 | 1,933 chars |

Retrieval cut prompt size 40% at the cost of one failure. The failing question
("which artists sold the most tracks") needs a 4-table join chain
artist -> album -> track -> invoice_line; `artist` ranks 7th of 11 in retrieval,
so it was absent from the prompt and the model produced SQL referencing a table
it could not see.

Conclusion: on an 11-table schema that fits comfortably in context, retrieval
trades correctness for tokens with no benefit. Semantic similarity ranks tables
by topical match, but SQL generation requires join reachability — a table can be
essential to a query while scoring poorly against the question text. Retrieval
becomes worthwhile only when the full schema exceeds the context budget, and
even then needs join-graph expansion rather than top-k alone.
