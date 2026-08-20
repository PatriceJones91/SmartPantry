# Smart Pantry

## Smart Pantry 2.0 — Pantry-Aware Meal Recommendation and Research System

Smart Pantry is a pantry-aware meal recommendation and decision-support application developed as a graduate capstone project at Full Sail University.

The system is designed to help users understand what food they already have, identify ingredients that should be used soon, receive practical meal recommendations, and record how pantry ingredients are actually used.

Smart Pantry is not intended to simply answer:

> **What recipes contain this ingredient?**

Instead, it is designed to support a more practical question:

> **What can I realistically make with the food I already have, and what should I use first?**

The current application uses a React/Vite frontend, FastAPI/Python backend, Supabase/PostgreSQL persistence, a structured recipe dataset, and a Random Forest model that supports the Nutrition Fit component of the recommendation process.

---

# Research Focus

Smart Pantry is being evaluated through a within-subject mixed-methods study.

### Research Question

**Does Smart Pantry improve pantry awareness, recommendation usefulness, and ingredient utilization compared with manual pantry tracking and an existing ingredient-based recipe application?**

### Alternative Hypothesis

**Participants using Smart Pantry will demonstrate statistically significant improvement in pantry awareness, recommendation usefulness, and ingredient utilization compared with the manual Pantry Note Tracker and the Samsung Food ingredient-based recipe-finder comparison.**

### Main Outcome Evidence

- **Pantry Awareness** = pre-study and post-study survey evidence
- **Recommendation Usefulness** = task feedback + Technology Acceptance Model (TAM) measures
- **Ingredient Utilization** = Smart Pantry behavioral evidence

TAM is used to evaluate:

- Perceived Ease of Use
- Perceived Usefulness
- Behavioral Intention

TAM supports interpretation of participant acceptance and usefulness. It does not replace the pantry-awareness or behavioral measures.

---

# Study Workflow

Participants move through the following study sequence:

1. Study website and consent
2. Pre-Study Survey
3. **Study Task 1 — Pantry Note Tracker**
4. Task 1 feedback
5. **Study Task 2 — Samsung Food Ingredient Recipe Finder**
6. Task 2 feedback
7. **Study Task 3 — Smart Pantry**
8. Task 3 feedback
9. Post-Study Survey
10. Study completion

The study is designed for adults age 18 or older and is conducted over approximately 7–14 days.

Survey and TAM responses are collected through Google Forms. Smart Pantry behavioral evidence and Pantry Note Tracker records are exported separately and combined for final analysis using participant identifiers.

---

# Core Application Roles

Smart Pantry supports three application roles.

## Participant

Participants can access:

- Dashboard
- Profile & Preferences
- My Pantry
- Meal Recommendations
- Recommendation History
- Log Out

Participant accounts are used during Study Task 3.

## Administrator

The administrator can access:

- Full Admin Dashboard
- Participant activity
- Pantry evidence
- Recommendation evidence
- Participant Evidence Matrix
- Study exports
- Participant account-support tools
- Committee Dashboard

## Committee

Committee accounts are routed to a dedicated **Committee Dashboard**.

The Committee Dashboard presents research-facing evidence without exposing account-management controls.

Route:

```text
/committee
```

The Committee Dashboard summarizes:

- Study participation
- Household size evidence
- Pantry activity
- Recommendation behavior
- Ingredient-utilization actions
- Study outcome evidence
- Participant-level evidence
- Research-measure alignment

---

# Pantry Management

Participants can maintain a digital pantry inventory containing fields such as:

- Item name
- Category
- Quantity
- Unit
- Container type
- Expiration date
- UPC / barcode
- Brand
- Notes

Supported pantry-entry methods include:

- Manual entry
- UPC lookup
- Camera barcode scanning
- Uploaded barcode images
- Grocery receipt image capture
- Receipt image upload
- Text / CSV import
- Manual fallback when lookup data is unavailable

Receipt and barcode workflows allow participants to review detected information before saving it to the pantry.

---

# Profile and Preferences

Participant profile information can include:

- Household size
- Allergies
- Dietary restrictions
- Foods to avoid
- Preferred meal types
- Preferred cuisines
- Quick-meal preferences
- Additional notes

Household size is also available to the Admin and Committee evidence views for participant-level research context.

---

# Meal Recommendation Engine

Smart Pantry evaluates the participant's current pantry against the recipe dataset and ranks realistic meal options.

The recommendation pipeline includes:

- Candidate discovery
- Ingredient normalization
- Pantry matching
- Profile safety
- Meal eligibility
- Expiration analysis
- Meal classification
- Nutrition Fit
- Preference Fit
- Smart Score calculation
- Recommendation-quality validation
- Smart Swap generation
- Recipe realism filtering
- Recipe-family diversity
- Behavior-learning signals

---

# Recipe Dataset

The main recipe dataset is stored at:

```text
backend/data/smart_pantry_recipe_dataset.csv
```

Recipe records include structured information such as:

- Recipe name
- Meal type
- Cuisine type
- Dish type
- Ingredients
- Ingredient quantity
- Ingredient measurement
- Ingredient weight
- Nutrition information
- Recipe servings
- Source URL
- Practicality / everyday-fit information

The source URL remains available for participants who want the full cooking instructions.

---

# Serving-Based Pantry Deduction

Smart Pantry can use structured recipe quantities when a participant chooses **Make This Meal**.

The participant selects how many servings were actually prepared. Smart Pantry then scales the recipe's ingredient quantities before updating pantry inventory.

Conceptually:

```text
Amount used =
Recipe ingredient amount
×
(Servings actually prepared / Recipe servings)
```

Example:

If a recipe serves 4 and uses 8 oz of pasta, preparing 2 servings results in:

```text
8 oz × (2 / 4) = 4 oz
```

Smart Pantry then passes the calculated amount through its quantity-conversion layer before deducting it from My Pantry.

Where a safe conversion cannot be determined, the application uses a participant-friendly fallback instead of inventing a precise value.

---

# Quantity Conversion

Smart Pantry supports common kitchen measurement concepts including:

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

Conversions between compatible units are automatic where possible.

Volume-to-weight and package conversions can depend on the ingredient and package size, so Smart Pantry avoids presenting false precision when the available pantry record does not support a safe conversion.

---

# Smart Score

Smart Pantry uses an explainable 100-point Smart Score.

Current weighting:

| Component | Weight |
|---|---:|
| Pantry Usefulness | 30 |
| Nutrition Fit | 25 |
| Expiration Priority | 20 |
| Practicality | 20 |
| Preference Fit | 5 |
| **Total** | **100** |

The weights are design weights developed through iterative implementation and testing. They were not statistically optimized.

Smart Score is intended to balance pantry usefulness, nutrition, expiration priority, practicality, and user preferences.

---

# Nutrition Fit

Smart Pantry includes a trained Random Forest model stored at:

```text
backend/ml/random_forest_nutrition_fit_model.pkl
```

The Random Forest model supports **Nutrition Fit only**. It does not generate the entire recommendation ranking.

Nutrition Fit uses structured recipe nutrition features such as:

- Calories
- Protein
- Carbohydrates
- Fat
- Ingredient count

Nutrition Fit is one component of the Smart Score and is not intended to provide medical or clinical nutrition advice.

---

# Expiration-Aware Recommendations

Expiration awareness is a major Smart Pantry feature.

The system can prioritize recipes that use ingredients approaching expiration so recommendations can answer both:

> **What can I make?**

and:

> **What should I consider using first?**

Participant-facing pantry alerts include:

- **Use Immediately!!** — approximately 0–1 days
- **Warning Use Soon!** — approximately 2–4 days
- **Plan Ahead** — approximately 5–10 days

---

# Smart Swaps

Smart Pantry can suggest substitutions when a recipe is missing an ingredient.

Smart Swaps are designed to consider:

- Food-family compatibility
- Culinary role
- Recipe context
- Participant allergies / avoid lists

The system prefers showing no swap over presenting an obviously inappropriate replacement.

Participants can also add their own substitution when necessary.

---

# Recommendation Actions

Current participant-facing recommendation outcomes include:

- **Made Meal**
- **Custom Meal**
- **Saved for Later**
- **Did Not Use**

## Made Meal

The participant prepared a Smart Pantry recommendation.

## Custom Meal

The participant prepared a different meal and can record pantry ingredients used in that meal.

Historical `used_elsewhere` records are preserved in the database but are combined with Custom Meal evidence in the current research-facing Admin and Committee views.

## Ingredient Utilization

For current analysis:

```text
Ingredient Utilization =
Made Meal + Custom Meal
```

Historical `used_elsewhere` records remain included in the combined Custom Meal / ingredient-utilization evidence so earlier study activity is not lost.

Saved for Later is useful recommendation evidence but is not counted as ingredient utilization.

---

# Recommendation History

Recommendation History allows participants to review recorded actions such as:

- Made Meal
- Custom Meal
- Saved for Later
- Did Not Use

Smart Scores are shown for Smart Pantry-ranked recommendations when available.

Custom meals are not generated by the recommendation engine, so a Smart Score is not expected for those entries.

---

# Admin Dashboard

The Admin Dashboard consolidates Smart Pantry study evidence.

It includes:

- Participant accounts
- Household size
- Task 1 manual-entry evidence
- Task 3 pantry activity
- Recommendation actions
- Ingredient-utilization evidence
- Recommendation history
- Participant Evidence Matrix
- CSV exports
- Participant account-support tools

Displayed and exported evidence uses **date-only formatting where the time of day is not analytically important**.

Original timestamps remain stored in the database for audit and data-integrity purposes.

---

# Committee Dashboard

The Committee Dashboard provides a research-focused view for defense and committee review.

It is available to users with the `committee` role and to administrators.

Committee accounts are directed to:

```text
/committee
```

The dashboard is designed to surface the evidence needed to understand the study without presenting participant account-management features.

---

# Research Data and Final Analysis

Smart Pantry does not use a live Google Sheets integration for final study analysis.

The final workflow is:

1. Export Google Forms response sheets as CSV.
2. Export Smart Pantry research evidence from the Admin Dashboard.
3. Export Pantry Note Tracker evidence.
4. Match data using participant identifiers.
5. Clean the final matched dataset.
6. Calculate descriptive statistics.
7. Evaluate paired participant outcomes using the appropriate inferential test.
8. Review open-ended feedback for recurring themes.
9. Evaluate the research question and hypotheses using the completed evidence.

Planned quantitative analysis includes:

- Valid response counts
- Frequencies
- Percentages
- Means
- Medians
- Standard deviations
- Paired-samples t-test when assumptions are met
- Wilcoxon signed-rank test when assumptions are not met

Qualitative responses are grouped into recurring themes such as:

- Usability
- Clarity
- Recommendation usefulness
- Pantry awareness
- Ingredient utilization
- Suggested improvements

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
- Recommendation services
- CSV-based recipe and barcode data
- Random Forest Nutrition Fit model

## Database

- Supabase
- PostgreSQL

## Deployment

- Vercel — frontend
- Render — backend
- Git / GitHub — source control

---

# Project Structure

```text
Smart_Pantry_2.0/
│
├── backend/
│   ├── data/
│   │   ├── openfoodfacts_barcode_lookup.csv
│   │   └── smart_pantry_recipe_dataset.csv
│   ├── ml/
│   │   └── random_forest_nutrition_fit_model.pkl
│   ├── models/
│   │   └── recommendation_api.py
│   ├── routes/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── barcodes.py
│   │   ├── pantry.py
│   │   ├── profile.py
│   │   ├── recommendations.py
│   │   └── surveys.py
│   ├── services/
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
├── database/
│   ├── schema.sql
│   └── migrations/
│
├── docs/
│
├── frontend/
│   ├── public/
│   │   └── SmartPantry_logo.png
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   │   └── Navbar.jsx
│   │   ├── pages/
│   │   │   ├── Admin.jsx
│   │   │   ├── Committee.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── History.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Pantry.jsx
│   │   │   ├── Profile.jsx
│   │   │   └── Recommendations.jsx
│   │   ├── utils/
│   │   │   └── quantityConversion.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vercel.json
│
├── .gitignore
└── README.md
```

---

# Running the Project Locally

## Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment if needed:

```bash
python -m venv venv
```

Activate it in Windows Git Bash:

```bash
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

The local backend normally runs at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## Frontend

Open another terminal and navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Vite:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

---

# Environment Variables

Environment files are intentionally excluded from Git version control.

Do **not** commit:

- Supabase service keys
- API credentials
- Account passwords
- Authentication secrets
- Local `.env` files

Use `.env.example` files to document required variable names without exposing secrets.

---

# Testing and Validation

The project includes testing for areas such as:

- Recommendation generation
- Candidate expansion
- Smart Score behavior
- Nutrition Fit
- Smart Swaps
- Meal classification
- Recipe realism
- Diversity
- Pantry quantity conversion
- Serving-based deductions
- Production-readiness behavior

Before deployment, verify both participant and administrative workflows locally.

Important user-role checks include:

- Participant login → participant application
- Admin login → Admin Dashboard
- Committee login → Committee Dashboard

---

# Known Limitations

Smart Pantry is a graduate research prototype.

Known limitations include:

- Recipe datasets can contain inconsistent ingredient names and measurements.
- Volume-to-weight conversions can depend on ingredient density.
- Package units such as boxes, bags, and cartons cannot always be converted safely without package-size information.
- Mixed-unit inventory tracking can require approximate input when pantry and recipe units do not directly convert.
- Smart Pantry does not directly measure exact household food waste prevented.
- Behavioral ingredient-utilization actions provide evidence of pantry ingredient use, not proof of exact consumption.
- Recommendation quality depends partly on the accuracy of participant pantry records.
- The Random Forest model supports Nutrition Fit only and is not the entire recommendation engine.

---

# Future Development

Potential future work includes:

- Expanded ingredient-specific conversion data
- Improved package-size interpretation
- More advanced mixed-unit inventory handling
- Continued Smart Swap refinement
- Additional recipe sources
- Recommendation-performance optimization
- Formal Smart Score weight optimization
- More advanced learning-to-rank approaches
- Expanded barcode coverage
- Grocery-list improvements
- Mobile-interface refinements
- Additional behavior-learning features

---

# Current Project Status

Smart Pantry 2.0 currently includes:

- Participant authentication
- Administrator authentication
- Committee authentication
- Committee Dashboard
- Pantry management
- Barcode / UPC lookup
- Camera and image-based pantry-entry support
- Grocery receipt support
- Household-size profile evidence
- Pantry quantity tracking
- Kitchen-unit conversion
- Serving-based recipe deductions
- Expiration awareness
- Participant profiles and preferences
- Pantry-aware meal recommendations
- Structured recipe dataset
- Smart Score ranking
- Random Forest-supported Nutrition Fit
- Missing-ingredient detection
- Smart Swaps
- User-defined swaps
- Recipe realism filtering
- Recipe-family diversity
- Custom Meal logging
- Recommendation History
- Ingredient-utilization evidence
- Admin research dashboard
- CSV research exports
- Date-only research display / export formatting where appropriate

The participant study and final analysis are still in progress. Final statistical results, conclusions, and hypothesis evaluation should only be reported after the study closes and the final matched dataset is analyzed.

---

# Research Context

Smart Pantry serves two purposes:

1. A functional pantry-management and meal-recommendation system.
2. A graduate research prototype for evaluating pantry awareness, recommendation usefulness, and ingredient utilization.

The project is actively being evaluated as part of the Full Sail University graduate capstone process.
