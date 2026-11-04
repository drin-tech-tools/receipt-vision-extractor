from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .config import settings
from .extractor import Extractor, get_extractor
from .schemas import DocType, ExtractResponse

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Receipt Vision Extractor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractResponse)
async def extract(
    doc_type: DocType = DocType.receipt,
    file: UploadFile = File(...),
    extractor: Extractor = Depends(get_extractor),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"Unsupported file type. Use one of: {sorted(ALLOWED_TYPES)}")
    image = await file.read()
    if len(image) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")
    try:
        result = extractor.extract(image, file.content_type, doc_type)
    except ValidationError as e:
        raise HTTPException(502, f"Model returned invalid data: {e.error_count()} errors") from e
    except Exception as e:
        raise HTTPException(502, "Vision model request failed") from e
    return ExtractResponse(
        doc_type=doc_type,
        data=result.data,
        confidence=result.confidence,
        model=extractor.model,
    )
