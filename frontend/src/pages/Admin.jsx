import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

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

function getUserName(userMap, userId) {
  return userMap[userId] || userId || "Unknown";
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function parseJsonPreview(value) {
  if (!value) return "N/A";

  if (typeof value === "object") {
    return Object.entries(value)
      .slice(0, 4)
      .map(([key, val]) => `${key}: ${val}`)
      .join(" | ");
  }

  try {
    const parsed = JSON.parse(value);

    if (typeof parsed === "object") {
      return Object.entries(parsed)
        .slice(0, 4)
        .map(([key, val]) => `${key}: ${val}`)
        .join(" | ");
    }
  } catch {
    return String(value);
  }

  return String(value);
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
      setError(err.message);
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
        username: user.username,
        pre: false,
        post: false,
      };
    });

    surveys.forEach((survey) => {
      if (!userSurveyMap[survey.user_id]) {
        userSurveyMap[survey.user_id] = {
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
    const usedElsewhere = logs.filter((log) => log.action === "used_elsewhere").length;
    const saved = logs.filter((log) => log.action === "saved").length;
    const notUsed = logs.filter((log) => log.action === "not_used").length;

    const preComplete = surveySummary.filter((item) => item.pre).length;
    const postComplete = surveySummary.filter((item) => item.post).length;

    const activePantryItems = pantry.filter((item) => item.status !== "deleted");

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
    };
  }, [users, participantUsers, surveySummary, pantry, logs]);

  return (
    <div>
      <div className="pageHeader adminHero">
        <div>
          <h1>Admin Dashboard</h1>
          <p>
            This page gives the admin a study-level view of participants, pantry activity,
            survey completion, and recommendation usage evidence.
          </p>
        </div>

        <button onClick={loadAdminData}>
          Refresh Admin Data
        </button>
      </div>

      {loading && <section className="card">Loading admin dashboard...</section>}
      {error && <section className="card error">{error}</section>}

      <section className="card">
        <h2>Outcome Summary</h2>
        <div className="adminMetricGrid">
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
        </div>
      </section>

      <section className="card">
        <h2>Study Metrics</h2>
        <div className="adminActionGrid">
          <div className="historyMade">
            <strong>{metrics.made}</strong>
            <span>Made Meal</span>
          </div>
          <div className="historyUsedElsewhere">
            <strong>{metrics.usedElsewhere}</strong>
            <span>Used Elsewhere</span>
          </div>
          <div className="historySaved">
            <strong>{metrics.saved}</strong>
            <span>Saved for Later</span>
          </div>
          <div className="historyNotUsed">
            <strong>{metrics.notUsed}</strong>
            <span>Did Not Use</span>
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Survey Completion by Participant</h2>

        {surveySummary.length === 0 ? (
          <p>No participant survey records yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Participant</th>
                <th>Pre-Study Survey</th>
                <th>Post-Study Survey</th>
              </tr>
            </thead>
            <tbody>
              {surveySummary.map((row) => (
                <tr key={row.username}>
                  <td>{row.username}</td>
                  <td>
                    <span className={row.pre ? "statusComplete" : "statusMissing"}>
                      {row.pre ? "Complete" : "Not Done"}
                    </span>
                  </td>
                  <td>
                    <span className={row.post ? "statusComplete" : "statusMissing"}>
                      {row.post ? "Complete" : "Not Done"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Admin Evidence Tables</h2>

        <div className="filterBar">
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
            <table>
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
            <table>
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
            <table>
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Quantity</th>
                  <th>Unit</th>
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
            <table>
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Recipe</th>
                  <th>Action</th>
                  <th>Score</th>
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
        <section className="card">
          <h2>Backend Summary</h2>
          <pre className="adminJsonPreview">
            {JSON.stringify(summary, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}
