# Phase 13 — Recommendation Quality Calibration

Phase 13 builds on Phase 12 candidate expansion without removing complete or near-complete recommendations.

## Changes

- Nutrition is displayed and evaluated per serving while retaining whole-recipe totals in the API payload.
- Pantry product names are shown as clean canonical ingredient names on recommendation cards.
- Common potato varieties such as Yukon Gold, russet, red, and gold potatoes match the canonical `potato` ingredient.
- Near-complete recipes receive a transparent practicality penalty based on the shopping burden of missing ingredients. Missing proteins cost more than ordinary staples.
- Diversity selection applies soft family caps before relaxing them to fill the requested recommendation count. This reduces repeated chicken or same-style dishes.
- Engine and Smart Score versions are updated to Phase 13.

## Compatibility

The API remains contract version 1.0. Existing whole-recipe nutrition fields remain available. A nested `nutrition.per_serving` object and `nutrition.basis` field were added.
