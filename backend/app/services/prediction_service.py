"""
Prediction service handling image validation, preprocessing, and inference.

Beginner Explanation:
1. When a user uploads a file, we check:
   - Is it an allowed image format (JPEG, PNG, WebP)?
   - Is it too large (over 10MB) or empty (0 bytes)?
   - Can Pillow read the image without corruption?
2. If valid, we pass the image to our PyTorch model.
3. We calculate softmax scores (probabilities that sum to 100%).
4. We pick the top 3 highest scoring foods and return them.
"""

import io
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
import torch

from app.core.config import settings
from app.ml.model_loader import food_model
from app.ml.transforms import preprocess_image
from app.schemas.prediction import ClassPrediction, PredictResponse


async def validate_image_upload(file: UploadFile) -> bytes:
    """
    Validates uploaded file MIME type and size, then returns the file bytes.
    Raises HTTPException (400 or 413) if invalid.
    """
    # 1. Check Content-Type header
    content_type = (file.content_type or "").lower()
    if content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: '{file.content_type}'. "
                f"Allowed types are: {', '.join(sorted(settings.ALLOWED_CONTENT_TYPES))}."
            ),
        )

    # 2. Read file contents into memory
    file_bytes = await file.read()

    # 3. Check for empty file
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    # 4. Check file size against maximum limit
    if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
        max_mb = settings.MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
        status_code = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        raise HTTPException(
            status_code=status_code,
            detail=f"File exceeds maximum allowed size of {max_mb} MB.",
        )

    return file_bytes


def open_and_verify_image(file_bytes: bytes) -> Image.Image:
    """
    Attempts to parse the image using PIL and verifies it is not corrupted.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # Verifies file integrity
        # Re-open after verify() because verify() can close or corrupt the file pointer
        image = Image.open(io.BytesIO(file_bytes))
        return image
    except (UnidentifiedImageError, OSError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted image file: {str(err)}",
        ) from err


def predict_food_image(image: Image.Image) -> PredictResponse:
    """
    Runs model inference on the validated PIL image and returns top 3 predictions.
    """
    if not food_model.is_ready or food_model.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready. Application is initializing.",
        )

    # 1. Preprocess the image into a [1, 3, 224, 224] tensor
    input_tensor = preprocess_image(image)

    # 2. Run inference in evaluation mode without tracking gradients
    with torch.no_grad():
        logits = food_model.model(input_tensor)
        # Softmax converts raw logits into confidence scores that sum to 1.0
        probabilities = torch.softmax(logits, dim=1)[0]

    # 3. Get top 3 predictions
    k = min(3, len(food_model.classes))
    top_scores, top_indices = torch.topk(probabilities, k=k)

    top3_predictions: list[ClassPrediction] = []
    for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
        class_name = food_model.classes[idx]
        confidence_percent = round(score * 100.0, 2)
        top3_predictions.append(
            ClassPrediction(food_class=class_name, confidence=confidence_percent)
        )

    primary = top3_predictions[0]

    return PredictResponse(
        prediction=primary.food_class,
        confidence=primary.confidence,
        top3=top3_predictions,
        model_version=food_model.version,
        needs_confirmation=True,
    )
