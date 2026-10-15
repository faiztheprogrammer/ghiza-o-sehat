from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Status response for GET /health."""
    status: str = Field(..., examples=["healthy"])
    model_ready: bool = Field(..., examples=[True])
    model_version: str = Field(..., examples=["v1"])
    classes_count: int = Field(..., examples=[17])
    device: str = Field(..., examples=["cpu"])


class ClassesResponse(BaseModel):
    """Response containing the list of recognizable food classes."""
    classes: list[str] = Field(..., description="Ordered list of food class labels")
    count: int = Field(..., description="Total number of classes")


class ClassPrediction(BaseModel):
    """A single candidate prediction and its model confidence score."""
    model_config = ConfigDict(populate_by_name=True)

    food_class: str = Field(..., alias="class", description="Name of the predicted food class")
    confidence: float = Field(..., description="Softmax confidence score percentage (0-100)")


class PredictResponse(BaseModel):
    """
    Response schema for POST /predict.
    Notice: needs_confirmation is always True because visual model confidence
    is not nutritional truth, and user confirmation is required.
    """
    model_config = ConfigDict(populate_by_name=True)

    prediction: str = Field(..., description="Top predicted food class")
    confidence: float = Field(..., description="Top predicted confidence score percentage (0-100)")
    top3: list[ClassPrediction] = Field(..., description="Top 3 predictions with confidence scores")
    model_version: str = Field(..., description="Active model version tag")
    needs_confirmation: bool = Field(default=True, description="Always true: human confirmation required")

