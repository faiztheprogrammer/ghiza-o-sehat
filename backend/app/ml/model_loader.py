"""
Model loader module for Ghiza-o-Sehat.

Beginner Explanation:
- Neural network weights are large and take time/CPU memory to load.
- Loading the model once at startup and keeping it in memory allows
  requests to run predictions in milliseconds without reloading the file every time.
- The model is put in 'eval()' mode to freeze dropout and batch normalization layers.
"""

import json
from pathlib import Path
from typing import Any
import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0

from app.core.config import settings


class FoodModel:
    """
    Singleton wrapper holding the PyTorch model and associated class metadata.
    """

    def __init__(self) -> None:
        self.device = torch.device("cpu")
        self.classes: list[str] = []
        self.metadata: dict[str, Any] = {}
        self.version: str = "v1"
        self.model: nn.Module | None = None
        self.is_ready: bool = False

    def load(
        self,
        weights_path: Path | None = None,
        classes_path: Path | None = None,
        metadata_path: Path | None = None,
    ) -> None:
        """
        Loads the class list, metadata, and PyTorch model state dictionary.
        """
        weights_file = weights_path or settings.weights_path
        classes_file = classes_path or settings.classes_path
        metadata_file = metadata_path or settings.metadata_path

        # 1. Validate file existence
        if not classes_file.exists():
            raise FileNotFoundError(f"Classes file not found at: {classes_file}")
        if not weights_file.exists():
            raise FileNotFoundError(f"Model weights file not found at: {weights_file}")

        # 2. Read class order from food_classes.json (single source of truth)
        with open(classes_file, "r", encoding="utf-8") as f:
            self.classes = json.load(f)

        if not isinstance(self.classes, list) or len(self.classes) == 0:
            raise ValueError("food_classes.json must contain a non-empty list of class names.")

        # 3. Read metadata if available
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
                self.version = self.metadata.get("model_version", "v1")
        else:
            self.metadata = {}
            self.version = "v1"

        # 4. Recreate torchvision EfficientNet-B0 without pre-trained weights
        model = efficientnet_b0(weights=None)

        # 5. Replace final classification linear layer to match the number of Pakistani food classes
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, len(self.classes))

        # 6. Load saved weights state dictionary
        state_dict = torch.load(
            weights_file,
            map_location=self.device,
            weights_only=True,
        )
        model.load_state_dict(state_dict)

        # 7. Move to CPU and set to evaluation mode
        model.to(self.device)
        model.eval()

        self.model = model
        self.is_ready = True


# Global singleton instance loaded once during application startup
food_model = FoodModel()
