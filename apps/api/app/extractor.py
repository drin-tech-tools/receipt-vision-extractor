from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel

from .config import settings
from .schemas import SCHEMAS, DocType

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


class Extractor(Protocol):
    model: str

    def extract(self, image: bytes, mime_type: str, doc_type: DocType) -> BaseModel: ...


class GeminiExtractor:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def extract(self, image: bytes, mime_type: str, doc_type: DocType) -> BaseModel:
        schema = SCHEMAS[doc_type]
        response = self._client.models.generate_content(
            model=self.model,
            contents=[types.Part.from_bytes(data=image, mime_type=mime_type), PROMPTS[doc_type]],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )
        return schema.model_validate_json(response.text)


def get_extractor() -> Extractor:
    return GeminiExtractor(settings.gemini_api_key, settings.gemini_model)
