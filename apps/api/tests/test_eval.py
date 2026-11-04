import json
from pathlib import Path

from app.schemas import SCHEMAS, DocType
from eval.scoring import aggregate, field_match, item_prf, score_document

DATA = Path(__file__).parent.parent / "eval" / "data"


def test_field_match_rules():
    assert field_match(12.5, 12.504)
    assert not field_match(12.5, 12.6)
    assert field_match("Blue  Heron CAFE", "blue heron cafe")
    assert field_match(None, None)
    assert not field_match(None, "x")
    assert not field_match("x", None)


def test_item_prf_partial():
    exp = [
        {"description": "A", "quantity": 1, "total": 1.0},
        {"description": "B", "quantity": 2, "total": 4.0},
    ]
    act = [{"description": "a", "quantity": 1, "total": 1.0}]
    p, r, f1 = item_prf(exp, act)
    assert (p, r) == (1.0, 0.5)
    assert round(f1, 3) == 0.667


def test_score_and_aggregate():
    exp = {"merchant_name": "X", "total": 5.0, "items": []}
    good = score_document(exp, {"merchant_name": "x", "total": 5.0, "items": []})
    bad = score_document(exp, {"merchant_name": "y", "total": 5.0, "items": []})
    assert good["exact"] and not bad["exact"]
    agg = aggregate([good, bad])
    assert agg["per_field"]["merchant_name"] == 0.5
    assert agg["exact_match_rate"] == 0.5


def test_dataset_is_consistent():
    manifest = json.loads((DATA / "manifest.json").read_text())
    assert len(manifest) >= 20
    for e in manifest:
        assert (DATA / e["image"]).exists()
        label = json.loads((DATA / e["label"]).read_text())
        SCHEMAS[DocType(e["doc_type"])].model_validate(label)


def test_receipt_labels_add_up():
    for p in (DATA / "receipt").glob("*.json"):
        label = json.loads(p.read_text())
        assert abs(sum(i["total"] for i in label["items"]) - label["subtotal"]) < 0.02
        assert abs(label["subtotal"] + label["tax"] + (label["tip"] or 0) - label["total"]) < 0.02
