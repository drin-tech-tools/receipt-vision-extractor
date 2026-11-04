# receipt-vision-extractor

Monorepo for a multimodal document scanner. Upload a photo of a receipt or ID and a vision LLM (Gemini) returns **validated, structured JSON**.

| Part | Stack | Path |
|------|-------|------|
| Backend | Python, FastAPI, Pydantic, `google-genai` | [`apps/api`](apps/api) |
| Frontend | Next.js (App Router), TypeScript | [`apps/web`](apps/web) |

## How it works

1. The web app uploads an image to `POST /extract?doc_type=receipt|id`.
2. The API sends the image to Gemini with a Pydantic-derived JSON schema (structured output).
3. The response is validated with Pydantic and returned as JSON, then rendered in the UI.

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

## Deployment

- **Web**: Vercel, root directory `apps/web`, env `NEXT_PUBLIC_API_URL`.
- **API**: Hugging Face Spaces (Docker) or Render, env `GEMINI_API_KEY`, `CORS_ORIGINS`.

## Roadmap

- [ ] Confidence scores and field-level highlighting
- [ ] Batch upload and CSV export
- [ ] Evaluation set with accuracy tracking

## License

MIT
