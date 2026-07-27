# Phase 12 — Candidate Expansion

The recommendation engine now builds a tiered candidate pool:

1. Complete recipes using expiring pantry ingredients.
2. Other complete pantry recipes.
3. Near-complete recipes missing one main ingredient.
4. Near-complete recipes missing two main ingredients, with at least 60% coverage and at least two pantry matches.

Complete meals always rank ahead of near-complete meals. Within each tier, Smart Score uses pantry usefulness, expiration priority, Nutrition Fit, preferences, and practicality. Near-complete cards clearly display what is still needed.

Nutrition Fit inference is batched for responsiveness. The engine evaluates all safe recipes, narrows them to a deterministic 200–300 candidate pool, and returns up to 15 diverse recommendations.

Before using Phase 12 with recommendation tracking, run:

`database/migrations/20260721_phase_12_candidate_expansion.sql`
