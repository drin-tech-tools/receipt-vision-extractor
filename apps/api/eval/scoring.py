"""Field-level scoring of extracted documents against labelled ground truth."""

import re
from collections import defaultdict
from typing import Any

NUM_TOL = 0.01


def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def field_match(expected: Any, actual: Any) -> bool:
    if expected is None or actual is None:
        return expected is None and actual is None
    if isinstance(expected, int | float) and not isinstance(expected, bool):
        try:
            return abs(float(expected) - float(actual)) <= NUM_TOL
        except (TypeError, ValueError):
            return False
    return _norm(expected) == _norm(actual)


def item_match(expected: dict, actual: dict) -> bool:
    return (
        _norm(expected["description"]) == _norm(actual.get("description", ""))
        and field_match(expected.get("quantity", 1), actual.get("quantity", 1))
        and field_match(expected.get("total"), actual.get("total"))
    )


def item_prf(expected: list[dict], actual: list[dict]) -> tuple[float, float, float]:
    """Precision/recall/F1 using greedy one-to-one matching of line items."""
    remaining = list(actual)
    hits = 0
    for e in expected:
        for i, a in enumerate(remaining):
            if item_match(e, a):
                hits += 1
                del remaining[i]
                break
    p = hits / len(actual) if actual else (1.0 if not expected else 0.0)
    r = hits / len(expected) if expected else (1.0 if not actual else 0.0)
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def score_document(expected: dict, actual: dict) -> dict[str, Any]:
    """Return per-field correctness (bool) and, for receipts, line-item F1."""
    fields = {k: field_match(v, actual.get(k)) for k, v in expected.items() if k != "items"}
    out: dict[str, Any] = {"fields": fields}
    if "items" in expected:
        out["item_f1"] = item_prf(expected["items"], actual.get("items") or [])[2]
    out["exact"] = all(fields.values()) and out.get("item_f1", 1.0) == 1.0
    return out


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    per_field: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        for k, ok in r["fields"].items():
            per_field[k].append(ok)
    f1s = [r["item_f1"] for r in results if "item_f1" in r]
    all_fields = [ok for oks in per_field.values() for ok in oks]
    return {
        "documents": len(results),
        "field_accuracy": sum(all_fields) / len(all_fields) if all_fields else 0.0,
        "exact_match_rate": sum(r["exact"] for r in results) / len(results) if results else 0.0,
        "item_f1": sum(f1s) / len(f1s) if f1s else None,
        "per_field": {k: sum(v) / len(v) for k, v in sorted(per_field.items())},
    }
