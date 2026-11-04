from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel

from .config import settings
from .schemas import DocType, extraction_model

PROMPTS = {
    DocType.receipt: (
        "Extract the data from this receipt. Use null for anything not visible. "
        "Do not guess values. Dates must be ISO 8601."
    ),
    DocType.id: (
        "Extract the fields from this identity document. Use null for anything not visible. "
        "Do not guess values. Dates must be ISO 8601."
    ),
}


CONFIDENCE_GUIDE = (
    " For every field also give a confidence between 0 and 1: 1.0 means clearly legible and"
    " unambiguous, below 0.5 means blurry, partly hidden or guessed. A field that is truly"
    " absent from the document should be null with high confidence. For `items`, give one"
    " overall confidence and also set `confidence` on each line item."
)


@dataclass
class ExtractionResult:
    data: BaseModel
    confidence: dict[str, float]


class Extractor(Protocol):
    model: str

    def extract(self, image: bytes, mime_type: str, doc_type: DocType) -> ExtractionResult: ...


class GeminiExtractor:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def extract(self, image: bytes, mime_type: str, doc_type: DocType) -> ExtractionResult:
        schema = extraction_model(doc_type)
        response = self._client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image, mime_type=mime_type),
                PROMPTS[doc_type] + CONFIDENCE_GUIDE,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )
        parsed = schema.model_validate_json(response.text)
        return ExtractionResult(data=parsed.data, confidence=parsed.confidence.model_dump())


def get_extractor() -> Extractor:
    return GeminiExtractor(settings.gemini_api_key, settings.gemini_model)
