# Phase 18 Validation Plan

## Release gate

A build is demo-ready only when all automated tests pass, the React production build succeeds, and the manual scenarios below behave as expected.

## Manual scenarios

### Cold start
- New participant with no behavior history receives safe, varied pantry-based recommendations.
- Empty pantry receives a clear empty state rather than a crash.

### Complete and near-complete meals
- A complete meal has no items under Still Needed.
- A near-complete meal lists only genuine missing main ingredients.
- Complete meals appear before near-complete fallback meals.

### Personalization
- Save several recipes from one cuisine and confirm only a gentle future boost.
- Mark a meal Made and confirm it receives a temporary fatigue penalty.
- Skip a recipe family repeatedly and confirm it appears less often without being permanently hidden.

### Smart Swaps
- Accept only food-family, culinary-role, and recipe-context compatible substitutions.
- Prefer no swap over a low-confidence or misleading swap.

### Diversity
- Top 10 should not contain several versions of the same recipe family.
- Show More preserves rank order and does not duplicate cards.

### Expiration behavior
- There is no participant-facing “Expiring within” dropdown.
- Recipes using soon-to-expire pantry items receive an automatic, explainable boost.

### Reliability
- Save, Made, Skip, feedback, filters, and history work end to end.
- API timeout and network failures show participant-friendly messages.
- `/api/health` returns status, version, and environment.
