import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function listText(items) {
  if (!items || items.length === 0) {
    return "None";
  }

  return items.join(", ");
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

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
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

function findPantryMatches(recipe, pantryItems) {
  const matchedIngredients = recipe.matched_ingredients || [];

  return pantryItems.filter((pantryItem) => {
    const pantryName = normalizeText(pantryItem.item_name);

    return matchedIngredients.some((ingredient) => {
      const ingredientName = normalizeText(ingredient);
      return pantryName.includes(ingredientName) || ingredientName.includes(pantryName);
    });
  });
}

function buildUsageRows(recipe, pantryItems) {
  return findPantryMatches(recipe, pantryItems).map((item) => ({
    item_id: item.id,
    item_name: item.item_name,
    current_quantity: item.quantity ?? 0,
    unit: item.unit || "item",
    amount_used: "",
  }));
}

function buildUsedIngredientSummary(usageRows, pantryItems) {
  return usageRows
    .filter((row) => row.item_id && cleanQuantity(row.amount_used) > 0)
    .map((row) => {
      const pantryItem = pantryItems.find((item) => item.id === row.item_id);
      if (!pantryItem) return null;
      return `${pantryItem.item_name}: ${row.amount_used} ${pantryItem.unit || "item"} used`;
    })
    .filter(Boolean);
}

export default function Recommendations() {
  const user = getUser();
  const [recommendations, setRecommendations] = useState([]);
  const [pantryItems, setPantryItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState({});
  const [filter, setFilter] = useState("all");
  const [usageByRecipe, setUsageByRecipe] = useState({});
  const [selectedSmartSwaps, setSelectedSmartSwaps] = useState({});
  const [customMealName, setCustomMealName] = useState("");
  const [customMealNotes, setCustomMealNotes] = useState("");
  const [customUsageRows, setCustomUsageRows] = useState([
    { item_id: "", amount_used: "" },
  ]);

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
        return `${useInstead} used instead of ${needed}`;
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
    setMessage(`Smart swap selected: use ${useInstead} instead of ${needed}. Enter the amount used, then click Made Meal or Used Elsewhere.`);

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
        current_quantity: pantryItem.quantity ?? pantryItem.current_quantity ?? "",
      };

      return {
        ...previous,
        [recipe.recipe_name]: [...currentRows, swapRow],
      };
    });
  }


  async function generate() {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const pantry = await loadPantryItems();
      const data = await api.generateRecommendations(user.id);
      const meals = data.recommendations || [];
      setRecommendations(meals);

      const nextUsage = {};
      meals.forEach((recipe) => {
        nextUsage[recipe.recipe_name] = buildUsageRows(recipe, pantry);
      });
      setUsageByRecipe(nextUsage);

      if (!data.recommendations || data.recommendations.length === 0) {
        setMessage("No recommendations found yet. Add more pantry items and try again.");
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

      const currentQuantity = cleanQuantity(pantryItem.quantity);
      const amountUsed = cleanQuantity(row.amount_used);
      const remainingQuantity = Math.max(currentQuantity - amountUsed, 0);

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
      const usageRows = usageByRecipe[recipe.recipe_name] || [];
      const usedIngredientSummary = buildUsedIngredientSummary(usageRows, pantryItems);

      if ((actionName === "made" || actionName === "used_elsewhere") && usedIngredientSummary.length > 0) {
        await updatePantryAmounts(usageRows);
      }

      await api.saveRecommendationAction({
        user_id: user.id,
        recipe_name: recipe.recipe_name,
        action: actionName,
        score: recipe.score,
        feedback: buildActionNotes(recipe),
        used_ingredients:
          usedIngredientSummary.length > 0
            ? usedIngredientSummary
            : recipe.matched_ingredients || [],
      });

      if (actionName === "made") {
        setMessage(
          usedIngredientSummary.length > 0
            ? `Saved: You made ${recipe.recipe_name}. Pantry amounts were updated.`
            : `Saved: You made ${recipe.recipe_name}.`
        );
      } else if (actionName === "used_elsewhere") {
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

    try {
      await updatePantryAmounts(customUsageRows);

      await api.saveRecommendationAction({
        user_id: user.id,
        recipe_name: customMealName.trim(),
        action: "custom_meal",
        score: null,
        feedback: customMealNotes,
        used_ingredients: usedIngredientSummary,
      });

      setCustomMealName("");
      setCustomMealNotes("");
      setCustomUsageRows([{ item_id: "", amount_used: "" }]);
      setMessage("Custom meal saved. Pantry amounts were updated.");
    } catch (err) {
      setError(err.message);
    }
  }

  const filteredRecommendations = useMemo(() => {
    if (filter === "core") {
      return recommendations.filter((recipe) => recipe.source_type === "core");
    }

    if (filter === "expanded") {
      return recommendations.filter((recipe) => recipe.source_type === "expanded");
    }

    if (filter === "expiring") {
      return recommendations.filter(
        (recipe) => recipe.expiring_items && recipe.expiring_items.length > 0
      );
    }

    return recommendations;
  }, [recommendations, filter]);

  const coreCount = recommendations.filter((recipe) => recipe.source_type === "core").length;
  const expandedCount = recommendations.filter((recipe) => recipe.source_type === "expanded").length;
  const expiringCount = recommendations.filter(
    (recipe) => recipe.expiring_items && recipe.expiring_items.length > 0
  ).length;

  return (
    <div>
      <div className="pageHeader recommendationsHero">
        <div>
          <h1>Meal Recommendations</h1>
          <p>
            Smart Pantry uses both the quick everyday recipe set and the expanded recipe library.
            Expiring pantry items are prioritized first, but regular pantry items can still create meal ideas.
          </p>
        </div>

        <button onClick={generate} disabled={loading}>
          {loading ? "Finding meals..." : "Find Meals"}
        </button>
      </div>

      {message && <section className="card success">{message}</section>}
      {error && <section className="card error">{error}</section>}

      {recommendations.length > 0 && (
        <section className="card recommendationSummary">
          <div>
            <strong>{recommendations.length}</strong>
            <span>Total recommendations</span>
          </div>
          <div>
            <strong>{coreCount}</strong>
            <span>Quick everyday meals</span>
          </div>
          <div>
            <strong>{expandedCount}</strong>
            <span>Expanded recipe options</span>
          </div>
          <div>
            <strong>{expiringCount}</strong>
            <span>Use expiring items first</span>
          </div>
        </section>
      )}

      {recommendations.length > 0 && (
        <section className="card filterBar">
          <button
            className={filter === "all" ? "activeFilter" : "secondary"}
            onClick={() => setFilter("all")}
          >
            All
          </button>
          <button
            className={filter === "core" ? "activeFilter" : "secondary"}
            onClick={() => setFilter("core")}
          >
            Quick Everyday
          </button>
          <button
            className={filter === "expanded" ? "activeFilter" : "secondary"}
            onClick={() => setFilter("expanded")}
          >
            Expanded Library
          </button>
          <button
            className={filter === "expiring" ? "activeFilter" : "secondary"}
            onClick={() => setFilter("expiring")}
          >
            Expiring Items
          </button>
        </section>
      )}

      <section className="card customMealSection">
        <div className="customMealHeader">
          <div>
            <h2>Add My Own Meal</h2>
            <p>
              If you made something that was not recommended, save it here and record how much pantry food was used.
            </p>
          </div>
        </div>

        <form className="customMealForm" onSubmit={saveCustomMeal}>
          <input
            value={customMealName}
            onChange={(e) => setCustomMealName(e.target.value)}
            placeholder="Meal name, example: Chicken rice bowl"
          />

          <textarea
            value={customMealNotes}
            onChange={(e) => setCustomMealNotes(e.target.value)}
            placeholder="Optional notes about the meal..."
          />

          <div className="usageRows">
            {customUsageRows.map((row, index) => {
              const selectedItem = pantryItems.find((item) => item.id === row.item_id);

              return (
                <div className="usageRow" key={index}>
                  <select
                    value={row.item_id}
                    onChange={(e) => changeCustomUsage(index, "item_id", e.target.value)}
                  >
                    <option value="">Select pantry item</option>
                    {pantryItems.map((item) => (
                      <option value={item.id} key={item.id}>
                        {item.item_name} ({item.quantity} {item.unit || "item"} left)
                      </option>
                    ))}
                  </select>

                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={row.amount_used}
                    onChange={(e) => changeCustomUsage(index, "amount_used", e.target.value)}
                    placeholder="Amount used"
                  />

                  <span>{selectedItem?.unit || "unit"}</span>

                  {customUsageRows.length > 1 && (
                    <button
                      type="button"
                      className="miniDelete"
                      onClick={() => removeCustomUsageRow(index)}
                    >
                      Remove
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div className="customMealActions">
            <button type="button" className="secondary" onClick={addCustomUsageRow}>
              Add Ingredient
            </button>
            <button type="submit">Save My Meal</button>
          </div>
        </form>
      </section>

      {recommendations.length === 0 && (
        <section className="card">
          <h2>No meals generated yet</h2>
          <p>
            Click <strong>Find Meals</strong> to generate recipes from your pantry items.
            The system will use quick everyday meals first while still including expanded recipe options.
          </p>
        </section>
      )}

      <div className="recommendationGrid">
        {filteredRecommendations.map((recipe, index) => (
          <section className="card recipeCard upgradedRecipeCard" key={`${recipe.recipe_name}-${index}`}>
            <div className="recipeTopRow">
              <span className={`sourceBadge ${sourceClass(recipe)}`}>
                {sourceLabel(recipe)}
              </span>
              <span className={`scoreBadgeInline ${scoreClass(recipe.score)}`}>
                Smart Score: {recipe.score}
              </span>
            </div>

            <h2>{recipe.recipe_name}</h2>

            <p className="whyText">{recipe.why}</p>

            <div className="meta recipeMeta">
              {recipe.meal_type && <span>{recipe.meal_type}</span>}
              {recipe.cuisine_type && <span>{recipe.cuisine_type}</span>}
              {recipe.dish_type && <span>{recipe.dish_type}</span>}
              {recipe.cook_time && <span>{recipe.cook_time} min</span>}
              {recipe.calories && <span>{recipe.calories} cal</span>}
              {recipe.protein && <span>{recipe.protein}g protein</span>}
            </div>

            <div className="nutritionFactsBox">
              <div className="nutritionFactsHeader">
                <h3>Nutrition Facts</h3>
                <span>
                  Nutrition Fit: {displayNumber(recipe.ml_nutrition_fit, "/15")}
                </span>
              </div>

              <div className="nutritionGrid">
                <div>
                  <strong>{displayNumber(nutritionValue(recipe, "calories"))}</strong>
                  <span>Calories</span>
                </div>
                <div>
                  <strong>{displayNumber(nutritionValue(recipe, "protein"), "g")}</strong>
                  <span>Protein</span>
                </div>
                <div>
                  <strong>{displayNumber(nutritionValue(recipe, "carbs"), "g")}</strong>
                  <span>Carbs</span>
                </div>
                <div>
                  <strong>{displayNumber(nutritionValue(recipe, "fat"), "g")}</strong>
                  <span>Fat</span>
                </div>
              </div>

              <div className="mlEvidenceLine">
                <strong>Nutrition Fit Score:</strong>{" "}
                {displayNumber(recipe.ml_nutrition_fit_percent, "%")} based on calories, protein, carbs, fat, and ingredient count.
              </div>
            </div>


            {recipe.expiring_items && recipe.expiring_items.length > 0 && (
              <div className="expiringBox">
                <strong>Use First:</strong> {listText(recipe.expiring_items)}
              </div>
            )}

            <div className="ingredientColumns">
              <div>
  
              <div className="recommendationEvidenceBox">
                <h3>Recommendation Evidence</h3>

                <div className="evidenceGrid">
                  <div>
                    <strong>{displayNumber(recipe.exact_pantry_match_percent, "%")}</strong>
                    <span>Exact pantry match</span>
                  </div>
                  <div>
                    <strong>{displayNumber(recipe.coverage_with_smart_swaps_percent, "%")}</strong>
                    <span>Coverage with swaps</span>
                  </div>
                  <div>
                    <strong>{displayNumber(recipe.everyday_recipe_fit, "/100")}</strong>
                    <span>Everyday recipe fit</span>
                  </div>
                  <div>
                    <strong>{displayNumber(recipe.score, "/100")}</strong>
                    <span>Smart score</span>
                  </div>
                </div>

                {recipe.score_breakdown && (
                  <div className="scoreBreakdownLine">
                    <strong>Smart Score is based on:</strong>{" "}
                    pantry match, expiration priority, simplicity, profile fit, missing ingredients, and recipe source.
                  </div>
                )}
              </div>

              <h3>Matched Pantry Items</h3>
                <div className="pillList goodPills">
                  {(recipe.matched_ingredients || []).length === 0 ? (
                    <span>None</span>
                  ) : (
                    recipe.matched_ingredients.map((item) => (
                      <span key={item}>{item}</span>
                    ))
                  )}
                </div>
              </div>

              <div>
                
              {recipe.smart_swaps && recipe.smart_swaps.length > 0 && (
                <div className="smartSwapOptionsBox">
                  <h3>Smart Swap Options</h3>
                  <p>
                    These are possible pantry-based swaps. Review them before cooking to make sure they make sense for the meal.
                  </p>

                  <div className="smartSwapList">
                    {recipe.smart_swaps.map((swap, index) => (
                      <div className="smartSwapCard" key={`${swap.needed}-${swap.use_instead}-${index}`}>
                        <strong>
                          Use {swap.use_instead} for {swap.needed}
                        </strong>
                        <span>{swap.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

<h3>Missing Ingredients</h3>
                <div className="pillList missingPills">
                  {(recipe.missing_ingredients || []).length === 0 ? (
                    <span>None</span>
                  ) : (
                    recipe.missing_ingredients.map((item) => (
                      <span key={item}>{item}</span>
                    ))
                  )}
                </div>
              </div>
            </div>

            <details className="recipeDetails">
              <summary>View instructions</summary>
              <p>{recipe.instructions || "No instructions available for this recipe yet."}</p>
            </details>

            {(usageByRecipe[recipe.recipe_name] || []).length > 0 && (
              <div className="ingredientUsageMiniBox">
  
              {getSelectedSwapsForRecipe(recipe).length > 0 && (
                <div className="selectedSwapsBox">
                  <h3>Selected Smart Swaps</h3>
                  {getSelectedSwapsForRecipe(recipe).map((swap, index) => (
                    <div key={`${recipe.recipe_name}-selected-swap-${index}`} className="selectedSwapItem">
                      <strong>
                        {swap.use_instead || swap.substitute} used instead of {swap.needed || swap.missing}
                      </strong>
                    </div>
                  ))}
                </div>
              )}

              <h3>Amount Used</h3>
                <p>
                  Optional: enter the amount used before clicking Made Meal or Used Elsewhere. This updates the pantry amount left.
                </p>

                <div className="usageRows compactUsageRows">
                  {(usageByRecipe[recipe.recipe_name] || []).map((row) => (
                    <div className="usageRow compactUsageRow" key={row.item_id}>
                      <span className="usageIngredientName">{row.item_name}</span>

                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={row.amount_used}
                        onChange={(e) => changeUsage(recipe.recipe_name, row.item_id, e.target.value)}
                        placeholder="Used"
                      />

                      <span>
                        {row.unit} / {row.current_quantity} {row.unit} left
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <label className="feedbackLabel">
              Feedback / notes
              <textarea
                maxLength="250"
                placeholder="Example: I made this, I used the cheese somewhere else, or this meal was not realistic."
                value={feedback[recipe.recipe_name] || ""}
                onChange={(e) => changeFeedback(recipe.recipe_name, e.target.value)}
              />
            </label>

            <div className="buttonRow recommendationActions">
              <button onClick={() => saveAction(recipe, "made")}>
                Made Meal
              </button>
              <button className="secondary" onClick={() => saveAction(recipe, "used_elsewhere")}>
                Used Elsewhere
              </button>
              <button className="secondary" onClick={() => saveAction(recipe, "saved")}>
                Save for Later
              </button>
              <button className="ghostButton" onClick={() => saveAction(recipe, "not_used")}>
                Did Not Use
              </button>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
