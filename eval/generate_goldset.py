"""Reverse-generate an eval set: valid SQL first, questions second.

Writing SQL and asking an LLM to describe it is far more reliable than the
reverse, because the SQL is correct by construction — it was written by hand
(as a template) and verified to execute and return rows before any question
was attached to it.

Limitation: generated questions are SQL translated into English, so they test
SQL generation but not natural language understanding. Real users phrase
things differently.
"""

import csv
import itertools

# (sql, difficulty, order_matters)
TEMPLATES = []

# --- easy: single-table filters and aggregates ---
for table, col, val in [
    ("customer", "country", "'Germany'"),
    ("customer", "country", "'Brazil'"),
    ("customer", "city", "'London'"),
    ("invoice", "billing_country", "'France'"),
    ("invoice", "billing_city", "'Berlin'"),
]:
    TEMPLATES.append((
        f"SELECT * FROM {table} WHERE {col} = {val};", "easy", False))

for table in ["track", "album", "artist", "invoice", "playlist", "genre"]:
    TEMPLATES.append((f"SELECT count(*) FROM {table};", "easy", False))

for col, op, val in [
    ("milliseconds", ">", 400000),
    ("milliseconds", "<", 60000),
    ("bytes", ">", 10000000),
    ("unit_price", ">", 1.0),
]:
    TEMPLATES.append((
        f"SELECT name, {col} FROM track WHERE {col} {op} {val};", "easy", False))

# --- medium: two-table joins and grouped aggregates ---
JOINS = [
    ("track", "genre", "track.genre_id = genre.genre_id", "track.name, genre.name"),
    ("track", "media_type", "track.media_type_id = media_type.media_type_id", "track.name, media_type.name"),
    ("album", "artist", "album.artist_id = artist.artist_id", "album.title, artist.name"),
    ("invoice", "customer", "invoice.customer_id = customer.customer_id", "invoice.total, customer.last_name"),
]
for left, right, on, cols in JOINS:
    TEMPLATES.append((
        f"SELECT {cols} FROM {left} JOIN {right} ON {on};", "medium", False))

for group_tbl, group_col, join_tbl, on in [
    ("genre", "name", "track", "track.genre_id = genre.genre_id"),
    ("media_type", "name", "track", "track.media_type_id = media_type.media_type_id"),
    ("artist", "name", "album", "album.artist_id = artist.artist_id"),
]:
    TEMPLATES.append((
        f"SELECT {group_tbl}.{group_col}, count(*) AS n "
        f"FROM {group_tbl} JOIN {join_tbl} ON {on} "
        f"GROUP BY {group_tbl}.{group_col} ORDER BY n DESC LIMIT 5;",
        "medium", True))

for col in ["billing_country", "billing_city"]:
    for agg in ["sum(total)", "avg(total)", "count(*)"]:
        TEMPLATES.append((
            f"SELECT {col}, {agg} AS v FROM invoice GROUP BY {col};",
            "medium", False))

# --- hard: revenue chains and multi-hop joins ---
for endpoint, join_path in [
    ("genre.name",
     "JOIN track ON invoice_line.track_id = track.track_id "
     "JOIN genre ON track.genre_id = genre.genre_id"),
    ("artist.name",
     "JOIN track ON invoice_line.track_id = track.track_id "
     "JOIN album ON track.album_id = album.album_id "
     "JOIN artist ON album.artist_id = artist.artist_id"),
    ("media_type.name",
     "JOIN track ON invoice_line.track_id = track.track_id "
     "JOIN media_type ON track.media_type_id = media_type.media_type_id"),
    ("album.title",
     "JOIN track ON invoice_line.track_id = track.track_id "
     "JOIN album ON track.album_id = album.album_id"),
]:
    for measure, alias in [
        ("sum(invoice_line.quantity)", "units_sold"),
        ("sum(invoice_line.unit_price * invoice_line.quantity)", "revenue"),
    ]:
        TEMPLATES.append((
            f"SELECT {endpoint}, {measure} AS {alias} "
            f"FROM invoice_line {join_path} "
            f"GROUP BY {endpoint} ORDER BY {alias} DESC LIMIT 5;",
            "hard", True))

for country in ["'USA'", "'Canada'", "'Brazil'"]:
    TEMPLATES.append((
        "SELECT sum(invoice_line.unit_price * invoice_line.quantity) AS revenue "
        "FROM invoice_line "
        "JOIN invoice ON invoice_line.invoice_id = invoice.invoice_id "
        f"WHERE invoice.billing_country = {country};",
        "hard", False))

TEMPLATES.append((
    "SELECT customer.last_name, count(DISTINCT track.genre_id) AS n "
    "FROM customer "
    "JOIN invoice ON invoice.customer_id = customer.customer_id "
    "JOIN invoice_line ON invoice_line.invoice_id = invoice.invoice_id "
    "JOIN track ON track.track_id = invoice_line.track_id "
    "GROUP BY customer.customer_id, customer.last_name "
    "HAVING count(DISTINCT track.genre_id) > 7;",
    "hard", False))

if __name__ == "__main__":
    print(f"{len(TEMPLATES)} candidate queries")
    with open("eval/generated_sql.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sql", "difficulty", "order_matters"])
        for sql, diff, order in TEMPLATES:
            w.writerow([sql, diff, str(order).lower()])
    print("written to eval/generated_sql.csv")
