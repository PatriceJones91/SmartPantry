import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeAction(action) {
  return action === "used_elsewhere" ? "custom_meal" : action;
}

export default function Committee() {
  const [users, setUsers] = useState([]);
  const [pantry, setPantry] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [usersData, pantryData, logsData] = await Promise.all([
          api.adminUsers(),
          api.adminPantry(),
          api.adminLogs(),
        ]);
        setUsers(safeArray(usersData));
        setPantry(safeArray(pantryData));
        setLogs(safeArray(logsData));
      } catch (err) {
        setError(err.message || "Could not load committee dashboard data.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const participantUsers = useMemo(() => users.filter((user) => user.role === "participant"), [users]);

  const metrics = useMemo(() => {
    const recommendationLogs = logs.filter((log) => log.action !== "general_feedback");
    const made = recommendationLogs.filter((log) => normalizeAction(log.action) === "made").length;
    const customMeal = recommendationLogs.filter((log) => normalizeAction(log.action) === "custom_meal").length;
    const saved = recommendationLogs.filter((log) => normalizeAction(log.action) === "saved").length;
    const notUsed = recommendationLogs.filter((log) => normalizeAction(log.action) === "not_used").length;
    const ingredientUtilization = made + customMeal;

    const task3ParticipantIds = new Set([
      ...pantry.map((item) => item.user_id),
      ...recommendationLogs.map((log) => log.user_id),
    ].filter(Boolean));

    const householdValues = participantUsers
      .map((user) => Number(user.household_size))
      .filter((value) => Number.isFinite(value) && value > 0);
    const avgHousehold = householdValues.length
      ? (householdValues.reduce((sum, value) => sum + value, 0) / householdValues.length).toFixed(1)
      : "N/A";

    return {
      participants: participantUsers.length,
      task3Participants: task3ParticipantIds.size,
      pantryItems: pantry.filter((item) => item.status !== "deleted").length,
      recommendationActions: recommendationLogs.length,
      made,
      customMeal,
      saved,
      notUsed,
      ingredientUtilization,
      avgHousehold,
    };
  }, [participantUsers, pantry, logs]);

  const evidenceRows = useMemo(() => participantUsers.map((user) => {
    const userLogs = logs.filter((log) => log.user_id === user.id && log.action !== "general_feedback");
    const userPantry = pantry.filter((item) => item.user_id === user.id && item.status !== "deleted");
    return {
      participant: user.username,
      household: user.household_size || "N/A",
      pantryItems: userPantry.length,
      made: userLogs.filter((log) => normalizeAction(log.action) === "made").length,
      custom: userLogs.filter((log) => normalizeAction(log.action) === "custom_meal").length,
      saved: userLogs.filter((log) => normalizeAction(log.action) === "saved").length,
      notUsed: userLogs.filter((log) => normalizeAction(log.action) === "not_used").length,
      utilization: userLogs.filter((log) => ["made", "custom_meal"].includes(normalizeAction(log.action))).length,
    };
  }), [participantUsers, pantry, logs]);

  return (
    <div className="committeePage">
      <section className="committeeHero">
        <div>
          <p className="eyebrow">Smart Pantry Research Review</p>
          <h1>Committee Dashboard</h1>
          <p>Study evidence prepared for committee review, including current participation, research outcomes, and Smart Pantry behavioral evidence.</p>
        </div>
      </section>

      {loading && <section className="card">Loading committee evidence...</section>}
      {error && <section className="card error">{error}</section>}

      {!loading && !error && (
        <>
          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>Current Study Status</h2><p>Live Smart Pantry evidence available from the application database.</p></div></div>
            <div className="committeeMetricGrid">
              <article><strong>{metrics.participants}</strong><span>Enrolled participant accounts</span></article>
              <article><strong>{metrics.task3Participants}</strong><span>Participants with Task 3 evidence</span></article>
              <article><strong>{metrics.pantryItems}</strong><span>Active pantry items</span></article>
              <article><strong>{metrics.avgHousehold}</strong><span>Average household size</span></article>
            </div>
          </section>

          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>How the Research Question Is Evaluated</h2><p>Each outcome uses a different source of evidence.</p></div></div>
            <div className="committeeOutcomeGrid">
              <article><h3>Pantry Awareness</h3><strong>Pre / Post</strong><p>Pre-study and post-study survey responses are compared within participants.</p></article>
              <article><h3>Recommendation Usefulness</h3><strong>Task Feedback + TAM</strong><p>Task ratings, Perceived Usefulness, Perceived Ease of Use, and Behavioral Intention support the usefulness analysis.</p></article>
              <article><h3>Ingredient Utilization</h3><strong>Application Behavior</strong><p>Made Meal and Custom Meal actions provide behavioral evidence of pantry ingredient use.</p></article>
            </div>
          </section>

          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>Smart Pantry Behavioral Evidence</h2><p>Task 3 actions recorded inside Smart Pantry.</p></div></div>
            <div className="committeeMetricGrid committeeActionGrid">
              <article><strong>{metrics.made}</strong><span>Made Meal</span></article>
              <article><strong>{metrics.customMeal}</strong><span>Custom Meals</span></article>
              <article><strong>{metrics.ingredientUtilization}</strong><span>Ingredient Utilization</span></article>
              <article><strong>{metrics.saved}</strong><span>Saved for Later</span></article>
              <article><strong>{metrics.notUsed}</strong><span>Did Not Use</span></article>
              <article><strong>{metrics.recommendationActions}</strong><span>Total recommendation actions</span></article>
            </div>
          </section>

          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>TAM Analysis</h2><p>TAM explains participant acceptance; it does not replace the pantry-awareness or behavioral measures.</p></div></div>
            <div className="committeeOutcomeGrid">
              <article><h3>Perceived Ease of Use</h3><strong>Can participants use it comfortably?</strong></article>
              <article><h3>Perceived Usefulness</h3><strong>Does it help with the pantry and meal-planning task?</strong></article>
              <article><h3>Behavioral Intention</h3><strong>Would participants want to use it again?</strong></article>
            </div>
            <p className="adminMutedNote">Final TAM values will be calculated from the Google Form response CSVs after data collection closes.</p>
          </section>

          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>Participant Evidence Snapshot</h2><p>Participant-level Smart Pantry evidence with household size included as contextual evidence.</p></div></div>
            <div className="adminTableWrap">
              <table className="adminDataTable wideAdminTable">
                <thead><tr><th>Participant</th><th>Household</th><th>Pantry Items</th><th>Made Meal</th><th>Custom Meals</th><th>Ingredient Utilization</th><th>Saved</th><th>Did Not Use</th></tr></thead>
                <tbody>{evidenceRows.map((row) => <tr key={row.participant}><td>{row.participant}</td><td>{row.household}</td><td>{row.pantryItems}</td><td>{row.made}</td><td>{row.custom}</td><td>{row.utilization}</td><td>{row.saved}</td><td>{row.notUsed}</td></tr>)}</tbody>
              </table>
            </div>
          </section>

          <section className="card committeeSection committeeStatusNote">
            <h2>Analysis Status</h2>
            <p>The study is still in progress. This dashboard shows current application evidence only. Final pre/post, TAM, descriptive, and inferential analyses will be completed after the final matched dataset is closed and cleaned.</p>
          </section>
        </>
      )}
    </div>
  );
}
