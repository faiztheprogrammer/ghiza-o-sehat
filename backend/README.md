# Ghiza-o-Sehat — Local FastAPI Inference and Nutrition Backend

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
pytest -v
```

The original 9 inference test cases verify:
- `/health` readiness
- `/classes` dynamic loading
- `/predict` with JPEG and PNG
- Image validation (disallowed MIME types, 0-byte files, corrupted files, and size limits)

The nutrition cases cover calculations for integer and fractional gram weights, explicit boolean confirmation, missing fields, invalid weights, unsupported foods, creamy-curry disambiguation, and rejection of extra inputs and obsolete portion IDs.

Verification (2026-10-18): **39 passed, 2 existing deprecation warnings in 9.07 seconds** (9 inference tests and 30 nutrition cases). Full suite command from `backend`: `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -v`.

The complete backend suite is run with the existing Python 3.11.9 environment:

```powershell
# From backend; uses the existing environment without installing anything.
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -v
```

The two pre-existing warnings concern Starlette's httpx TestClient integration and the old HTTP 413 constant used by image upload validation. They do not fail the tests. Inference tests load the real model but use synthetic images, so this is not a food-recognition accuracy evaluation.

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

## 7. Chapati nutrition and portion endpoint

`POST /estimate-calories` is independent of image prediction. It accepts a confirmed canonical dish name and a positive numeric `portion_grams` supplied by the user, then uses local curated data. There is no image, model-confidence or Gemini input to the calculation.

### Source and record selection

Source: [Food Composition Table for Pakistan, hosted by FAO](https://www.fao.org/fileadmin/templates/food_composition/documents/regional/Book_Food_Composition_Table_for_Pakistan_.pdf#page=15), visually inspected on 2026-10-18.

- Selected record: printed page **8**, PDF page **15**, **Composition of Food**, section **A) Cereal and cereal products**, row **19**, English name **Wheat Bread**, Urdu-column name **Chapati**. Published energy: **259 kcal per 100 g edible portion**.
- This directly identifies prepared wheat chapati rather than dry flour, naan or paratha, and maps to the user's confirmed `chapati` dish.
- Another entry, **Traditional Foods**, item **1. Chapati**, printed page **48**, PDF page **54**, reports **282 kcal/100 g** and refers to Appendix 1 (printed page 54, PDF page 60). It is a separate record. We select the cereal-table entry as the reference for this MVP; we do not average the two values or turn their difference into a nutritional range. The selected value is not claimed to describe every recipe.
- `kcal_per_100g` is **259**. The JSON record stores this single value, English/Urdu names, aliases, source and notes; it contains no predefined portions or weight bounds. Requests use the canonical `chapati` identifier; aliases are descriptive metadata, not automatic substitutions.

### Weight and limitations

The user supplies the cooked edible weight in grams. There are no predefined serving sizes, standard chapati weights or piece-count conversions. The API requires a positive finite JSON number (integer or fractional); numeric strings and booleans are rejected. It trusts the supplied weight and confirmation and cannot independently verify either.

Use only for plain wheat chapati. Added ghee, oil, butter, fillings and accompaniments are not covered. The result is an estimate: recipes and measurement accuracy vary. No image, confidence score or LLM supplies weights or calorie values.

```text
calories = kcal_per_100g * portion_grams / 100
50 g:   259 * 50 / 100 = 129.5 kcal
75.5 g: 259 * 75.5 / 100 = 195.545 kcal
```

The API returns the calculation without explicit decimal rounding or artificial minimum/maximum bounds. Numerical precision does not imply nutritional certainty.

### Usage

With the backend running, execute in PowerShell:

```powershell
$nutritionRequest = @{
    confirmed_food = "chapati"
    food_confirmed = $true
    portion_grams = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/estimate-calories" `
    -Method Post -ContentType "application/json" -Body $nutritionRequest |
    ConvertTo-Json -Depth 5
```

Success returns HTTP 200 with `status: "estimated"`, `confirmed_food: "chapati"`, `portion_grams: 50`, `kcal_per_100g: 259`, `calories: 129.5`, and `source_name`, `source_reference`, and explanatory `notes` explicitly labelling the result as an estimate.

| Request condition | Result |
|---|---|
| Confirmed chapati with positive numeric `portion_grams` | HTTP 200, one calculated estimate with source and notes |
| Missing confirmation, `false`, string `"true"`, numeric `1`, or null | HTTP 422; confirmation must be the JSON boolean `true` |
| Missing food/weight, zero, negative or invalid weight | HTTP 422 |
| Unsupported food, e.g. `biryani` | HTTP 200, `status: "unavailable"`, confirmed food and reason; no calorie fields |
| `creamy_chicken_curry` | HTTP 200, unavailable; requires a specific supported dish |
| `butter_chicken` or `chicken_tikka_masala` | Still unavailable: no sourced nutrition records exist for these dishes |
| Extra fields such as image, confidence, `grams` or old `portion` | HTTP 422 |

Food, explicit confirmation and a valid weight are required even for unsupported foods. Replace the old `portion` field with `portion_grams`; legacy portion IDs are no longer accepted.

Implementation: `app/schemas/nutrition.py` defines request/response shapes; `app/services/nutrition_service.py` loads `app/data/nutrition_seed.json` once on import and performs the lookup/calculation; `app/main.py` exposes the route. Model artifacts, preprocessing and prediction logic are unchanged.
