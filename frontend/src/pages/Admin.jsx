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
    custom_meal: "Custom Meal",
    general_feedback: "General Feedback",
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
    general_feedback: "historyGeneralFeedback",
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
function getSupabaseConfig() {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    throw new Error(
      "Missing Supabase settings. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to .env.local."
    );
  }

  return { url, anonKey };
}

async function fetchActivity1AdminRows() {
  const { url, anonKey } = getSupabaseConfig();

  const response = await fetch(`${url}/rest/v1/rpc/activity1_admin_rows`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: anonKey,
      Authorization: `Bearer ${anonKey}`,
    },
    body: JSON.stringify({}),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.message || data?.hint || "Could not load Activity 1 manual tracking data."
    );
  }

  return data || [];
}


function AdminAccountTools() {
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

  const [resetForm, setResetForm] = useState({
    admin_password: "",
    target_username: "",
    new_password: "Smart1234",
  });

  const [deleteForm, setDeleteForm] = useState({
    admin_password: "",
    target_username: "",
    confirm_text: "",
  });

  const [toolMessage, setToolMessage] = useState("");
  const [toolError, setToolError] = useState("");

  function getAdminUsername() {
    try {
      const user = JSON.parse(localStorage.getItem("sp2_user") || "{}");
      return user.username || "admin";
    } catch {
      return "admin";
    }
  }

  function updateReset(field, value) {
    setResetForm((current) => ({ ...current, [field]: value }));
  }

  function updateDelete(field, value) {
    setDeleteForm((current) => ({ ...current, [field]: value }));
  }

  async function sendAdminRequest(path, payload) {
    setToolMessage("");
    setToolError("");

    const response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "The admin request did not work.");
    }

    return data;
  }

  async function handleResetPassword() {
    try {
      if (!resetForm.target_username || !resetForm.new_password || !resetForm.admin_password) {
        setToolError("Enter the participant username, temporary password, and admin password.");
        return;
      }

      const data = await sendAdminRequest("/auth/admin/reset-password", {
        admin_username: getAdminUsername(),
        admin_password: resetForm.admin_password,
        target_username: resetForm.target_username,
        new_password: resetForm.new_password,
      });

      setToolMessage(data.message || "Participant password was reset.");
      setResetForm((current) => ({ ...current, admin_password: "" }));
    } catch (err) {
      setToolError(err.message);
    }
  }

  async function handleDeleteTester() {
    try {
      if (!deleteForm.target_username || !deleteForm.confirm_text || !deleteForm.admin_password) {
        setToolError("Enter the tester username, confirmation text, and admin password.");
        return;
      }

      const data = await sendAdminRequest("/auth/admin/delete-test-user", {
        admin_username: getAdminUsername(),
        admin_password: deleteForm.admin_password,
        target_username: deleteForm.target_username,
        confirm_text: deleteForm.confirm_text,
      });

      setToolMessage(data.message || "Tester account was deleted.");
      setDeleteForm({
        admin_password: "",
        target_username: "",
        confirm_text: "",
      });
    } catch (err) {
      setToolError(err.message);
    }
  }

  return (
    <section className="adminAccountTools">
      <div>
        <p className="sectionEyebrow">Admin account support</p>
        <h2>Participant Account Tools</h2>
        <p>
          Use this section if a participant forgets their password or needs account support. 
          Passwords are reset, not viewed, so participant privacy stays protected.
        </p>
      </div>

      <div className="adminToolGrid">
        <div className="adminToolCard">
          <h3>Reset participant password</h3>
          <input
            placeholder="Participant username"
            value={resetForm.target_username}
            onChange={(e) => updateReset("target_username", e.target.value)}
          />
          <input
            placeholder="Temporary password"
            value={resetForm.new_password}
            onChange={(e) => updateReset("new_password", e.target.value)}
          />
          <input
            type="password"
            placeholder="Admin password"
            value={resetForm.admin_password}
            onChange={(e) => updateReset("admin_password", e.target.value)}
          />
          <button type="button" onClick={handleResetPassword}>
            Reset Password
          </button>
        </div>

        <div className="adminToolCard dangerTool">
          <h3>Delete fake/test account</h3>
          <input
            placeholder="Tester username"
            value={deleteForm.target_username}
            onChange={(e) => updateDelete("target_username", e.target.value)}
          />
          <input
            placeholder='Type: DELETE username'
            value={deleteForm.confirm_text}
            onChange={(e) => updateDelete("confirm_text", e.target.value)}
          />
          <input
            type="password"
            placeholder="Admin password"
            value={deleteForm.admin_password}
            onChange={(e) => updateDelete("admin_password", e.target.value)}
          />
          <button type="button" className="dangerButton" onClick={handleDeleteTester}>
            Delete Tester Account
          </button>
        </div>
      </div>

      {toolMessage && <p className="success">{toolMessage}</p>}
      {toolError && <p className="error">{toolError}</p>}
    </section>
  );
}

export default function Admin() {
  const [summary, setSummary] = useState(null);
  const [users, setUsers] = useState([]);
  const [pantry, setPantry] = useState([]);
  const [logs, setLogs] = useState([]);
  const [activity1Rows, setActivity1Rows] = useState([]);
  const [activity1Loading, setActivity1Loading] = useState(false);
  const [activity1Error, setActivity1Error] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTable, setActiveTable] = useState("users");

  async function loadActivity1Rows() {
    setActivity1Loading(true);
    setActivity1Error("");

    try {
      const data = await fetchActivity1AdminRows();
      setActivity1Rows(safeArray(data));
    } catch (err) {
      setActivity1Error(
        err.message || "Could not load Activity 1 manual tracking data."
      );
      setActivity1Rows([]);
    } finally {
      setActivity1Loading(false);
    }
  }

  async function loadAdminData() {
    setLoading(true);
    setError("");

    try {
      const [summaryData, usersData, pantryData, logsData] =
        await Promise.all([
          api.adminSummary(),
          api.adminUsers(),
          api.adminPantry(),
          api.adminLogs(),
        ]);

      setSummary(summaryData || {});
      setUsers(safeArray(usersData));
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
    loadActivity1Rows();
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

  const activity1ParticipantCount = useMemo(() => {
    const names = activity1Rows
      .map((row) => row.username || row.participant_id)
      .filter(Boolean);

    return new Set(names).size;
  }, [activity1Rows]);

  const activity1MostRecent = useMemo(() => {
    if (activity1Rows.length === 0) return null;

    return [...activity1Rows].sort(
      (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
    )[0];
  }, [activity1Rows]);

  const metrics = useMemo(() => {
    const recommendationLogs = logs.filter((log) => log.action !== "general_feedback");

    const made = recommendationLogs.filter((log) => log.action === "made").length;
    const usedElsewhere = recommendationLogs.filter(
      (log) => log.action === "used_elsewhere"
    ).length;
    const saved = recommendationLogs.filter((log) => log.action === "saved").length;
    const notUsed = recommendationLogs.filter((log) => log.action === "not_used").length;
    const customMeal = recommendationLogs.filter((log) => log.action === "custom_meal").length;

    const activePantryItems = pantry.filter((item) => item.status !== "deleted");

    const positiveActions = made + usedElsewhere + saved + customMeal;
    const acceptanceRate =
      recommendationLogs.length > 0
        ? Math.round((positiveActions / recommendationLogs.length) * 100)
        : 0;

    return {
      participants: participantUsers.length,
      totalUsers: users.length,
      pantryItems: activePantryItems.length,
      recommendationActions: recommendationLogs.length,
      made,
      usedElsewhere,
      saved,
      notUsed,
      customMeal,
      acceptanceRate,
    };
  }, [users, participantUsers, pantry, logs]);

  const recentLogs = useMemo(() => {
    return [...logs]
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 8);
  }, [logs]);

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
    const rows = participantUsers.map((user) => ({
      participant: user.username,
      pantry_items: pantry.filter((item) => item.user_id === user.id).length,
      recommendation_actions: logs.filter(
        (log) => log.user_id === user.id && log.action !== "general_feedback"
      ).length,
      survey_tracking: "Google Forms response sheets",
    }));

    downloadCsv("smart_pantry_participant_activity.csv", rows);
  }

  function exportActivity1() {
    const rows = activity1Rows.map((item) => ({
      participant: item.username || item.participant_id,
      participant_id: item.participant_id,
      row_order: item.row_order,
      item_name: item.item_name,
      quantity: item.quantity,
      unit: item.unit,
      category: item.category,
      expiration_date: item.expiration_date,
      notes: item.notes,
      saved_at: formatDate(item.created_at),
    }));

    downloadCsv("pantry_note_tracker.csv", rows);
  }

  return (
    <div className="adminPage">
      <section className="adminHeroCard">
        <div>
          <p className="eyebrow">Smart Pantry Admin</p>
          <h1>Admin Dashboard</h1>
          <p>
            This page gives the admin a study-level view of participants, pantry
            activity, recommendation behavior, and ingredient-use evidence.
            Pre-study and post-study survey responses are tracked separately in Google Forms.
          </p>
        </div>

        <button
          onClick={() => {
            loadAdminData();
            loadActivity1Rows();
          }}
        >
          Refresh Admin Data
        </button>
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
            <strong>Google Forms</strong>
            <span>Survey responses tracked separately</span>
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
            <h2>Activity 1 Manual Tracking Data</h2>
            <p>Manual pantry entries submitted through Pantry Note Tracker.</p>
          </div>
          <button onClick={loadActivity1Rows}>Refresh Activity 1 Data</button>
        </div>

        <div className="polishedAdminGrid">
          <div>
            <strong>{activity1ParticipantCount}</strong>
            <span>Activity 1 participants</span>
          </div>
          <div>
            <strong>{activity1Rows.length}</strong>
            <span>Manual items entered</span>
          </div>
          <div>
            <strong>{activity1MostRecent ? formatDate(activity1MostRecent.created_at) : "N/A"}</strong>
            <span>Most recent manual save</span>
          </div>
        </div>

        {activity1Loading && <p>Loading Activity 1 manual tracking data...</p>}
        {activity1Error && <p className="error">{activity1Error}</p>}

        {!activity1Loading && !activity1Error && (
          activity1Rows.length === 0 ? (
            <div className="groceryEmpty">No Activity 1 manual tracking entries yet.</div>
          ) : (
            <div className="adminTableWrap">
              <table className="adminDataTable wideAdminTable">
                <thead>
                  <tr>
                    <th>Participant</th>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Category</th>
                    <th>Expiration</th>
                    <th>Notes</th>
                    <th>Saved</th>
                  </tr>
                </thead>
                <tbody>
                  {activity1Rows.map((item) => (
                    <tr key={item.id}>
                      <td>{item.username || item.participant_id || "Unknown"}</td>
                      <td>{item.item_name || "N/A"}</td>
                      <td>{item.quantity || "N/A"}</td>
                      <td>{item.unit || "N/A"}</td>
                      <td>{item.category || "N/A"}</td>
                      <td>{item.expiration_date || "N/A"}</td>
                      <td>{item.notes || "N/A"}</td>
                      <td>{formatDate(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
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
            <h2>Export Study Data</h2>
            <p>Download CSV files for thesis charts and results analysis.</p>
          </div>
        </div>

        <div className="exportButtonGrid">
          <button onClick={exportLogs}>Export Recommendation Logs CSV</button>
          <button onClick={exportPantry}>Export Pantry Data CSV</button>
          <button onClick={exportParticipants}>
            Export Participant Activity CSV
          </button>
          <button onClick={exportActivity1}>
            Export Pantry Note Tracker CSV
          </button>
        </div>
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Participant Activity</h2>
            <p>
              Survey completion is checked in the Google Forms response sheets.
              This table shows Smart Pantry activity only.
            </p>
          </div>
        </div>

        {participantUsers.length === 0 ? (
          <p>No participant accounts yet.</p>
        ) : (
          <div className="adminTableWrap">
            <table className="adminDataTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Survey Tracking</th>
                  <th>Pantry Items</th>
                  <th>Recommendation Actions</th>
                </tr>
              </thead>
              <tbody>
                {participantUsers.map((user) => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>
                      <span className="statusComplete">
                        Check Google Forms
                      </span>
                    </td>
                    <td>
                      {pantry.filter((item) => item.user_id === user.id).length}
                    </td>
                    <td>
                      {logs.filter(
                        (log) =>
                          log.user_id === user.id &&
                          log.action !== "general_feedback"
                      ).length}
                    </td>
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

      <AdminAccountTools />

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Admin Evidence Tables</h2>
            <p>Raw evidence tables for users, pantry items, Activity 1, and recommendation logs.</p>
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
            className={activeTable === "pantry" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("pantry")}
          >
            Pantry Items
          </button>
          <button
            className={activeTable === "activity1" ? "activeFilter" : "secondary"}
            onClick={() => setActiveTable("activity1")}
          >
            Activity 1 Manual Tracking
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

        {activeTable === "activity1" && (
          <div className="adminTableWrap">
            <table className="adminDataTable wideAdminTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Item</th>
                  <th>Quantity</th>
                  <th>Unit</th>
                  <th>Category</th>
                  <th>Expiration</th>
                  <th>Notes</th>
                  <th>Saved</th>
                </tr>
              </thead>
              <tbody>
                {activity1Rows.map((item) => (
                  <tr key={item.id}>
                    <td>{item.username || item.participant_id || "Unknown"}</td>
                    <td>{item.item_name || "N/A"}</td>
                    <td>{item.quantity || "N/A"}</td>
                    <td>{item.unit || "N/A"}</td>
                    <td>{item.category || "N/A"}</td>
                    <td>{item.expiration_date || "N/A"}</td>
                    <td>{item.notes || "N/A"}</td>
                    <td>{formatDate(item.created_at)}</td>
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
