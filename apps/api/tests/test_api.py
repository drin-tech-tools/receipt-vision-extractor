from fastapi.testclient import TestClient

from app.extractor import ExtractionResult, get_extractor
from app.main import app
from app.schemas import Receipt

client = TestClient(app)


class FakeExtractor:
    model = "fake"

    def extract(self, image, mime_type, doc_type):
        return ExtractionResult(
            data=Receipt(merchant_name="Cafe Test", total=12.5, currency="USD"),
            confidence={"merchant_name": 0.97, "total": 0.88},
        )


def setup_function():
    app.dependency_overrides[get_extractor] = lambda: FakeExtractor()


def teardown_function():
    app.dependency_overrides.clear()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_extract_receipt():
    r = client.post("/extract", files={"file": ("a.png", b"123", "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["merchant_name"] == "Cafe Test"
    assert body["model"] == "fake"
    assert body["confidence"] == {"merchant_name": 0.97, "total": 0.88}


def test_rejects_non_image():
    r = client.post("/extract", files={"file": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 415


def test_rejects_bad_doc_type():
    r = client.post("/extract?doc_type=nope", files={"file": ("a.png", b"1", "image/png")})
    assert r.status_code == 422


def test_extraction_model_has_confidence_for_every_field():
    from app.schemas import DocType, extraction_model

    for dt in DocType:
        m = extraction_model(dt)
        data_fields = set(m.model_fields["data"].annotation.model_fields)
        conf_fields = set(m.model_fields["confidence"].annotation.model_fields)
        assert data_fields == conf_fields
