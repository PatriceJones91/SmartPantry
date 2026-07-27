const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 20000);

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = Number(options.timeoutMs ?? API_TIMEOUT_MS);
  const { timeoutMs: _ignoredTimeoutMs, ...fetchOptions } = options;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {}),
    },
      ...fetchOptions,
      signal: fetchOptions.signal || controller.signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("The server took too long to respond. Please try again.");
    }
    throw new Error("Could not connect to Smart Pantry. Check the server and try again.");
  } finally {
    window.clearTimeout(timeoutId);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Something went wrong.";
    throw new Error(detail);
  }

  return data;
}

export const api = {
  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ role: "participant", ...payload }),
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

  generateRecommendations: (userId, options = {}) =>
    request("/recommendations/generate", {
      method: "POST",
      timeoutMs: Number(import.meta.env.VITE_RECOMMENDATION_TIMEOUT_MS || 90000),
      body: JSON.stringify({
        user_id: userId,
        limit: options.limit ?? 15,
        candidate_limit: options.candidateLimit ?? 300,
        expiry_window_days: options.expiryWindowDays ?? 7,
        include_debug: Boolean(options.includeDebug),
        meal_types: options.mealTypes ?? [],
        cuisine_types: options.cuisineTypes ?? [],
      }),
    }),

  getRecommendationContract: () => request("/recommendations/contract"),

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

  submitGeneralFeedback: (payload) =>
    request("/recommendations/general-feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  adminSummary: () => request("/admin/summary"),
  adminUsers: () => request("/admin/users"),
  adminSurveys: () => request("/admin/surveys"),
  adminPantry: () => request("/admin/pantry"),
  adminLogs: () => request("/admin/recommendation-logs"),
};
