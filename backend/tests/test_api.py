"""
Acceptance test suite for Ghiza-o-Sehat FastAPI Inference Backend.
"""

import io
import json
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Session-scoped TestClient that triggers FastAPI lifespan (model load)."""
    with TestClient(app) as test_client:
        yield test_client


def create_test_image(format: str = "JPEG", size: tuple[int, int] = (250, 250), color: str = "orange") -> bytes:
    """Creates a valid synthetic image in memory for testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Health Endpoint Tests
# ---------------------------------------------------------------------------

def test_health_endpoint(client: TestClient):
    """Test GET /health returns 200 and confirms model readiness."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_ready"] is True
    assert data["model_version"] == "v1"
    assert data["classes_count"] == 17
    assert data["device"] == "cpu"


# ---------------------------------------------------------------------------
# 2. Classes Endpoint Tests
# ---------------------------------------------------------------------------

def test_classes_endpoint(client: TestClient):
    """Test GET /classes returns all 17 classes matching food_classes.json."""
    response = client.get("/classes")
    assert response.status_code == 200

    data = response.json()
    assert "classes" in data
    assert data["count"] == 17
    assert len(data["classes"]) == 17

    # Verify against actual disk file
    classes_file = settings.classes_path
    with open(classes_file, "r", encoding="utf-8") as f:
        expected_classes = json.load(f)

    assert data["classes"] == expected_classes
    assert "biryani" in data["classes"]
    assert "creamy_chicken_curry" in data["classes"]


# ---------------------------------------------------------------------------
# 3. Predict Endpoint Tests
# ---------------------------------------------------------------------------

def test_predict_valid_jpeg(client: TestClient):
    """Test POST /predict with a valid JPEG image."""
    img_bytes = create_test_image(format="JPEG", color="gold")
    response = client.post(
        "/predict",
        files={"file": ("test_biryani.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200

    data = response.json()
    # Check required fields
    assert "prediction" in data
    assert "confidence" in data
    assert "top3" in data
    assert "model_version" in data
    assert "needs_confirmation" in data

    # Verify top3 schema
    assert len(data["top3"]) == 3
    assert data["needs_confirmation"] is True
    assert data["model_version"] == "v1"

    # Verify top prediction matches first element of top3
    assert data["prediction"] == data["top3"][0]["class"]
    assert data["confidence"] == data["top3"][0]["confidence"]

    # Check confidences are valid numbers between 0 and 100
    for item in data["top3"]:
        assert 0.0 <= item["confidence"] <= 100.0


def test_predict_valid_png(client: TestClient):
    """Test POST /predict with a valid PNG image."""
    img_bytes = create_test_image(format="PNG", color="green")
    response = client.post(
        "/predict",
        files={"file": ("test_bhindi.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["top3"]) == 3
    assert data["needs_confirmation"] is True


def test_predict_invalid_mime_type(client: TestClient):
    """Test POST /predict with a disallowed file type (e.g. text file)."""
    fake_txt = b"This is a text file, not a food image."
    response = client.post(
        "/predict",
        files={"file": ("notes.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_predict_empty_file(client: TestClient):
    """Test POST /predict with an empty 0-byte file."""
    response = client.post(
        "/predict",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_predict_corrupted_image(client: TestClient):
    """Test POST /predict with invalid image content disguised as JPEG."""
    corrupted_bytes = b"NOT_A_REAL_IMAGE_DATA_123456789"
    response = client.post(
        "/predict",
        files={"file": ("corrupted.jpg", corrupted_bytes, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


def test_predict_oversized_file(client: TestClient, monkeypatch):
    """Test POST /predict with a file exceeding MAX_IMAGE_SIZE_BYTES."""
    # Temporarily reduce limit for unit testing
    monkeypatch.setattr(settings, "MAX_IMAGE_SIZE_BYTES", 100)
    oversized_data = b"X" * 150
    response = client.post(
        "/predict",
        files={"file": ("large.jpg", oversized_data, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()


def test_root_endpoint(client: TestClient):
    """Test GET / returns project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Ghiza-o-Sehat"
    assert "/docs" in data["docs"]
