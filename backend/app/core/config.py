from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings.
    Beginner-friendly: Centralizes all paths and constants so they aren't scattered across files.
    """
    APP_NAME: str = "Ghiza-o-Sehat Inference API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = ""

    # Path to the backend root directory (e.g., .../ghiza-o-sehat/backend)
    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Look for model artifacts in 'model' first, fallback to 'models'
    MODEL_DIR_NAME: str = "model"

    # Image upload constraints
    MAX_IMAGE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB maximum
    ALLOWED_CONTENT_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/jpg",
    }

    # Model input specifications
    IMAGE_SIZE: tuple[int, int] = (224, 224)
    NORM_MEAN: list[float] = [0.485, 0.456, 0.406]
    NORM_STD: list[float] = [0.229, 0.224, 0.225]

    @property
    def model_dir(self) -> Path:
        """Resolves the active model directory."""
        primary = self.BACKEND_DIR / self.MODEL_DIR_NAME
        fallback = self.BACKEND_DIR / "models"
        if primary.exists():
            return primary
        if fallback.exists():
            return fallback
        return primary

    @property
    def weights_path(self) -> Path:
        return self.model_dir / "ghiza_efficientnet_b0_v1.pth"

    @property
    def classes_path(self) -> Path:
        return self.model_dir / "food_classes.json"

    @property
    def metadata_path(self) -> Path:
        return self.model_dir / "model_metadata.json"


settings = Settings()
