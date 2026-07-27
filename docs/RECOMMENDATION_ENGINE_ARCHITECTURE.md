# Recommendation Engine Architecture

## Purpose

Smart Pantry ranks practical meals from the participant's pantry while keeping the recommendation logic explainable. The engine is a decision-support pipeline rather than a single opaque model.

## Pipeline

1. **Load context** — pantry inventory, profile preferences, and recent recommendation actions.
2. **Normalize ingredients** — clean product names, collapse aliases, and identify generic food families.
3. **Safety filtering** — remove recipes that conflict with allergies, dietary restrictions, or avoided foods.
4. **Candidate evaluation** — evaluate the realistic recipe pool instead of stopping after the first matches.
5. **Pantry evidence** — classify exact matches, compatible aliases, safe Smart Swaps, and truly missing ingredients.
6. **Eligibility** — label recipes as complete or near-complete using validated evidence.
7. **Scoring** — combine pantry match, expiration urgency, quantity coverage, nutrition fit, preferences, behavior learning, and pantry utilization.
8. **Diversity control** — limit repeated recipe families, proteins, cuisines, and cooking patterns in the visible results.
9. **Confidence and explanation** — validate the recommendation and produce a participant-facing reason.
10. **Tracking** — save the generation session and later Save, Made, Skip, and feedback actions.

## Ranking priorities

Safety is a hard gate. Complete meals rank before near-complete meals. Behavior signals are gentle adjustments and cannot override safety or strong pantry evidence. Recently made recipes receive a temporary fatigue penalty so the list stays fresh.

## Explainability

Each card exposes the evidence used by the engine: Pantry Match, Nutrition Fit, ingredients used, expiring ingredients, missing ingredients, Smart Swaps, Smart Score, and a plain-language recommendation explanation.

## Failure behavior

The API returns a stable versioned contract. Recommendation tracking failure does not block the participant from receiving results. In production, internal exception details are logged with a request ID but are not returned to the browser.
