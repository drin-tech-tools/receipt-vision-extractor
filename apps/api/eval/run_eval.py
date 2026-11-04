"""Run the extractor over the labelled dataset and report accuracy.

python -m eval.run_eval                    # uses GEMINI_API_KEY
python -m eval.run_eval --limit 5 --out eval/results/latest.json
"""

import argparse
import json
import mimetypes
import time
from pathlib import Path

from app.extractor import get_extractor
from app.schemas import DocType

from .scoring import aggregate, score_document

DATA = Path(__file__).parent / "data"


def run(limit: int | None, out: Path | None) -> dict:
    extractor = get_extractor()
    manifest = json.loads((DATA / "manifest.json").read_text())[:limit]
    by_type: dict[str, list[dict]] = {}
    latencies: list[float] = []
    rows = []
    for entry in manifest:
        image_path = DATA / entry["image"]
        expected = json.loads((DATA / entry["label"]).read_text())
        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        t0 = time.perf_counter()
        try:
            actual = extractor.extract(image_path.read_bytes(), mime, DocType(entry["doc_type"]))
            actual = actual.model_dump(mode="json")
            err = None
        except Exception as e:  # count failures as fully wrong rather than aborting the run
            actual, err = {}, str(e)
        latencies.append(time.perf_counter() - t0)
        res = score_document(expected, actual)
        res["error"] = err
        by_type.setdefault(entry["doc_type"], []).append(res)
        rows.append({"image": entry["image"], **res})
        print(f"{'OK ' if res['exact'] else 'DIFF'} {entry['image']}")

    report = {
        "model": extractor.model,
        "avg_latency_s": sum(latencies) / len(latencies) if latencies else None,
        "by_doc_type": {t: aggregate(r) for t, r in by_type.items()},
        "documents": rows,
    }
    for t, agg in report["by_doc_type"].items():
        print(
            f"\n[{t}] docs={agg['documents']} field_acc={agg['field_accuracy']:.1%} "
            f"exact={agg['exact_match_rate']:.1%} item_f1={agg['item_f1']}"
        )
        for k, v in agg["per_field"].items():
            print(f"   {k:<18}{v:.0%}")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    run(args.limit, args.out)
