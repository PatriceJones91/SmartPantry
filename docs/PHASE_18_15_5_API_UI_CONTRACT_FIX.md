# Phase 18.15.5 — Recommendation API/UI Contract Fix

## Root cause

The recommendation backend and the React recommendation page were speaking two different data contracts.

The modular Phase 18 recommendation API returns fields such as:

- `smart_score`
- `pantry_match_percent`
- `nutrition_fit.score_percent`
- `nutrition_fit.score_out_of_15`
- `nutrition.per_serving`
- `matched_ingredients` as structured ingredient-match objects
- `expiring_ingredients` as structured ingredient-match objects

The recommendation page was still rendering the older flattened fields:

- `score`
- `exact_pantry_match_percent`
- `ml_nutrition_fit_percent`
- `ml_nutrition_fit`
- top-level calorie/protein/carb/fat values
- `matched_ingredients` as strings

That mismatch caused `N/A`, blank Smart Score values, and `[object Object]` in the UI.

## Fix

A frontend normalization adapter was added to `frontend/src/pages/Recommendations.jsx`.

It converts the stable modular API response into the page's existing display shape without changing:

- ranking;
- Smart Score calculations;
- pantry matching;
- Smart Swaps;
- meal classification;
- diversity logic;
- Supabase schema;
- recommendation API response models.

This is intentionally a presentation/contract compatibility fix rather than another recommendation-engine rewrite.

## Important mapping examples

- `smart_score` -> UI `score`
- `pantry_match_percent` -> UI `exact_pantry_match_percent`
- `nutrition_fit.score_percent` -> UI `ml_nutrition_fit_percent`
- `nutrition_fit.score_out_of_15` -> UI `ml_nutrition_fit`
- `nutrition.per_serving.*` -> UI nutrition values
- structured matched ingredient objects -> readable ingredient names
- structured expiring ingredient objects -> readable use-soon details

The structured ingredient objects are also preserved internally on the normalized recipe as `matched_ingredient_objects` and `expiring_ingredient_objects` so future UI work can use their richer metadata.
