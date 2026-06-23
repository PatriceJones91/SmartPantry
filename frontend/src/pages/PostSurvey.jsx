import SurveyForm from "../components/SurveyForm.jsx";
import { postStudyQuestions } from "../data/surveyQuestions.js";

export default function PostSurvey() {
  return (
    <SurveyForm
      surveyType="post"
      title="Post-Study Survey"
      description="Please complete this survey after using Smart Pantry. These questions help measure your experience, satisfaction, and whether the app supported pantry awareness and ingredient use."
      questions={postStudyQuestions}
    />
  );
}
