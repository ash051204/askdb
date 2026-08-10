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
        "Named collections of tracks curated in the store, such as Classical or "
        "Heavy Metal playlists. Contains only the playlist name. Not related to "
        "sales or customers. Use for questions about playlists."
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
