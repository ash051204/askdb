import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def run_query(sql: str):
    """Execute a query and return (columns, rows, error).

    Returns error as a string rather than raising, because the retry loop
    needs the database's own message to send back to the model.
    """
    conn = None
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        return columns, rows, None
    except psycopg2.Error as e:
        return None, None, str(e).strip()
    finally:
        if conn is not None:
            conn.close()
