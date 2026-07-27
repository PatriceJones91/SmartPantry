# Phase 18.15.4 — Safe Diversity Performance Fix

This hotfix is based directly on the current Smart Pantry project supplied for diagnosis.

## Problem

The recommendation engine was not in an infinite loop, but the diversity selection stage behaved like one on large candidate pools because it repeatedly:

- rebuilt recipe signatures;
- re-tokenized recipe titles and ingredients;
- recomputed near-duplicate checks against the full selected list;
- recomputed maximum similarity against the full selected list;
- rescanned family counts;
- rebuilt diversity anchors for metadata.

The cost grew rapidly as the number of candidates and requested recommendations increased.

## Fix

Only the diversity-selection implementation was optimized.

The selection rules remain the same:

- Smart Score remains the base quality signal;
- top-quality anchors remain protected;
- expiration-led anchors remain limited;
- Nutrition Fit anchors remain;
- protein, dish, starch, and cuisine diversity rules remain;
- recipe-family duplicate suppression remains;
- progressive recommendation ordering remains.

The optimized implementation now:

- computes each recipe signature once per selection pass;
- caches pairwise similarity;
- maintains maximum similarity incrementally;
- maintains family/category counts incrementally;
- tracks duplicate status incrementally;
- reuses the original anchor count instead of rebuilding anchors.

No API response contract, frontend recommendation object shape, Smart Score formula,
meal classification, Smart Swap logic, pantry matching, or Supabase schema was changed.

## Validation

- Full backend test suite: 106 tests passed.
- Original-vs-optimized behavior comparison on a 100-candidate synthetic pool:
  - limit 15: identical recipe order;
  - limit 30: identical recipe order.
- Synthetic diversity benchmark:
  - limit 15: ~62x faster;
  - limit 30: ~178x faster.
- Full recommendation pipeline test using the real recipe dataset completed in roughly
  3–6 seconds for limits of 60, 100, and 300 in the test environment.

Timing will vary by machine, but the large repeated-work bottleneck has been removed.
