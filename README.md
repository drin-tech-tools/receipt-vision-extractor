# receipt-vision-extractor

Monorepo for a multimodal document scanner. Upload a photo of a receipt or ID and a vision LLM (Gemini) returns **validated, structured JSON**.

| Part | Stack | Path |
|------|-------|------|
| Backend | Python, FastAPI, Pydantic, `google-genai` | [`apps/api`](apps/api) |
| Frontend | Next.js (App Router), TypeScript | [`apps/web`](apps/web) |

## How it works

1. The web app uploads an image to `POST /extract?doc_type=receipt|id`.
2. The API sends the image to Gemini with a Pydantic-derived JSON schema (structured output).
3. The model also reports a 0-1 confidence for every field. The response is validated with Pydantic and returned as `{doc_type, data, confidence, model}`.
4. The UI shows a confidence badge per field and highlights anything under 70% for review.

Confidence is self-reported by the model, not a calibrated probability. `eval.run_eval` prints how well it tracks correctness (mean confidence when right vs wrong, and accuracy at confidence of 0.8 or higher).

## Quick start

```bash
cp .env.example .env          # add your GEMINI_API_KEY

# API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload  # http://localhost:8000/docs

# Web (new terminal)
cd apps/web
npm install
npm run dev                    # http://localhost:3000
```

Or run both with `docker compose up --build`.

## Tests

```bash
cd apps/api && pytest && ruff check .
cd apps/web && npm run lint && npm run build
```

## Evaluation

`apps/api/eval` holds a labelled test set (18 receipts, 4 IDs) and a scorer. Every third receipt is rotated and blurred to be harder. The data is synthetic: fictional merchants and people, and IDs marked SPECIMEN. It is generated deterministically by `eval/generate_dataset.py`, which writes the images and ground-truth JSON.

```bash
cd apps/api
python -m eval.run_eval --out eval/results/latest.json   # needs GEMINI_API_KEY
```

It reports per-field accuracy, exact-document match rate, line-item F1 and average latency per document type. Numbers match within 0.01 and strings match case-insensitively. Failed requests count as wrong rather than aborting the run. The scoring logic and dataset integrity are covered by unit tests that run in CI without an API key.

## Deployment

- **Web**: Vercel, root directory `apps/web`, env `NEXT_PUBLIC_API_URL`.
- **API**: Render via the [`render.yaml`](render.yaml) blueprint (New > Blueprint, pick this repo), then set `GEMINI_API_KEY` and `CORS_ORIGINS` in the dashboard. Hugging Face Spaces (Docker) also works.

## Roadmap

- [ ] Batch upload and CSV export

## License

MIT
