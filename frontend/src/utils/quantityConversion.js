const UNIT_ALIASES = {
  tsp: "tsp", teaspoon: "tsp", teaspoons: "tsp",
  tbsp: "tbsp", tablespoon: "tbsp", tablespoons: "tbsp",
  c: "cup", cup: "cup", cups: "cup",
  ml: "ml", milliliter: "ml", milliliters: "ml",
  l: "l", liter: "l", liters: "l",
  gal: "gallon", gallon: "gallon", gallons: "gallon",
  oz: "oz", ounce: "oz", ounces: "oz",
  lb: "lb", lbs: "lb", pound: "lb", pounds: "lb",
  g: "g", gram: "g", grams: "g",
  kg: "kg", kilogram: "kg", kilograms: "kg",
  unit: "unit", "<unit>": "unit", item: "unit", items: "unit", each: "unit",
  serving: "serving", servings: "serving",
  egg: "unit", eggs: "unit", piece: "unit", pieces: "unit",
  slice: "slice", slices: "slice",
  clove: "clove", cloves: "clove",
  dozen: "dozen", dozens: "dozen",
};

const WEIGHT_TO_GRAMS = { g: 1, kg: 1000, oz: 28.349523125, lb: 453.59237 };
const VOLUME_TO_ML = { tsp: 4.92892159375, tbsp: 14.78676478125, cup: 236.5882365, ml: 1, l: 1000, gallon: 3785.411784 };
const COUNT_UNITS = new Set(["unit", "slice", "clove", "dozen"]);

// Conservative fallback densities in grams per milliliter. These are used only
// when the recipe row has no usable gram weight and the ingredient is common.
const DENSITY_G_PER_ML = {
  "all purpose flour": 0.528,
  flour: 0.528,
  sugar: 0.845,
  "brown sugar": 0.93,
  butter: 0.959,
  milk: 1.03,
  "olive oil": 0.91,
  "vegetable oil": 0.92,
  rice: 0.78,
  oats: 0.36,
  cheddar: 0.47,
  parmesan: 0.41,
};

export function normalizeUnit(value) {
  const key = String(value || "").trim().toLowerCase().replace(/\.$/, "");
  return UNIT_ALIASES[key] || key;
}

export function unitFamily(unit) {
  const normalized = normalizeUnit(unit);
  if (WEIGHT_TO_GRAMS[normalized]) return "weight";
  if (VOLUME_TO_ML[normalized]) return "volume";
  if (COUNT_UNITS.has(normalized)) return "count";
  return "unknown";
}

export function formatSmartQuantity(value, maxDigits = 2) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) < 0.005) return "0";
  const rounded = Number(n.toFixed(maxDigits));
  return String(rounded);
}

export function displayUnit(unit, quantity = 2) {
  const normalized = normalizeUnit(unit);
  const singular = Math.abs(Number(quantity) - 1) < 1e-9;
  const labels = {
    tsp: singular ? "tsp" : "tsp",
    tbsp: singular ? "tbsp" : "tbsp",
    cup: singular ? "cup" : "cups",
    ml: "ml", l: "L", gallon: singular ? "gallon" : "gallons",
    g: "g", kg: "kg", oz: "oz", lb: "lb",
    unit: singular ? "item" : "items",
    slice: singular ? "slice" : "slices",
    clove: singular ? "clove" : "cloves",
    dozen: singular ? "dozen" : "dozen",
  };
  return labels[normalized] || unit || (singular ? "item" : "items");
}

function countToBase(quantity, unit) {
  const normalized = normalizeUnit(unit);
  if (normalized === "dozen") return quantity * 12;
  if (["unit", "slice", "clove"].includes(normalized)) return quantity;
  return null;
}

function baseToCount(quantity, unit) {
  const normalized = normalizeUnit(unit);
  if (normalized === "dozen") return quantity / 12;
  if (["unit", "slice", "clove"].includes(normalized)) return quantity;
  return null;
}

function ingredientDensity(name) {
  const key = String(name || "").trim().toLowerCase();
  if (DENSITY_G_PER_ML[key]) return DENSITY_G_PER_ML[key];
  return Object.entries(DENSITY_G_PER_ML).find(([candidate]) => key.includes(candidate))?.[1] || null;
}

/**
 * Convert a recipe-native amount into the unit stored for the pantry item.
 * The returned pantryAmount is what can safely be subtracted from pantry.quantity.
 */
export function convertRecipeAmountToPantry({ match, pantryItem, recipeAmount, scale = 1 }) {
  const recipeUnit = normalizeUnit(match?.recipe_measure);
  const pantryUnit = normalizeUnit(pantryItem?.unit);
  const amount = Number(recipeAmount);
  const scaledAmount = Number.isFinite(amount) ? amount * scale : null;
  const recipeFamily = unitFamily(recipeUnit);
  const pantryFamily = unitFamily(pantryUnit);
  const scaledWeightGrams = Number.isFinite(Number(match?.recipe_weight_grams))
    ? Number(match.recipe_weight_grams) * scale
    : null;

  if (!Number.isFinite(scaledAmount) || scaledAmount < 0 || !pantryUnit) {
    return { comparable: false, confidence: "manual", reason: "Recipe quantity or pantry unit is missing." };
  }

  if (recipeFamily === "weight" && pantryFamily === "weight") {
    const grams = scaledAmount * WEIGHT_TO_GRAMS[recipeUnit];
    return { comparable: true, confidence: "exact", pantryAmount: grams / WEIGHT_TO_GRAMS[pantryUnit] };
  }

  if (recipeFamily === "volume" && pantryFamily === "volume") {
    const ml = scaledAmount * VOLUME_TO_ML[recipeUnit];
    return { comparable: true, confidence: "exact", pantryAmount: ml / VOLUME_TO_ML[pantryUnit] };
  }

  if (recipeFamily === "count" && pantryFamily === "count") {
    const baseCount = countToBase(scaledAmount, recipeUnit);
    const pantryAmount = baseCount == null ? null : baseToCount(baseCount, pantryUnit);
    if (pantryAmount != null) return { comparable: true, confidence: "exact", pantryAmount, baseCount };
  }

  // The recipe dataset includes an estimated gram weight for many volume/count
  // ingredients. This is ideal for cases such as 2 tbsp flour from a 6 lb bag.
  if (pantryFamily === "weight" && scaledWeightGrams != null && scaledWeightGrams >= 0) {
    return {
      comparable: true,
      confidence: recipeFamily === "weight" ? "exact" : "estimated",
      pantryAmount: scaledWeightGrams / WEIGHT_TO_GRAMS[pantryUnit],
      weightGrams: scaledWeightGrams,
      reason: recipeFamily === "weight" ? undefined : "Converted using the recipe dataset's gram estimate.",
    };
  }

  // Conservative density fallback for volume <-> weight only.
  const density = ingredientDensity(match?.normalized_ingredient || match?.recipe_ingredient || pantryItem?.item_name);
  if (density && recipeFamily === "volume" && pantryFamily === "weight") {
    const ml = scaledAmount * VOLUME_TO_ML[recipeUnit];
    const grams = ml * density;
    return { comparable: true, confidence: "estimated", pantryAmount: grams / WEIGHT_TO_GRAMS[pantryUnit], weightGrams: grams, reason: "Estimated with an ingredient-specific density profile." };
  }

  if (density && recipeFamily === "weight" && pantryFamily === "volume") {
    const grams = scaledAmount * WEIGHT_TO_GRAMS[recipeUnit];
    const ml = grams / density;
    return { comparable: true, confidence: "estimated", pantryAmount: ml / VOLUME_TO_ML[pantryUnit], weightGrams: grams, reason: "Estimated with an ingredient-specific density profile." };
  }

  return {
    comparable: false,
    confidence: "manual",
    reason: `Smart Pantry cannot safely convert ${match?.recipe_measure || "the recipe unit"} to ${pantryItem?.unit || "the pantry unit"}.`,
  };
}

export function recommendedStep(unit) {
  const normalized = normalizeUnit(unit);
  if (["unit", "slice", "clove"].includes(normalized)) return 1;
  if (normalized === "dozen") return 1 / 12;
  if (["tsp", "tbsp"].includes(normalized)) return 0.25;
  if (normalized === "cup") return 0.25;
  if (["g", "ml"].includes(normalized)) return 5;
  if (["kg", "lb", "l", "gallon"].includes(normalized)) return 0.1;
  if (normalized === "oz") return 0.25;
  return 0.25;
}

// Phase 18.10: kitchen-friendly quantity helpers. These helpers keep the
// database quantity untouched while presenting counts people actually cook
// with (eggs, slices, strips, patties, etc.). Estimates are always labelled.
const KITCHEN_COUNT_PROFILES = [
  { test: /\begg(s)?\b/i, unit: "egg", plural: "eggs" },
  { test: /\b(lunch ?meat|deli ?meat|turkey slices?|ham slices?)\b/i, unit: "slice", plural: "slices", ozPerUnit: 0.75 },
  { test: /\bbacon\b/i, unit: "strip", plural: "strips", ozPerUnit: 1.0 },
  { test: /\b(burger|hamburger|beef) patt(y|ies)\b/i, unit: "patty", plural: "patties", ozPerUnit: 4 },
  { test: /\b(chicken breast|pork chop|lamb chop)s?\b/i, unit: "piece", plural: "pieces", ozPerUnit: 6 },
  { test: /\b(tortilla|wrap)s?\b/i, unit: "piece", plural: "pieces" },
  { test: /\bbread\b/i, unit: "slice", plural: "slices" },
];

function profileForIngredient(name) {
  const text = String(name || "");
  return KITCHEN_COUNT_PROFILES.find((profile) => profile.test.test(text)) || null;
}

export function kitchenUnitOptions(name, recipeUnit) {
  const profile = profileForIngredient(name);
  if (profile) return [profile.unit];
  const family = unitFamily(recipeUnit);
  if (family === "volume") return ["tsp", "tbsp", "cup", "ml"];
  if (family === "weight") return ["oz", "lb", "g"];
  return [normalizeUnit(recipeUnit || "unit")];
}

export function kitchenUnitLabel(unit, quantity = 2) {
  const singular = Math.abs(Number(quantity) - 1) < 1e-9;
  const labels = {
    egg: singular ? "egg" : "eggs",
    strip: singular ? "strip" : "strips",
    patty: singular ? "patty" : "patties",
    piece: singular ? "piece" : "pieces",
    slice: singular ? "slice" : "slices",
  };
  return labels[unit] || displayUnit(unit, quantity);
}

export function pantryKitchenDisplay(pantryItem) {
  const quantity = Number(pantryItem?.quantity);
  const unit = normalizeUnit(pantryItem?.unit);
  const name = pantryItem?.item_name || pantryItem?.display_name || "";
  const profile = profileForIngredient(name);
  if (!Number.isFinite(quantity)) return null;

  if (profile?.unit === "egg" && unit === "dozen") {
    return { amount: quantity * 12, unit: "egg", confidence: "exact", secondary: `${formatSmartQuantity(quantity)} dozen` };
  }
  if (profile && profile.unit === "slice" && unit === "slice") {
    return { amount: quantity, unit: "slice", confidence: "exact" };
  }
  if (profile && ["unit"].includes(unit)) {
    return { amount: quantity, unit: profile.unit, confidence: "exact" };
  }
  if (profile?.ozPerUnit && unit === "oz") {
    return { amount: quantity / profile.ozPerUnit, unit: profile.unit, confidence: "estimated", secondary: `${formatSmartQuantity(quantity)} oz package` };
  }
  if (profile?.ozPerUnit && unit === "lb") {
    return { amount: quantity * 16 / profile.ozPerUnit, unit: profile.unit, confidence: "estimated", secondary: `${formatSmartQuantity(quantity)} lb package` };
  }
  return { amount: quantity, unit, confidence: "exact" };
}

export function convertKitchenAmountToPantry({ pantryItem, ingredientName, kitchenAmount, kitchenUnit }) {
  const amount = Number(kitchenAmount);
  const pantryUnit = normalizeUnit(pantryItem?.unit);
  const profile = profileForIngredient(ingredientName || pantryItem?.item_name);
  if (!Number.isFinite(amount) || amount < 0) return { comparable: false, confidence: "manual" };

  if (profile?.unit === "egg" && kitchenUnit === "egg" && pantryUnit === "dozen") {
    return { comparable: true, confidence: "exact", pantryAmount: amount / 12 };
  }
  if (profile && kitchenUnit === profile.unit && pantryUnit === "unit") {
    return { comparable: true, confidence: "exact", pantryAmount: amount };
  }
  if (profile && kitchenUnit === profile.unit && pantryUnit === "slice" && profile.unit === "slice") {
    return { comparable: true, confidence: "exact", pantryAmount: amount };
  }
  if (profile?.ozPerUnit && kitchenUnit === profile.unit && pantryUnit === "oz") {
    return { comparable: true, confidence: "estimated", pantryAmount: amount * profile.ozPerUnit, reason: `Estimated at about ${profile.ozPerUnit} oz per ${profile.unit}.` };
  }
  if (profile?.ozPerUnit && kitchenUnit === profile.unit && pantryUnit === "lb") {
    return { comparable: true, confidence: "estimated", pantryAmount: amount * profile.ozPerUnit / 16, reason: `Estimated at about ${profile.ozPerUnit} oz per ${profile.unit}.` };
  }
  return null;
}

export function smartRecipeAmountEstimate({ recipeName, ingredientName, servings = 1 }) {
  const recipe = String(recipeName || "").toLowerCase();
  const ingredient = String(ingredientName || "").toLowerCase();
  const s = Math.max(1, Number(servings) || 1);

  if (/egg/.test(ingredient)) {
    const perServing = /(scrambl|omelet|omelette|egg sandwich|breakfast)/.test(recipe) ? 2 : 1;
    return { amount: perServing * s, unit: "egg", confidence: "estimated", reason: "Smart estimate based on this type of egg dish and serving count." };
  }
  if (/bread/.test(ingredient) && /(sandwich|toast)/.test(recipe)) {
    return { amount: 2 * s, unit: "slice", confidence: "estimated", reason: "Smart estimate based on two bread slices per serving." };
  }
  if (/(lunch ?meat|deli ?meat|turkey|ham)/.test(ingredient) && /sandwich/.test(recipe)) {
    return { amount: 3 * s, unit: "slice", confidence: "estimated", reason: "Smart estimate based on a typical sandwich portion." };
  }
  if (/bacon/.test(ingredient)) return { amount: 2 * s, unit: "strip", confidence: "estimated", reason: "Smart estimate based on a typical bacon portion." };
  if (/(burger|hamburger).*patt|ground beef patt/.test(ingredient)) return { amount: 1 * s, unit: "patty", confidence: "estimated", reason: "Smart estimate based on one patty per serving." };
  if (/(chicken breast|pork chop|lamb chop)/.test(ingredient)) return { amount: 1 * s, unit: "piece", confidence: "estimated", reason: "Smart estimate based on one piece per serving." };
  if (/butter/.test(ingredient)) return { amount: 1 * s, unit: "tbsp", confidence: "estimated", reason: "Smart estimate; adjust if your recipe uses more or less." };
  if (/milk/.test(ingredient)) return { amount: 2 * s, unit: "tbsp", confidence: "estimated", reason: "Smart estimate for cooking; adjust if needed." };
  return null;
}

// Phase 18.12: participant-selected per-ingredient kitchen quantities.
// The user chooses an amount and unit for each ingredient after selecting
// "I made this". Smart Pantry converts that selection into the pantry item's
// stored unit before subtraction. Unsafe cross-family conversions are blocked.
export const PARTICIPANT_UNIT_OPTIONS = [
  { value: "tsp", label: "teaspoon(s)" },
  { value: "tbsp", label: "tablespoon(s)" },
  { value: "cup", label: "cup(s)" },
  { value: "oz", label: "ounce(s)" },
  { value: "lb", label: "pound(s)" },
  { value: "g", label: "gram(s)" },
  { value: "kg", label: "kilogram(s)" },
  { value: "ml", label: "milliliter(s)" },
  { value: "l", label: "liter(s)" },
  { value: "gallon", label: "gallon(s)" },
  { value: "unit", label: "item(s)" },
  { value: "serving", label: "serving(s)" },
  { value: "slice", label: "slice(s)" },
  { value: "piece", label: "piece(s)" },
  { value: "egg", label: "egg(s)" },
  { value: "strip", label: "strip(s)" },
  { value: "patty", label: "patty/patties" },
  { value: "clove", label: "clove(s)" },
  { value: "dozen", label: "dozen" },
];

function profileUnitMatchesSelection(profile, selectedUnit) {
  if (!profile) return false;
  if (selectedUnit === profile.unit) return true;
  if (profile.unit === "piece" && selectedUnit === "unit") return true;
  if (profile.unit === "egg" && selectedUnit === "unit") return true;
  return false;
}

export function participantUnitOptions(ingredientName, pantryUnit, suggestedUnit) {
  const profile = profileForIngredient(ingredientName);
  const preferred = [];
  const add = (unit) => {
    const normalized = normalizeUnit(unit);
    const special = ["egg", "strip", "patty", "piece", "serving"].includes(unit) ? unit : normalized;
    if (special && !preferred.includes(special)) preferred.push(special);
  };

  if (suggestedUnit) add(suggestedUnit);
  if (profile?.unit) add(profile.unit);
  add(pantryUnit);

  for (const option of PARTICIPANT_UNIT_OPTIONS) add(option.value);
  return preferred.map((value) => PARTICIPANT_UNIT_OPTIONS.find((option) => option.value === value) || {
    value,
    label: kitchenUnitLabel(value, 2),
  });
}

export function convertParticipantAmountToPantry({ pantryItem, ingredientName, amount, selectedUnit }) {
  const numericAmount = Number(amount);
  const pantryUnit = normalizeUnit(pantryItem?.unit);
  const rawSelected = String(selectedUnit || "").trim().toLowerCase();
  const selected = ["egg", "strip", "patty", "piece", "serving"].includes(rawSelected)
    ? rawSelected
    : normalizeUnit(rawSelected);
  const profile = profileForIngredient(ingredientName || pantryItem?.item_name);

  if (!Number.isFinite(numericAmount) || numericAmount < 0 || !pantryUnit || !selected) {
    return { comparable: false, confidence: "manual", reason: "Choose a valid amount and unit." };
  }

  // Exact same-unit subtraction.
  if (selected === pantryUnit) {
    return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
  }

  // Standard weight conversions.
  if (WEIGHT_TO_GRAMS[selected] && WEIGHT_TO_GRAMS[pantryUnit]) {
    const grams = numericAmount * WEIGHT_TO_GRAMS[selected];
    return { comparable: true, confidence: "exact", pantryAmount: grams / WEIGHT_TO_GRAMS[pantryUnit] };
  }

  // Standard volume conversions.
  if (VOLUME_TO_ML[selected] && VOLUME_TO_ML[pantryUnit]) {
    const ml = numericAmount * VOLUME_TO_ML[selected];
    return { comparable: true, confidence: "exact", pantryAmount: ml / VOLUME_TO_ML[pantryUnit] };
  }

  // Ingredient-aware count/package handling.
  if (/\begg(s)?\b/i.test(String(ingredientName || pantryItem?.item_name || ""))) {
    if (["egg", "unit", "piece"].includes(selected) && pantryUnit === "dozen") {
      return { comparable: true, confidence: "exact", pantryAmount: numericAmount / 12 };
    }
    if (selected === "dozen" && pantryUnit === "unit") {
      return { comparable: true, confidence: "exact", pantryAmount: numericAmount * 12 };
    }
  }

  if (profileUnitMatchesSelection(profile, selected)) {
    if (pantryUnit === "unit") {
      return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
    }
    if (profile?.unit === "slice" && pantryUnit === "slice") {
      return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
    }
    if (profile?.ozPerUnit && pantryUnit === "oz") {
      return { comparable: true, confidence: "estimated", pantryAmount: numericAmount * profile.ozPerUnit, reason: `Estimated at about ${profile.ozPerUnit} oz per ${profile.unit}.` };
    }
    if (profile?.ozPerUnit && pantryUnit === "lb") {
      return { comparable: true, confidence: "estimated", pantryAmount: numericAmount * profile.ozPerUnit / 16, reason: `Estimated at about ${profile.ozPerUnit} oz per ${profile.unit}.` };
    }
  }

  // Slices and cloves are exact only when the pantry uses the same count unit.
  if (selected === "slice" && pantryUnit === "slice") {
    return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
  }
  if (selected === "clove" && pantryUnit === "clove") {
    return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
  }
  if (["unit", "piece"].includes(selected) && pantryUnit === "unit") {
    return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
  }
  if (selected === "serving" && pantryUnit === "serving") {
    return { comparable: true, confidence: "exact", pantryAmount: numericAmount };
  }

  // Ingredient-aware volume <-> weight conversion.
  const density = ingredientDensity(ingredientName || pantryItem?.item_name);
  if (density && VOLUME_TO_ML[selected] && WEIGHT_TO_GRAMS[pantryUnit]) {
    const ml = numericAmount * VOLUME_TO_ML[selected];
    const grams = ml * density;
    return {
      comparable: true,
      confidence: "estimated",
      pantryAmount: grams / WEIGHT_TO_GRAMS[pantryUnit],
      reason: "Estimated using an ingredient-specific kitchen conversion profile.",
    };
  }
  if (density && WEIGHT_TO_GRAMS[selected] && VOLUME_TO_ML[pantryUnit]) {
    const grams = numericAmount * WEIGHT_TO_GRAMS[selected];
    const ml = grams / density;
    return {
      comparable: true,
      confidence: "estimated",
      pantryAmount: ml / VOLUME_TO_ML[pantryUnit],
      reason: "Estimated using an ingredient-specific kitchen conversion profile.",
    };
  }

  return {
    comparable: false,
    confidence: "manual",
    reason: `Smart Pantry cannot safely convert ${kitchenUnitLabel(selected, numericAmount)} to ${displayUnit(pantryUnit, pantryItem?.quantity)} for this pantry item. Choose another unit.`,
  };
}
