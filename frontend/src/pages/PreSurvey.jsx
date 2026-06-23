import SurveyForm from "../components/SurveyForm.jsx";
import { preStudyQuestions } from "../data/surveyQuestions.js";

export default function PreSurvey() {
  return (
    <SurveyForm
      surveyType="pre"
      title="Pre-Study Survey"
      description="Please complete this survey before using Smart Pantry. These questions help measure your normal pantry habits before the study begins."
      questions={preStudyQuestions}
    />
  );
}
