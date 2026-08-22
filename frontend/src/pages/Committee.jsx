import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function formatLastUpdated(value) {
  if (!value) return "Not refreshed yet";

  return value.toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function Committee() {
  const [evidenceRows, setEvidenceRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [studyStatus, setStudyStatus] = useState({
    status: "in_progress",
    label: "Study In Progress",
  });

  const studyComplete = studyStatus.status === "completed";
  const studyProcessing = studyStatus.status === "processing";

  async function loadCommitteeData(showLoading = true) {
    try {
      if (showLoading) {
        setLoading(true);
        setError("");
      }
      const evidenceData = await api.committeeEvidence();
      setEvidenceRows(safeArray(evidenceData?.participants));
      setStudyStatus(evidenceData?.studyStatus || {
        status: "in_progress",
        label: "Study In Progress",
      });
      setLastUpdated(evidenceData?.generatedAt ? new Date(evidenceData.generatedAt) : new Date());
    } catch (err) {
      if (showLoading) {
        setError(err.message || "Could not load committee dashboard data.");
      }
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    loadCommitteeData();
    const refreshTimer = window.setInterval(() => loadCommitteeData(false), 30000);
    return () => window.clearInterval(refreshTimer);
  }, []);

  const metrics = useMemo(() => {
    const householdValues = evidenceRows
      .map((row) => Number(row.household))
      .filter((value) => Number.isFinite(value) && value > 0);
    const avgHousehold = householdValues.length
      ? (householdValues.reduce((sum, value) => sum + value, 0) / householdValues.length).toFixed(1)
      : "N/A";

    return evidenceRows.reduce((totals, row) => ({
      ...totals,
      task1Participants: totals.task1Participants + (row.task1Items > 0 ? 1 : 0),
      task3Participants: totals.task3Participants + (row.task3Items > 0 || row.recommendationActions > 0 ? 1 : 0),
      pantryItems: totals.pantryItems + row.task3Items,
      recommendationActions: totals.recommendationActions + row.recommendationActions,
      made: totals.made + row.made,
      customMeal: totals.customMeal + row.custom,
      saved: totals.saved + row.saved,
      notUsed: totals.notUsed + row.notUsed,
      ingredientUtilization: totals.ingredientUtilization + row.utilization,
    }), {
      participants: evidenceRows.length,
      task1Participants: 0,
      task3Participants: 0,
      pantryItems: 0,
      recommendationActions: 0,
      made: 0,
      customMeal: 0,
      saved: 0,
      notUsed: 0,
      ingredientUtilization: 0,
      avgHousehold,
    });
  }, [evidenceRows]);

  return (
    <div className="committeePage">
      <section className="committeeHero">
        <div>
          <p className="eyebrow">Smart Pantry Research Review</p>
          <h1>Committee Dashboard</h1>
          <p>Study evidence prepared for committee review, including current participation, research outcomes, and Smart Pantry behavioral evidence.</p>
        </div>
        <div className="committeeRefreshPanel">
          <span className={`committeeStudyStatus ${studyComplete ? "isComplete" : studyProcessing ? "isProcessing" : "isInProgress"}`}>
            {studyStatus.label || "Study In Progress"}
          </span>
          <button type="button" onClick={() => loadCommitteeData(true)} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh Current Data"}
          </button>
          <small>Last updated: {formatLastUpdated(lastUpdated)}</small>
        </div>
      </section>

      {loading && <section className="card">Loading committee evidence...</section>}
      {error && <section className="card error">{error}</section>}

      {!loading && !error && (
        <>
          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>Current Study Status</h2><p>Fresh participant-only evidence from Smart Pantry and the Task 1 Pantry Note Tracker.</p></div></div>
            <div className="committeeMetricGrid">
              <article><strong>{metrics.participants}</strong><span>Enrolled participant accounts</span></article>
              <article><strong>{metrics.task1Participants}</strong><span>Participants with Task 1 evidence</span></article>
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
            <p className="adminMutedNote">
              {studyComplete
                ? "Final TAM results come from the closed, cleaned Google Forms dataset and remain separate from the live application counts shown here."
                : studyProcessing
                  ? "TAM and matched survey results are currently being processed from the closed Google Forms datasets."
                  : "Final TAM values will be calculated from the Google Form response CSVs after data collection closes."}
            </p>
          </section>

          <section className="card committeeSection">
            <div className="adminSectionHeader"><div><h2>Participant Evidence Matrix</h2><p>One participant-level view of manual baseline evidence and Smart Pantry behavioral evidence. Survey/TAM responses are analyzed separately from Google Sheets.</p></div></div>
            <div className="committeePrivacyNotice" role="note">
              <strong>Participant Privacy Protected</strong>
              <span>Committee members see anonymous participant numbers only. Participant 1 through Participant {metrics.participants} follow the same row order as the private Admin evidence matrix.</span>
            </div>
            <div className="adminTableWrap">
              <table className="adminDataTable wideAdminTable">
                <thead><tr><th>Anonymous Participant</th><th>Household Size</th><th>Task 1 Manual Items</th><th>Task 3 Pantry Items</th><th>Recommendation Actions</th><th>Made Meal</th><th>Custom Meal</th><th>Ingredient Utilization</th><th>Saved</th><th>Did Not Use</th></tr></thead>
                <tbody>{evidenceRows.map((row) => <tr key={row.participantNumber}><td>{row.participant}</td><td>{row.household}</td><td>{row.task1Items}</td><td>{row.task3Items}</td><td>{row.recommendationActions}</td><td>{row.made}</td><td>{row.custom}</td><td>{row.utilization}</td><td>{row.saved}</td><td>{row.notUsed}</td></tr>)}</tbody>
              </table>
            </div>
          </section>

          <section className="card committeeSection committeeStatusNote">
            <h2>{studyComplete ? "Study Completed" : studyProcessing ? "Results Being Processed" : "Analysis Status"}</h2>
            <p>
              {studyComplete
                ? "The study is marked completed. This dashboard shows the final participant-only application and Task 1 evidence. Final conclusions are reported from the closed and cleaned matched dataset."
                : studyProcessing
                  ? "Data collection is closed and the matched survey, TAM, descriptive, and inferential results are being cleaned and analyzed. The participant-only application evidence remains available for committee review."
                  : "The study is still in progress. Refresh Current Data reloads the latest participant-only application and Task 1 evidence. Final pre/post, TAM, descriptive, and inferential analyses will be completed after the final matched dataset is closed and cleaned."}
            </p>
          </section>
        </>
      )}
    </div>
  );
}
