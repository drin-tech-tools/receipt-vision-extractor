import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field, create_model


class DocType(StrEnum):
    receipt = "receipt"
    id = "id"


class LineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float | None = None
    total: float | None = None
    confidence: float | None = Field(
        default=None, ge=0, le=1, description="Confidence 0-1 that this line item is correct"
    )


class Receipt(BaseModel):
    merchant_name: str | None = None
    merchant_address: str | None = None
    date: dt.date | None = Field(default=None, description="Purchase date, ISO 8601")
    currency: str | None = Field(default=None, description="ISO 4217 code, e.g. USD")
    items: list[LineItem] = []
    subtotal: float | None = None
    tax: float | None = None
    tip: float | None = None
    total: float | None = None
    payment_method: str | None = None


class IDDocument(BaseModel):
    document_type: str | None = Field(default=None, description="e.g. driver license, passport")
    full_name: str | None = None
    document_number: str | None = None
    date_of_birth: dt.date | None = None
    expiry_date: dt.date | None = None
    nationality: str | None = None
    address: str | None = None


SCHEMAS: dict[DocType, type[BaseModel]] = {
    DocType.receipt: Receipt,
    DocType.id: IDDocument,
}


def _confidence_model(model: type[BaseModel]) -> type[BaseModel]:
    """One 0-1 float per field of `model`. For `items`, a single score for the whole list."""
    fields = {
        name: (
            float,
            Field(
                ge=0,
                le=1,
                description=f"Confidence 0-1 that `{name}` was read correctly (or is truly absent)",
            ),
        )
        for name in model.model_fields
    }
    return create_model(f"{model.__name__}Confidence", **fields)


def extraction_model(doc_type: DocType) -> type[BaseModel]:
    """Schema sent to the LLM: the extracted data plus per-field confidence."""
    data_model = SCHEMAS[doc_type]
    return create_model(
        f"{data_model.__name__}Extraction",
        data=(data_model, ...),
        confidence=(_confidence_model(data_model), ...),
    )


class ExtractResponse(BaseModel):
    doc_type: DocType
    data: Receipt | IDDocument
    confidence: dict[str, float] = Field(
        description="Model-reported confidence per top-level field, 0-1"
    )
    model: str
