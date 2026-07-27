import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import { participantUnitOptions, convertParticipantAmountToPantry, displayUnit, formatSmartQuantity } from "../utils/quantityConversion.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function listText(items) {
  if (!items || items.length === 0) {
    return "None";
  }

  return items
    .map((item) => (typeof item === "string" ? item : ingredientDisplayName(item)))
    .filter(Boolean)
    .join(", ") || "None";
}

function sourceLabel(recipe) {
  if (recipe.source_type === "core") {
    return "Quick Everyday Meal";
  }

  return "Expanded Recipe Library";
}

function sourceClass(recipe) {
  if (recipe.source_type === "core") {
    return "sourceCore";
  }

  return "sourceExpanded";
}

function scoreClass(score) {
  if (score >= 80) return "scoreHigh";
  if (score >= 60) return "scoreMedium";
  return "scoreLow";
}

function nutritionValue(recipe, key) {
  const value = recipe?.[key];

  if (value === null || value === undefined || value === "") {
    return null;
  }

  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? Math.round(numberValue * 10) / 10 : null;
}

function displayNumber(value, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  return `${value}${suffix}`;
}


function ingredientDisplayName(value) {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return "";

  return (
    value.display_name ||
    value.pantry_item_name ||
    value.pantry_name ||
    value.normalized_ingredient ||
    value.recipe_ingredient ||
    ""
  );
}

function percentFromComponent(component) {
  if (!component || typeof component !== "object") return null;
  const points = Number(component.points);
  const maxPoints = Number(component.max_points);
  if (!Number.isFinite(points) || !Number.isFinite(maxPoints) || maxPoints <= 0) return null;
  return Math.round((points / maxPoints) * 1000) / 10;
}

function normalizeRecommendationForUi(rawRecipe) {
  const recipe = rawRecipe || {};
  const matchedObjects = Array.isArray(recipe.matched_ingredients) ? recipe.matched_ingredients : [];
  const matchedNames = matchedObjects.map(ingredientDisplayName).filter(Boolean);
  const expiringObjects = Array.isArray(recipe.expiring_ingredients)
    ? recipe.expiring_ingredients
    : Array.isArray(recipe.expiring_items)
      ? recipe.expiring_items
      : [];
  const expiringNames = expiringObjects.map(ingredientDisplayName).filter(Boolean);

  const nutrition = recipe.nutrition || {};
  const perServing = nutrition.per_serving || {};
  const nutritionFit = recipe.nutrition_fit || {};
  const scoreDetails = recipe.smart_score_details || {};
  const breakdown = scoreDetails.breakdown || {};
  const practicality = breakdown.practicality || {};
  const preferenceFit = breakdown.preference_fit || {};

  const mainIngredients = Array.isArray(recipe.main_ingredients) ? recipe.main_ingredients : [];
  const missingIngredients = Array.isArray(recipe.missing_ingredients) ? recipe.missing_ingredients : [];
  const swaps = Array.isArray(recipe.smart_swaps) ? recipe.smart_swaps : [];
  const swappedMissing = new Set(
    swaps
      .map((swap) => normalizeText(swap?.needed || swap?.missing || ""))
      .filter(Boolean)
  );

  const matchedCount = matchedNames.length;
  const totalMain = Math.max(mainIngredients.length, matchedCount + missingIngredients.length, 1);
  const coveredWithSwaps = Math.min(totalMain, matchedCount + swappedMissing.size);
  const coverageWithSwaps = Math.round((coveredWithSwaps / totalMain) * 1000) / 10;

  let recommendationPhase = recipe.recommendation_phase;
  if (!recommendationPhase) {
    if (missingIngredients.length === 0) {
      recommendationPhase = expiringNames.length > 0 ? "Expiring First" : "Pantry Match";
    } else {
      recommendationPhase = "Almost There";
    }
  }

  const expiringDetails = expiringObjects.map((item) => {
    const itemName = ingredientDisplayName(item) || "Pantry item";
    const days = Number(item?.days_until_expiration);
    let label = "Use soon";
    if (Number.isFinite(days)) {
      if (days < 0) label = "Past date";
      else if (days === 0) label = "Use today";
      else if (days === 1) label = "1 day left";
      else label = `${days} days left`;
    }
    return { item_name: itemName, label, days };
  });

  const practicalityPercent = percentFromComponent(practicality);

  return {
    ...recipe,

    // Phase 18 modular API -> existing recommendation-page UI aliases.
    score: recipe.score ?? recipe.smart_score ?? scoreDetails.score ?? null,
    exact_pantry_match_percent:
      recipe.exact_pantry_match_percent ?? recipe.pantry_match_percent ?? null,
    coverage_with_smart_swaps_percent:
      recipe.coverage_with_smart_swaps_percent ?? coverageWithSwaps,
    ml_nutrition_fit_percent:
      recipe.ml_nutrition_fit_percent ?? nutritionFit.score_percent ?? null,
    ml_nutrition_fit:
      recipe.ml_nutrition_fit ?? nutritionFit.score_out_of_15 ?? null,
    meal_practicality_score:
      recipe.meal_practicality_score ?? practicalityPercent,
    everyday_recipe_fit:
      recipe.everyday_recipe_fit ?? recipe.everyday_fit_score ?? practicalityPercent,

    calories: recipe.calories ?? perServing.calories ?? nutrition.calories ?? null,
    protein: recipe.protein ?? perServing.protein ?? nutrition.protein ?? null,
    carbs: recipe.carbs ?? perServing.carbs ?? nutrition.carbs ?? null,
    fat: recipe.fat ?? perServing.fat ?? nutrition.fat ?? null,

    score_breakdown: recipe.score_breakdown || {
      pantry_match: breakdown.pantry_usefulness?.points,
      expiration_priority: breakdown.expiration_priority?.points,
      simplicity: practicality.simplicity_points,
      profile_fit: preferenceFit.points,
      nutrition_fit: breakdown.nutrition_fit?.points,
      missing_penalty: practicality.missing_penalty,
    },

    matched_ingredient_objects: matchedObjects,
    matched_ingredients: matchedNames,
    expiring_ingredient_objects: expiringObjects,
    expiring_items: expiringNames,
    expiring_details: recipe.expiring_details || expiringDetails,

    smart_meal_types:
      recipe.smart_meal_types || (Array.isArray(recipe.meal_types) ? recipe.meal_types : []),
    smart_primary_meal_type:
      recipe.smart_primary_meal_type || recipe.meal_types?.[0] || recipe.meal_type || "",
    meal_type: recipe.meal_type || recipe.meal_types?.[0] || "",
    dish_type: recipe.dish_type || recipe.dish_types?.[0] || "",

    recommendation_phase: recommendationPhase,
    best_meal_reasons: recipe.best_meal_reasons || recipe.reasons || [],

    // The new public contract currently does not expose legacy recipe-source metadata.
    // Leave any existing source_type intact; otherwise use the neutral expanded label.
    source_type: recipe.source_type || "expanded",
  };
}

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
}

function normalizeIngredientName(value) {
  const stopWords = new Set([
    "fresh", "frozen", "canned", "can", "package", "pkg", "cup", "cups", "tbsp",
    "tsp", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "chopped", "diced",
    "sliced", "shredded", "grated", "large", "small", "medium", "thin", "thick",
    "optional", "cooked", "uncooked", "boneless", "skinless", "ground", "whole",
    "pieces", "piece", "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds",
  ]);

  return String(value || "")
    .toLowerCase()
    .replace(/\([^)]*\)/g, " ")
    .replace(/\b\d+[\/\d.]*\b/g, " ")
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .map((word) => word.trim())
    .filter((word) => word && !stopWords.has(word))
    .map((word) => {
      if (word === "tomatoes") return "tomato";
      if (word === "potatoes") return "potato";
      if (word === "tortillas") return "tortilla";
      if (word === "eggs") return "egg";
      if (word.length > 4 && word.endsWith("ies")) return `${word.slice(0, -3)}y`;
      if (word.length > 3 && word.endsWith("es")) return word.slice(0, -2);
      if (word.length > 3 && word.endsWith("s") && !word.endsWith("ss")) return word.slice(0, -1);
      return word;
    })
    .join(" ")
    .trim();
}

function ingredientNamesMatch(pantryName, recipeIngredient) {
  const pantryClean = normalizeIngredientName(pantryName);
  const ingredientClean = normalizeIngredientName(recipeIngredient);

  if (!pantryClean || !ingredientClean) return false;
  if (pantryClean === ingredientClean) return true;
  if (pantryClean.includes(ingredientClean) || ingredientClean.includes(pantryClean)) return true;

  const pantryTokens = new Set(pantryClean.split(/\s+/).filter((token) => token.length > 2));
  const ingredientTokens = ingredientClean.split(/\s+/).filter((token) => token.length > 2);

  return ingredientTokens.some((token) => pantryTokens.has(token));
}

function cleanQuantity(value) {
  const number = Number(value || 0);
  if (Number.isNaN(number) || number < 0) return 0;
  return number;
}

function cleanDate(value) {
  if (!value) return "";
  return String(value).slice(0, 10);
}

function phaseClass(phase) {
  const clean = normalizeText(phase);

  if (clean.includes("expiring")) return "phaseExpiring";
  if (clean.includes("plan")) return "phasePlan";
  if (clean.includes("pantry")) return "phaseFull";
  if (clean.includes("almost")) return "phaseAlmost";
  if (clean.includes("quick")) return "phaseQuick";

  return "phaseDefault";
}

function scoreBreakdownRows(recipe) {
  const breakdown = recipe.score_breakdown || {};

  return [
    ["Pantry match", breakdown.pantry_match],
    ["Expiration priority", breakdown.expiration_priority],
    ["Simplicity", breakdown.simplicity],
    ["Profile fit", breakdown.profile_fit],
    ["Nutrition fit", breakdown.nutrition_fit],
    ["Missing penalty", breakdown.missing_penalty],
  ].filter((row) => row[1] !== undefined && row[1] !== null);
}

function findPantryMatches(recipe, pantryItems) {
  const matchedIngredients = recipe.matched_ingredients || [];
  const seenIds = new Set();
  const matches = [];

  matchedIngredients.forEach((ingredient) => {
    const pantryItem = pantryItems.find((item) =>
      !seenIds.has(item.id) && ingredientNamesMatch(item.item_name, ingredient)
    );

    if (pantryItem) {
      seenIds.add(pantryItem.id);
      matches.push(pantryItem);
    }
  });

  return matches;
}

function buildUsageRows(recipe, pantryItems) {
  return findPantryMatches(recipe, pantryItems).map((item) => ({
    item_id: item.id,
    item_name: item.item_name,
    current_quantity: item.quantity ?? 0,
    unit: item.unit || "item",
    amount_used: "",
    selected_unit: item.unit || "item",
  }));
}

function buildUsedIngredientSummary(usageRows, pantryItems) {
  return usageRows
    .filter((row) => row.item_id && cleanQuantity(row.amount_used) > 0)
    .map((row) => {
      const pantryItem = pantryItems.find((item) => item.id === row.item_id);
      if (!pantryItem) return null;
      const selectedUnit = row.selected_unit || pantryItem.unit || "item";
      return `${pantryItem.item_name}: ${row.amount_used} ${displayUnit(selectedUnit, row.amount_used)} used`;
    })
    .filter(Boolean);
}

export default function Recommendations() {
  const user = getUser();
  const [recommendations, setRecommendations] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  const [pantryItems, setPantryItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState({});
  const [filter, setFilter] = useState("all");
  const [mealTypeFilter, setMealTypeFilter] = useState("all");
  const [usageByRecipe, setUsageByRecipe] = useState({});
  const [selectedSmartSwaps, setSelectedSmartSwaps] = useState({});
  const [customSwapForms, setCustomSwapForms] = useState({});
  const [customMealName, setCustomMealName] = useState("");
  const [customMealNotes, setCustomMealNotes] = useState("");
  const [customUsageRows, setCustomUsageRows] = useState([
    { item_id: "", amount_used: "" },
  ]);
  const [expandedRecipes, setExpandedRecipes] = useState({});
  const [customMealOpen, setCustomMealOpen] = useState(false);
  const [extraFiltersOpen, setExtraFiltersOpen] = useState(false);
  const [mealUsageModal, setMealUsageModal] = useState(null);
  const [mealUsageAction, setMealUsageAction] = useState("made");

  async function loadPantryItems() {
    const pantry = await api.getPantry(user.id);
    setPantryItems(pantry || []);
    return pantry || [];
  }

  useEffect(() => {
    loadPantryItems().catch(() => {
      setError("Could not load pantry items for ingredient tracking.");
    });
  }, []);

  function normalizeSmartSwapText(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function findPantryItemForSwap(swap) {
    const swapName = swap.use_instead || swap.substitute || swap.useInstead || "";
    const cleanSwapName = normalizeSmartSwapText(swapName);

    if (!cleanSwapName) {
      return null;
    }

    return pantryItems.find((item) => {
      const cleanItemName = normalizeSmartSwapText(item.item_name || item.name || "");

      if (!cleanItemName) {
        return false;
      }

      return (
        cleanItemName === cleanSwapName ||
        cleanItemName.includes(cleanSwapName) ||
        cleanSwapName.includes(cleanItemName)
      );
    });
  }

  function getSelectedSwapsForRecipe(recipe) {
    return selectedSmartSwaps[recipe.recipe_name] || [];
  }

  function buildSmartSwapNotes(recipe) {
    const swaps = getSelectedSwapsForRecipe(recipe);

    if (!swaps.length) {
      return "";
    }

    return swaps
      .map((swap) => {
        const needed = swap.needed || swap.missing || "missing ingredient";
        const useInstead = swap.use_instead || swap.substitute || "selected pantry item";
        const source = swap.custom ? "Participant custom swap" : "Suggested Smart Swap";
        return `${source}: ${useInstead} used instead of ${needed}`;
      })
      .join("; ");
  }

  function buildActionNotes(recipe) {
    const typedNote = feedback[recipe.recipe_name] || "";
    const swapNote = buildSmartSwapNotes(recipe);

    if (typedNote && swapNote) {
      return `${typedNote}\nSmart Swap Used: ${swapNote}`;
    }

    if (swapNote) {
      return `Smart Swap Used: ${swapNote}`;
    }

    return typedNote;
  }

  function selectSmartSwap(recipe, swap) {
    const pantryItem = findPantryItemForSwap(swap);
    const needed = swap.needed || swap.missing || "the missing ingredient";
    const useInstead = swap.use_instead || swap.substitute || swap.useInstead || "";

    if (!pantryItem) {
      setError(`I could not find ${useInstead} in this pantry account. Add it to My Pantry first, then select the swap again.`);
      return;
    }

    setError("");
    setMessage(`Suggested smart swap selected: use ${useInstead} instead of ${needed}. Enter the amount used, then click Made Meal or Used Elsewhere.`);

    setSelectedSmartSwaps((previous) => {
      const current = previous[recipe.recipe_name] || [];
      const exists = current.some((item) => {
        const currentNeeded = item.needed || item.missing || "";
        const currentUseInstead = item.use_instead || item.substitute || "";
        return (
          normalizeSmartSwapText(currentNeeded) === normalizeSmartSwapText(needed) &&
          normalizeSmartSwapText(currentUseInstead) === normalizeSmartSwapText(useInstead)
        );
      });

      if (exists) {
        return previous;
      }

      return {
        ...previous,
        [recipe.recipe_name]: [...current, swap],
      };
    });

    setUsageByRecipe((previous) => {
      const currentRows = previous[recipe.recipe_name] || [];
      const alreadyAdded = currentRows.some((row) => row.item_id === pantryItem.id);

      if (alreadyAdded) {
        return previous;
      }

      const swapRow = {
        item_id: pantryItem.id,
        item_name: pantryItem.item_name || pantryItem.name || useInstead,
        amount_used: "",
        unit: pantryItem.unit || "item",
        selected_unit: pantryItem.unit || "item",
        current_quantity: pantryItem.quantity ?? pantryItem.current_quantity ?? "",
      };

      return {
        ...previous,
        [recipe.recipe_name]: [...currentRows, swapRow],
      };
    });
  }

  function updateCustomSwapForm(recipeName, field, value) {
    setCustomSwapForms((previous) => ({
      ...previous,
      [recipeName]: {
        needed: "",
        pantryItemId: "",
        note: "",
        ...(previous[recipeName] || {}),
        [field]: value,
      },
    }));
  }

  function addCustomSmartSwap(recipe) {
    const form = customSwapForms[recipe.recipe_name] || {};
    const pantryItem = pantryItems.find((item) => item.id === form.pantryItemId);
    const needed = String(form.needed || "").trim();

    if (!needed || !pantryItem) {
      setError("Choose the missing ingredient and the pantry item you want to use as your swap.");
      return;
    }

    const useInstead = pantryItem.item_name || pantryItem.name || "selected pantry item";
    const customSwap = {
      needed,
      use_instead: useInstead,
      reason: form.note
        ? `Participant chose this swap: ${form.note}`
        : "Participant chose this pantry item as their own swap.",
      custom: true,
      source: "participant_custom",
    };

    setError("");
    setMessage(`Custom smart swap added: use ${useInstead} instead of ${needed}. Enter the amount used, then click Made Meal or Used Elsewhere.`);

    setSelectedSmartSwaps((previous) => {
      const current = previous[recipe.recipe_name] || [];
      const exists = current.some((item) => {
        const currentNeeded = item.needed || item.missing || "";
        const currentUseInstead = item.use_instead || item.substitute || "";
        return (
          normalizeSmartSwapText(currentNeeded) === normalizeSmartSwapText(needed) &&
          normalizeSmartSwapText(currentUseInstead) === normalizeSmartSwapText(useInstead)
        );
      });

      if (exists) {
        return previous;
      }

      return {
        ...previous,
        [recipe.recipe_name]: [...current, customSwap],
      };
    });

    setUsageByRecipe((previous) => {
      const currentRows = previous[recipe.recipe_name] || [];
      const alreadyAdded = currentRows.some((row) => row.item_id === pantryItem.id);

      if (alreadyAdded) {
        return previous;
      }

      const swapRow = {
        item_id: pantryItem.id,
        item_name: useInstead,
        amount_used: "",
        unit: pantryItem.unit || "item",
        selected_unit: pantryItem.unit || "item",
        current_quantity: pantryItem.quantity ?? pantryItem.current_quantity ?? "",
      };

      return {
        ...previous,
        [recipe.recipe_name]: [...currentRows, swapRow],
      };
    });

    setCustomSwapForms((previous) => ({
      ...previous,
      [recipe.recipe_name]: { needed: "", pantryItemId: "", note: "" },
    }));
  }

  async function generate() {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const pantry = await loadPantryItems();
      const data = await api.generateRecommendations(user.id);
      const meals = (data.recommendations || []).map(normalizeRecommendationForUi);
      setRecommendations(meals);
      setCurrentSessionId(data?.metadata?.session_id || "");

      const nextUsage = {};
      meals.forEach((recipe) => {
        nextUsage[recipe.recipe_name] = buildUsageRows(recipe, pantry);
      });
      setUsageByRecipe(nextUsage);

      if (!data.recommendations || data.recommendations.length === 0) {
        setMessage("No recommendations found yet. Add more pantry items and try again.");
      } else {
        setMessage(`Smart Pantry found ${meals.length} ranked meal option(s). Expiring items and pantry matches are shown first.`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function changeFeedback(recipeName, value) {
    setFeedback((prev) => ({
      ...prev,
      [recipeName]: value,
    }));
  }

  function changeUsage(recipeName, itemId, value) {
    setUsageByRecipe((prev) => ({
      ...prev,
      [recipeName]: (prev[recipeName] || []).map((row) =>
        row.item_id === itemId
          ? {
              ...row,
              amount_used: value,
            }
          : row
      ),
    }));
  }

  function changeUsageUnit(recipeName, itemId, value) {
    setUsageByRecipe((prev) => ({
      ...prev,
      [recipeName]: (prev[recipeName] || []).map((row) =>
        row.item_id === itemId
          ? {
              ...row,
              selected_unit: value,
            }
          : row
      ),
    }));
  }

  function openMealUsageModal(recipe, actionName = "made") {
    setError("");
    setMessage("");
    setMealUsageAction(actionName);
    setMealUsageModal(recipe);
  }

  function closeMealUsageModal() {
    setMealUsageModal(null);
    setMealUsageAction("made");
  }

  function changeCustomUsage(index, field, value) {
    setCustomUsageRows((prev) =>
      prev.map((row, rowIndex) =>
        rowIndex === index
          ? {
              ...row,
              [field]: value,
            }
          : row
      )
    );
  }

  function addCustomUsageRow() {
    setCustomUsageRows((prev) => [...prev, { item_id: "", amount_used: "" }]);
  }

  function removeCustomUsageRow(indexToRemove) {
    setCustomUsageRows((prev) => prev.filter((_row, index) => index !== indexToRemove));
  }

  async function updatePantryAmounts(usageRows) {
    const rowsToUpdate = usageRows.filter(
      (row) => row.item_id && cleanQuantity(row.amount_used) > 0
    );

    for (const row of rowsToUpdate) {
      const pantryItem = pantryItems.find((item) => item.id === row.item_id);
      if (!pantryItem) continue;

      const conversion = convertParticipantAmountToPantry({
        pantryItem,
        ingredientName: row.item_name || pantryItem.item_name,
        amount: row.amount_used,
        selectedUnit: row.selected_unit || pantryItem.unit,
      });

      if (!conversion.comparable) {
        throw new Error(
          `${pantryItem.item_name}: ${conversion.reason || "Choose a measurement that can be converted to the pantry quantity."}`
        );
      }

      const currentQuantity = cleanQuantity(pantryItem.quantity);
      const amountUsedInPantryUnit = cleanQuantity(conversion.pantryAmount);
      const remainingQuantity = Math.max(currentQuantity - amountUsedInPantryUnit, 0);

      await api.updatePantryItem(pantryItem.id, {
        item_name: pantryItem.item_name,
        category: pantryItem.category,
        quantity: remainingQuantity,
        unit: pantryItem.unit,
        container_type: pantryItem.container_type,
        expiration_date: cleanDate(pantryItem.expiration_date),
        barcode: pantryItem.barcode || "",
        brand: pantryItem.brand || "",
        source: pantryItem.source || "",
        notes: pantryItem.notes || "",
      });
    }

    await loadPantryItems();
  }

  async function saveAction(recipe, actionName) {
    setMessage("");
    setError("");

    try {
      if (!currentSessionId) {
        throw new Error("Recommendation session is missing. Refresh meal recommendations and try again.");
      }

      if (!recipe?.recipe_id) {
        throw new Error("This recommendation is missing its recipe ID. Refresh meal recommendations and try again.");
      }

      const usageRows = usageByRecipe[recipe.recipe_name] || [];
      const usedIngredientSummary = buildUsedIngredientSummary(usageRows, pantryItems);

      // Save the recommendation action first using the current v1 backend contract.
      // This prevents pantry quantities from being deducted when action validation fails.
      await api.saveRecommendationAction({
        user_id: user.id,
        session_id: currentSessionId,
        recommendation_result_id: recipe.recommendation_result_id || null,
        recipe_id: recipe.recipe_id,
        recipe_name: recipe.recipe_name,
        action: actionName,
        smart_score: Number.isFinite(Number(recipe.smart_score))
          ? Number(recipe.smart_score)
          : Number.isFinite(Number(recipe.score))
            ? Number(recipe.score)
            : null,
        metadata: {
          feedback: buildActionNotes(recipe),
          used_ingredients:
            usedIngredientSummary.length > 0
              ? usedIngredientSummary
              : recipe.matched_ingredients || [],
        },
      });

      if ((actionName === "made" || actionName === "used_elsewhere") && usedIngredientSummary.length > 0) {
        await updatePantryAmounts(usageRows);
      }

      if (actionName === "made") {
        closeMealUsageModal();
        setMessage(
          usedIngredientSummary.length > 0
            ? `Saved: You made ${recipe.recipe_name}. Pantry amounts were updated.`
            : `Saved: You made ${recipe.recipe_name}.`
        );
      } else if (actionName === "used_elsewhere") {
        closeMealUsageModal();
        setMessage(
          usedIngredientSummary.length > 0
            ? `Saved: You used ingredients from ${recipe.recipe_name} somewhere else. Pantry amounts were updated.`
            : `Saved: You used ingredients from ${recipe.recipe_name} somewhere else.`
        );
      } else if (actionName === "saved") {
        setMessage(`Saved ${recipe.recipe_name} for later.`);
      } else {
        setMessage(`Saved: Did not use ${recipe.recipe_name}.`);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveCustomMeal(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!customMealName.trim()) {
      setError("Enter a meal name before saving your meal.");
      return;
    }

    const usedIngredientSummary = buildUsedIngredientSummary(customUsageRows, pantryItems);

    if (usedIngredientSummary.length === 0) {
      setError("Select at least one pantry item and enter the amount used.");
      return;
    }

    if (!currentSessionId) {
      setError("Generate meal recommendations first so this custom meal can be linked to the current recommendation session.");
      return;
    }

    try {
      const customName = customMealName.trim();
      const customRecipeId = `custom:${normalizeText(customName).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "meal"}`;

      await api.saveRecommendationAction({
        user_id: user.id,
        session_id: currentSessionId,
        recommendation_result_id: null,
        recipe_id: customRecipeId,
        recipe_name: customName,
        action: "custom_meal",
        smart_score: null,
        metadata: {
          feedback: customMealNotes,
          used_ingredients: usedIngredientSummary,
        },
      });

      await updatePantryAmounts(customUsageRows);

      setCustomMealName("");
      setCustomMealNotes("");
      setCustomUsageRows([{ item_id: "", amount_used: "" }]);
      setMessage("Custom meal saved. Pantry amounts were updated.");
    } catch (err) {
      setError(err.message);
    }
  }

  const filteredRecommendations = useMemo(() => {
    const phaseFiltered = (() => {
      if (filter === "core") return recommendations.filter((recipe) => recipe.source_type === "core");
      if (filter === "expanded") return recommendations.filter((recipe) => recipe.source_type === "expanded");
      if (filter === "expiring") return recommendations.filter((recipe) => recipe.expiring_items && recipe.expiring_items.length > 0);
      if (filter === "pantry") return recommendations.filter((recipe) => recipe.recommendation_phase === "Pantry Match" || ((recipe.missing_ingredients || []).length === 0 && Number(recipe.exact_pantry_match_percent || 0) >= 99));
      if (filter === "almost") return recommendations.filter((recipe) => recipe.recommendation_phase === "Almost There");
      return recommendations;
    })();

    if (mealTypeFilter === "all") return phaseFiltered;
    return phaseFiltered.filter((recipe) => {
      // Phase 18.15: use Smart Pantry's validated meal-context classification
      // instead of trusting the raw dataset meal_type/dish_type labels.
      const smartTypes = Array.isArray(recipe.smart_meal_types)
        ? recipe.smart_meal_types.map(normalizeText)
        : [normalizeText(recipe.smart_primary_meal_type || recipe.meal_type || recipe.dish_type)];

      if (mealTypeFilter === "quick") return smartTypes.includes("quick meal");
      if (mealTypeFilter === "dessert") return smartTypes.includes("dessert");
      return smartTypes.includes(mealTypeFilter);
    });
  }, [recommendations, filter, mealTypeFilter]);


  const expiringCount = recommendations.filter(
    (recipe) => recipe.expiring_items && recipe.expiring_items.length > 0
  ).length;

  const pantryReadyCount = recommendations.filter(
    (recipe) =>
      recipe.recommendation_phase === "Pantry Match" ||
      ((recipe.missing_ingredients || []).length === 0 &&
        Number(recipe.exact_pantry_match_percent || 0) >= 99)
  ).length;

  const almostThereCount = recommendations.filter(
    (recipe) => recipe.recommendation_phase === "Almost There"
  ).length;

  function toggleRecipe(recipeName) {
    setExpandedRecipes((previous) => ({
      ...previous,
      [recipeName]: !previous[recipeName],
    }));
  }

  function mealIcon(recipe) {
    const name = normalizeText(recipe.recipe_name);
    if (name.includes("soup") || name.includes("stew")) return "🍲";
    if (name.includes("salad")) return "🥗";
    if (name.includes("pasta") || name.includes("macaroni")) return "🍝";
    if (name.includes("rice")) return "🍚";
    if (name.includes("chicken") || name.includes("turkey")) return "🍗";
    if (name.includes("fish") || name.includes("salmon") || name.includes("tuna")) return "🐟";
    if (name.includes("breakfast") || name.includes("egg")) return "🍳";
    return "🍽️";
  }

  return (
    <div className="recommendationsPage optionCRecommendations">
      {loading && (
        <div className="mealLoadingOverlay" role="status" aria-live="polite">
          <div className="mealLoadingCard">
            <div className="loadingSpinner" />
            <h2>Smart Pantry is building your meal recommendations...</h2>
            <p>
              Checking pantry items, expiration dates, missing ingredients, profile preferences,
              Nutrition Fit, and Smart Score.
            </p>
          </div>
        </div>
      )}

      <header className="optionCHeader">
        <div>
          <span className="optionCBreadcrumb">⌂ &nbsp;/&nbsp; Meal Recommendations</span>
          <h1>Meal Recommendations</h1>
          <p>Delicious meal ideas based on your pantry and saved preferences.</p>
        </div>
        <button className="optionCFindButton" onClick={generate} disabled={loading}>
          {loading ? "Finding meals..." : "✨ Find Meal Recommendations ✨"}
        </button>
      </header>

      {message && <section className="card success optionCNotice">{message}</section>}
      {error && <section className="card error optionCNotice">{error}</section>}

      <section className="optionCStats" aria-label="Recommendation summary">
          <article><span className="blue">🥇</span><div><strong>{recommendations[0]?.score || "—"}</strong><small>Top recommendation score</small></div></article>
          <article><span className="orange">◷</span><div><strong>{expiringCount}</strong><small>Use expiring items</small></div></article>
          <article><span className="green">✓</span><div><strong>{pantryReadyCount}</strong><small>Pantry match</small></div></article>
          <article><span className="purple">☆</span><div><strong>{almostThereCount}</strong><small>Almost-there meals</small></div></article>
        </section>

      <section className="optionCFilterRow">
          <div className="optionCPrimaryFilters">
            <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>Best Matches</button>
            <button className={filter === "expiring" ? "active" : ""} onClick={() => setFilter("expiring")}>Use Soon First</button>
            <button className={filter === "pantry" ? "active" : ""} onClick={() => setFilter("pantry")}>Pantry Matches</button>
            <button className={filter === "almost" ? "active" : ""} onClick={() => setFilter("almost")}>Almost There</button>
          </div>
          <button className="optionCMoreFilters" onClick={() => setExtraFiltersOpen((open) => !open)}>
            ☰ Filters
          </button>
          {extraFiltersOpen && (
            <div className="optionCExtraFilters">
              <button className={filter === "core" ? "active" : ""} onClick={() => setFilter("core")}>Quick Everyday</button>
              <button className={filter === "expanded" ? "active" : ""} onClick={() => setFilter("expanded")}>Expanded Library</button>
              <label className="mealTypeFilterLabel">Meal type
                <select value={mealTypeFilter} onChange={(event) => setMealTypeFilter(event.target.value)}>
                  <option value="all">All meals</option>
                  <option value="breakfast">Breakfast</option>
                  <option value="lunch">Lunch</option>
                  <option value="dinner">Dinner</option>
                  <option value="quick">Quick meals</option>
                  <option value="brunch">Brunch</option>
                  <option value="snack">Snack</option>
                  <option value="dessert">Dessert</option>
                </select>
              </label>
            </div>
          )}
      </section>

      {recommendations.length > 0 && filter === "all" && mealTypeFilter === "all" && (
        <section className="topMealSpotlight" aria-label="Today's best meal">
          <div className="topMealBadge">🥇 Today's Best Meal</div>
          <div className="topMealContent">
            <div>
              <h2>{recommendations[0].recipe_name}</h2>
              <p>Why this is today's best choice:</p>
              <ul>{(recommendations[0].best_meal_reasons || []).map((reason) => <li key={reason}>✓ {reason}</li>)}</ul>
            </div>
            <div className="topMealScore"><small>Smart Score</small><strong>{recommendations[0].score}</strong><span>Practicality {displayNumber(recommendations[0].meal_practicality_score, "/100")}</span></div>
          </div>
        </section>
      )}

      <section className="optionCCustomMealPrompt">
        <span>Add your own meal to keep pantry usage and recommendation history accurate.</span>
        <button onClick={() => setCustomMealOpen((open) => !open)}>
          {customMealOpen ? "Close" : "Add My Own Meal"}
        </button>
      </section>

      {customMealOpen && (
        <section className="card customMealSection optionCCustomMealPanel">
          <div className="customMealIntro">
            <span className="customMealIcon" aria-hidden="true">+</span>
            <div>
              <span className="eyebrow">CUSTOM MEAL</span>
              <h2>Add My Own Meal</h2>
              <p>Record a meal Smart Pantry did not recommend and update the pantry ingredients you used.</p>
            </div>
          </div>

          <form className="customMealForm redesignedCustomMealForm" onSubmit={saveCustomMeal}>
            <div className="customMealTopFields">
              <label>Meal name
                <input value={customMealName} onChange={(e) => setCustomMealName(e.target.value)} placeholder="Example: Chicken rice bowl" />
              </label>
              <label>Notes <span>(optional)</span>
                <textarea value={customMealNotes} onChange={(e) => setCustomMealNotes(e.target.value)} placeholder="Add any useful details..." />
              </label>
            </div>
            <div className="usageRows">
              {customUsageRows.map((row, index) => {
                const selectedItem = pantryItems.find((item) => item.id === row.item_id);
                return (
                  <div className="usageRow" key={index}>
                    <select value={row.item_id} onChange={(e) => changeCustomUsage(index, "item_id", e.target.value)}>
                      <option value="">Select pantry item</option>
                      {pantryItems.map((item) => <option value={item.id} key={item.id}>{item.item_name} ({item.quantity} {item.unit || "item"} left)</option>)}
                    </select>
                    <input type="number" min="0" step="0.01" value={row.amount_used} onChange={(e) => changeCustomUsage(index, "amount_used", e.target.value)} placeholder="Amount used" />
                    <span>{selectedItem?.unit || "unit"}</span>
                    {customUsageRows.length > 1 && <button type="button" className="miniDelete" onClick={() => removeCustomUsageRow(index)}>Remove</button>}
                  </div>
                );
              })}
            </div>
            <div className="customMealActions">
              <button type="button" className="secondary" onClick={addCustomUsageRow}>Add Ingredient</button>
              <button type="submit">Save My Meal</button>
            </div>
          </form>
        </section>
      )}

      {recommendations.length === 0 && (
        <section className="optionCEmptyState" aria-label="No recommendations yet">
          <div className="optionCEmptyIcon" aria-hidden="true">🍲</div>
          <div className="optionCEmptyCopy">
            <span className="eyebrow">READY WHEN YOU ARE</span>
            <h2>No meal recommendations yet</h2>
            <p>
              Select <strong>Find Meal Recommendations</strong> to create ranked meal ideas
              from your current pantry.
            </p>
          </div>
          <div className="optionCEmptyActions">
            <button type="button" className="optionCEmptyPrimary" onClick={generate} disabled={loading}>
              {loading ? "Finding meals..." : "Find Meals"}
            </button>
            <button
              type="button"
              className="optionCEmptySecondary"
              onClick={() => { window.location.href = "/pantry"; }}
            >
              Go to My Pantry
            </button>
          </div>
        </section>
      )}

      <div className="optionCRecipeList">
        {filteredRecommendations.map((recipe, index) => {
          const expanded = Boolean(expandedRecipes[recipe.recipe_name]);
          return (
            <section className={`optionCRecipeCard ${expanded ? "expanded" : ""}`} key={`${recipe.recipe_name}-${index}`}>
              <button className="optionCRecipeSummary" onClick={() => toggleRecipe(recipe.recipe_name)} aria-expanded={expanded}>
                <span className="optionCMealIcon" aria-hidden="true">{mealIcon(recipe)}</span>
                <span className="optionCRecipeIdentity">
                  <span className={`phaseBadge ${phaseClass(recipe.recommendation_phase)}`}>{recipe.recommendation_phase || sourceLabel(recipe)}</span>
                  <strong>{recipe.recipe_name}</strong>
                  {recipe.expiring_items && recipe.expiring_items.length > 0 && <small>Uses expiring items within 10 days</small>}
                </span>
                <span className="optionCMetric"><small>Pantry match</small><strong>{displayNumber(recipe.exact_pantry_match_percent, "%")}</strong></span>
                <span className="optionCMetric"><small>Coverage with swaps</small><strong>{displayNumber(recipe.coverage_with_smart_swaps_percent, "%")}</strong></span>
                <span className="optionCMetric"><small>Nutrition Fit</small><strong>{displayNumber(recipe.ml_nutrition_fit_percent, "%")}</strong></span>
                <span className="optionCIngredients"><small><b>Matched:</b> {listText((recipe.matched_ingredients || []).slice(0, 4))}</small><small><b>Missing:</b> {listText((recipe.missing_ingredients || []).slice(0, 3))}</small></span>
                <span className={`optionCScore ${scoreClass(recipe.score)}`}><small>Smart Score</small><strong>{recipe.score}</strong></span>
                <span className="optionCChevron" aria-hidden="true">{expanded ? "⌃" : "⌄"}</span>
              </button>

              {expanded && (
                <div className="optionCRecipeDetails">
                  <div className="optionCDetailActions">
                    <button type="button" className="ghostButton" onClick={() => toggleRecipe(recipe.recipe_name)}>Hide Details</button>
                    <button onClick={() => openMealUsageModal(recipe, "made")}>Make This Meal</button>
                    <button className="secondary" onClick={() => saveAction(recipe, "saved")}>Save for Later</button>
                  </div>

                  <div className="nutritionFactsBox">
                    <div className="nutritionFactsHeader"><h3>Nutrition Facts</h3><span>Nutrition Fit: {displayNumber(recipe.ml_nutrition_fit, "/15")}</span></div>
                    <div className="nutritionGrid">
                      <div><strong>{displayNumber(nutritionValue(recipe, "calories"))}</strong><span>Calories</span></div>
                      <div><strong>{displayNumber(nutritionValue(recipe, "protein"), "g")}</strong><span>Protein</span></div>
                      <div><strong>{displayNumber(nutritionValue(recipe, "carbs"), "g")}</strong><span>Carbs</span></div>
                      <div><strong>{displayNumber(nutritionValue(recipe, "fat"), "g")}</strong><span>Fat</span></div>
                    </div>
                    <div className="mlEvidenceLine"><strong>Nutrition Fit:</strong> {displayNumber(recipe.ml_nutrition_fit_percent, "%")} based on calories, protein, carbs, fat, and ingredient count.</div>
                  </div>

                  {recipe.expiring_details && recipe.expiring_details.length > 0 && (
                    <div className="expiringBox"><strong>Use First:</strong><div className="expiringDetailGrid">{recipe.expiring_details.map((item) => <span key={`${recipe.recipe_name}-${item.item_name}`}>{item.item_name} — {item.label}</span>)}</div></div>
                  )}

                  <div className="recommendationEvidenceBox">
                    <h3>Recommendation Evidence</h3>
                    <div className="evidenceGrid">
                      <div><strong>{displayNumber(recipe.exact_pantry_match_percent, "%")}</strong><span>Exact pantry match</span></div>
                      <div><strong>{displayNumber(recipe.coverage_with_smart_swaps_percent, "%")}</strong><span>Coverage with swaps</span></div>
                      <div><strong>{displayNumber(recipe.everyday_recipe_fit, "/100")}</strong><span>Everyday recipe fit</span></div><div><strong>{displayNumber(recipe.meal_practicality_score, "/100")}</strong><span>Meal practicality</span></div>
                      <div><strong>{displayNumber(recipe.score, "/100")}</strong><span>Smart score</span></div>
                    </div>
                    {recipe.score_breakdown && <div className="scoreBreakdownBox"><h4>Smart Score Breakdown</h4><div className="scoreBreakdownGrid">{scoreBreakdownRows(recipe).map(([label, value]) => <span key={`${recipe.recipe_name}-${label}`}><strong>{label}</strong>{displayNumber(value)}</span>)}</div></div>}
                  </div>

                  <div className="ingredientColumns">
                    <div><h3>Matched Pantry Items</h3><div className="pillList goodPills">{(recipe.matched_ingredients || []).length === 0 ? <span>None</span> : recipe.matched_ingredients.map((item) => <span key={item}>{item}</span>)}</div></div>
                    <div><h3>Missing Ingredients</h3><div className="pillList missingPills">{(recipe.missing_ingredients || []).length === 0 ? <span>None</span> : recipe.missing_ingredients.map((item) => <span key={item}>{item}</span>)}</div></div>
                  </div>

                  {((recipe.smart_swaps && recipe.smart_swaps.length > 0) || (recipe.missing_ingredients || []).length > 0) && (
                    <div className="smartSwapCallout">
                      <strong>Smart Swap options available</strong>
                      <span>Choose Make This Meal to review swaps and enter the amounts you will actually use.</span>
                    </div>
                  )}

                  <details className="recipeDetails"><summary>View instructions</summary><p>{recipe.instructions || "No instructions available for this recipe yet."}</p></details>

                  <label className="feedbackLabel">Meal feedback or notes<textarea maxLength="250" placeholder="Share what happened with this recommendation." value={feedback[recipe.recipe_name] || ""} onChange={(e) => changeFeedback(recipe.recipe_name, e.target.value)} /></label>
                  <div className="buttonRow recommendationActions">
                    <button onClick={() => openMealUsageModal(recipe, "made")}>Make This Meal</button>
                    <button className="secondary" onClick={() => openMealUsageModal(recipe, "used_elsewhere")}>Used Elsewhere</button>
                    <button className="secondary" onClick={() => saveAction(recipe, "saved")}>Save for Later</button>
                    <button className="ghostButton" onClick={() => saveAction(recipe, "not_used")}>Did Not Use</button>
                  </div>
                </div>
              )}
            </section>
          );
        })}
        {recommendations.length > 0 && filteredRecommendations.length === 0 && (
          <section className="optionCNoFilterResults">
            <strong>No meals match this filter.</strong>
            <span>Try Best Matches or choose another filter.</span>
          </section>
        )}
      </div>


      {mealUsageModal && (() => {
        const recipe = mealUsageModal;
        const usageRows = usageByRecipe[recipe.recipe_name] || [];
        const selectedSwaps = getSelectedSwapsForRecipe(recipe);
        const hasSwapArea =
          (recipe.smart_swaps && recipe.smart_swaps.length > 0) ||
          (recipe.missing_ingredients || []).length > 0;

        return (
          <div className="mealUsageOverlay" role="dialog" aria-modal="true" aria-labelledby="meal-usage-title">
            <div className="mealUsageDialog">
              <div className="mealUsageHeader">
                <div>
                  <p className="eyebrow">{mealUsageAction === "made" ? "Make this meal" : "Ingredient usage"}</p>
                  <h2 id="meal-usage-title">{recipe.recipe_name}</h2>
                  <p>Choose what you actually used. Smart Pantry converts the amount back to the unit stored in My Pantry.</p>
                </div>
                <button type="button" className="mealUsageClose" onClick={closeMealUsageModal} aria-label="Close">×</button>
              </div>

              {hasSwapArea && (
                <section className="mealUsageSwapSection">
                  <div className="mealUsageSectionHeading">
                    <div>
                      <h3>Smart Swap</h3>
                      <p>Use a safe suggested swap, add your own, or leave the missing ingredient unchanged.</p>
                    </div>
                  </div>

                  {recipe.smart_swaps && recipe.smart_swaps.length > 0 && (
                    <div className="mealUsageSwapCards">
                      {recipe.smart_swaps.map((swap, swapIndex) => {
                        const alreadySelected = selectedSwaps.some((selected) =>
                          normalizeSmartSwapText(selected.needed || selected.missing) === normalizeSmartSwapText(swap.needed || swap.missing) &&
                          normalizeSmartSwapText(selected.use_instead || selected.substitute) === normalizeSmartSwapText(swap.use_instead || swap.substitute)
                        );
                        return (
                          <div className={`mealUsageSwapCard ${alreadySelected ? "selected" : ""}`} key={`${swap.needed}-${swap.use_instead}-${swapIndex}`}>
                            <div>
                              <strong>Use {swap.use_instead} for {swap.needed}</strong>
                              <span>{swap.reason}</span>
                            </div>
                            <button type="button" onClick={() => selectSmartSwap(recipe, swap)} disabled={alreadySelected}>
                              {alreadySelected ? "Selected" : "Use Swap"}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="mealUsageCustomSwap">
                    <strong>Add your own swap</strong>
                    <div className="mealUsageCustomSwapGrid">
                      <select value={(customSwapForms[recipe.recipe_name] || {}).needed || ""} onChange={(e) => updateCustomSwapForm(recipe.recipe_name, "needed", e.target.value)}>
                        <option value="">Ingredient to replace</option>
                        {(recipe.missing_ingredients || []).map((ingredient) => <option key={ingredient} value={ingredient}>{ingredient}</option>)}
                      </select>
                      <select value={(customSwapForms[recipe.recipe_name] || {}).pantryItemId || ""} onChange={(e) => updateCustomSwapForm(recipe.recipe_name, "pantryItemId", e.target.value)}>
                        <option value="">Pantry item to use instead</option>
                        {pantryItems.map((item) => <option key={item.id} value={item.id}>{item.item_name} ({item.quantity} {item.unit || "item"} left)</option>)}
                      </select>
                      <input value={(customSwapForms[recipe.recipe_name] || {}).note || ""} onChange={(e) => updateCustomSwapForm(recipe.recipe_name, "note", e.target.value)} placeholder="Optional note" />
                      <button type="button" onClick={() => addCustomSmartSwap(recipe)}>Add Swap</button>
                    </div>
                  </div>
                </section>
              )}

              <section className="mealUsageAmountSection">
                <div className="mealUsageSectionHeading">
                  <div>
                    <h3>How much did you use?</h3>
                    <p>Enter the amount in the measurement that makes sense to you for this meal.</p>
                  </div>
                </div>

                {usageRows.length === 0 ? (
                  <div className="mealUsageEmpty">No matched pantry ingredients are available to deduct for this recipe.</div>
                ) : (
                  <div className="mealUsageRows">
                    {usageRows.map((row) => {
                      const pantryItem = pantryItems.find((item) => item.id === row.item_id);
                      const selectedUnit = row.selected_unit || row.unit || pantryItem?.unit || "item";
                      const options = participantUnitOptions(row.item_name, pantryItem?.unit || row.unit, selectedUnit);
                      const conversion = cleanQuantity(row.amount_used) > 0 && pantryItem
                        ? convertParticipantAmountToPantry({
                            pantryItem,
                            ingredientName: row.item_name,
                            amount: row.amount_used,
                            selectedUnit,
                          })
                        : null;

                      return (
                        <div className="mealUsageRow" key={row.item_id}>
                          <div className="mealUsageIngredient">
                            <strong>{row.item_name}</strong>
                            <small>You have {formatSmartQuantity(row.current_quantity)} {displayUnit(row.unit, row.current_quantity)}</small>
                          </div>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            inputMode="decimal"
                            value={row.amount_used}
                            onChange={(e) => changeUsage(recipe.recipe_name, row.item_id, e.target.value)}
                            placeholder="Amount"
                            aria-label={`Amount of ${row.item_name} used`}
                          />
                          <select
                            value={selectedUnit}
                            onChange={(e) => changeUsageUnit(recipe.recipe_name, row.item_id, e.target.value)}
                            aria-label={`Unit used for ${row.item_name}`}
                          >
                            {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                          </select>
                          <div className={`mealUsageConversion ${conversion && !conversion.comparable ? "warning" : ""}`}>
                            {!conversion
                              ? <small>Nothing will be removed until you enter an amount.</small>
                              : conversion.comparable
                                ? <small>Removes about {formatSmartQuantity(conversion.pantryAmount)} {displayUnit(pantryItem?.unit, conversion.pantryAmount)} from My Pantry{conversion.confidence === "estimated" ? " (estimated)" : ""}.</small>
                                : <small>{conversion.reason}</small>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              <label className="mealUsageNotes">
                <span>Meal feedback or notes</span>
                <textarea
                  maxLength="250"
                  placeholder="Optional: what changed, what swap did you use, or anything you want to remember?"
                  value={feedback[recipe.recipe_name] || ""}
                  onChange={(e) => changeFeedback(recipe.recipe_name, e.target.value)}
                />
              </label>

              <div className="mealUsageActions">
                <button type="button" className="ghostButton" onClick={closeMealUsageModal}>Cancel</button>
                <button type="button" onClick={() => saveAction(recipe, mealUsageAction)}>
                  {mealUsageAction === "made" ? "Confirm Made Meal" : "Confirm Used Elsewhere"}
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      <button className="optionCHelpBar" type="button" onClick={() => setMessage("Smart Pantry ranks meals using pantry coverage, expiration priority, profile fit, simplicity, and Nutrition Fit.")}>💡 New here? See how recommendations work <span>›</span></button>
    </div>
  );
}
