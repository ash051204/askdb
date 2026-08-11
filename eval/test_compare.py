from decimal import Decimal
from eval.compare_results import compare

CASES = [
    ("identical",
     (["a", "b"], [("x", 1)]), (["a", "b"], [("x", 1)]), False, True),

    ("column order swapped",
     (["a", "b"], [("x", 1)]), (["b", "a"], [(1, "x")]), False, True),

    ("row order differs, order_matters=False",
     (["a"], [("x",), ("y",)]), (["a"], [("y",), ("x",)]), False, True),

    ("row order differs, order_matters=True",
     (["a"], [("x",), ("y",)]), (["a"], [("y",), ("x",)]), True, False),

    ("Decimal vs float",
     (["a"], [(Decimal("138.60"),)]), (["a"], [(138.6,)]), False, True),

    ("rounded to 2dp vs full precision",
     (["a"], [(1.0508050242649158,)]), (["a"], [(1.05,)]), False, False),

    ("extra column",
     (["a"], [("x",)]), (["id", "a"], [(1, "x")]), False, False),

    ("different data",
     (["a"], [("x",)]), (["a"], [("y",)]), False, False),

    ("model errored",
     (["a"], [("x",)]), (None, None), False, False),

    ("NULL handling",
     (["a"], [(None,)]), (["a"], [(None,)]), False, True),
]

passed = 0
for name, gold, pred, order, expected in CASES:
    got, reason = compare(gold[0], gold[1], pred[0], pred[1], order)
    ok = got == expected
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:40} got={got} {reason}")

print(f"\n{passed}/{len(CASES)} tests passed")
