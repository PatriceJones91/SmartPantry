import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

const VARIABLE_MAP = {
  pre_pantry_awareness: "Pantry Awareness",
  post_pantry_awareness: "Pantry Awareness",
  pre_expiration_awareness: "Expiration Awareness",
  post_expiration_awareness: "Expiration Awareness",
  pre_ingredient_utilization: "Ingredient Utilization",
  post_ingredient_utilization: "Ingredient Utilization",
  pre_meal_planning_confidence: "Meal Planning Confidence",
  post_meal_planning_confidence: "Meal Planning Confidence",
  pre_current_method_easy: "Ease of Current Method",
  post_ease_of_use: "Ease of Use / Usability",
  post_recommendation_usefulness: "Recommendation Usefulness",
  post_recommendation_quality: "Recommendation Quality",
  post_overall_satisfaction: "User Satisfaction",
  post_continued_use: "Continued Use Intention",
};

function formatDate(value) {
  if (!value) return "N/A";

  try {
    return new Date(value).toLocaleString();
  } catch {
    return "N/A";
  }
}

function actionLabel(action) {
  const labels = {
    made: "Made Meal",
    used_elsewhere: "Used Elsewhere",
    saved: "Saved for Later",
    not_used: "Did Not Use",
    custom_meal: "Custom Meal",
  };

  return labels[action] || action || "Unknown";
}

function actionClass(action) {
  const classes = {
    made: "historyMade",
    used_elsewhere: "historyUsedElsewhere",
    saved: "historySaved",
    not_used: "historyNotUsed",
    custom_meal: "historyCustomMeal",
  };

  return classes[action] || "historyNotUsed";
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeJson(value) {
  if (!value) return null;
  if (typeof value === "object") return value;

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function getUserName(userMap, userId) {
  return userMap[userId] || userId || "Unknown";
}

function parseJsonPreview(value) {
  if (!value) return "N/A";

  const parsed = safeJson(value);

  if (Array.isArray(parsed)) {
    return parsed.slice(0, 4).join(", ");
  }

  if (parsed && typeof parsed === "object") {
    return Object.entries(parsed)
      .slice(0, 4)
      .map(([key, val]) => `${key}: ${val}`)
      .join(" | ");
  }

  return String(value);
}

function average(values) {
  const clean = values
    .map((value) => Number(value))
    .filter((value) => !Number.isNaN(value));

  if (clean.length === 0) return null;

  return clean.reduce((sum, value) => sum + value, 0) / clean.length;
}

function formatAverage(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(1);
}

function formatChange(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}`;
}

function formatUsedIngredients(value) {
  if (!value) return "N/A";

  const parsed = safeJson(value);

  if (Array.isArray(parsed)) {
    return parsed.join(", ");
  }

  if (parsed && typeof parsed === "object") {
    return Object.entries(parsed)
      .map(([key, val]) => `${key}: ${val}`)
      .join(", ");
  }

  return String(value);
}

function toCsvValue(value) {
  if (value === null || value === undefined) return "";

  const clean = typeof value === "object" ? JSON.stringify(value) : String(value);
  return `"${clean.replace(/"/g, '""')}"`;
}

function downloadCsv(filename, rows) {
  if (!rows || rows.length === 0) return;

  const headers = Object.keys(rows[0]);
  const lines = [
    headers.map(toCsvValue).join(","),
    ...rows.map((row) =>
      headers.map((header) => toCsvValue(row[header])).join(",")
    ),
  ];

  const blob = new Blob([lines.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function Admin() {
  const [summary, setSummary] = useState(null);
  const [users, setUsers] = useState([]);
  const [surveys, setSurveys] = useState([]);
  const [pantry, setPantry] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTable, setActiveTable] = useState("users");

  async function loadAdminData() {
    setLoading(true);
    setError("");

    try {
      const [summaryData, usersData, surveysData, pantryData, logsData] =
        await Promise.all([
          api.adminSummary(),
          api.adminUsers(),
          api.adminSurveys(),
          api.adminPantry(),
          api.adminLogs(),
        ]);

      setSummary(summaryData || {});
      setUsers(safeArray(usersData));
      setSurveys(safeArray(surveysData));
      setPantry(safeArray(pantryData));
      setLogs(safeArray(logsData));
    } catch (err) {
      setError(err.message || "Could not load admin data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAdminData();
  }, []);

  const userMap = useMemo(() => {
    const map = {};

    users.forEach((user) => {
      map[user.id] = user.username || user.id;
    });

    return map;
  }, [users]);

  const participantUsers = useMemo(() => {
    return users.filter((user) => user.role !== "admin");
  }, [users]);

  const surveySummary = useMemo(() => {
    const userSurveyMap = {};

    participantUsers.forEach((user) => {
      userSurveyMap[user.id] = {
        user_id: user.id,
        username: user.username,
        pre: false,
        post: false,
      };
    });

    surveys.forEach((survey) => {
      if (!userSurveyMap[survey.user_id]) {
        userSurveyMap[survey.user_id] = {
          user_id: survey.user_id,
          username: getUserName(userMap, survey.user_id),
          pre: false,
          post: false,
        };
      }

      if (survey.survey_type === "pre") {
        userSurveyMap[survey.user_id].pre = true;
      }

      if (survey.survey_type === "post") {
        userSurveyMap[survey.user_id].post = true;
      }
    });

    return Object.values(userSurveyMap);
  }, [participantUsers, surveys, userMap]);

  const metrics = useMemo(() => {
    const made = logs.filter((log) => log.action === "made").length;
    const usedElsewhere = logs.filter(
      (log) => log.action === "used_elsewhere"
    ).length;
    const saved = logs.filter((log) => log.action === "saved").length;
    const notUsed = logs.filter((log) => log.action === "not_used").length;
    const customMeal = logs.filter((log) => log.action === "custom_meal").length;

    const preComplete = surveySummary.filter((item) => item.pre).length;
    const postComplete = surveySummary.filter((item) => item.post).length;
    const activePantryItems = pantry.filter((item) => item.status !== "deleted");

    const positiveActions = made + usedElsewhere + saved + customMeal;
    const acceptanceRate =
      logs.length > 0 ? Math.round((positiveActions / logs.length) * 100) : 0;

    return {
      participants: participantUsers.length,
      totalUsers: users.length,
      preComplete,
      postComplete,
      pantryItems: activePantryItems.length,
      recommendationActions: logs.length,
      made,
      usedElsewhere,
      saved,
      notUsed,
      customMeal,
      acceptanceRate,
    };
  }, [users, participantUsers, surveySummary, pantry, logs]);

  const variableRows = useMemo(() => {
    const grouped = {};

    surveys.forEach((survey) => {
      const responses = safeJson(survey.responses);

      if (!responses || typeof responses !== "object") return;

      Object.entries(responses).forEach(([questionId, value]) => {
        const variable = VARIABLE_MAP[questionId];

        if (!variable) return;

        if (!grouped[variable]) {
          grouped[variable] = {
            variable,
            pre: [],
            post: [],
          };
        }

        if (questionId.startsWith("pre_")) {
          grouped[variable].pre.push(value);
        }

        if (questionId.startsWith("post_")) {
          grouped[variable].post.push(value);
        }
      });
    });

    return Object.values(grouped).map((row) => {
      const preAverage = average(row.pre);
      const postAverage = average(row.post);
      const change =
        preAverage !== null && postAverage !== null
          ? postAverage - preAverage
          : null;

      return {
        variable: row.variable,
        preAverage,
        postAverage,
        change,
      };
    });
  }, [surveys]);

  const recentLogs = useMemo(() => {
    return [...logs]
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 8);
  }, [logs]);

  function exportSurveys() {
    const rows = surveys.map((survey) => ({
      participant: getUserName(userMap, survey.user_id),
      survey_type: survey.survey_type,
      responses: survey.responses,
      comments: survey.comments,
      created_at: formatDate(survey.created_at),
    }));

    downloadCsv("smart_pantry_surveys.csv", rows);
  }

  function exportPantry() {
    const rows = pantry.map((item) => ({
      participant: getUserName(userMap, item.user_id),
      item_name: item.item_name,
      category: item.category,
      quantity: item.quantity,
      unit: item.unit,
      container_type: item.container_type,
      barcode: item.barcode,
      brand: item.brand,
      expiration_date: item.expiration_date,
      notes: item.notes,
    }));

    downloadCsv("smart_pantry_pantry_items.csv", rows);
  }

  function exportLogs() {
    const rows = logs.map((log) => ({
      participant: getUserName(userMap, log.user_id),
      recipe_name: log.recipe_name,
      action: actionLabel(log.action),
      score: log.score,
      used_ingredients: formatUsedIngredients(log.used_ingredients),
      feedback: log.feedback,
      created_at: formatDate(log.created_at),
    }));

    downloadCsv("smart_pantry_recommendation_logs.csv", rows);
  }

  function exportParticipants() {
    const rows = surveySummary.map((row) => ({
      participant: row.username,
      pre_survey: row.pre ? "Complete" : "Not Done",
      post_survey: row.post ? "Complete" : "Not Done",
      pantry_items: pantry.filter((item) => item.user_id === row.user_id).length,
      recommendation_actions: logs.filter((log) => log.user_id === row.user_id)
        .length,
    }));

    downloadCsv("smart_pantry_participant_activity.csv", rows);
  }

  return (
    <div className="adminPage">
      <section className="adminHeroCard">
        <div>
          <p className="eyebrow">Smart Pantry Admin</p>
          <h1>Admin Dashboard</h1>
          <p>
            This page gives the admin a study-level view of participants, pantry
            activity, survey completion, recommendation behavior, and ingredient
            use evidence.
          </p>
        </div>

        <button onClick={loadAdminData}>Refresh Admin Data</button>
      </section>

      {loading && <section className="card">Loading admin dashboard...</section>}
      {error && <section className="card error">{error}</section>}

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Outcome Summary</h2>
            <p>Quick overview of study participation and saved activity.</p>
          </div>
        </div>

        <div className="polishedAdminGrid">
          <div>
            <strong>{metrics.participants}</strong>
            <span>Participants</span>
          </div>
          <div>
            <strong>{metrics.preComplete}</strong>
            <span>Pre-study surveys</span>
          </div>
          <div>
            <strong>{metrics.postComplete}</strong>
            <span>Post-study surveys</span>
          </div>
          <div>
            <strong>{metrics.pantryItems}</strong>
            <span>Pantry items entered</span>
          </div>
          <div>
            <strong>{metrics.recommendationActions}</strong>
            <span>Recommendation actions</span>
          </div>
          <div>
            <strong>{metrics.acceptanceRate}%</strong>
            <span>Acceptance rate</span>
          </div>
        </div>
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Metrics</h2>
            <p>Behavior evidence from meal recommendation actions.</p>
          </div>
        </div>

        <div className="polishedActionGrid">
          <div className="adminActionCard madeCard">
            <strong>{metrics.made}</strong>
            <span>Made Meal</span>
          </div>
          <div className="adminActionCard usedCard">
            <strong>{metrics.usedElsewhere}</strong>
            <span>Used Elsewhere</span>
          </div>
          <div className="adminActionCard savedCard">
            <strong>{metrics.saved}</strong>
            <span>Saved for Later</span>
          </div>
          <div className="adminActionCard customCard">
            <strong>{metrics.customMeal}</strong>
            <span>Custom Meals</span>
          </div>
          <div className="adminActionCard notUsedCard">
            <strong>{metrics.notUsed}</strong>
            <span>Did Not Use</span>
          </div>
        </div>
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Survey Results by Variable</h2>
            <p>
              Pre/post averages help connect the questions to measurable study
              variables.
            </p>
          </div>
        </div>

        {variableRows.length === 0 ? (
          <div className="groceryEmpty">No survey variable data yet.</div>
        ) : (
          <div className="adminTableWrap">
            <table className="adminDataTable">
              <thead>
                <tr>
                  <th>Variable</th>
                  <th>Pre Average</th>
                  <th>Post Average</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                {variableRows.map((row) => (
                  <tr key={row.variable}>
                    <td>{row.variable}</td>
                    <td>{formatAverage(row.preAverage)}</td>
                    <td>{formatAverage(row.postAverage)}</td>
                    <td>{formatChange(row.change)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Export Study Data</h2>
            <p>Download CSV files for thesis charts and results analysis.</p>
          </div>
        </div>

        <div className="exportButtonGrid">
          <button onClick={exportSurveys}>Export Survey Data CSV</button>
          <button onClick={exportLogs}>Export Recommendation Logs CSV</button>
          <button onClick={exportPantry}>Export Pantry Data CSV</button>
          <button onClick={exportParticipants}>
            Export Participant Activity CSV
          </button>
        </div>
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Survey Completion by Participant</h2>
            <p>Tracks who has completed each study survey.</p>
          </div>
        </div>

        {surveySummary.length === 0 ? (
          <p>No participant survey records yet.</p>
        ) : (
          <div className="adminTableWrap">
            <table className="adminDataTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Pre-Study Survey</th>
                  <th>Post-Study Survey</th>
                  <th>Pantry Items</th>
                  <th>Recommendation Actions</th>
                </tr>
              </thead>
              <tbody>
                {surveySummary.map((row) => (
                  <tr key={row.user_id}>
                    <td>{row.username}</td>
                    <td>
                      <span
                        className={row.pre ? "statusComplete" : "statusMissing"}
                      >
                        {row.pre ? "Complete" : "Not Done"}
                      </span>
                    </td>
                    <td>
                      <span
                        className={row.post ? "statusComplete" : "statusMissing"}
                      >
                        {row.post ? "Complete" : "Not Done"}
                      </span>
                    </td>
                    <td>{pantry.filter((item) => item.user_id === row.user_id).length}</td>
                    <td>{logs.filter((log) => log.user_id === row.user_id).length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Recent Recommendation Evidence</h2>
            <p>Latest meal actions, feedback, and used ingredient evidence.</p>
          </div>
        </div>

        {recentLogs.length === 0 ? (
          <div className="groceryEmpty">No recommendation evidence yet.</div>
        ) : (
          <div className="recentEvidenceList">
            {recentLogs.map((log) => (
              <div className="recentEvidenceItem" key={log.id}>
                <div>
                  <span className={`adminActionBadge ${actionClass(log.action)}`}>
                    {actionLabel(log.action)}
                  </span>
                  <h3>{log.recipe_name}</h3>
                  <p>{getUserName(userMap, log.user_id)} • {formatDate(log.created_at)}</p>
                </div>

                <div>
                  <strong>Used / matched ingredients</strong>
                  <p>{formatUsedIngredients(log.used_ingredients)}</p>
                </div>

                <div>
                  <strong>Feedback</strong>
                  <p>{log.feedback || "N/A"}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Admin Evidence Tables</h2>
            <p>Raw evidence tables for users, surveys, pantry items, and logs.</p>
          </div>
        </div>

        <div className="filterBar adminFilterBar">
          <button
            className={activeTable === "users" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("users")}
          >
            Users
          </button>
          <button
            className={activeTable === "surveys" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("surveys")}
          >
            Surveys
          </button>
          <button
            className={activeTable === "pantry" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("pantry")}
          >
            Pantry Items
          </button>
          <button
            className={activeTable === "logs" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("logs")}
          >
            Recommendation Logs
          </button>
        </div>

        {activeTable === "users" && (
          <div className="adminTableWrap">
            <table className="adminDataTable">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>{user.role}</td>
                    <td>{formatDate(user.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTable === "surveys" && (
          <div className="adminTableWrap">
            <table className="adminDataTable wideAdminTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Survey Type</th>
                  <th>Response Preview</th>
                  <th>Comments</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {surveys.map((survey) => (
                  <tr key={survey.id}>
                    <td>{getUserName(userMap, survey.user_id)}</td>
                    <td>{survey.survey_type}</td>
                    <td>{parseJsonPreview(survey.responses)}</td>
                    <td>{survey.comments || "N/A"}</td>
                    <td>{formatDate(survey.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTable === "pantry" && (
          <div className="adminTableWrap">
            <table className="adminDataTable wideAdminTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Quantity</th>
                  <th>Unit</th>
                  <th>Container</th>
                  <th>Barcode</th>
                  <th>Brand</th>
                  <th>Expiration</th>
                </tr>
              </thead>
              <tbody>
                {pantry.map((item) => (
                  <tr key={item.id}>
                    <td>{getUserName(userMap, item.user_id)}</td>
                    <td>{item.item_name}</td>
                    <td>{item.category}</td>
                    <td>{item.quantity}</td>
                    <td>{item.unit}</td>
                    <td>{item.container_type || "N/A"}</td>
                    <td>{item.barcode || "Manual"}</td>
                    <td>{item.brand || "N/A"}</td>
                    <td>{item.expiration_date || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTable === "logs" && (
          <div className="adminTableWrap">
            <table className="adminDataTable wideAdminTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Recipe</th>
                  <th>Action</th>
                  <th>Score</th>
                  <th>Used Ingredients</th>
                  <th>Feedback</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{getUserName(userMap, log.user_id)}</td>
                    <td>{log.recipe_name}</td>
                    <td>
                      <span className={`adminActionBadge ${actionClass(log.action)}`}>
                        {actionLabel(log.action)}
                      </span>
                    </td>
                    <td>{log.score ?? "N/A"}</td>
                    <td>{formatUsedIngredients(log.used_ingredients)}</td>
                    <td>{log.feedback || "N/A"}</td>
                    <td>{formatDate(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {summary && Object.keys(summary).length > 0 && (
        <details className="card adminSectionCard technicalSummary">
          <summary>Technical Backend Summary</summary>
          <pre className="adminJsonPreview">
            {JSON.stringify(summary, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
