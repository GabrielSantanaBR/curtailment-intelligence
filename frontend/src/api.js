async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  overview: () => request("/api/v1/overview"),
  plants: () => request("/api/v1/plants"),
  forecast: (plantCode) => request(`/api/v1/plants/${plantCode}/forecast`),
  history: (plantCode, limit = 168) =>
    request(`/api/v1/plants/${plantCode}/history?limit=${limit}`),
  patterns: () => request("/api/v1/analytics/patterns"),
  modelMetrics: () => request("/api/v1/model/metrics"),
  scenarios: (limit = 8) => request(`/api/v1/scenarios?limit=${limit}`),
  optimize: (payload) =>
    request("/api/v1/optimize", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
