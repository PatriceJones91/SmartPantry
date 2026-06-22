cat > README.md <<'EOF'
# Smart Pantry

## Smart Pantry 2.0 - React + FastAPI + Supabase Version

Smart Pantry is a pantry-aware recommendation and decision-support system designed to help users track pantry items, reduce food waste, and receive meal recommendations based on the ingredients they already have. This version of the project uses a React frontend, FastAPI backend, and Supabase database to make the system more responsive, organized, and easier to expand beyond the original Streamlit prototype.

The goal of Smart Pantry is not only to recommend meals, but to help users make better decisions about what to use first. The system prioritizes items that are close to expiring while still allowing recommendations from non-expiring pantry items. This supports the project’s research focus on pantry awareness, recommendation usefulness, and ingredient utilization.

## Project Purpose

Smart Pantry was created as a graduate capstone project for Full Sail University. The project explores whether a pantry management and meal recommendation system can improve how users understand their pantry inventory, use ingredients before they expire, and make meal decisions from available food items.

The system supports a 7–14 day user study where participants can create an account, add pantry items, complete pre-study and post-study surveys, receive meal recommendations, and record whether they made a recommended meal or used ingredients somewhere else.

## Core Features

### User Accounts

Participants can register and log in with their own username and password. Each participant only sees their own pantry items, surveys, recommendations, and history. The admin account can view study-level activity through the admin dashboard.

### Pantry Management

Users can add pantry items with item name, category, quantity, unit, container type, expiration date, barcode/UPC, brand, and notes. Pantry items are used to power dashboard charts, expiration alerts, and meal recommendations.

### Barcode and Item Lookup

Smart Pantry 2.0 includes barcode and item lookup support using the local barcode dataset. Users can enter a barcode/UPC or search for a common item to help autofill pantry item details.

### Dashboard

The dashboard provides a quick view of pantry status, including survey completion, pantry item count, total usable quantity, pantry category breakdown, expiration alerts, and suggested grocery items.

### Profile and Preferences

Participants can save household size, allergies, foods to avoid, dietary restrictions, preferred meal types, preferred cuisines, and whether they prefer quick meals. These preferences are used to make recommendations more personalized and realistic.

### Meal Recommendations

The recommendation system uses two recipe sources:

1. A core everyday recipe dataset for quick, practical, familiar meals.
2. A larger cleaned recipe dataset for expanded recipe coverage.

The system scores recommendations using pantry ingredient matches, expiration urgency, recipe simplicity, dataset source priority, missing ingredient penalties, and user profile preferences.

### Recommendation History

Participants can record what happened after receiving a recommendation. Actions include:

- Made Meal
- Used Elsewhere
- Saved for Later
- Did Not Use

The history page uses color-coded cards so users and the study admin can understand how recommendations were used.

### Surveys

The system includes pre-study and post-study survey pages. Survey responses are saved to Supabase and support the research evaluation of pantry awareness, recommendation usefulness, and ingredient utilization.

### Admin Dashboard

The admin dashboard provides study-level visibility, including participant accounts, survey completion, pantry activity, recommendation logs, and outcome metrics.

## Technology Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Recharts

### Backend

- FastAPI
- Python
- Supabase Python Client
- CSV-based recipe and barcode loading

### Database

- Supabase PostgreSQL

## Main Folders

```text
Smart_Pantry_2.0/
  backend/
    main.py
    routes/
    services/
    models/
    data/
  frontend/
    src/
      api/
      components/
      data/
      pages/
  database/
    schema.sql
  README.md
  .gitignore
