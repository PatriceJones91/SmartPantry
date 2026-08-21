import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function formatDate(value) {
  if (!value) return "N/A";

  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return "N/A";
  }
}

function actionLabel(action) {
  const labels = {
    made: "Made Meal",
    used_elsewhere: "Custom Meal",
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
    used_elsewhere: "historyCustomMeal",
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


function normalizeParticipantKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function formatScore(value) {
  return value === null || value === undefined || value === "" ? "—" : Number(value).toFixed(2);
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
  const [participantFilter, setParticipantFilter] = useState("all");

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
    return users.filter((user) => user.role === "participant");
  }, [users]);

  const selectedParticipant = useMemo(() => {
    if (participantFilter === "all") return null;
    return participantUsers.find((user) => user.id === participantFilter) || null;
  }, [participantFilter, participantUsers]);

  const selectedParticipantKey = normalizeParticipantKey(selectedParticipant?.username);

  const activity1ParticipantCount = useMemo(() => {
    const names = activity1Rows
      .map((row) => row.username || row.participant_id)
      .filter(Boolean);

    return new Set(names).size;
  }, [activity1Rows]);

  const metrics = useMemo(() => {
    const recommendationLogs = logs.filter((log) => log.action !== "general_feedback");

    const made = recommendationLogs.filter((log) => log.action === "made").length;
    const saved = recommendationLogs.filter((log) => log.action === "saved").length;
    const notUsed = recommendationLogs.filter((log) => log.action === "not_used").length;
    const customMeal = recommendationLogs.filter(
      (log) => log.action === "custom_meal" || log.action === "used_elsewhere"
    ).length;
    const ingredientUtilization = made + customMeal;

    const activePantryItems = pantry.filter((item) => item.status !== "deleted");

    const positiveActions = made + saved + customMeal;
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
      saved,
      notUsed,
      customMeal,
      ingredientUtilization,
      acceptanceRate,
    };
  }, [users, participantUsers, pantry, logs]);

  const filteredPantry = useMemo(() => {
    if (participantFilter === "all") return pantry;
    return pantry.filter((item) => item.user_id === participantFilter);
  }, [pantry, participantFilter]);

  const filteredLogs = useMemo(() => {
    if (participantFilter === "all") return logs;
    return logs.filter((log) => log.user_id === participantFilter);
  }, [logs, participantFilter]);

  const filteredActivity1Rows = useMemo(() => {
    if (participantFilter === "all") return activity1Rows;

    const selected = participantUsers.find((user) => user.id === participantFilter);
    if (!selected) return activity1Rows;

    return activity1Rows.filter((row) =>
      [row.username, row.participant_id]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase() === String(selected.username).toLowerCase())
    );
  }, [activity1Rows, participantFilter, participantUsers]);

  const recentLogs = useMemo(() => {
    return [...filteredLogs].slice(0, 8);
  }, [filteredLogs]);

  const participantEvidence = useMemo(() => {
    return participantUsers.map((user) => {
      const userPantry = pantry.filter((item) => item.user_id === user.id);
      const userLogs = logs.filter(
        (log) => log.user_id === user.id && log.action !== "general_feedback"
      );
      const task1Items = activity1Rows.filter((row) =>
        [row.username, row.participant_id]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase() === String(user.username).toLowerCase())
      );

      return {
        participant: user.username,
        household_size: user.household_size || "N/A",
        task1_manual_items: task1Items.length,
        task3_pantry_items: userPantry.length,
        task3_recommendation_actions: userLogs.length,
        made_meal: userLogs.filter((log) => log.action === "made").length,
        custom_meal: userLogs.filter(
          (log) => log.action === "custom_meal" || log.action === "used_elsewhere"
        ).length,
        ingredient_utilization: userLogs.filter(
          (log) =>
            log.action === "made" ||
            log.action === "used_elsewhere" ||
            log.action === "custom_meal"
        ).length,
        saved_for_later: userLogs.filter((log) => log.action === "saved").length,
        did_not_use: userLogs.filter((log) => log.action === "not_used").length,
      };
    });
  }, [participantUsers, pantry, logs, activity1Rows]);

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
      score: log.smart_score,
      used_ingredients: formatUsedIngredients(log.used_ingredients),
      feedback: log.feedback,
    }));

    downloadCsv("smart_pantry_recommendation_logs.csv", rows);
  }

  function exportParticipants() {
    downloadCsv("smart_pantry_participant_evidence_matrix.csv", participantEvidence);
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
            Review participant activity, research evidence, Smart Pantry behavior, and exports in one place.
          </p>
        </div>

        <button
          onClick={() => {
            loadAdminData();
            loadActivity1Rows();
                  }}
        >
          Refresh All Study Data
        </button>
      </section>

      <section className="card adminSectionCard adminQuickControls">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Review Controls</h2>
            <p>Filter the evidence by participant, then jump directly to the section you need.</p>
          </div>
        </div>

        <div className="adminControlRow">
          <label>
            Participant
            <select value={participantFilter} onChange={(e) => setParticipantFilter(e.target.value)}>
              <option value="all">All participants</option>
              {participantUsers.map((user) => (
                <option key={user.id} value={user.id}>{user.username}</option>
              ))}
            </select>
          </label>
          <div className="adminJumpLinks">
            <a href="#study-progress">Study Progress</a>
            <a href="#research-outcomes">Research Outcomes</a>
            <a href="#task1">Task 1</a>
            <a href="#task2">Task 2</a>
            <a href="#task3">Task 3</a>
            <a href="#exports">Exports</a>
            <a href="#raw-evidence">Raw Evidence</a>
          </div>
        </div>
      </section>

      {loading && <section className="card">Loading admin dashboard...</section>}
      {error && <section className="card error">{error}</section>}

      <section id="study-progress" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Data Sources</h2>
            <p>Smart Pantry activity is shown here. Survey and TAM responses remain in Google Forms and will be imported for final analysis.</p>
          </div>
          <span className="statusReady">Separate data sources</span>
        </div>

        <div className="studyProgressGrid externalStudyGrid">
          <div><strong>Google Forms</strong><span>Consent, Pre-Study, Task Feedback, Post-Study</span></div>
          <div><strong>Smart Pantry</strong><span>Pantry activity and recommendation behavior</span></div>
          <div><strong>Task 1</strong><span>Pantry Note Tracker manual entries</span></div>
          <div><strong>Final Analysis</strong><span>Export Google Sheets as CSV and combine with dashboard exports</span></div>
        </div>
      </section>

      <section id="research-outcomes" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Research Outcome Summary</h2>
            <p>Quick evidence view aligned with pantry awareness, recommendation usefulness, and ingredient utilization.</p>
          </div>
        </div>

        <div className="polishedAdminGrid">
          <div><strong>{metrics.participants}</strong><span>Participant accounts</span></div>
          <div><strong>{metrics.pantryItems}</strong><span>Smart Pantry items</span></div>
          <div><strong>{metrics.recommendationActions}</strong><span>Recommendation actions</span></div>
          <div><strong>{metrics.ingredientUtilization}</strong><span>Ingredient utilization actions</span></div>
          <div><strong>{metrics.acceptanceRate}%</strong><span>Positive action rate</span></div>
        </div>


      </section>

      <section className="card adminSectionCard researchAlignmentCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Hypothesis Evidence Map</h2>
            <p>Use these evidence groups when explaining how the study evaluates the hypothesis.</p>
          </div>
        </div>
        <div className="researchEvidenceGrid">
          <div><h3>Pantry Awareness</h3><strong>Survey + pantry evidence</strong><p>Pre/Post survey responses are analyzed with Task 1 and Smart Pantry pantry activity.</p></div>
          <div><h3>Recommendation Usefulness</h3><strong>TAM + recommendation evidence</strong><p>Task feedback is analyzed with recommendation actions such as made meal, saved, or did not use.</p></div>
          <div><h3>Ingredient Utilization</h3><strong>{metrics.ingredientUtilization} utilization actions</strong><p>Made Meal and Custom Meal actions provide behavioral evidence that participants used pantry ingredients.</p></div>
        </div>
      </section>

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>TAM Analysis Plan</h2>
            <p>TAM responses stay in the Google Form response sheets during data collection and are imported after the study closes.</p>
          </div>
        </div>
        <div className="tamGrid">
          <div><h3>Perceived Ease of Use</h3><strong>Questions 1–2</strong><p>Compared across the study task feedback forms.</p></div>
          <div><h3>Perceived Usefulness</h3><strong>Task-specific usefulness items</strong><p>Compared with Smart Pantry behavioral evidence.</p></div>
          <div><h3>Behavioral Intention</h3><strong>Question 8</strong><p>Used to compare willingness to use each approach again.</p></div>
        </div>
        <p className="adminMutedNote">When data collection ends, export each Google response sheet as CSV. Those files can be combined with the dashboard CSV exports for final statistical analysis.</p>
      </section>

      <section id="task1" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Task 1 – Pantry Note Tracker</h2>
            <p>Manual baseline pantry entries submitted through the Pantry Note Tracker.</p>
          </div>
          <button onClick={loadActivity1Rows}>Refresh Task 1 Data</button>
        </div>

        <div className="polishedAdminGrid">
          <div>
            <strong>{activity1ParticipantCount}</strong>
            <span>Task 1 participants</span>
          </div>
          <div>
            <strong>{activity1Rows.length}</strong>
            <span>Manual items entered</span>
          </div>
        </div>

        <p className="adminMutedNote">Task 1 feedback and TAM responses remain in Google Forms and will be imported for final analysis.</p>


        {activity1Loading && <p>Loading Study Task 1 data...</p>}
        {activity1Error && <p className="error">{activity1Error}</p>}

        {!activity1Loading && !activity1Error && (
          activity1Rows.length === 0 ? (
            <div className="groceryEmpty">No Study Task 1 Pantry Note Tracker entries yet.</div>
          ) : (
            <details className="evidenceDetails">
              <summary>View Task 1 manual pantry entries ({filteredActivity1Rows.length})</summary>
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
                  </tr>
                </thead>
                <tbody>
                  {filteredActivity1Rows.map((item) => (
                    <tr key={item.id}>
                      <td>{item.username || item.participant_id || "Unknown"}</td>
                      <td>{item.item_name || "N/A"}</td>
                      <td>{item.quantity || "N/A"}</td>
                      <td>{item.unit || "N/A"}</td>
                      <td>{item.category || "N/A"}</td>
                      <td>{item.expiration_date || "N/A"}</td>
                      <td>{item.notes || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            </details>
          )
        )}
      </section>

      <section id="task2" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Task 2 – Samsung Food</h2>
            <p>The Ingredient Recipe Finder feedback and TAM responses are collected in Google Forms and remain separate during the live study.</p>
          </div>
          <span className="statusReady">Google Forms</span>
        </div>
        <div className="researchEvidenceGrid">
          <div><h3>Perceived Ease of Use</h3><strong>Questions 1 and 2</strong></div>
          <div><h3>Perceived Usefulness</h3><strong>Questions 3, 5, 6, and 7</strong></div>
          <div><h3>Behavioral Intention</h3><strong>Question 8</strong></div>
        </div>
        <p className="adminMutedNote">Export the Study Task 2 Google Sheet as CSV when you are ready for final analysis.</p>
      </section>

      <section id="task3" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Task 3 – Smart Pantry</h2>
            <p>Behavioral evidence recorded inside Smart Pantry. Task 3 TAM feedback remains in Google Forms for final analysis.</p>
          </div>
        </div>



        <div className="polishedActionGrid">
          <div className="adminActionCard madeCard"><strong>{metrics.made}</strong><span>Made Meal</span></div>
          <div className="adminActionCard savedCard"><strong>{metrics.saved}</strong><span>Saved for Later</span></div>
          <div className="adminActionCard customCard"><strong>{metrics.customMeal}</strong><span>Custom Meals</span></div>
          <div className="adminActionCard notUsedCard"><strong>{metrics.notUsed}</strong><span>Did Not Use</span></div>
        </div>


      </section>

      <section id="exports" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Export Study Evidence</h2>
            <p>Download CSV files for thesis charts and results analysis.</p>
          </div>
        </div>

        <div className="exportButtonGrid">
          <button onClick={exportParticipants}>Export Participant Evidence CSV</button>
          <button onClick={exportLogs}>Export Recommendation Logs CSV</button>
          <button onClick={exportPantry}>Export Smart Pantry Data CSV</button>
          <button onClick={exportActivity1}>Export Pantry Note Tracker Entries CSV</button>
        </div>
        <p className="adminMutedNote">Survey and TAM responses are exported separately from Google Sheets and combined with these files during final analysis.</p>
      </section>



      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Participant Evidence Matrix</h2>
            <p>
              One participant-level view of manual baseline evidence and Smart Pantry behavioral evidence. Survey/TAM responses are analyzed separately from Google Sheets.
            </p>
          </div>
        </div>

        {participantUsers.length === 0 ? (
          <p>No participant accounts yet.</p>
        ) : (
          <div className="adminTableWrap">
            <table className="adminDataTable wideAdminTable">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Household Size</th>
                  <th>Task 1 Manual Items</th>
                  <th>Task 3 Pantry Items</th>
                  <th>Recommendation Actions</th>
                  <th>Made Meal</th>
                  <th>Custom Meal</th>
                  <th>Ingredient Utilization</th>
                  <th>Saved</th>
                  <th>Did Not Use</th>
                </tr>
              </thead>
              <tbody>
                {participantEvidence
                  .filter((row) => !selectedParticipantKey || normalizeParticipantKey(row.participant) === selectedParticipantKey)
                  .map((row) => (
                  <tr key={row.participant}>
                    <td>{row.participant}</td>
                    <td>{row.household_size}</td>
                    <td>{row.task1_manual_items}</td>
                    <td>{row.task3_pantry_items}</td>
                    <td>{row.task3_recommendation_actions}</td>
                    <td>{row.made_meal}</td>
                    <td>{row.custom_meal}</td>
                    <td>{row.ingredient_utilization}</td>
                    <td>{row.saved_for_later}</td>
                    <td>{row.did_not_use}</td>
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
                  <p>{getUserName(userMap, log.user_id)}</p>
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

      <section id="raw-evidence" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Raw Study Evidence Tables</h2>
            <p>Detailed records used to verify the summary metrics and participant-level evidence.</p>
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
            Study Task 1 – Pantry Note Tracker
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
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>{user.role}</td>
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
                {filteredPantry.map((item) => (
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
                {filteredActivity1Rows.map((item) => (
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
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{getUserName(userMap, log.user_id)}</td>
                    <td>{log.recipe_name}</td>
                    <td>
                      <span className={`adminActionBadge ${actionClass(log.action)}`}>
                        {actionLabel(log.action)}
                      </span>
                    </td>
                    <td>{log.smart_score ?? "N/A"}</td>
                    <td>{formatUsedIngredients(log.used_ingredients)}</td>
                    <td>{log.feedback || "N/A"}</td>
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
