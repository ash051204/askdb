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
