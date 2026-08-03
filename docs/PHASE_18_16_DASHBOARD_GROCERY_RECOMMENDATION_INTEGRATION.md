# Phase 18.16 — Dashboard Grocery Recommendation Integration

The Dashboard **Suggested Grocery List** now uses the latest recorded Meal Recommendations
instead of a separate hard-coded grocery idea list.

## Source of truth

1. The participant generates meal recommendations.
2. The recommendation session and recommendation snapshots are stored in Supabase.
3. The Dashboard loads the participant's latest recommendation session.
4. Missing ingredients are normalized and counted across those recommendations.
5. Ingredients already in My Pantry are excluded.
6. Missing ingredients covered by an available Smart Swap are excluded.
7. The most useful remaining items are shown first based on how many recommended meals
   they help unlock.

The section name remains **Suggested Grocery List**.

Participant-added custom grocery items are preserved and remain separate from the
recommendation-generated suggestions.

No Smart Score, candidate ranking, recipe classification, Smart Swap generation,
or recommendation-page layout was changed.
