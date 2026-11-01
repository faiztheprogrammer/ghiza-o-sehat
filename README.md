# Ghiza-o-Sehat (غذائیں اور صحت)

**Intelligent Pakistani Diet & Wellness Assistant**

Ghiza-o-Sehat is an FYP project designed to assist users in tracking traditional Pakistani meals with intelligent visual recognition, deterministic nutrition estimation, and grounded conversational wellness guidance.

---

## 1. Project Decisions & Status

The project follows the canonical roadmap documented in [`GhizaOSehat_Master_Handoff.md`](./GhizaOSehat_Master_Handoff.md):
- **Model V1 Frozen for MVP**: EfficientNet-B0 trained on 17 Pakistani food classes.
- **Human-in-the-Loop**: Image prediction -> user confirms/corrects dish -> user supplies weight in grams -> deterministic nutrition calculation.
- **Day 1 Milestone**: Local FastAPI inference backend (`/health`, `/classes`, `/predict`).
- **Nutrition milestone (2026-10-18)**: `POST /estimate-calories` accepts `confirmed_food`, `food_confirmed: true`, and positive numeric `portion_grams`. Only chapati is supported: 259 kcal/100 g, so 50 g returns one estimate of 129.5 kcal. No predefined serving sizes or calorie ranges. See the backend README for the preserved source, limitations and usage.

---

## 2. Quickstart (Backend)

Refer to [`backend/README.md`](./backend/README.md) for detailed instructions.

### Windows / PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Run Test Suite:

```powershell
pytest -v
```

Verification (2026-10-18): **39 passed, 2 existing deprecation warnings in 9.07 seconds** (9 inference tests and 30 nutrition cases). Full suite command from `backend`: `.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -v`.

## 3. Flutter interface

The Android Flutter project is in [`frontend/`](frontend/README.md). It provides
photo selection, prediction/top-three display, explicit food confirmation,
user-entered grams, and the backend calorie estimate or unavailable message.
The backend and Model V1 are unchanged.

See the frontend README for backend startup, emulator/phone networking, Flutter
commands, prerequisites and smoke tests. No Android device/emulator was available
during implementation; Android licenses also require user acceptance.
