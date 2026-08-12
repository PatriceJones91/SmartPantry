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
  const [studyEvidence, setStudyEvidence] = useState(null);
  const [studyEvidenceLoading, setStudyEvidenceLoading] = useState(false);
  const [studyEvidenceError, setStudyEvidenceError] = useState("");

  function getAdminSession() {
    try {
      return JSON.parse(sessionStorage.getItem("sp2_admin_session") || "null");
    } catch {
      return null;
    }
  }

  async function loadGoogleStudyEvidence() {
    const adminSession = getAdminSession();
    if (!adminSession?.username || !adminSession?.password) {
      setStudyEvidenceError("Admin study access expired. Log out and back in to refresh it.");
      return;
    }

    setStudyEvidenceLoading(true);
    setStudyEvidenceError("");
    try {
      const data = await api.adminStudyEvidence({
        admin_username: adminSession.username,
        admin_password: adminSession.password,
      });
      setStudyEvidence(data || null);
    } catch (err) {
      setStudyEvidenceError(err.message || "Could not load Google study responses.");
    } finally {
      setStudyEvidenceLoading(false);
    }
  }

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
    loadGoogleStudyEvidence();
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

  const selectedParticipant = useMemo(() => {
    if (participantFilter === "all") return null;
    return participantUsers.find((user) => user.id === participantFilter) || null;
  }, [participantFilter, participantUsers]);

  const selectedParticipantKey = normalizeParticipantKey(selectedParticipant?.username);

  function studyRows(section) {
    const rows = safeArray(studyEvidence?.[section]);
    if (!selectedParticipantKey) return rows;
    return rows.filter((row) => normalizeParticipantKey(row.participant) === selectedParticipantKey);
  }

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
    return [...filteredLogs]
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 8);
  }, [filteredLogs]);

  const studyEvidenceByParticipant = useMemo(() => {
    const result = {};
    if (!studyEvidence) return result;
    ["consent", "pre", "task1", "task2", "task3", "post"].forEach((section) => {
      safeArray(studyEvidence[section]).forEach((row) => {
        const key = normalizeParticipantKey(row.participant);
        if (!key) return;
        result[key] = result[key] || {};
        result[key][section] = row;
      });
    });
    return result;
  }, [studyEvidence]);

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

      const sheetEvidence = studyEvidenceByParticipant[normalizeParticipantKey(user.username)] || {};
      return {
        participant: user.username,
        consent: sheetEvidence.consent?.consented ? "Yes" : "—",
        pre_study: sheetEvidence.pre ? "Complete" : "—",
        task1_items: task1Items.length,
        task1_tam_ease: sheetEvidence.task1?.ease_of_use ?? "",
        task1_tam_usefulness: sheetEvidence.task1?.perceived_usefulness ?? "",
        task1_tam_intention: sheetEvidence.task1?.behavioral_intention ?? "",
        task1_awareness: sheetEvidence.task1?.pantry_awareness ?? "",
        task2_tam_ease: sheetEvidence.task2?.ease_of_use ?? "",
        task2_tam_usefulness: sheetEvidence.task2?.perceived_usefulness ?? "",
        task2_tam_intention: sheetEvidence.task2?.behavioral_intention ?? "",
        task2_awareness: sheetEvidence.task2?.pantry_awareness ?? "",
        task3_pantry_items: userPantry.length,
        task3_tam_ease: sheetEvidence.task3?.ease_of_use ?? "",
        task3_tam_usefulness: sheetEvidence.task3?.perceived_usefulness ?? "",
        task3_tam_intention: sheetEvidence.task3?.behavioral_intention ?? "",
        task3_awareness: sheetEvidence.task3?.pantry_awareness ?? "",
        task3_recommendation_actions: userLogs.length,
        made_meal: userLogs.filter((log) => log.action === "made").length,
        used_elsewhere: userLogs.filter((log) => log.action === "used_elsewhere").length,
        saved_for_later: userLogs.filter((log) => log.action === "saved").length,
        did_not_use: userLogs.filter((log) => log.action === "not_used").length,
        post_study: sheetEvidence.post ? "Complete" : "—",
      };
    });
  }, [participantUsers, pantry, logs, activity1Rows, studyEvidenceByParticipant]);

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
      saved_at: formatDate(item.created_at),
    }));

    downloadCsv("pantry_note_tracker.csv", rows);
  }

  function exportGoogleStudySection(section, filename) {
    const rows = safeArray(studyEvidence?.[section]);
    if (rows.length === 0) return;
    downloadCsv(filename, rows);
  }

  function exportTamSummary() {
    if (!studyEvidence?.tam_summary) return;
    const labels = {
      task1: "Study Task 1 – Pantry Note Tracker",
      task2: "Study Task 2 – Samsung Food",
      task3: "Study Task 3 – Smart Pantry",
    };
    const rows = Object.entries(studyEvidence.tam_summary).map(([task, values]) => ({
      study_task: labels[task],
      responses: values.responses,
      perceived_ease_of_use: values.ease_of_use,
      perceived_usefulness: values.perceived_usefulness,
      behavioral_intention: values.behavioral_intention,
      pantry_awareness: values.pantry_awareness,
      ingredient_utilization: values.ingredient_utilization,
    }));
    downloadCsv("smart_pantry_tam_summary.csv", rows);
  }

  function exportResearchOutcomeSummary() {
    if (!studyEvidence?.tam_summary) return;
    const rows = [
      {
        outcome: "Pantry Awareness",
        task1: studyEvidence.tam_summary.task1?.pantry_awareness,
        task2: studyEvidence.tam_summary.task2?.pantry_awareness,
        task3: studyEvidence.tam_summary.task3?.pantry_awareness,
        pre_average: studyEvidence.pre_post_awareness?.pre_average,
        post_average: studyEvidence.pre_post_awareness?.post_average,
        pre_post_change: studyEvidence.pre_post_awareness?.change,
      },
      {
        outcome: "Recommendation Usefulness",
        task1: studyEvidence.tam_summary.task1?.perceived_usefulness,
        task2: studyEvidence.tam_summary.task2?.perceived_usefulness,
        task3: studyEvidence.tam_summary.task3?.perceived_usefulness,
      },
      {
        outcome: "Ingredient Utilization",
        task1: studyEvidence.tam_summary.task1?.ingredient_utilization,
        task2: studyEvidence.tam_summary.task2?.ingredient_utilization,
        task3: studyEvidence.tam_summary.task3?.ingredient_utilization,
        made_meal: metrics.made,
        used_elsewhere: metrics.usedElsewhere,
        saved_for_later: metrics.saved,
        did_not_use: metrics.notUsed,
      },
    ];
    downloadCsv("smart_pantry_research_outcome_summary.csv", rows);
  }

  return (
    <div className="adminPage">
      <section className="adminHeroCard">
        <div>
          <p className="eyebrow">Smart Pantry Admin</p>
          <h1>Admin Dashboard</h1>
          <p>
            Review participant progress, TAM measures, research outcomes, Smart Pantry behavior, and exports in one place.
          </p>
        </div>

        <button
          onClick={() => {
            loadAdminData();
            loadActivity1Rows();
            loadGoogleStudyEvidence();
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
            <a href="#tam-comparison">TAM Comparison</a>
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
            <h2>Study Progress</h2>
            <p>Response counts from the connected study forms. These are not final study results.</p>
          </div>
          <span className={studyEvidence ? "statusReady" : "statusMissing"}>
            {studyEvidence ? "Google study responses connected" : studyEvidenceLoading ? "Loading responses" : "Responses unavailable"}
          </span>
        </div>

        {studyEvidenceLoading && <p>Loading study responses...</p>}
        {!studyEvidenceLoading && studyEvidenceError && (
          <div className="groceryEmpty"><strong>Study response data unavailable.</strong> {studyEvidenceError}</div>
        )}

        <div className="studyProgressGrid">
          <div><strong>{studyEvidence?.sources?.consent ?? 0}</strong><span>Consent</span></div>
          <div><strong>{studyEvidence?.sources?.pre ?? 0}</strong><span>Pre-Study</span></div>
          <div><strong>{studyEvidence?.sources?.task1 ?? 0}</strong><span>Task 1 Feedback</span></div>
          <div><strong>{studyEvidence?.sources?.task2 ?? 0}</strong><span>Task 2 Feedback</span></div>
          <div><strong>{studyEvidence?.sources?.task3 ?? 0}</strong><span>Task 3 Feedback</span></div>
          <div><strong>{studyEvidence?.sources?.post ?? 0}</strong><span>Post-Study</span></div>
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
          <div><strong>{metrics.made + metrics.usedElsewhere}</strong><span>Made meal / used elsewhere</span></div>
          <div><strong>{metrics.acceptanceRate}%</strong><span>Positive action rate</span></div>
        </div>

        {studyEvidence?.pre_post_awareness && (
          <div className="prePostStrip">
            <div><span>Matched Pre/Post Awareness</span><strong>{studyEvidence.pre_post_awareness.matched_participants}</strong></div>
            <div><span>Pre</span><strong>{formatScore(studyEvidence.pre_post_awareness.pre_average)}</strong></div>
            <div><span>Post</span><strong>{formatScore(studyEvidence.pre_post_awareness.post_average)}</strong></div>
            <div><span>Change</span><strong>{studyEvidence.pre_post_awareness.change == null ? "—" : `${studyEvidence.pre_post_awareness.change > 0 ? "+" : ""}${studyEvidence.pre_post_awareness.change}`}</strong></div>
          </div>
        )}
      </section>

      <section className="card adminSectionCard researchAlignmentCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Hypothesis Evidence Map</h2>
            <p>Use these evidence groups when explaining how the study evaluates the hypothesis.</p>
          </div>
        </div>
        <div className="researchEvidenceGrid">
          <div>
            <h3>Pantry Awareness</h3>
            <strong>{formatScore(studyEvidence?.tam_summary?.task3?.pantry_awareness)} / 10</strong>
            <p>Task feedback, Smart Pantry activity, and matched Pre/Post awareness ratings.</p>
          </div>
          <div>
            <h3>Recommendation Usefulness</h3>
            <strong>{formatScore(studyEvidence?.tam_summary?.task3?.perceived_usefulness)} / 10</strong>
            <p>Compare usefulness ratings across all three tasks and review recommendation actions.</p>
          </div>
          <div>
            <h3>Ingredient Utilization</h3>
            <strong>{metrics.made + metrics.usedElsewhere}</strong>
            <p>Made Meal and Used Elsewhere provide behavioral evidence alongside task ratings.</p>
          </div>
        </div>
        <p className="adminMutedNote">This dashboard organizes descriptive evidence. Statistical significance is determined after the study closes.</p>
      </section>

      <section id="tam-comparison" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>TAM Comparison</h2>
            <p>Side-by-side perceived ease of use, perceived usefulness, and behavioral intention.</p>
          </div>
        </div>
        <div className="adminTableWrap">
          <table className="adminDataTable tamComparisonTable">
            <thead><tr><th>Study Task</th><th>Responses</th><th>Ease of Use</th><th>Usefulness</th><th>Behavioral Intention</th><th>Pantry Awareness</th></tr></thead>
            <tbody>
              {[
                ["Study Task 1 – Pantry Note Tracker", studyEvidence?.tam_summary?.task1],
                ["Study Task 2 – Samsung Food", studyEvidence?.tam_summary?.task2],
                ["Study Task 3 – Smart Pantry", studyEvidence?.tam_summary?.task3],
              ].map(([label, values]) => (
                <tr key={label}>
                  <td><strong>{label}</strong></td>
                  <td>{values?.responses ?? 0}</td>
                  <td>{formatScore(values?.ease_of_use)}</td>
                  <td>{formatScore(values?.perceived_usefulness)}</td>
                  <td>{formatScore(values?.behavioral_intention)}</td>
                  <td>{formatScore(values?.pantry_awareness)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
          <div>
            <strong>{activity1MostRecent ? formatDate(activity1MostRecent.created_at) : "N/A"}</strong>
            <span>Most recent manual save</span>
          </div>
        </div>

        {studyEvidence && (
          <>
            <div className="tamGrid">
              <div><h3>Perceived Ease of Use</h3><strong>{formatScore(studyEvidence.tam_summary?.task1?.ease_of_use)} / 10</strong></div>
              <div><h3>Perceived Usefulness</h3><strong>{formatScore(studyEvidence.tam_summary?.task1?.perceived_usefulness)} / 10</strong></div>
              <div><h3>Behavioral Intention</h3><strong>{formatScore(studyEvidence.tam_summary?.task1?.behavioral_intention)} / 10</strong></div>
            </div>
            {studyRows("task1").length > 0 && (
              <details className="evidenceDetails">
                <summary>View Task 1 participant feedback</summary>
                <div className="adminTableWrap">
                  <table className="adminDataTable wideAdminTable">
                    <thead><tr><th>Participant</th><th>Ease</th><th>Usefulness</th><th>Intention</th><th>What Worked</th><th>Confusing / Missing</th><th>Would Improve</th></tr></thead>
                    <tbody>{studyRows("task1").map((row, index) => (
                      <tr key={`${row.participant}-${index}`}><td>{row.participant || "Unknown"}</td><td>{formatScore(row.ease_of_use)}</td><td>{formatScore(row.perceived_usefulness)}</td><td>{formatScore(row.behavioral_intention)}</td><td>{row.worked_well || "—"}</td><td>{row.confusing_or_missing || "—"}</td><td>{row.make_more_useful || "—"}</td></tr>
                    ))}</tbody>
                  </table>
                </div>
              </details>
            )}
          </>
        )}

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
            </details>
          )
        )}
      </section>

      <section id="task2" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Task 2 – Samsung Food</h2>
            <p>Ingredient Recipe Finder comparison. Feedback is pulled from the connected Google response sheet.</p>
          </div>
          <span className={studyEvidence ? "statusReady" : "statusMissing"}>
            {studyEvidence ? `${studyEvidence.sources?.task2 ?? 0} responses` : studyEvidenceLoading ? "Loading" : "Unavailable"}
          </span>
        </div>

        {studyEvidence && (
          <>
            <div className="tamGrid">
              <div><h3>Perceived Ease of Use</h3><strong>{formatScore(studyEvidence.tam_summary?.task2?.ease_of_use)} / 10</strong><p>Questions 1 and 2</p></div>
              <div><h3>Perceived Usefulness</h3><strong>{formatScore(studyEvidence.tam_summary?.task2?.perceived_usefulness)} / 10</strong><p>Questions 3, 5, 6, and 7</p></div>
              <div><h3>Behavioral Intention</h3><strong>{formatScore(studyEvidence.tam_summary?.task2?.behavioral_intention)} / 10</strong><p>Question 8</p></div>
            </div>

            <div className="adminTableWrap">
              <table className="adminDataTable wideAdminTable">
                <thead><tr><th>Participant</th><th>Ease</th><th>Usefulness</th><th>Intention</th><th>Pantry Awareness</th><th>What Worked</th><th>Confusing / Missing</th><th>Would Improve</th></tr></thead>
                <tbody>
                  {studyRows("task2").map((row, index) => (
                    <tr key={`${row.participant}-${index}`}>
                      <td>{row.participant || "Unknown"}</td>
                      <td>{formatScore(row.ease_of_use)}</td>
                      <td>{formatScore(row.perceived_usefulness)}</td>
                      <td>{formatScore(row.behavioral_intention)}</td>
                      <td>{formatScore(row.pantry_awareness)}</td>
                      <td>{row.worked_well || "—"}</td>
                      <td>{row.confusing_or_missing || "—"}</td>
                      <td>{row.make_more_useful || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {studyRows("task2").length === 0 && <div className="groceryEmpty">No Task 2 feedback for this participant yet.</div>}
          </>
        )}
      </section>

      <section id="task3" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Study Task 3 – Smart Pantry</h2>
            <p>TAM feedback plus behavioral evidence recorded inside Smart Pantry.</p>
          </div>
        </div>

        {studyEvidence && (
          <div className="tamGrid">
            <div><h3>Perceived Ease of Use</h3><strong>{formatScore(studyEvidence.tam_summary?.task3?.ease_of_use)} / 10</strong></div>
            <div><h3>Perceived Usefulness</h3><strong>{formatScore(studyEvidence.tam_summary?.task3?.perceived_usefulness)} / 10</strong></div>
            <div><h3>Behavioral Intention</h3><strong>{formatScore(studyEvidence.tam_summary?.task3?.behavioral_intention)} / 10</strong></div>
          </div>
        )}

        <div className="polishedActionGrid">
          <div className="adminActionCard madeCard"><strong>{metrics.made}</strong><span>Made Meal</span></div>
          <div className="adminActionCard usedCard"><strong>{metrics.usedElsewhere}</strong><span>Used Elsewhere</span></div>
          <div className="adminActionCard savedCard"><strong>{metrics.saved}</strong><span>Saved for Later</span></div>
          <div className="adminActionCard customCard"><strong>{metrics.customMeal}</strong><span>Custom Meals</span></div>
          <div className="adminActionCard notUsedCard"><strong>{metrics.notUsed}</strong><span>Did Not Use</span></div>
        </div>

        {studyEvidence && studyRows("task3").length > 0 && (
          <details className="evidenceDetails">
            <summary>View Task 3 participant feedback</summary>
            <div className="adminTableWrap">
              <table className="adminDataTable wideAdminTable">
                <thead><tr><th>Participant</th><th>Ease</th><th>Usefulness</th><th>Intention</th><th>What Worked</th><th>Confusing / Missing</th><th>Would Improve</th></tr></thead>
                <tbody>{studyRows("task3").map((row, index) => (
                  <tr key={`${row.participant}-${index}`}><td>{row.participant || "Unknown"}</td><td>{formatScore(row.ease_of_use)}</td><td>{formatScore(row.perceived_usefulness)}</td><td>{formatScore(row.behavioral_intention)}</td><td>{row.worked_well || "—"}</td><td>{row.confusing_or_missing || "—"}</td><td>{row.make_more_useful || "—"}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </details>
        )}
      </section>

      <section id="exports" className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Export Study Evidence</h2>
            <p>Download CSV files for thesis charts and results analysis.</p>
          </div>
        </div>

        <div className="exportButtonGrid">
          <button onClick={exportParticipants}>Export Analysis-Ready Participant CSV</button>
          <button onClick={exportResearchOutcomeSummary} disabled={!studyEvidence}>Export Research Outcome Summary CSV</button>
          <button onClick={exportTamSummary} disabled={!studyEvidence}>Export TAM Summary CSV</button>
          <button onClick={() => exportGoogleStudySection("task1", "study_task_1_feedback.csv")} disabled={!studyEvidence}>Export Task 1 Feedback CSV</button>
          <button onClick={() => exportGoogleStudySection("task2", "study_task_2_samsung_food.csv")} disabled={!studyEvidence}>Export Task 2 Feedback CSV</button>
          <button onClick={() => exportGoogleStudySection("task3", "study_task_3_smart_pantry_tam.csv")} disabled={!studyEvidence}>Export Task 3 TAM CSV</button>
          <button onClick={() => exportGoogleStudySection("pre", "pre_study_survey.csv")} disabled={!studyEvidence}>Export Pre-Study CSV</button>
          <button onClick={() => exportGoogleStudySection("post", "post_study_survey.csv")} disabled={!studyEvidence}>Export Post-Study CSV</button>
          <button onClick={exportLogs}>Export Recommendation Logs CSV</button>
          <button onClick={exportPantry}>Export Smart Pantry Data CSV</button>
          <button onClick={exportActivity1}>Export Pantry Note Tracker Entries CSV</button>
        </div>
        {!studyEvidence && <p className="adminMutedNote">Survey/TAM exports are available when the private study response connection is active.</p>}
      </section>

      {studyEvidence?.notes?.length > 0 && (
        <section className="card adminSectionCard researchNoteCard">
          <div className="adminSectionHeader"><div><h2>Study Data Notes</h2><p>Source issues or scoring notes to remember during analysis.</p></div></div>
          <ul>{studyEvidence.notes.map((note) => <li key={note}>{note}</li>)}</ul>
        </section>
      )}

      <section className="card adminSectionCard">
        <div className="adminSectionHeader">
          <div>
            <h2>Participant Evidence Matrix</h2>
            <p>
              One participant-level view combining Google survey completion, TAM scores, manual baseline evidence, and Smart Pantry behavioral evidence.
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
                  <th>Participant</th><th>Consent</th><th>Pre</th><th>Task 1 Items</th><th>Task 1 Useful</th>
                  <th>Task 2 Useful</th><th>Task 2 Intention</th>
                  <th>Task 3 Pantry</th><th>Task 3 Useful</th><th>Task 3 Intention</th>
                  <th>Actions</th><th>Made</th><th>Used Elsewhere</th><th>Saved</th><th>Not Used</th><th>Post</th>
                </tr>
              </thead>
              <tbody>
                {participantEvidence
                  .filter((row) => !selectedParticipantKey || normalizeParticipantKey(row.participant) === selectedParticipantKey)
                  .map((row) => (
                  <tr key={row.participant}>
                    <td>{row.participant}</td><td>{row.consent}</td><td>{row.pre_study}</td><td>{row.task1_items}</td><td>{formatScore(row.task1_tam_usefulness)}</td>
                    <td>{formatScore(row.task2_tam_usefulness)}</td><td>{formatScore(row.task2_tam_intention)}</td>
                    <td>{row.task3_pantry_items}</td><td>{formatScore(row.task3_tam_usefulness)}</td><td>{formatScore(row.task3_tam_intention)}</td>
                    <td>{row.task3_recommendation_actions}</td><td>{row.made_meal}</td><td>{row.used_elsewhere}</td><td>{row.saved_for_later}</td><td>{row.did_not_use}</td><td>{row.post_study}</td>
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
                  <th>Created</th>
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
