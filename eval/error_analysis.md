# Error analysis — 40-question eval, full-schema mode, 28/40 (70.0%)

| Category | Count | Questions |
|---|---|---|
| Column selection (logic correct) | 5 | 18, 19, 24, 27, 34 |
| Comparison artifact (extra ID col / unresolved FK) | 3 | 30, 35, 39 |
| Incorrect SQL | 3 | 31, 36, 40 |
| Ambiguous question | 1 | 28 |

## The three real failures

**Q31 — "which 5 artists sold the most tracks"**: counted tracks in the
catalogue rather than tracks sold; never joined `invoice_line`. Returns a
plausible ranking that answers a different question. The most dangerous
failure mode here — silently wrong, not an error.

**Q36 — "customers who spent more than average"**: compared each invoice
against the average invoice, rather than each customer's total against the
average customer total. Nested aggregates require a subquery the model did
not produce.

**Q40 — "most purchased genre per country"**: grouped correctly but omitted
the ranking step, returning all 237 country-genre pairs instead of 24 winners.
Requires ROW_NUMBER() OVER (PARTITION BY ...); the model did not use a window
function.

## Interpretation

Only 3 of 12 failures are incorrect SQL. Scored on "did the query answer the
question", accuracy is 37/40 = 92.5%; under strict column matching it is
28/40 = 70%.

Strict matching was retained: accepting column supersets makes the metric
unfalsifiable, since a query returning every column of every table would pass
every question. But the 22-point gap shows a text-to-SQL accuracy figure is
uninterpretable without stating the comparison rule.

## Intervention

Adding one prompt rule ("return only the columns the question asks for")
raised overall accuracy 67.5% -> 70.0% and easy-tier accuracy 93.3% -> 100%.
It also regressed Q36 from a column mismatch to a row-count error: dropping a
column changed the GROUP BY and broke the aggregation. Prompt rules interact.
