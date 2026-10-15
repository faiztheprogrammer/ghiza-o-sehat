"""
Image preprocessing transformations for EfficientNet-B0 inference.

Beginner Explanation:
A neural network cannot directly read image pixels (JPEG/PNG bytes).
We must convert an uploaded image into the exact format and scale that
the model saw during training:
1. Ensure the image is in RGB color mode (3 channels: Red, Green, Blue).
2. Resize the image to 224x224 pixels.
3. Convert pixel values (0-255) to a PyTorch tensor (floats between 0.0 and 1.0).
4. Normalize the pixel values using ImageNet mean and standard deviation.
"""

from PIL import Image
import torch
from torchvision import transforms

from app.core.config import settings


def get_eval_transform() -> transforms.Compose:
    """
    Returns the deterministic preprocessing pipeline for model evaluation.
    Matches the training validation transform from Step 18 / Colab notebook.
    """
    return transforms.Compose([
        transforms.Resize(settings.IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=settings.NORM_MEAN,
            std=settings.NORM_STD,
        ),
    ])


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Takes a PIL Image, ensures RGB mode, applies evaluation transforms,
    and adds a batch dimension (shape: [1, 3, 224, 224]).
    """
    # Convert RGBA, Grayscale, or CMYK to standard 3-channel RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    transform = get_eval_transform()
    tensor = transform(image)

    # Add batch dimension: [3, 224, 224] -> [1, 3, 224, 224]
    return tensor.unsqueeze(0)
