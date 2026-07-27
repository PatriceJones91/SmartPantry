# Phase 18.12 — Per-Ingredient Quantity Selector

This phase changes the "I made this" pantry-update workflow.

## Participant workflow

For every matched pantry ingredient, the participant can:

1. Check or uncheck whether that ingredient should be removed from My Pantry.
2. Choose the amount actually used from a quantity selector (common fractions plus 1–100).
3. Choose the unit actually used from a kitchen-unit dropdown.
4. Review the projected pantry quantity after cooking.
5. Confirm "Made meal" to subtract only the checked, convertible amounts.

Supported unit choices include teaspoons, tablespoons, cups, ounces, pounds,
grams, kilograms, milliliters, liters, items, servings, slices, pieces, eggs,
strips, patties, cloves, and dozens.

## Safety

Smart Pantry performs exact conversions within the same measurement family
(weight-to-weight and volume-to-volume), count/package conversions when they
are semantically safe, and ingredient-aware estimated volume/weight
conversions for supported ingredients. If a selected unit cannot be safely
converted into the pantry item's stored unit, the pantry update is blocked for
that ingredient until the participant selects a compatible unit.

No database migration is required.
