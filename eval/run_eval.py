"""Run all eval questions through the pipeline and score them."""

import argparse
import csv
import time

from askdb.db import run_query
from askdb.pipeline import answer
from eval.compare_results import compare


def load_questions(path="eval/questions.csv"):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    mode = "rag" if args.retrieval else "full"
    out_path = args.out or f"eval/results_{mode}.csv"

    questions = load_questions()
    if args.limit:
        questions = questions[: args.limit]

    results = []
    for q in questions:
        order_matters = q["order_matters"].strip().lower() == "true"

        gold_cols, gold_rows, gold_err = run_query(q["gold_sql"])

        log = []
        start = time.time()
        pred_sql, pred_cols, pred_rows, pred_err = answer(
            q["question"], use_retrieval=args.retrieval, log=log
        )
        elapsed = round(time.time() - start, 1)

        match, reason = compare(
            gold_cols, gold_rows, pred_cols, pred_rows, order_matters
        )

        results.append({
            "id": q["id"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "correct": match,
            "reason": reason or ("db error" if pred_err else ""),
            "attempts": len(log),
            "seconds": elapsed,
            "pred_sql": pred_sql or "",
            "pred_error": pred_err or "",
        })

        flag = "ok " if match else "XX "
        print(f"{flag}{q['id']:>3} [{q['difficulty']:<6}] {elapsed:>5}s  "
              f"{q['question'][:45]:<45} {reason}")

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    total = len(results)
    correct = sum(r["correct"] for r in results)
    print(f"\n=== mode: {mode} ===")
    print(f"overall: {correct}/{total} = {100 * correct / total:.1f}%")

    for tier in ["easy", "medium", "hard"]:
        sub = [r for r in results if r["difficulty"] == tier]
        if sub:
            c = sum(r["correct"] for r in sub)
            print(f"{tier:<7}: {c}/{len(sub)} = {100 * c / len(sub):.1f}%")

    retried = sum(1 for r in results if r["attempts"] > 1)
    print(f"retries fired: {retried}/{total}")
    print(f"written to {out_path}")


if __name__ == "__main__":
    main()
