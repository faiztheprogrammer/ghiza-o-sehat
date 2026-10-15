# Ghiza-o-Sehat (غذائیں اور صحت)

**Intelligent Pakistani Diet & Wellness Assistant**

Ghiza-o-Sehat is an FYP project designed to assist users in tracking traditional Pakistani meals with intelligent visual recognition, deterministic nutrition estimation, and grounded conversational wellness guidance.

---

## 1. Project Decisions & Status

The project follows the canonical roadmap documented in [`GhizaOSehat_Master_Handoff.md`](./GhizaOSehat_Master_Handoff.md):
- **Model V1 Frozen for MVP**: EfficientNet-B0 trained on 17 Pakistani food classes.
- **Human-in-the-Loop**: Image prediction -> user confirms/corrects dish -> user specifies portion -> deterministic nutrition calculation.
- **Day 1 Milestone**: Local FastAPI inference backend (`/health`, `/classes`, `/predict`).

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
pytest -v tests/test_api.py
```
