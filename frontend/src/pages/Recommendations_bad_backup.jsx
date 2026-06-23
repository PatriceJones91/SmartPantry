import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
}

function cleanQuantity(value) {
  const number = Number(value || 0);
  if (Number.isNaN(number) || number < 0) return 0;
  return number;
}

function findMatchingPantryItems(recipe, pantryItems) {
  const matchedIngredients = recipe.matched_ingredients || [];

  if (matchedIngredients.length === 0) {
    return [];
  }

  return pantryItems.filter((item) => {
    const pantryName = normalizeText(item.item_name);

    return matchedIngredients.some((ingredient) => {
      const ingredientName = normalizeText(ingredient);
      return pantryName.includes(ingredientName) || ingredientName.includes(pantryName);
    });
  });
}

function buildUsedIngredientText(usageRows, pantryItems) {
  return usageRows
    .filter((row) => cleanQuantity(row.amount_used) > 0)
    .map((row) => {
      const pantryItem = pantryItems.find((item) => item.id === row.item_id);
      if (!pantryItem) return null;

      return `${pantryItem.item_name}: ${row.amount_used} ${pantryItem.unit || "item"}`;
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

  const [usageByRecipe, setUsageByRecipe] = useState({});
  const [customMealName, setCustomMealName] = useState("");
  const [customMealNotes, setCustomMealNotes] = useState("");
  const [customUsageRows, setCustomUsageRows] = useState([
    { item_id: "", amount_used: "" },
  ]);

  async function loadPantry() {
    const pantry = await api.getPantry(user.id);
    setPantryItems(pantry || []);
  }

  useEffect(() => {
    loadPantry().catch(() => {
      setError("Could not load pantry items. Make sure the backend is running.");
    });
  }, []);

  async function generate() {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const data = await api.generateRecommendations(user.id);
      const meals = data.recommendations || [];
      setRecommendations(meals);

      const nextUsage = {};

      meals.forEach((recipe) => {
        const matchingItems = findMatchingPantryItems(recipe, pantryItems);

        nextUsage[recipe.recipe_name] = matchingItems.map((item) => ({
          item_id: item.id,
          item_name: item.item_name,
          current_quantity: item.quantity,
          unit: item.unit || "item",
          amount_used: "",
        }));
      });

      setUsageByRecipe(nextUsage);
    } catch (err) {
      setError(err.message || "Could not generate recommendations.");
    } finally {
      setLoading(false);
    }
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

  async function updatePantryQuantities(usageRows) {
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
        expiration_date: pantryItem.expiration_date,
        barcode: pantryItem.barcode,
        brand: pantryItem.brand,
        source: pantryItem.source,
        notes: pantryItem.notes,
      });
    }

    await loadPantry();
  }

  async function saveRecommendationAction(recipe, actionName) {
    setMessage("");
    setError("");

    try {
      const usageRows = usageByRecipe[recipe.recipe_name] || [];
      const usedIngredients = buildUsedIngredientText(usageRows, pantryItems);

      if (actionName === "made" || actionName === "used_elsewhere") {
        await updatePantryQuantities(usageRows);
      }

      await api.saveRecommendationAction({
        user_id: user.id,
        recipe_name: recipe.recipe_name,
        action: actionName,
        score: recipe.score,
        feedback: "",
        used_ingredients: usedIngredients,
      });

      setMessage(
        actionName === "made"
          ? `Saved: ${recipe.recipe_name}. Pantry amounts were updated.`
          : `Saved action: ${actionName} for ${recipe.recipe_name}.`
      );
    } catch (err) {
      setError(err.message || "Could not save this meal action.");
    }
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
    setCustomUsageRows((prev) =>
      prev.filter((_row, index) => index !== indexToRemove)
    );
  }

  async function saveCustomMeal(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!customMealName.trim()) {
      setError("Enter a meal name before saving your meal.");
      return;
    }

    const usedIngredients = buildUsedIngredientText(customUsageRows, pantryItems);

    if (usedIngredients.length === 0) {
      setError("Add at least one pantry item and amount used for this meal.");
      return;
    }

    try {
      await updatePantryQuantities(customUsageRows);

      await api.saveRecommendationAction({
        user_id: user.id,
        recipe_name: customMealName.trim(),
        action: "custom_meal",
        score: null,
        feedback: customMealNotes,
        used_ingredients: usedIngredients,
      });

      setCustomMealName("");
      setCustomMealNotes("");
      setCustomUsageRows([{ item_id: "", amount_used: "" }]);
      setMessage("Custom meal saved. Pantry amounts were updated.");
    } catch (err) {
      setError(err.message || "Could not save custom meal.");
    }
  }

  const pantrySelectOptions = useMemo(() => {
    return pantryItems.map((item) => ({
      id: item.id,
      label: `${item.item_name} (${item.quantity} ${item.unit || "item"} left)`,
    }));
  }, [pantryItems]);

  return (
    <div className="recommendationsPage">
      <section className="surveyHero">
        <p className="eyebrow">Smart Pantry Meals</p>
        <h1>Meal Recommendations</h1>
        <p>
          Generate meal ideas from pantry items, then record how much of each
          ingredient was used so the pantry stays accurate.
        </p>
      </section>

      <section className="card recommendationControlCard">
        <button onClick={generate} disabled={loading}>
          {loading ? "Finding meals..." : "Find Meals"}
        </button>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card customMealCard">
        <h2>Add Your Own Meal</h2>
        <p>
          If you made a meal that was not recommended, add it here and record how
          much of each pantry item was used.
        </p>

        <form onSubmit={saveCustomMeal} className="customMealForm">
          <input
            value={customMealName}
            onChange={(e) => setCustomMealName(e.target.value)}
            placeholder="Meal name, example: Chicken rice bowl"
          />

          <textarea
            value={customMealNotes}
            onChange={(e) => setCustomMealNotes(e.target.value)}
            placeholder="Optional notes about what you made..."
          />

          <div className="usageRows">
            {customUsageRows.map((row, index) => {
              const selectedItem = pantryItems.find(
                (item) => item.id === row.item_id
              );

              return (
                <div className="usageRow" key={index}>
                  <select
                    value={row.item_id}
                    onChange={(e) =>
                      changeCustomUsage(index, "item_id", e.target.value)
                    }
                  >
                    <option value="">Select pantry item</option>
                    {pantrySelectOptions.map((option) => (
                      <option value={option.id} key={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>

                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={row.amount_used}
                    onChange={(e) =>
                      changeCustomUsage(index, "amount_used", e.target.value)
                    }
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
            <button type="button" className="ghostButton" onClick={addCustomUsageRow}>
              Add Ingredient
            </button>

            <button type="submit">Save My Meal</button>
          </div>
        </form>
      </section>

      <div className="recommendationGrid">
        {recommendations.map((recipe) => {
          const usageRows = usageByRecipe[recipe.recipe_name] || [];

          return (
            <section className="card recipeCard" key={recipe.recipe_name}>
              <div className="scoreBadge">{recipe.score}</div>

              <h2>{recipe.recipe_name}</h2>
              <p>{recipe.why}</p>

              <div className="meta">
                <span>{recipe.meal_type}</span>
                <span>{recipe.cuisine_type}</span>
                <span>{recipe.calories} cal</span>
                <span>{recipe.protein}g protein</span>
              </div>

              <details>
                <summary>View details</summary>
                <p>
                  <strong>Matched:</strong>{" "}
                  {(recipe.matched_ingredients || []).join(", ") || "None"}
                </p>
                <p>
                  <strong>Missing:</strong>{" "}
                  {(recipe.missing_ingredients || []).join(", ") || "None"}
                </p>
                <p>
                  <strong>Instructions:</strong> {recipe.instructions}
                </p>
              </details>

              <div className="ingredientUsageBox">
                <h3>Ingredient Amounts Used</h3>
                <p>
                  Enter how much was used before clicking Made Meal. This updates
                  what is left in the pantry.
                </p>

                {usageRows.length === 0 ? (
                  <div className="groceryEmpty">
                    No matched pantry ingredients were found for this meal.
                  </div>
                ) : (
                  <div className="usageRows">
                    {usageRows.map((row) => (
                      <div className="usageRow" key={row.item_id}>
                        <span className="usageIngredientName">
                          {row.item_name}
                        </span>

                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={row.amount_used}
                          onChange={(e) =>
                            changeUsage(
                              recipe.recipe_name,
                              row.item_id,
                              e.target.value
                            )
                          }
                          placeholder="Amount used"
                        />

                        <span>
                          {row.unit} used / {row.current_quantity} {row.unit} left
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="buttonRow">
                <button onClick={() => saveRecommendationAction(recipe, "made")}>
                  Made Meal
                </button>

                <button
                  className="secondary"
                  onClick={() => saveRecommendationAction(recipe, "saved")}
                >
                  Save
                </button>

                <button
                  className="ghostButton"
                  onClick={() => saveRecommendationAction(recipe, "used_elsewhere")}
                >
                  Used Elsewhere
                </button>

                <button
                  className="ghostButton"
                  onClick={() => saveRecommendationAction(recipe, "not_used")}
                >
                  Did Not Use
                </button>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
