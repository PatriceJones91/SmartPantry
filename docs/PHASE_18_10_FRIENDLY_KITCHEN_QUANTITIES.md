# Phase 18.10 — Friendly Kitchen Quantities

This phase improves the quantity workflow shown after **I made this**.

## What changed

- Dozens of eggs are displayed as individual eggs (1 dozen -> 12 eggs).
- Lunch meat can be displayed and adjusted as slices; when only package weight is available, Smart Pantry uses a clearly labelled estimate.
- Bread is adjusted as slices.
- Bacon can be adjusted as strips.
- Patties are adjusted as patties.
- Chicken breasts and chops can be adjusted as pieces when appropriate.
- Missing recipe amounts can receive conservative Smart Estimates for common cooking situations instead of defaulting immediately to manual entry.
- Estimated values remain editable with +/- controls.
- Pantry subtraction still occurs in the pantry item's stored unit, so the database quantity remains consistent.

## Safety rule

Smart Pantry only uses deterministic conversions when they are exact. Package-to-piece conversions that require assumptions are labelled **Smart estimate / Estimated** and remain user-adjustable. If no safe estimate is available, the interface still falls back to manual confirmation rather than inventing precision.
