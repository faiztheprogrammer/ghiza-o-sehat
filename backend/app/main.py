"""
Ghiza-o-Sehat FastAPI Inference Server.

Sprint Target:
1. GET /health    -> Confirms API and model status
2. GET /classes   -> Returns the 17 loaded food classes from food_classes.json
3. POST /predict  -> Accepts image file, returns top-3 predictions with confidence scores
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.ml.model_loader import food_model
from app.schemas.nutrition import CalorieEstimate, EstimateCaloriesRequest, NutritionUnavailable
from app.services.nutrition_service import estimate_calories
from app.schemas.prediction import (
    ClassesResponse,
    HealthResponse,
    PredictResponse,
)
from app.services.prediction_service import (
    open_and_verify_image,
    predict_food_image,
    validate_image_upload,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Loads the PyTorch EfficientNet-B0 model once at startup into memory.
    """
    print("=" * 60)
    print("Starting Ghiza-o-Sehat Inference Server...")
    print(f"Loading model from: {settings.model_dir}")
    try:
        food_model.load()
        print(f"Model loaded successfully! Version: {food_model.version}")
        print(f"Recognized classes ({len(food_model.classes)}): {food_model.classes}")
        print("=" * 60)
    except Exception as exc:
        print(f"CRITICAL: Failed to load model at startup: {exc}")
        raise exc

    yield

    print("Shutting down Ghiza-o-Sehat Inference Server...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "FastAPI backend for Ghiza-o-Sehat Pakistani food recognition. "
        "Uses EfficientNet-B0 transfer learning with human-in-the-loop confirmation."
    ),
    lifespan=lifespan,
)

# Enable CORS for local development and future Flutter mobile client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and model readiness check",
    tags=["System"],
)
async def get_health() -> HealthResponse:
    """
    Confirms whether the API is alive and the model is loaded into memory.
    """
    return HealthResponse(
        status="healthy" if food_model.is_ready else "initializing",
        model_ready=food_model.is_ready,
        model_version=food_model.version,
        classes_count=len(food_model.classes),
        device=str(food_model.device),
    )


@app.get(
    "/classes",
    response_model=ClassesResponse,
    summary="List supported food classes",
    tags=["ML Model"],
)
async def get_classes() -> ClassesResponse:
    """
    Returns the exact 17 Pakistani food classes loaded dynamically from food_classes.json.
    """
    return ClassesResponse(
        classes=food_model.classes,
        count=len(food_model.classes),
    )


@app.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict food class from uploaded meal photo",
    tags=["ML Model"],
)
async def predict_meal(
    file: UploadFile = File(..., description="Uploaded meal image (JPEG, PNG, or WebP)"),
) -> PredictResponse:
    """
    Accepts an uploaded image file and returns:
    - Top predicted Pakistani food class
    - Top-3 candidate predictions with model confidence scores
    - Active model version
    - needs_confirmation: true (always true to enforce human-in-the-loop confirmation)
    """
    # 1. Validate MIME type, non-empty, and file size
    file_bytes = await validate_image_upload(file)

    # 2. Decode and verify image integrity with Pillow
    image = open_and_verify_image(file_bytes)

    # 3. Preprocess and run inference
    result = predict_food_image(image)

    return result


@app.post(
    "/estimate-calories",
    response_model=CalorieEstimate | NutritionUnavailable,
    summary="Estimate calories for a confirmed food and user-supplied weight in grams",
    tags=["Nutrition"],
)
async def estimate_meal_calories(
    request: EstimateCaloriesRequest,
) -> CalorieEstimate | NutritionUnavailable:
    return estimate_calories(request)


@app.get("/", summary="Root API Info", tags=["System"])
async def root() -> JSONResponse:
    """Convenience endpoint providing API summary and Swagger link."""
    return JSONResponse({
        "project": "Ghiza-o-Sehat",
        "description": "Pakistani Diet & Wellness Assistant Backend",
        "docs": "/docs",
        "health": "/health",
        "classes": "/classes",
        "predict": "/predict",
    })
