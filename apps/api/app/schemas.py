import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field


class DocType(StrEnum):
    receipt = "receipt"
    id = "id"


class LineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float | None = None
    total: float | None = None


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


class ExtractResponse(BaseModel):
    doc_type: DocType
    data: Receipt | IDDocument
    model: str
