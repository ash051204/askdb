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