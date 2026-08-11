from askdb.pipeline import answer, build_prompt

QUESTIONS = [
    "Which tracks are longer than 5 minutes?",
    "Which customers are in Canada?",
    "What are the 10 most expensive tracks?",
    "How many invoices came from each billing country?",
    "List every track name with its genre name",
    "Which employee is the support rep for each customer?",
    "List track name, album title, and artist name together",
    "How many tracks does each genre have?",
    "Which 5 artists have the most albums?",
    "What was the total revenue in 2021?",
    "Which artists sold the most tracks?",
    "Which country spent the most money?",
]

for mode in [False, True]:
    print("\n=== retrieval =", mode, "===")
    chars = 0
    errors = 0
    for q in QUESTIONS:
        chars += len(build_prompt(q, use_retrieval=mode))
        sql, cols, rows, err = answer(q, use_retrieval=mode)
        status = "ERR " if err else "ok  "
        if err:
            errors += 1
        print(f"{status}{q[:50]:50} {str(rows[:1]) if rows else err[:40] if err else ''}")
    print(f"errors: {errors}/{len(QUESTIONS)}   avg prompt: {chars // len(QUESTIONS)} chars")
