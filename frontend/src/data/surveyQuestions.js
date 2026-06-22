export const preStudyQuestions = [
  {
    id: "current_method",
    type: "select",
    label: "How do you currently keep track of pantry items?",
    options: [
      "I mostly remember what I have",
      "I write items down",
      "I use notes or a phone app",
      "I check my pantry when needed",
      "I do not currently track pantry items",
      "Other",
    ],
  },
  {
    id: "pantry_awareness",
    type: "scale",
    label: "Before using Smart Pantry, how aware are you of what food items you currently have at home?",
  },
  {
    id: "expiration_awareness",
    type: "scale",
    label: "How aware are you of which pantry items are close to expiring?",
  },
  {
    id: "ingredient_utilization",
    type: "scale",
    label: "How often do you use ingredients you already have before buying more food?",
  },
  {
    id: "meal_planning_confidence",
    type: "scale",
    label: "How confident are you in planning meals based on food already in your pantry?",
  },
  {
    id: "food_waste_awareness",
    type: "scale",
    label: "How aware are you of food that gets wasted or forgotten in your home?",
  },
  {
    id: "recommendation_expectation",
    type: "scale",
    label: "How useful do you think meal recommendations based on your pantry items would be?",
  },
  {
    id: "baseline_satisfaction",
    type: "scale",
    label: "How satisfied are you with your current pantry or meal-planning method?",
  },
  {
    id: "technology_comfort",
    type: "scale",
    label: "How comfortable are you using a web app to track pantry items and meal ideas?",
  },
  {
    id: "expected_usefulness",
    type: "scale",
    label: "How useful do you expect Smart Pantry to be for managing pantry items?",
  },
  {
    id: "biggest_challenge",
    type: "text",
    label: "What is your biggest challenge when trying to use food before it expires?",
  },
  {
    id: "what_you_want_help_with",
    type: "text",
    label: "What would you want Smart Pantry to help you with the most?",
  },
  {
    id: "current_food_waste_reason",
    type: "text",
    label: "What usually causes food to go unused or forgotten in your home?",
  },
];

export const postStudyQuestions = [
  {
    id: "pantry_awareness",
    type: "scale",
    label: "After using Smart Pantry, how aware are you of what food items you currently have at home?",
  },
  {
    id: "expiration_awareness",
    type: "scale",
    label: "After using Smart Pantry, how aware are you of which items are close to expiring?",
  },
  {
    id: "recommendation_usefulness",
    type: "scale",
    label: "How useful were the meal recommendations provided by Smart Pantry?",
  },
  {
    id: "ingredient_utilization",
    type: "scale",
    label: "How much did Smart Pantry help you use ingredients you already had?",
  },
  {
    id: "ease_of_use",
    type: "scale",
    label: "How easy was Smart Pantry to use during the study period?",
  },
  {
    id: "dashboard_usefulness",
    type: "scale",
    label: "How useful was the dashboard for understanding your pantry status?",
  },
  {
    id: "expiration_alert_usefulness",
    type: "scale",
    label: "How useful were the expiration alerts?",
  },
  {
    id: "grocery_suggestion_usefulness",
    type: "scale",
    label: "How useful were the grocery suggestions or missing ingredient information?",
  },
  {
    id: "baseline_comparison",
    type: "scale",
    label: "Compared to your normal pantry method, how much better was Smart Pantry for managing pantry items?",
  },
  {
    id: "continued_use",
    type: "scale",
    label: "How likely would you be to keep using Smart Pantry or a similar app?",
  },
  {
    id: "most_helpful_feature",
    type: "text",
    label: "What feature helped you the most?",
  },
  {
    id: "least_helpful_feature",
    type: "text",
    label: "What feature was confusing, missing, or not useful?",
  },
  {
    id: "recommendation_feedback",
    type: "text",
    label: "How could the meal recommendations be improved?",
  },
  {
    id: "overall_feedback",
    type: "text",
    label: "What would make Smart Pantry easier or more useful for you?",
  },
];
