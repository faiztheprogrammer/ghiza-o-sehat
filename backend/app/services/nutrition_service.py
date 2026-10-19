"""Deterministic lookup and portion calculation; no image or model dependency."""

import json
from pathlib import Path

from app.schemas.nutrition import (
    CalorieEstimate,
    EstimateCaloriesRequest,
    NutritionUnavailable,
)


with (Path(__file__).resolve().parents[1] / "data" / "nutrition_seed.json").open(
    encoding="utf-8"
) as seed_file:
    NUTRITION_DATA = json.load(seed_file)


def estimate_calories(
    request: EstimateCaloriesRequest,
) -> CalorieEstimate | NutritionUnavailable:
    food = request.confirmed_food
    if food == "creamy_chicken_curry":
        return NutritionUnavailable(
            confirmed_food=food,
            reason=(
                "This is a visual class, not a specific dish. Confirm a specific dish "
                "such as butter_chicken or chicken_tikka_masala; it must also have "
                "supported nutrition data. Neither is currently supported."
            ),
        )

    record = NUTRITION_DATA.get(food)
    if record is None:
        return NutritionUnavailable(
            confirmed_food=food,
            reason="No supported nutrition data for this food. Currently only chapati is supported.",
        )

    # Energy per 100 g scaled by the weight supplied by the user.
    calories = record["kcal_per_100g"] * request.portion_grams / 100
    return CalorieEstimate(
        confirmed_food=food,
        portion_grams=request.portion_grams,
        kcal_per_100g=record["kcal_per_100g"],
        calories=calories,
        source_name=record["source_name"],
        source_reference=record["source_reference"],
        notes=record["notes"],
    )