"""Execution-accuracy comparison for text-to-SQL evaluation.

Design decisions (each defensible, each has a cost):

1. Column ORDER is ignored, column COUNT is not. Values within a row are
   sorted before comparison, so (name, price) matches (price, name). But a
   result with an extra column is WRONG — accepting supersets would let a
   query returning every column of every table pass every question.

2. Row order is ignored unless the question implies an ordering, controlled
   per-question by the `order_matters` flag. "Top 5 artists" implies order;
   "which customers are in Canada" does not.

3. Numerics are rounded to 4dp. Postgres returns Decimal for SUM and float
   for AVG; 4dp absorbs that noise while still catching a model that rounds
   to 2dp (1.05 != 1.0508).

4. NULL becomes the sentinel string "NULL" so it compares consistently and
   is distinguishable from the literal string "None".
"""

from decimal import Decimal


def _normalise(value):
    if value is None:
        return "NULL"
    if isinstance(value, (Decimal, float, int)) and not isinstance(value, bool):
        return round(float(value), 4)
    return str(value)


def _normalise_row(row, sort_values: bool):
    values = [_normalise(v) for v in row]
    if sort_values:
        values = sorted(values, key=lambda v: (type(v).__name__, v))
    return tuple(values)


def compare(gold_cols, gold_rows, pred_cols, pred_rows, order_matters=False):
    """Return (is_match, reason). reason is '' when matched."""
    if pred_rows is None or pred_cols is None:
        return False, "no result"
    if gold_rows is None or gold_cols is None:
        return False, "gold query failed"

    if len(gold_cols) != len(pred_cols):
        return False, f"column count {len(pred_cols)} != {len(gold_cols)}"

    if len(gold_rows) != len(pred_rows):
        return False, f"row count {len(pred_rows)} != {len(gold_rows)}"

    gold_norm = [_normalise_row(r, sort_values=True) for r in gold_rows]
    pred_norm = [_normalise_row(r, sort_values=True) for r in pred_rows]

    if order_matters:
        if gold_norm == pred_norm:
            return True, ""
        return False, "row order or values differ"

    if sorted(gold_norm) == sorted(pred_norm):
        return True, ""
    return False, "values differ"
