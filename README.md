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
