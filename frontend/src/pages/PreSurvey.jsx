import SurveyForm from "../components/SurveyForm.jsx";
import { preStudyQuestions } from "../data/surveyQuestions.js";

export default function PreSurvey() {
  return (
    <SurveyForm
      surveyType="pre"
      title="Pre-Study Survey"
      description="Answer these before using Smart Pantry during the 7–14 day study period."
      questions={preStudyQuestions}
    />
  );
}
