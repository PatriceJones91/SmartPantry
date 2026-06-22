import { useEffect, useState } from "react";
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

  useEffect(() => {
    api.getSurveyStatus(user.id).then(setStatus).catch(() => {});
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

      setMessage("Survey submitted. Thank you.");
      const updatedStatus = await api.getSurveyStatus(user.id);
      setStatus(updatedStatus);
    } catch (err) {
      setError(err.message);
    }
  }

  const alreadyCompleted =
    surveyType === "pre" ? status?.pre : surveyType === "post" ? status?.post : false;

  return (
    <div>
      <div className="pageHeader">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      {alreadyCompleted && (
        <div className="card success">
          This survey has already been submitted. You can update and submit again if you need to correct something.
        </div>
      )}

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
