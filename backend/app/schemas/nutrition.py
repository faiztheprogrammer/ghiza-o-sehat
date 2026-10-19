"""The nutrition request is separate from image prediction."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class EstimateCaloriesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed_food: str = Field(min_length=1, description="User-confirmed canonical dish name")
    food_confirmed: StrictBool = Field(description="Must explicitly be true")
    portion_grams: float = Field(
        gt=0, strict=True, allow_inf_nan=False,
        description="User-supplied cooked edible food weight in grams",
    )

    @field_validator("food_confirmed")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Confirm or correct the food before estimating calories.")
        return value


class CalorieEstimate(BaseModel):
    status: Literal["estimated"] = "estimated"
    confirmed_food: str
    portion_grams: float
    kcal_per_100g: float
    calories: float
    source_name: str
    source_reference: str
    notes: list[str]


class NutritionUnavailable(BaseModel):
    status: Literal["unavailable"] = "unavailable"
    confirmed_food: str
    reason: str

