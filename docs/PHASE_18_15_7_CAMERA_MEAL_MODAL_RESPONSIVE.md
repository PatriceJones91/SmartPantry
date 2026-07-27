# Phase 18.15.7 — Camera, Make This Meal Modal, and Responsive Layout

## Product barcode camera
The product barcode camera now opens the browser camera using `getUserMedia`, the same
camera-access path used by the working receipt camera. ZXing decodes the live stream after
permission has been granted. A generic webcam fallback is used when a device rejects the
rear-camera constraint.

## Make This Meal flow
Clicking **Make This Meal** now opens a focused modal instead of immediately recording the action.

The modal contains:
- suggested Smart Swaps when available;
- Add Your Own Swap;
- amount-used entry for each pantry ingredient;
- a measurement dropdown for each ingredient;
- conversion preview back to the unit stored in My Pantry;
- optional meal notes;
- final confirmation before pantry quantities are updated.

`Used Elsewhere` uses the same quantity modal.

## Quantity behavior
Participants can enter the measurement they actually used (for example 3 oz today and 1 cup
for a later recipe). The existing ingredient-aware conversion helper converts that amount back
to the pantry's stored unit before subtraction.

## Responsive behavior
Final responsive overrides were added for tablets and phones. The camera dialogs and meal-use
modal use viewport-relative sizing, stack controls on small screens, and avoid horizontal overflow.
