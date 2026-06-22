import { useMemo, useState } from "react";
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

export default function Recommendations() {
  const user = getUser();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState({});
  const [filter, setFilter] = useState("all");

  async function generate() {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const data = await api.generateRecommendations(user.id);
      setRecommendations(data.recommendations || []);

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

  async function saveAction(recipe, actionName) {
    setMessage("");
    setError("");

    try {
      await api.saveRecommendationAction({
        user_id: user.id,
        recipe_name: recipe.recipe_name,
        action: actionName,
        score: recipe.score,
        feedback: feedback[recipe.recipe_name] || "",
        used_ingredients: recipe.matched_ingredients || [],
      });

      if (actionName === "made") {
        setMessage(`Saved: You made ${recipe.recipe_name}.`);
      } else if (actionName === "used_elsewhere") {
        setMessage(`Saved: You used ingredients from ${recipe.recipe_name} somewhere else.`);
      } else if (actionName === "saved") {
        setMessage(`Saved ${recipe.recipe_name} for later.`);
      } else {
        setMessage(`Saved: Did not use ${recipe.recipe_name}.`);
      }
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

            {recipe.expiring_items && recipe.expiring_items.length > 0 && (
              <div className="expiringBox">
                <strong>Use First:</strong> {listText(recipe.expiring_items)}
              </div>
            )}

            <div className="ingredientColumns">
              <div>
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
