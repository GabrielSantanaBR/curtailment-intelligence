async function request(path, options = {}) {
  const response = await fetch(path, options);
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
  history: (plantCode, limit = 72) =>
    request(`/api/v1/plants/${plantCode}/history?limit=${limit}`),
};
