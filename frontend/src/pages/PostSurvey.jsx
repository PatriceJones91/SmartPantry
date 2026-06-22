import SurveyForm from "../components/SurveyForm.jsx";
import { postStudyQuestions } from "../data/surveyQuestions.js";

export default function PostSurvey() {
  return (
    <SurveyForm
      surveyType="post"
      title="Post-Study Survey"
      description="Answer these after using Smart Pantry during the study period."
      questions={postStudyQuestions}
    />
  );
}
