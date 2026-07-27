# Phase 18.15.6a — Recommendation Session ID Hotfix

## Symptom
After recommendations generated successfully, clicking Made Meal, Used Elsewhere,
Save for Later, or Did Not Use displayed:

`Recommendation session is missing. Refresh meal recommendations and try again.`

## Root cause
Phase 18.15.6 added `currentSessionId` state and required it for action tracking,
but the successful generation handler never copied `metadata.session_id` from the
backend response into that state.

## Fix
The generation handler now runs:

`setCurrentSessionId(data?.metadata?.session_id || "");`

immediately after storing the generated recommendations.

No recommendation ranking, Smart Score, Smart Swap, diversity, pantry matching,
classification, or API response logic was changed.
