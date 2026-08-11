# AskDB — Natural Language to SQL

A text-to-SQL system over the Chinook music-store database (11 tables, PostgreSQL),
built entirely on open-source, locally-hosted components. Questions in plain English
are converted to SQL, validated, executed against a read-only database role, and
returned as tables.

**Measured at 70.0% execution accuracy on a hand-written 40-question evaluation set**
(100% easy / 60% medium / 40% hard), using `qwen2.5-coder:7b` running locally via
Ollama at temperature 0.

---

## Results

### Execution accuracy (40 questions, strict column matching)

| Mode | Overall | Easy (15) | Medium (15) | Hard (10) | Avg prompt |
|---|---|---|---|---|---|
| Full schema | 28/40 (70.0%) | 15/15 (100%) | 9/15 (60%) | 4/10 (40%) | 3,231 chars |
| Schema retrieval (k=6) | 28/40 (70.0%) | 14/15 (93%) | 9/15 (60%) | 5/10 (50%) | 1,933 chars |

An earlier full-schema run scored 27/40 (67.5%). Error analysis showed the largest
single failure category was column-selection mismatch, so one rule was added to the
prompt — *"return only the columns the question asks for"* — which lifted overall
accuracy to 70.0% and easy-tier accuracy from 93.3% to 100%.

### What "70%" actually means

Of the 12 failures, only **3 were incorrect SQL**. The remaining 9 were logically
correct queries that returned a different column set from the gold query.

Scored on *"did the query answer the question"*, accuracy is **37/40 = 92.5%**.
Under strict column matching it is **28/40 = 70.0%**.

Strict matching was retained deliberately: accepting column supersets makes the
metric unfalsifiable, since a query returning every column of every table would pass
every question. But the 22-point gap demonstrates that a text-to-SQL accuracy figure
is uninterpretable without stating the comparison rule alongside it.

---

## Architecture
Every component runs locally. No API keys, no external calls, no spend.

### Design decisions

**Read-only database role as the security boundary.** The application connects as
`chinook_readonly`, which holds `SELECT` and nothing else. The `validate_sql` string
check exists alongside it to fail fast with a clear message rather than after a
database round-trip — but the role is what makes damage impossible. Verified by
attempting `DROP TABLE album` as the app user and confirming rejection.

**Foreign keys included in the schema prompt.** Each table block is followed by
comment lines naming its relationships. Without these the model can see column names
but not which ones connect, and guesses wrong on exactly the multi-join questions
that make up the hard tier.

**Retry exactly once.** At temperature 0 the model is deterministic, so a second
identical retry would produce identical output unless the prompt changed. A fixed
retry budget also keeps the accuracy figure interpretable.

**Plain Python, no orchestration framework.** The whole pipeline is roughly 250 lines.
A framework would have hidden the parts worth understanding.

---

## Setup

Tested on macOS (Apple Silicon). Note the non-default port and the from-source
pgvector build — both are consequences of this machine already running PostgreSQL 17.

### 1. PostgreSQL 16 and the Chinook dataset

```bash
brew install postgresql@16
brew services start postgresql@16
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

`postgresql@16` is keg-only, so it must be added to PATH explicitly. This install
listens on **port 5433**, not the default 5432, to coexist with an existing
PostgreSQL 17 system service.

Load Chinook from https://github.com/lerocha/chinook-database — the script drops and
recreates the `chinook` database itself. Table names in this version are lowercase
snake_case (`album`, `invoice_line`), so no identifier quoting is required in
generated SQL.

### 2. Read-only application role

```sql
CREATE ROLE chinook_readonly LOGIN PASSWORD 'change_me';
GRANT CONNECT ON DATABASE chinook TO chinook_readonly;
GRANT USAGE ON SCHEMA public TO chinook_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chinook_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO chinook_readonly;
ALTER ROLE chinook_readonly SET statement_timeout = '10s';
```

### 3. pgvector

The Homebrew bottle ships extensions for PostgreSQL 17 and 18 only, so it must be
built from source against PG16:

```bash
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
export PG_CONFIG=/opt/homebrew/opt/postgresql@16/bin/pg_config
make && make install
psql -p 5433 -d chinook -c "CREATE EXTENSION vector;"
```

### 4. Ollama and the model

```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5-coder:7b
```

~4.7GB on disk; needs roughly 6–8GB of RAM at Q4 quantization.

### 5. Python environment

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Python 3.12 or newer.** macOS ships 3.9, which fails on the PyTorch dependency
that `sentence-transformers` pulls in.

### 6. Configuration

```bash
cp .env.example .env
```

Fill in `DATABASE_URL` (the read-only role) and `ADMIN_DATABASE_URL` (a role that can
create tables, needed only for building the retrieval index).

### 7. Build the retrieval index (optional)

```bash
python -c "from askdb.retrieval import build_index; build_index()"
```

---

## Usage

Command line:

```bash
python -m askdb "Which 5 artists have the most albums?"
```

Web interface:

```bash
streamlit run app.py
```

Run the evaluation:

```bash
python -m eval.run_eval                # full schema
python -m eval.run_eval --retrieval    # with schema retrieval
```

---

## Findings

### Schema retrieval did not improve accuracy

Both modes scored 28/40. Retrieval cut average prompt size by 40% (3,231 → 1,933
characters) but scored identically overall, and the two modes failed on almost the
same questions. This indicates schema size was never the bottleneck — model
capability on multi-join aggregation was.

The retrieval mechanism itself has a specific, measurable weakness. On *"which
artists sold the most tracks"*, the `artist` table ranks **7th of 11** despite the
question naming it outright. Similarity scores cluster in a narrow band (0.43–0.78)
against a ~0.47 baseline for unrelated text, so ranking is weakly discriminative, and
longer table descriptions outrank shorter ones regardless of relevance.

The underlying reason: **embedding similarity ranks tables by topical match, while
SQL generation requires join reachability.** A table can be essential to a query
while scoring poorly against the question text. On an 11-table schema that fits
comfortably in a 32k context window, retrieval trades correctness for tokens with no
compensating benefit. It becomes worthwhile only when the schema exceeds the context
budget — and even then, top-k alone is insufficient; join-graph expansion would be
needed.

Sharpening the `playlist` table description moved it from rank 1 to rank 6 on the
artist question, confirming description wording measurably changes retrieval without
fixing the structural limitation.

### Error analysis

| Category | Count | Questions |
|---|---|---|
| Column selection (logic correct) | 5 | 18, 19, 24, 27, 34 |
| Comparison artifact (extra ID column, unresolved FK) | 3 | 30, 35, 39 |
| Incorrect SQL | 3 | 31, 36, 40 |
| Ambiguous question | 1 | 28 |

**The three genuine failures:**

**Q31 — "which 5 artists sold the most tracks"** counted tracks in the *catalogue*
rather than tracks *sold*, never joining `invoice_line`. It returns a plausible,
confidently-formatted ranking that answers a different question. No error is raised.
This is the most dangerous failure mode in a text-to-SQL system: silently wrong
rather than visibly broken, and undetectable without a gold answer to compare against.

**Q36 — "customers who spent more than average"** compared each individual invoice
against the average invoice, rather than each customer's total against the average
customer total. Correct handling requires nesting an aggregate inside a subquery,
which the model did not produce.

**Q40 — "most purchased genre in each country"** grouped correctly by country and
genre but omitted the ranking step, returning all 237 combinations instead of 24
winners. Requires `ROW_NUMBER() OVER (PARTITION BY ...)`; the model did not reach for
a window function.

Two of the three are model capability limits rather than prompt problems.

### Prompt rules interact

The column-selection rule that lifted overall accuracy also *regressed* Q36: dropping
a column changed the `GROUP BY`, converting a column mismatch into a row-count error.
Prompt changes are not independent, and a net improvement can hide localised
regressions.

### Schema extraction and database privileges

Foreign keys are read from `pg_catalog`, not `information_schema`. The latter is
privilege-filtered and returns **zero rows** for the read-only application role,
which silently produced a schema with no relationships at all — no error, just eleven
missing lines that would have degraded every join question. A direct and non-obvious
consequence of the read-only security design.

---

## Evaluation methodology

40 questions written **before** any system output was examined, split 15 easy /
15 medium / 10 hard. Each has hand-written gold SQL, verified to execute successfully
and return a non-empty result under the application's read-only role.

One question was rewritten during construction: *"tracks appearing on more than one
playlist"* matched all 3,503 tracks, making the correct answer "everything" and
giving zero discriminating power. It was retargeted to a threshold matching ~3% of
tracks.

**Comparison rule** (`eval/compare_results.py`, 10 unit tests):

- Column *order* ignored — values sorted within each row before comparison
- Column *count* must match — supersets rejected
- Row order ignored unless the question implies an ordering, set per-question via an
  `order_matters` flag
- Numerics normalised to 4 decimal places, absorbing Decimal/float differences while
  still catching a model that rounds to 2dp
- `NULL` mapped to a sentinel string

The `order_matters` flag was set to false for the top-10-most-expensive-tracks
question because all ten prices tie at 1.99, making the ordering arbitrary and
non-deterministic.

---

## Known limitations

- **`validate_sql` splits on `;` naively**, so a semicolon inside a string literal
  would be rejected. This is a false negative, never a false positive — the
  read-only role is the actual security guarantee. Correct handling would require a
  SQL parser such as `sqlglot`.
- **Foreign key extraction uses `conkey[1]`**, taking only the first column of a
  constraint. Composite foreign keys would be truncated. Chinook has none.
- **Strict column matching penalises correct queries.** Nine of twelve failures fall
  into this category. The alternative (accepting supersets) is worse, but a
  three-way scoring scheme — correct / correct-with-different-columns / wrong —
  would be more informative than a single binary.
- **Retrieval index must be rebuilt manually** after editing table descriptions.
- **Single-turn only.** No follow-up questions or conversational context.
- **One model, one dataset.** Results are specific to `qwen2.5-coder:7b` on an
  11-table schema and should not be assumed to generalise.

---

## What I would do next

1. **Compare model sizes.** Run the identical eval against `qwen2.5-coder:14b` and
   a frontier API model. This measures capability rather than tuning, and would
   establish how much of the 30-point gap is model size versus method.
2. **Test retrieval on a schema where it matters.** The RAG finding is a negative
   result on 11 tables. Running the same comparison on a 100-table schema would turn
   a single data point into a curve, and is where join-graph expansion could be
   tested against plain top-k.
3. **Three-way scoring.** Separate "wrong answer" from "right answer, different
   columns" so the metric distinguishes logic failures from formatting differences.
4. **Detect silent wrongness.** Q31's failure mode — a confident answer to a
   different question — is the one that matters in production and the one this
   pipeline cannot currently catch.

---

## Dataset notes

- Invoice dates span 2021-01-01 to 2025-12-22 (not the classic 2009–2013 Chinook
  range). Evaluation questions use years inside this window.
- 3,503 tracks, 347 albums, 59 customers, 24 billing countries.
- All tracks have a `genre_id`, so track–genre joins drop no rows.
- Two playlists share the name "Music" and two share "TV Shows", with distinct IDs.
  This makes *"how many tracks are on each playlist"* genuinely ambiguous — grouping
  by name yields 12 rows, grouping by ID yields 14. Retained in the eval set as a
  legitimate ambiguity category.

---

## Stack

PostgreSQL 16 · pgvector · Ollama (`qwen2.5-coder:7b`) ·
sentence-transformers (`BAAI/bge-small-en-v1.5`) · psycopg2 · Streamlit · Python 3.12

All components open source and locally hosted.
