import { useState } from "react";
import { api } from "../api/client.js";

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("sp2_user") || "null");
  } catch {
    return null;
  }
}

export default function Feedback() {
  const user = getUser();
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [loading, setLoading] = useState(false);

  async function submitFeedback(e) {
    e.preventDefault();

    const cleaned = feedback.trim();

    if (!cleaned) {
      setStatus({
        type: "error",
        message: "Please type your feedback before sending.",
      });
      return;
    }

    if (!user?.id) {
      setStatus({
        type: "error",
        message: "Please log in again before sending feedback.",
      });
      return;
    }

    setLoading(true);
    setStatus({ type: "", message: "" });

    try {
      await api.submitGeneralFeedback({
        user_id: user.id,
        feedback: cleaned,
      });

      setFeedback("");
      setStatus({
        type: "success",
        message: "Thank you. Your feedback was saved.",
      });
    } catch (err) {
      setStatus({
        type: "error",
        message: err.message || "Could not save feedback right now.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="feedbackPage">
      <section className="feedbackHero">
        <div>
          <p className="eyebrow">Participant feedback</p>
          <h1>Feedback</h1>
          <p>
            Use this page to share anything about Smart Pantry that was helpful,
            confusing, too slow, hard to use, or not working the way you expected.
          </p>
        </div>
      </section>

      <section className="card generalFeedbackCard feedbackPageCard">
        <div>
          <h2>Share App Feedback</h2>
          <p>
            This feedback is separate from the meal recommendation buttons. You can
            use it for login issues, layout problems, mobile sizing, pantry entry,
            surveys, recommendations, or anything else you want the researcher to know.
          </p>
        </div>

        <form onSubmit={submitFeedback} className="generalFeedbackForm">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Type your feedback here..."
            maxLength={500}
          />

          <div className="feedbackFormFooter">
            <span>{feedback.length}/500 characters</span>
            <button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Send Feedback"}
            </button>
          </div>
        </form>

        {status.message && (
          <p className={status.type === "success" ? "success" : "error"}>
            {status.message}
          </p>
        )}
      </section>
    </div>
  );
}
