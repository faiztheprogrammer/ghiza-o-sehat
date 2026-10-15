# Ghiza-o-Sehat — Local FastAPI Inference Backend (Day 1)

This is the Day 1 local inference service for **Ghiza-o-Sehat** (غذائیں اور صحت), an intelligent Pakistani diet and wellness assistant.

It serves an EfficientNet-B0 image classifier fine-tuned on 17 Pakistani food classes, enforcing a **human-in-the-loop** architecture where model predictions require user confirmation before portion and calorie estimation.

---

## 1. Prerequisites

- **Windows 10 / 11**
- **Python 3.11** (64-bit)
- PowerShell

---

## 2. Setup Instructions (Windows / PowerShell)

Open PowerShell and navigate to the `backend` directory:

```powershell
cd C:\Users\hp\OneDrive\Desktop\ghiza-o-sehat\backend
```

### Step 2.1: Create Virtual Environment (Python 3.11)

```powershell
py -3.11 -m venv .venv
```

### Step 2.2: Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

*(Note: If script execution is disabled on your system, enable it for your user session with: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

### Step 2.3: Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 3. Running the Server

Start the local FastAPI development server:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once started:
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 4. Running Automated Tests

Run the full pytest suite with verbose output:

```powershell
pytest -v tests/test_api.py
```

All 9 test cases will run against the API, verifying:
- `/health` readiness
- `/classes` dynamic loading
- `/predict` with JPEG and PNG
- Image validation (disallowed MIME types, 0-byte files, corrupted files, and size limits)

---

## 5. Testing Endpoints Manually via PowerShell

### 5.1 Test Health Endpoint

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get | ConvertTo-Json
```

**Expected Response**:
```json
{
  "status": "healthy",
  "model_ready": true,
  "model_version": "v1",
  "classes_count": 17,
  "device": "cpu"
}
```

### 5.2 Test Classes Endpoint

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/classes" -Method Get | ConvertTo-Json
```

**Expected Response**:
```json
{
  "classes": [
    "aloo_gobi",
    "aloo_matar",
    "bhindi_masala",
    "biryani",
    "chana_masala",
    "chapati",
    "chicken_tikka",
    "creamy_chicken_curry",
    "dal_makhani",
    "dal_tadka",
    "gajar_ka_halwa",
    "gulab_jamun",
    "jalebi",
    "kofta",
    "naan",
    "ras_malai",
    "sheer_korma"
  ],
  "count": 17
}
```

### 5.3 Test Prediction Endpoint (`POST /predict`)

Using `curl.exe` in PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/predict" -F "file=@path\to\your_food_image.jpg"
```

**Example Response**:
```json
{
  "prediction": "biryani",
  "confidence": 74.35,
  "top3": [
    { "class": "biryani", "confidence": 74.35 },
    { "class": "creamy_chicken_curry", "confidence": 4.94 },
    { "class": "dal_makhani", "confidence": 4.14 }
  ],
  "model_version": "v1",
  "needs_confirmation": true
}
```

---

## 6. Architecture & Implementation Notes

- **Model Loading**: The model is instantiated and loaded into memory **once** at application startup via FastAPI's `lifespan` handler. It is not reloaded per request.
- **Model Architecture**: Recreates `torchvision.models.efficientnet_b0(weights=None)` and replaces `model.classifier[1]` with `nn.Linear(in_features, 17)`.
- **Inference Mode**: Set to `model.eval()` and wrapped in `torch.no_grad()` to ensure zero gradient overhead during evaluation.
- **Preprocessing Pipeline**: Input images are converted to RGB, resized to `(224, 224)`, converted to tensors `(0.0-1.0)`, and normalized with ImageNet stats (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).
- **Single Source of Truth**: The classes list is read dynamically from `food_classes.json`. No secondary class list is hardcoded in Python.
- **Human-in-the-Loop**: `needs_confirmation: true` is always returned. Softmax scores are heuristic model scores, not calibrated nutritional certainties.
