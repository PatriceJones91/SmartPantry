# Smart Pantry

Smart Pantry is a pantry-aware meal recommendation and study-tracking web application developed as a graduate capstone project for Full Sail University. The app helps users track pantry items, monitor expiration dates, review meal recommendations, and record pantry usage so the researcher can evaluate pantry awareness, recommendation usefulness, and ingredient utilization.

This project uses AI-assisted recommendation logic to prioritize recipes based on available pantry ingredients, near-expiring items, serving amounts, missing ingredients, and user preferences. The official project title is **Smart Pantry**.

## Project Purpose

Many households forget what food they already have, buy duplicate groceries, or let ingredients expire before they are used. Smart Pantry is designed to help users:

- See what is currently in their pantry.
- Track item quantities and expiration dates.
- Receive meal ideas based on what they already have.
- Prioritize meals that use ingredients before they expire.
- Save, use, dislike, or skip recommendations.
- Support a research study through pre-study and post-study survey responses.

## Current Features

### Participant Features

- Participant login and account separation
- Personal pantry inventory
- Add, edit, and remove pantry items
- Quantity tracking by usable amount
- Expiration alerts
- Pantry category breakdown chart
- Suggested grocery list
- Meal recommendation page
- Recommendation history
- Pre-study survey
- Post-study survey
- User profile preferences, including allergies, disliked ingredients, preferred meal types, and cuisine preferences

### Recommendation Features

- Ingredient matching based on pantry inventory
- Expiration-aware recipe prioritization
- Smart scoring for recommendation quality
- Missing ingredient display
- Suggested grocery items to unlock more meals
- Save for later option
- Made meal tracking
- Did not use / do not like feedback tracking
- Ingredient usage logging

### Admin / Researcher Features

- Admin dashboard
- Participant count
- Pantry item count
- Recommendation log review
- Ingredient usage review
- Survey results review
- Open-ended survey response review
- CSV export options for study data

## Research Focus

Smart Pantry supports a capstone research study focused on whether a pantry-aware recommendation system can improve:

1. Pantry awareness
2. Recommendation usefulness
3. Ingredient utilization

The system collects participant activity and survey responses to compare user experience and pantry behavior before and after using the app.

## Technology Stack

- Python
- Streamlit
- Supabase
- Pandas
- Plotly
- Scikit-learn
- Joblib
- GitHub

## Project Structure

```text
Smart_Pantry/
  main.py
  smartpantry_core.py
  database_supabase.py
  requirements.txt
  README.md

  app_pages/
    admin_page.py
    history_page.py
    home_page.py
    pantry_page.py
    profile_page.py
    recommendation_page.py
    survey_page.py

  assets/
    SmartPantry_logo.png

  data/
    smart_pantry_recipes_clean.csv
    barcode_lookup.csv

  engine/
    recipe_loader.py
    scoring_engine.py
    substitutions.py

  ml/
    recommendation_model.pkl

  services/
    admin_service.py
    auth_service.py
    pantry_service.py
    profile_service.py
    recommendation_service.py
    survey_service.py

  utils/
    cache_helpers.py
    formatting.py
    ui_helpers.py
```

## Dataset

The app uses a cleaned recipe and nutrition dataset located in:

```text
data/smart_pantry_recipes_clean.csv
```

The dataset supports recipe matching and includes information such as:

- Recipe name
- Ingredients
- Meal type
- Cuisine type
- Nutrition information
- Calories
- Protein
- Carbohydrates
- Fat

The app also supports barcode/item lookup data through:

```text
data/barcode_lookup.csv
```

## Author

Patrice Jones  
Graduate Capstone Project  
Full Sail University
