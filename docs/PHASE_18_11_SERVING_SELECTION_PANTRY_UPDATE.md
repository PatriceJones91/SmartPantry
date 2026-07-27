# Phase 18.11 — Serving Selection + Select-to-Remove Pantry Update

This phase simplifies the post-meal pantry update workflow.

## Changes

- Replaces the +/- serving control with a simple **servings dropdown**.
- Scaling the serving count automatically scales recipe ingredient quantities.
- Each matched pantry ingredient now has a **checkbox**.
- Checked ingredients are the only items changed in **My Pantry** when the participant confirms **Made meal**.
- Participants can use **Select all** or **Clear all**.
- Unchecked ingredients explicitly show **No change**.
- When a recipe/pantry unit cannot be safely converted, a small manual quantity field appears only for that selected ingredient.
- The pantry summary reports how many selected items will be reduced or completely used.

## Safety

The existing unit-conversion layer is preserved. Smart Pantry still avoids guessing an unsafe subtraction. A selected item with no safe conversion must either receive a manual amount or be unchecked before the pantry can be updated.

## Database

No database migration is required.
