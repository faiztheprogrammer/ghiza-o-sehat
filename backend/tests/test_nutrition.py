"""Nutrition endpoint contracts, calculation and confirmation safeguards."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # Nutrition does not need model startup; test_api covers the real lifespan.
    return TestClient(app)


def payload(**changes):
    return {
        "confirmed_food": "chapati",
        "food_confirmed": True,
        "portion_grams": 50,
        **changes,
    }


@pytest.mark.parametrize("grams, expected_calories", [(50, 129.5), (75.5, 195.545)])
def test_chapati_estimate(client, grams, expected_calories):
    response = client.post("/estimate-calories", json=payload(portion_grams=grams))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "estimated"
    assert data["confirmed_food"] == "chapati"
    assert data["portion_grams"] == grams
    assert data["kcal_per_100g"] == 259
    assert data["calories"] == pytest.approx(expected_calories)
    assert "calories_min" not in data
    assert "calories_max" not in data
    assert "row 19" in data["source_reference"]
    assert "fao.org" in data["source_reference"]
    assert any("estimate" in note for note in data["notes"])
    assert any("282" in note for note in data["notes"])


@pytest.mark.parametrize("confirmation", [False, "true", 1, None])
def test_explicit_boolean_confirmation_required(client, confirmation):
    response = client.post("/estimate-calories", json=payload(food_confirmed=confirmation))
    assert response.status_code == 422
    assert "calories" not in response.json()


@pytest.mark.parametrize("field", ["food_confirmed", "confirmed_food", "portion_grams"])
def test_required_fields(client, field):
    request = payload()
    del request[field]
    assert client.post("/estimate-calories", json=request).status_code == 422


@pytest.mark.parametrize("grams", [0, -1, "invalid", "50", "", None, True, False, [], {}, "NaN", "Infinity"])
def test_invalid_weight(client, grams):
    assert client.post("/estimate-calories", json=payload(portion_grams=grams)).status_code == 422


@pytest.mark.parametrize("food", ["biryani", "unknown_food", "butter_chicken", "chicken_tikka_masala"])
def test_unsupported_food_has_no_calories(client, food):
    response = client.post("/estimate-calories", json=payload(confirmed_food=food))
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert response.json()["confirmed_food"] == food
    assert "calories" not in response.json()
    assert "kcal_per_100g" not in response.json()


def test_creamy_curry_requires_supported_specific_dish(client):
    response = client.post("/estimate-calories", json=payload(confirmed_food="creamy_chicken_curry"))
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert "specific dish" in response.json()["reason"]
    assert "calories" not in response.json()


@pytest.mark.parametrize("extra", [{"confidence": 99}, {"grams": 50}, {"image": "photo.jpg"}, {"portion": "cooked_40_60g"}])
def test_extra_inputs_cannot_override_estimate(client, extra):
    assert client.post("/estimate-calories", json=payload(**extra)).status_code == 422
