# Smart Pantry 2.0

Smart Pantry is a pantry-aware meal recommendation and research platform built with React, FastAPI, and Supabase. It helps participants track food, notice expiration risk, receive practical meal recommendations, and record what happened after each recommendation.

The capstone research focus is whether pantry-aware recommendations improve pantry awareness, recommendation usefulness, and ingredient utilization.

## Core features

- Participant registration and login
- User-specific pantry inventory
- Barcode and item lookup
- Profile preferences, allergies, and foods to avoid
- Explainable meal recommendations
- Smart Score, Pantry Match, Nutrition Fit, expiration priority, and Smart Swaps
- Complete and near-complete meal classification
- Meal and cuisine filters with Top 10 plus Show More
- Adaptive learning from Save, Made, and Skip actions
- Recipe-fatigue and diversity controls
- Recommendation history and feedback
- Pre-study and post-study surveys
- Admin study metrics and exports

## Recommendation engine

The engine evaluates the realistic candidate pool, applies safety filters, validates pantry evidence, scores pantry usefulness and nutrition, applies gentle preference and behavior adjustments, controls recipe-family repetition, and returns participant-facing explanations. See `docs/RECOMMENDATION_ENGINE_ARCHITECTURE.md`.

## Technology

- **Frontend:** React, Vite, JavaScript, CSS, Recharts
- **Backend:** FastAPI, Python, Pydantic, Supabase client
- **Database:** Supabase PostgreSQL
- **Data:** cleaned recipe and barcode CSV files
- **ML support:** Random Forest Nutrition Fit model

## Project structure

```text
Smart_Pantry_2.0/
  backend/
    main.py
    config.py
    routes/
    services/
    models/
    tests/
    data/
    ml/
  frontend/
    src/
      api/
      components/
      pages/
  database/
  docs/
  scripts/
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Activate the environment for your operating system.
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Enter working Supabase values in `backend/.env` before using participant data routes.

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

The default frontend expects the API at `http://127.0.0.1:8000/api`.

## Validation

From the project root:

```bash
./scripts/validate_release.sh
```

This compiles the Python code, runs the backend test suite, and creates the React production build.

## Release documentation

- `PHASE_18_NOTES.md`
- `docs/PHASE_18_VALIDATION_PLAN.md`
- `docs/DEPLOYMENT_CHECKLIST.md`
- `docs/DEMO_CHECKLIST.md`
- `docs/RECOMMENDATION_ENGINE_ARCHITECTURE.md`

No Phase 18 database migration is required.
