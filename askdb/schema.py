import os
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv

load_dotenv()

COLUMNS_QUERY = """
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
"""

# Read FKs from pg_catalog rather than information_schema: the latter is
# privilege-filtered and returns nothing for the read-only app role.
# Note: conkey[1]/confkey[1] take only the first column, so composite
# foreign keys would be truncated. Chinook has none.
FKS_QUERY = """
SELECT
    src.relname  AS table_name,
    src_col.attname AS column_name,
    tgt.relname  AS foreign_table,
    tgt_col.attname AS foreign_column
FROM pg_constraint AS c
JOIN pg_class AS src ON src.oid = c.conrelid
JOIN pg_class AS tgt ON tgt.oid = c.confrelid
JOIN pg_namespace AS n ON n.oid = src.relnamespace
JOIN pg_attribute AS src_col
    ON src_col.attrelid = c.conrelid AND src_col.attnum = c.conkey[1]
JOIN pg_attribute AS tgt_col
    ON tgt_col.attrelid = c.confrelid AND tgt_col.attnum = c.confkey[1]
WHERE c.contype = 'f'
  AND n.nspname = 'public'
ORDER BY src.relname, src_col.attname;
"""


def get_schema() -> str:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    cur.execute(COLUMNS_QUERY)
    column_rows = cur.fetchall()

    cur.execute(FKS_QUERY)
    fk_rows = cur.fetchall()

    cur.close()
    conn.close()

    # Group columns by table
    tables = defaultdict(list)
    for table_name, column_name, data_type in column_rows:
        tables[table_name].append((column_name, data_type))

    # Group foreign keys by table
    foreign_keys = defaultdict(list)
    for table_name, column_name, ftable, fcolumn in fk_rows:
        foreign_keys[table_name].append((column_name, ftable, fcolumn))

    # Build the text
    blocks = []
    for table_name, columns in tables.items():
        lines = [f"CREATE TABLE {table_name} ("]
        for column_name, data_type in columns:
            lines.append(f"  {column_name} {data_type},")
        lines[-1] = lines[-1].rstrip(",")   # drop trailing comma
        lines.append(");")

        for column_name, ftable, fcolumn in foreign_keys[table_name]:
            lines.append(f"-- {table_name}.{column_name} references {ftable}.{fcolumn}")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)
