import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function getDefaultAnswers(questions) {
  const answers = {};

  questions.forEach((question) => {
    if (question.type === "scale") {
      answers[question.id] = "5";
    } else if (question.type === "select") {
      answers[question.id] = question.options?.[0] || "";
    } else {
      answers[question.id] = "";
    }
  });

  return answers;
}

export default function SurveyForm({ surveyType, title, description, questions }) {
  const user = getUser();
  const [answers, setAnswers] = useState(() => getDefaultAnswers(questions));
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await api.getSurveyStatus(user.id);
        setStatus(data);
      } catch {
        setStatus({ pre: false, post: false });
      } finally {
        setLoadingStatus(false);
      }
    }

    loadStatus();
  }, [user.id]);

  function change(questionId, value) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  }

  async function submit(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      const textResponses = questions
        .filter((question) => question.type === "text")
        .map((question) => `${question.label}: ${answers[question.id] || ""}`)
        .join("\n\n");

      await api.submitSurvey({
        user_id: user.id,
        survey_type: surveyType,
        responses: answers,
        comments: textResponses,
      });

      setMessage("Survey saved successfully. You may continue using Smart Pantry.");

      const updatedStatus = await api.getSurveyStatus(user.id);
      setStatus(updatedStatus);
    } catch (err) {
      setError(err.message);
    }
  }

  const alreadyCompleted =
    surveyType === "pre" ? status?.pre : surveyType === "post" ? status?.post : false;

  if (loadingStatus) {
    return (
      <div>
        <div className="pageHeader">
          <h1>{title}</h1>
          <p>{description}</p>
        </div>

        <section className="card">
          Loading survey status...
        </section>
      </div>
    );
  }

  if (alreadyCompleted) {
    return (
      <div>
        <div className="pageHeader">
          <h1>{title}</h1>
          <p>{description}</p>
        </div>

        <section className="card surveyCompleteCard">
          <div className="surveyCompleteIcon">✓</div>

          <div>
            <h2>
              {surveyType === "pre"
                ? "Pre-Study Survey Complete"
                : "Post-Study Survey Complete"}
            </h2>

            <p>
              Thank you. Your survey response has already been saved for the Smart Pantry study.
              You do not need to complete this survey again.
            </p>

            <div className="surveyCompleteActions">
              <Link to="/">Back to Dashboard</Link>

              {surveyType === "pre" && (
                <Link to="/pantry">Continue to My Pantry</Link>
              )}

              {surveyType === "post" && (
                <Link to="/history">View Recommendation History</Link>
              )}
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div>
      <div className="pageHeader">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      <section className="card">
        <form className="surveyForm" onSubmit={submit}>
          {questions.map((question, index) => (
            <div className="questionBlock" key={question.id}>
              <label>
                {index + 1}. {question.label}
              </label>

              {question.type === "scale" && (
                <>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={answers[question.id]}
                    onChange={(e) => change(question.id, e.target.value)}
                  />
                  <div className="scaleRow">
                    <span>1 - Low</span>
                    <strong>{answers[question.id]}</strong>
                    <span>10 - High</span>
                  </div>
                </>
              )}

              {question.type === "select" && (
                <select
                  value={answers[question.id]}
                  onChange={(e) => change(question.id, e.target.value)}
                >
                  {question.options.map((option) => (
                    <option key={option}>{option}</option>
                  ))}
                </select>
              )}

              {question.type === "text" && (
                <textarea
                  value={answers[question.id]}
                  onChange={(e) => change(question.id, e.target.value)}
                  placeholder="Type your response here..."
                />
              )}
            </div>
          ))}

          <button type="submit">
            Submit {surveyType === "pre" ? "Pre-Study" : "Post-Study"} Survey
          </button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </div>
  );
}
