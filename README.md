# Smart Pantry

## Smart Pantry 2.0 — Pantry-Aware Meal Recommendation and Decision-Support System

Smart Pantry is a pantry-aware meal recommendation and decision-support system designed to help users better understand the food they already have, reduce food waste, and make realistic meal decisions based on available pantry ingredients.

Smart Pantry 2.0 is a rebuilt version of the original Smart Pantry prototype. The current application uses a React frontend, FastAPI backend, and Supabase PostgreSQL database. The rebuild provides a more scalable architecture for pantry tracking, personalized meal recommendations, recommendation history, user study data collection, and future expansion.

The goal of Smart Pantry is not simply to generate recipes. The system is designed to answer a more practical question:

> **What can I realistically make with the food I already have, and what should I use first?**

Smart Pantry considers pantry availability, expiration dates, missing ingredients, user preferences, nutrition information, recipe characteristics, and prior recommendation activity when generating meal suggestions. Users remain in control of the final decision and can record what they actually made, substitute ingredients, or report that pantry ingredients were used elsewhere.

---

## Project Purpose

Smart Pantry was developed as a graduate capstone project for Full Sail University.

The project investigates whether a pantry management and meal recommendation system can improve:

- Pantry awareness
- Ingredient utilization
- Meal decision-making
- Use of food before expiration
- Perceived usefulness of pantry-based recommendations

The application supports a 7–14 day user study in which participants can create an account, complete study surveys, build a pantry inventory, receive meal recommendations, and record what they actually did with those recommendations.

Rather than treating recipe recommendation as an isolated task, Smart Pantry connects recommendation behavior with pantry inventory and ingredient usage.

---

## Smart Pantry Workflow

1. A participant creates an account and completes the pre-study survey.
2. The participant adds food items to their pantry.
3. Pantry quantities, categories, and expiration dates are stored in Supabase.
4. Smart Pantry evaluates the participant's current pantry and saved preferences.
5. The recommendation engine searches the recipe library for realistic meal possibilities.
6. Recommendations are ranked using pantry availability, expiration priority, nutrition fit, missing ingredients, user preferences, diversity, and recommendation quality rules.
7. The participant can save a recommendation, make the meal, use ingredients elsewhere, or indicate that the recommendation was not used.
8. Pantry usage and recommendation activity are recorded for later analysis.
9. Participants complete a post-study survey at the end of the study period.

---

# Core Features

## User Accounts

Participants can register and log in using their own credentials.

Each participant has access to their own:

- Pantry inventory
- Profile and preferences
- Meal recommendations
- Recommendation history
- Survey responses

An administrator account provides study-level visibility through the Smart Pantry admin dashboard.

---

## Pantry Management

Users can create and maintain a digital pantry inventory.

Pantry records can include:

- Item name
- Category
- Quantity
- Measurement unit
- Container or package type
- Expiration date
- Barcode / UPC
- Brand
- Notes

Smart Pantry supports multiple quantity and measurement formats so pantry inventory does not have to use the same measurement as a recipe.

Supported measurement concepts include:

- Teaspoons
- Tablespoons
- Cups
- Fluid ounces
- Ounces
- Pounds
- Grams
- Kilograms
- Milliliters
- Liters
- Gallons
- Items
- Servings
- Slices
- Pieces
- Dozens
- Strips
- Patties
- Eggs
- Cloves

---

## Barcode and Item Lookup

Smart Pantry includes barcode and item lookup functionality to make pantry entry easier.

Users can enter a barcode / UPC or search for common food items to help populate pantry information.

Manual entry remains available when barcode data is unavailable.

---

## Grocery Receipt and Camera Support

Smart Pantry includes a grocery receipt workflow that allows users to upload or photograph a receipt for pantry entry support.

On compatible devices, the application can access the device camera for receipt capture. Manual image upload remains available as a fallback.

---

## Dashboard

The participant dashboard provides a quick overview of pantry and study activity.

Dashboard information can include:

- Survey completion
- Pantry item count
- Pantry quantities
- Pantry category distribution
- Expiration alerts
- Items that should be used soon
- Suggested grocery items
- Study activity indicators

---

## Profile and Preferences

Participants can save information used to personalize recommendations.

Profile information includes:

- Household size
- Allergies
- Dietary restrictions
- Foods to avoid
- Preferred meal types
- Preferred cuisines
- Quick-meal preferences
- Additional profile notes

---

# Meal Recommendation Engine

Smart Pantry's recommendation system is designed to recommend **realistic meals**, not simply recipes containing one matching ingredient.

The engine evaluates the user's current pantry against available recipe data and ranks eligible recipes according to multiple factors.

The recommendation pipeline includes services for:

- Candidate discovery
- Ingredient normalization
- Pantry matching
- Profile safety
- Meal eligibility
- Meal classification
- Expiration analysis
- Nutrition Fit
- Preference fit
- Smart Score calculation
- Recommendation quality validation
- Smart Swap generation
- Recipe realism filtering
- Recipe-family diversity
- Behavior learning

---

## Recipe Data

Smart Pantry uses a cleaned recipe dataset stored in:

```text
backend/data/smart_pantry_recipe_dataset.csv
```

The system evaluates a broad candidate pool rather than stopping after a small number of recipe matches.

---

## Ingredient Matching

Recipe ingredients are normalized and compared with ingredients currently available in the user's pantry.

Recommendations identify ingredients that are:

- Available in the pantry
- Missing from the pantry
- Potential candidates for substitution

---

## Pantry Match

Pantry Match represents how well the ingredients required by a recipe correspond to ingredients currently available in the participant's pantry.

Recipes with stronger pantry coverage can rank higher because they require fewer additional ingredients.

---

## Expiration-Aware Recommendations

Expiration awareness is one of the central features of Smart Pantry.

The recommendation engine can prioritize recipes that use pantry ingredients approaching their expiration dates.

This allows the system to recommend not only:

> "What can you make?"

but also:

> "What could you make that helps use food before it expires?"

---

## Missing Ingredients and Near-Complete Meals

Smart Pantry can distinguish between:

- Complete pantry meals
- Strong pantry matches
- Near-complete meals
- Meals requiring a limited number of additional ingredients
- Lower-priority recipes requiring too many missing ingredients

---

## Smart Swaps

When a recipe is missing an ingredient, Smart Pantry can support ingredient substitutions through **Smart Swaps**.

Automatic Smart Swaps are intended to consider:

- Food-family compatibility
- Culinary-role compatibility
- Recipe context

The system prefers showing **no swap** over suggesting an obviously inappropriate replacement.

When an automatic substitution is unavailable, users can use **Add Your Own Smart Swap**.

---

## Nutrition Fit

Smart Pantry includes a Nutrition Fit evaluation pipeline.

The backend contains a trained Random Forest model:

```text
backend/ml/random_forest_nutrition_fit_model.pkl
```

This model is used as part of the Nutrition Fit evaluation process so recipe nutrition information can contribute to recommendation quality.

Nutrition Fit is one recommendation signal among several and is not intended to provide medical or clinical nutrition advice.

---

## Smart Score

Smart Pantry combines multiple recommendation signals into a **Smart Score**.

Recommendation scoring can consider:

- Pantry ingredient coverage
- Expiration priority
- Missing ingredient penalties
- Nutrition Fit
- User preferences
- Meal context
- Recipe practicality
- Recommendation quality
- Behavior-learning signals

---

## Context-Aware Meal Classification

Smart Pantry includes a second classification layer that evaluates recipe characteristics instead of blindly trusting the original dataset label.

Meal classification can consider:

- Recipe title
- Ingredient structure
- Dish type
- Original dataset meal type
- Cooking context
- Recipe characteristics

Supported participant-facing meal filters include:

- Breakfast
- Lunch
- Dinner
- Snack
- Quick Meal
- Brunch

---

## Recipe Realism and Diversity

Smart Pantry includes realism and diversity rules intended to reduce:

- Novelty or gimmick recipes that are unlikely to be useful
- Duplicate recipe families
- Repeated versions of nearly identical dishes
- Overrepresentation of one protein or meal family

---

## Behavior Learning

Smart Pantry records participant interactions with recommendations.

Behavior signals can include:

- Saved recipes
- Made recipes
- Skipped or unused recipes

These signals can gently influence future rankings without replacing pantry usefulness, dietary safety, or recommendation quality.

---

## Add My Own Meal

The **Add My Own Meal** feature allows participants to record something they prepared independently.

This helps keep pantry quantities and recommendation-history data representative of actual behavior.

---

## Pantry Usage and Quantity Adjustment

Smart Pantry allows participants to enter the amount and measurement unit used for individual ingredients.

Example:

- Pantry inventory: **5 lb bag of flour**
- Meal 1 usage: **3 oz flour**
- Meal 2 usage: **1 cup flour**

The quantity conversion layer supports common kitchen-unit conversions and safer handling of ingredient-specific conversions.

---

# Recommendation Actions and History

Participants can record what happened after receiving a recommendation.

Recommendation actions include:

- **Made Meal**
- **Used Elsewhere**
- **Saved for Later**
- **Did Not Use**

---

# Surveys and Research Data

Smart Pantry includes pre-study and post-study surveys.

Survey responses are stored in Supabase and support evaluation of the project's research questions.

---

# Admin Dashboard

The Smart Pantry admin dashboard provides study-level visibility into participant activity.

Administrative information can include:

- Participant accounts
- Survey completion
- Pantry activity
- Recommendation activity
- Recommendation outcomes
- Study participation metrics

---

# Technology Stack

## Frontend

- React
- Vite
- JavaScript
- CSS
- Recharts

## Backend

- FastAPI
- Python
- Supabase Python Client
- CSV-based recipe and barcode loading
- Recommendation services
- Random Forest Nutrition Fit model

## Database

- Supabase
- PostgreSQL

## Development and Deployment

- Git
- GitHub
- Vercel-compatible frontend configuration
- FastAPI / Uvicorn development server

---

# Project Structure

```text
Smart_Pantry_2.0/
│
├── backend/
│   ├── .env.example
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   │
│   ├── data/
│   │   ├── openfoodfacts_barcode_lookup.csv
│   │   └── smart_pantry_recipe_dataset.csv
│   │
│   ├── ml/
│   │   └── random_forest_nutrition_fit_model.pkl
│   │
│   ├── models/
│   │   ├── recommendation_api.py
│   │   ├── schemas.py
│   │   └── __init__.py
│   │
│   ├── routes/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── barcodes.py
│   │   ├── pantry.py
│   │   ├── profile.py
│   │   ├── recommendations.py
│   │   ├── surveys.py
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── barcode_service.py
│   │   ├── recipe_filters.py
│   │   ├── recommendation_service.py
│   │   ├── recommendation_tracking.py
│   │   ├── supabase_service.py
│   │   ├── __init__.py
│   │   │
│   │   └── recommendations/
│   │       ├── api_adapter.py
│   │       ├── behavior_learning.py
│   │       ├── candidate_discovery.py
│   │       ├── contracts.py
│   │       ├── diversity.py
│   │       ├── engine.py
│   │       ├── expiry_analyzer.py
│   │       ├── ingredient_normalizer.py
│   │       ├── meal_classifier.py
│   │       ├── meal_context.py
│   │       ├── meal_eligibility.py
│   │       ├── nutrition_fit.py
│   │       ├── pantry_matcher.py
│   │       ├── preference_fit.py
│   │       ├── profile_safety.py
│   │       ├── recipe_realism.py
│   │       ├── recipe_repository.py
│   │       ├── recommendation_quality.py
│   │       ├── recommendation_service.py
│   │       ├── smart_score.py
│   │       ├── smart_swaps.py
│   │       └── __init__.py
│   │
│   └── tests/
│       ├── test_meal_classifier.py
│       ├── test_phase18_production_readiness.py
│       ├── test_recommendation_phase11.py
│       ├── test_recommendation_phase12.py
│       ├── test_recommendation_phase13.py
│       ├── test_recommendation_phase14.py
│       ├── test_recommendation_phase16.py
│       ├── test_recommendation_phase17.py
│       ├── test_recommendation_phase18_2.py
│       ├── test_recommendation_phase18_4.py
│       ├── test_recommendation_phase18_5.py
│       ├── test_recommendation_phase18_9.py
│       └── earlier recommendation-engine tests
│
├── database/
│   ├── schema.sql
│   └── migrations/
│       └── 20260721_phase_12_candidate_expansion.sql
│
├── docs/
│   ├── DEMO_CHECKLIST.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── PHASE_12_CANDIDATE_EXPANSION.md
│   ├── PHASE_13_RECOMMENDATION_QUALITY_CALIBRATION.md
│   ├── PHASE_18_10_FRIENDLY_KITCHEN_QUANTITIES.md
│   ├── PHASE_18_11_SERVING_SELECTION_PANTRY_UPDATE.md
│   ├── PHASE_18_12_PER_INGREDIENT_QUANTITY_SELECTOR.md
│   ├── PHASE_18_VALIDATION_PLAN.md
│   ├── RECIPE_DATASET_AUDIT.json
│   └── RECOMMENDATION_ENGINE_ARCHITECTURE.md
│
├── frontend/
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vercel.json
│   │
│   ├── public/
│   │   └── SmartPantry_logo.png
│   │
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── styles.css
│       │
│       ├── api/
│       │   └── client.js
│       │
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── StatCard.jsx
│       │   └── SurveyForm.jsx
│       │
│       ├── data/
│       │   └── surveyQuestions.js
│       │
│       ├── pages/
│       │   ├── Admin.jsx
│       │   ├── Dashboard.jsx
│       │   ├── History.jsx
│       │   ├── Login.jsx
│       │   ├── Pantry.jsx
│       │   ├── Profile.jsx
│       │   └── Recommendations.jsx
│       │
│       └── utils/
│           └── quantityConversion.js
│
├── Project doc/
│   ├── Jones_Thesis_Draft2.docx
│   └── study flyer.png
│
├── scripts/
│   └── validate_release.sh
│
├── .gitignore
├── package-lock.json
└── README.md
```

---

# Running the Project Locally

## Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment if needed:

```bash
python -m venv venv
```

Activate it in Windows Git Bash:

```bash
source venv/Scripts/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

The backend normally runs at:

```text
http://127.0.0.1:8000
```

## Frontend

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

---

# Environment Variables

Environment files are intentionally excluded from Git version control.

The repository includes `.env.example` files where applicable.

Do **not** commit:

- Supabase service keys
- Private API credentials
- Passwords
- Authentication secrets
- Local `.env` files

---

# Testing and Validation

The backend contains automated tests covering multiple stages of the rebuilt recommendation engine.

Testing includes:

- Recommendation generation
- Candidate expansion
- Recommendation quality
- Smart Score behavior
- Smart Swaps
- Meal classification
- Recipe realism
- Diversity
- Pantry quantity conversion
- Production-readiness behavior

The `docs/` directory also contains validation and demo checklists used during development.

---

# Current Project Status

Smart Pantry 2.0 currently includes:

- Participant authentication
- Pantry management
- Barcode and item lookup
- Grocery receipt capture support
- Pantry quantity tracking
- Kitchen-unit conversion
- Expiration awareness
- Participant profiles and preferences
- Pantry-based meal recommendations
- Large recipe-library evaluation
- Smart Score ranking
- Nutrition Fit evaluation
- Random Forest Nutrition Fit model
- Missing ingredient detection
- Smart Swaps
- User-defined Smart Swaps
- Context-aware meal classification
- Recipe realism filtering
- Recipe-family diversity
- Behavior-learning signals
- Add My Own Meal functionality
- Recommendation actions and history
- Pre-study and post-study surveys
- Administrative study monitoring

The system continues to be tested and refined, particularly around recommendation ranking, recipe classification, ingredient normalization, quantity conversion, and recommendation response time.

---

# Known Limitations

Smart Pantry is a capstone research prototype and is not intended to provide medical or clinical nutrition advice.

Recipe datasets can contain inconsistent:

- Ingredient names
- Measurement formats
- Meal classifications
- Dish types
- Nutrition information
- Recipe titles

Smart Pantry includes normalization, validation, classification, and filtering logic to improve recommendation quality, but some recipe metadata may still require refinement.

Ingredient substitutions are context-dependent. A technically similar ingredient is not always an appropriate cooking substitution, which is why Smart Pantry prioritizes conservative Smart Swaps and allows participants to provide their own substitutions.

Quantity conversion between volume and weight can also depend on the ingredient itself. Where a safe deterministic conversion is unavailable, the application should avoid presenting false precision.

Recommendation quality ultimately depends in part on the accuracy of the participant's pantry inventory.

---

# Future Development

Potential future improvements include:

- Expanded ingredient normalization
- Additional ingredient-specific unit conversions
- Improved automatic Smart Swap suggestions
- Continued recipe and meal-type classification refinement
- Additional recipe sources
- Recommendation performance optimization
- More advanced nutrition personalization
- Grocery-list integration
- Expanded barcode coverage
- Improved package-size interpretation
- Mobile-focused interface improvements
- Additional recommendation-learning features based on participant behavior

---

# Research Context

Smart Pantry is being developed as a graduate capstone research project at Full Sail University.

The application serves both as:

1. A functional pantry-management and meal recommendation system.
2. A research prototype for studying pantry-aware recommendation, food-use decision support, and participant interaction with recommendation systems.

The project is currently under active development and evaluation.
