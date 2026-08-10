"""Schema retrieval: embed table descriptions, retrieve relevant tables per question.

Descriptions are written to match the vocabulary of user *questions*, not to
list columns. A question says "best-selling artist", never "invoice_line.quantity",
so the description has to bridge that gap.
"""

TABLE_DESCRIPTIONS = {
    "album": (
        "Music albums released by artists. Each album has a title and belongs "
        "to one artist, and contains many tracks. Use for questions about "
        "albums, records, how many albums an artist released, or album titles."
    ),
    "artist": (
        "Musicians and bands. Each artist has a name and may have many albums. "
        "Use for questions about artists, bands, performers, or which artist "
        "made a particular album or song."
    ),
    "customer": (
        "People who buy music from the store. Includes name, email, phone, "
        "company, and full address with city, state, country and postal code. "
        "Each customer is assigned a support representative. Use for questions "
        "about customers, buyers, where customers live, or customers by country."
    ),
    "employee": (
        "Staff members of the music store. Includes job title, hire date, birth "
        "date, contact details, and which employee each one reports to, forming "
        "a management hierarchy. Some employees act as sales support "
        "representatives for customers. Use for questions about employees, "
        "staff, managers, support reps, or who reports to whom."
    ),
    "genre": (
        "Musical genres such as Rock, Jazz, Latin, Metal and Classical. Each "
        "track belongs to one genre. Use for questions about music styles, "
        "genres, or counting and comparing tracks by genre."
    ),
    "invoice": (
        "Customer purchase receipts. Each invoice records one purchase by one "
        "customer, with the invoice date, billing address, and the total amount "
        "paid. Use for questions about sales, orders, revenue totals, spending "
        "over time, or purchases by country."
    ),
    "invoice_line": (
        "Individual line items on customer invoices. Each row links one invoice "
        "to one purchased track, with the unit price and quantity bought. This "
        "is the only link between customer purchases and specific music. Use for "
        "revenue by track, album or artist, best-selling music, and any question "
        "connecting what customers spent to what they bought."
    ),
    "media_type": (
        "Audio file formats, such as MPEG audio, AAC, and protected files. Each "
        "track has one media type. Use for questions about file formats or "
        "encoding types."
    ),
    "playlist": (
        "User-created playlists. Contains only a playlist name. Playlists are "
        "not sold and have no price, revenue, artist or genre information. Use "
        "only for questions that explicitly mention playlists."
    ),
    "playlist_track": (
        "A junction table linking playlists to the tracks they contain. Holds "
        "only two ID columns and no other data. Not related to sales, revenue or "
        "customers. Use only when a question needs which tracks are on which "
        "playlist."
    ),
    "track": (
        "Individual songs sold by the store. Includes the song name, composer, "
        "duration in milliseconds, file size in bytes, and unit price. Each "
        "track belongs to an album, a genre and a media type. Use for questions "
        "about songs, track names, song length or duration, composers, or track "
        "prices."
    ),
}


import os

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_model = None


def get_model():
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(text: str) -> list:
    return get_model().encode(text).tolist()


def build_index():
    """Embed every table description and store it. Run once, or after edits."""
    conn = psycopg2.connect(os.environ["ADMIN_DATABASE_URL"])
    cur = conn.cursor()

    for table_name, description in TABLE_DESCRIPTIONS.items():
        vector = embed(description)
        cur.execute(
            """
            INSERT INTO table_docs (table_name, description, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (table_name)
            DO UPDATE SET description = EXCLUDED.description,
                          embedding   = EXCLUDED.embedding;
            """,
            (table_name, description, vector),
        )
        print("indexed:", table_name)

    conn.commit()
    cur.close()
    conn.close()


def retrieve_tables(question: str, k: int = 4) -> list:
    """Return the k table names whose descriptions best match the question."""
    vector = embed(question)

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name, 1 - (embedding <=> %s::vector) AS similarity
        FROM table_docs
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (vector, vector, k),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [(name, round(score, 3)) for name, score in rows]
