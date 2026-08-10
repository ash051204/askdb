import re

from askdb.schema import get_schema

PROMPT_TEMPLATE = """You are a PostgreSQL expert. Write a single SQL query that answers the user's question.

Database schema:
{schema}

Rules:
- Return ONLY the SQL query. No explanation, no commentary.
- Use only tables and columns that appear in the schema above.
- Write a SELECT query only. Never modify the database.
- If the question implies a top-N ("top 5", "most", "best"), use ORDER BY and LIMIT.
- Date columns are timestamps. For a date range use `col >= 'start' AND col < 'next_start'`, not BETWEEN.

Question: {question}

SQL:"""


def build_prompt(question: str) -> str:
    return PROMPT_TEMPLATE.format(schema=get_schema(), question=question)


def extract_sql(text: str) -> str:
    """Pull the SQL statement out of an LLM response.

    The model still wraps output in a markdown fence despite being told not
    to, so strip it. If there's no fence, assume the whole reply is SQL.
    """
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return text.strip()


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
