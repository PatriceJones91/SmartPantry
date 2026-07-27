# Phase 18.15.8 — Manual Pantry-Unit Fallback

When Smart Pantry can safely convert the participant's meal measurement to the unit stored
in My Pantry, the existing automatic conversion remains unchanged.

When the units are not safely convertible, the Make This Meal dialog now asks:

**How much should be removed from My Pantry?**

The participant enters the amount directly in the pantry item's stored unit.

Example:

- Recipe usage: 1 cup shredded cheese
- Pantry storage: servings
- Participant confirms: 2 servings used
- Smart Pantry subtracts 2 servings

This avoids inventing unreliable conversions between unrelated measurement families while
still allowing the participant to record what they actually used.

The app also prevents the participant from subtracting more than the quantity currently
stored in My Pantry.

No Smart Score, recommendation ranking, Smart Swap, meal classification, diversity,
barcode camera, or backend API behavior was changed.
