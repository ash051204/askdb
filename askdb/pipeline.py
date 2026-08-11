import re

from tabulate import tabulate

from askdb.schema import get_schema

PROMPT_TEMPLATE = """You are a PostgreSQL expert. Write a single SQL query that answers the user's question.

Database schema:
{schema}

Rules:
- Return ONLY the SQL query. No explanation, no commentary.
- Use only tables and columns that appear in the schema above.
- Write a SELECT query only. Never modify the database.
- If the question implies a top-N ("top 5", "most", "best"), use ORDER BY and LIMIT.
- Return only the columns the question asks for. Do not add ID columns or
  extra context columns that were not requested.
- Date columns are timestamps. For a date range use `col >= 'start' AND col < 'next_start'`, not BETWEEN.

Question: {question}

SQL:"""


def build_prompt(question: str, use_retrieval: bool = False, k: int = 6) -> str:
    """Build the prompt. With use_retrieval, include only the top-k tables."""
    if use_retrieval:
        from askdb.retrieval import retrieve_tables
        tables = [name for name, _ in retrieve_tables(question, k=k)]
        schema = get_schema(tables)
    else:
        schema = get_schema()
    return PROMPT_TEMPLATE.format(schema=schema, question=question)


def extract_sql(text: str) -> str:
    """Pull the SQL statement out of an LLM response.

    The model still wraps output in a markdown fence despite being told not
    to, so strip it. If there's no fence, assume the whole reply is SQL.
    """
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return text.strip()


def format_results(columns, rows) -> str:
    """Render query results as a text table."""
    if not rows:
        return "No rows returned."
    return tabulate(rows, headers=columns)


class UnsafeSQLError(Exception):
    """Raised when generated SQL fails validation."""


def validate_sql(sql: str) -> str:
    """Reject anything that isn't a single read-only statement.

    The read-only DB role is the real guarantee; this exists to fail fast
    with a clear message rather than after a database round-trip.
    """
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    if len(statements) == 0:
        raise UnsafeSQLError("No SQL statement found.")
    if len(statements) > 1:
        raise UnsafeSQLError(f"Expected one statement, got {len(statements)}.")

    statement = statements[0]
    first_word = statement.split()[0].upper()

    if first_word not in ("SELECT", "WITH"):
        raise UnsafeSQLError(f"Only SELECT queries are allowed, got {first_word}.")

    return statement


RETRY_TEMPLATE = """You are a PostgreSQL expert. Your previous query failed.

Database schema:
{schema}

Question: {question}

Your previous SQL:
{failed_sql}

The database returned this error:
{error}

Write a corrected SQL query. Return ONLY the SQL, no explanation.

SQL:"""


def answer(question: str, use_retrieval: bool = False, log=None):
    """Question -> SQL -> result, with one retry on failure.

    Returns (sql, columns, rows, error). Error is None on success.
    """
    from askdb.db import run_query
    from askdb.llm import generate

    attempts = []

    sql = extract_sql(generate(build_prompt(question, use_retrieval=use_retrieval)))
    try:
        sql = validate_sql(sql)
    except UnsafeSQLError as e:
        return sql, None, None, str(e)

    columns, rows, error = run_query(sql)
    attempts.append({"sql": sql, "error": error})

    if error is not None:
        retry_prompt = RETRY_TEMPLATE.format(
            schema=get_schema(),
            question=question,
            failed_sql=sql,
            error=error,
        )
        sql = extract_sql(generate(retry_prompt))
        try:
            sql = validate_sql(sql)
        except UnsafeSQLError as e:
            return sql, None, None, str(e)

        columns, rows, error = run_query(sql)
        attempts.append({"sql": sql, "error": error})

    if log is not None:
        log.extend(attempts)

    return sql, columns, rows, error
