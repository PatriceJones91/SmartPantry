# Phase 18.15.6 — Recommendation Action Tracking Fix

## Symptom

The recommendation page displayed correctly after Phase 18.15.5, but clicking
Made Meal / Used Elsewhere / Save for Later / Did Not Use could return:

`POST /api/recommendations/action 422 Unprocessable Entity`

## Root cause

The frontend was still sending the legacy action payload:

- `score`
- `feedback`
- `used_ingredients`

The current backend contract requires:

- `session_id`
- `recommendation_result_id`
- `recipe_id`
- `smart_score`
- `metadata`

The backend action whitelist also did not include the participant-facing
`used_elsewhere`, `not_used`, and `custom_meal` actions.

## Fix

- Store the generated recommendation `session_id` in the React page.
- Send the current v1 action payload contract.
- Preserve the recommendation result ID and recipe ID returned by the engine.
- Put notes and ingredient usage inside `metadata`.
- Allow the participant-facing action names in backend tracking.
- Save the action before modifying pantry quantities so a validation failure
  cannot silently deduct pantry inventory.
- Link Add My Own Meal to the active recommendation session with a stable custom recipe ID.

No Smart Score, ranking, meal classification, Smart Swap, diversity, or pantry-matching
logic was changed.
