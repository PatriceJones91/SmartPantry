const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong.");
  }

  return data;
}

export const api = {
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getPantry: (userId) => request(`/pantry/${userId}`),

  addPantryItem: (payload) =>
    request("/pantry", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updatePantryItem: (itemId, payload) =>
    request(`/pantry/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deletePantryItem: (itemId) =>
    request(`/pantry/${itemId}`, {
      method: "DELETE",
    }),

  lookupBarcode: (barcode) => request(`/barcodes/${barcode}`),

  searchBarcodeItems: (query) =>
    request(`/barcodes?q=${encodeURIComponent(query)}&limit=10`),

  submitSurvey: (payload) =>
    request("/surveys", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getSurveyStatus: (userId) => request(`/surveys/status/${userId}`),

  generateRecommendations: (userId) =>
    request("/recommendations/generate", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  saveRecommendationAction: (payload) =>
    request("/recommendations/action", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getRecommendationHistory: (userId) =>
    request(`/recommendations/history/${userId}`),

  getProfile: (userId) => request(`/profile/${userId}`),

  updateProfile: (userId, payload) =>
    request(`/profile/${userId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  adminSummary: () => request("/admin/summary"),
  adminUsers: () => request("/admin/users"),
  adminSurveys: () => request("/admin/surveys"),
  adminPantry: () => request("/admin/pantry"),
  adminLogs: () => request("/admin/recommendation-logs"),
};
