import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function actionLabel(action) {
  const labels = {
    made: "Made Meal",
    used_elsewhere: "Used Elsewhere",
    saved: "Saved for Later",
    not_used: "Did Not Use",
  };

  return labels[action] || action || "Unknown";
}

function actionClass(action) {
  const classes = {
    made: "historyMade",
    used_elsewhere: "historyUsedElsewhere",
    saved: "historySaved",
    not_used: "historyNotUsed",
  };

  return classes[action] || "historyNotUsed";
}

function formatDate(value) {
  if (!value) return "N/A";

  try {
    return new Date(value).toLocaleString();
  } catch {
    return "N/A";
  }
}

function parseUsedIngredients(value) {
  if (!value) return [];

  if (Array.isArray(value)) {
    return value;
  }

  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);

      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch {
      return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    }
  }

  return [];
}

export default function History() {
  const user = getUser();
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadHistory() {
    setMessage("");
    setError("");

    try {
      const data = await api.getRecommendationHistory(user.id);
      setLogs(data || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadHistory();
  }, [user.id]);

  const filteredLogs = useMemo(() => {
    if (filter === "all") {
      return logs;
    }

    return logs.filter((log) => log.action === filter);
  }, [logs, filter]);

  const summary = useMemo(() => {
    return {
      total: logs.length,
      made: logs.filter((log) => log.action === "made").length,
      usedElsewhere: logs.filter((log) => log.action === "used_elsewhere").length,
      saved: logs.filter((log) => log.action === "saved").length,
      notUsed: logs.filter((log) => log.action === "not_used").length,
    };
  }, [logs]);

  return (
    <div>
      <div className="pageHeader historyHero">
        <div>
          <h1>Recommendation History</h1>
          <p>
            This page tracks what happened after a recommendation was shown.
            It supports the study by showing whether participants made the meal,
            used ingredients somewhere else, saved it, or did not use it.
          </p>
        </div>

        <button onClick={loadHistory}>Refresh History</button>
      </div>

      {message && <section className="card success">{message}</section>}
      {error && <section className="card error">{error}</section>}

      <section className="card historySummary">
        <div>
          <strong>{summary.total}</strong>
          <span>Total actions</span>
        </div>
        <div className="historyMade">
          <strong>{summary.made}</strong>
          <span>Made meal</span>
        </div>
        <div className="historyUsedElsewhere">
          <strong>{summary.usedElsewhere}</strong>
          <span>Used elsewhere</span>
        </div>
        <div className="historySaved">
          <strong>{summary.saved}</strong>
          <span>Saved for later</span>
        </div>
        <div className="historyNotUsed">
          <strong>{summary.notUsed}</strong>
          <span>Did not use</span>
        </div>
      </section>

      <section className="card filterBar">
        <button
          className={filter === "all" ? "activeFilter" : "secondary"}
          onClick={() => setFilter("all")}
        >
          All
        </button>
        <button
          className={filter === "made" ? "activeFilter" : "secondary"}
          onClick={() => setFilter("made")}
        >
          Made Meal
        </button>
        <button
          className={filter === "used_elsewhere" ? "activeFilter" : "secondary"}
          onClick={() => setFilter("used_elsewhere")}
        >
          Used Elsewhere
        </button>
        <button
          className={filter === "saved" ? "activeFilter" : "secondary"}
          onClick={() => setFilter("saved")}
        >
          Saved for Later
        </button>
        <button
          className={filter === "not_used" ? "activeFilter" : "secondary"}
          onClick={() => setFilter("not_used")}
        >
          Did Not Use
        </button>
      </section>

      {filteredLogs.length === 0 ? (
        <section className="card">
          <h2>No history yet</h2>
          <p>
            Go to Meal Recommendations, click Find Meals, and save an action such as
            Made Meal or Used Elsewhere. The action will show here.
          </p>
        </section>
      ) : (
        <div className="historyGrid">
          {filteredLogs.map((log) => {
            const usedIngredients = parseUsedIngredients(log.used_ingredients);

            return (
              <section
                className={`card historyCard ${actionClass(log.action)}`}
                key={log.id || `${log.recipe_name}-${log.created_at}`}
              >
                <div className="historyCardTop">
                  <span className="historyActionBadge">
                    {actionLabel(log.action)}
                  </span>
                  <span className="historyScore">
                    Smart Score: {log.score ?? "N/A"}
                  </span>
                </div>

                <h2>{log.recipe_name}</h2>

                <div className="historyMeta">
                  <span>{formatDate(log.created_at)}</span>
                </div>

                {usedIngredients.length > 0 && (
                  <div>
                    <h3>Used / matched ingredients</h3>
                    <div className="pillList">
                      {usedIngredients.map((ingredient) => (
                        <span key={ingredient}>{ingredient}</span>
                      ))}
                    </div>
                  </div>
                )}

                {log.feedback && (
                  <div className="historyFeedback">
                    <h3>Feedback / notes</h3>
                    <p>{log.feedback}</p>
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
