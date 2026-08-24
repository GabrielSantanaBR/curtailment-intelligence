const isGitHubPages =
  typeof window !== "undefined" && window.location.hostname.endsWith("github.io");

const DEMO_PLANTS = [
  { code: "DEMO-WIND-01", name: "Parque Eólico Alpha", source: "wind", region: "NE", capacity_mw: 180 },
  { code: "DEMO-WIND-02", name: "Parque Eólico Beta", source: "wind", region: "NE", capacity_mw: 220 },
  { code: "DEMO-SOLAR-01", name: "Complexo Solar Gamma", source: "solar", region: "NE", capacity_mw: 145 },
  { code: "DEMO-SOLAR-02", name: "Complexo Solar Delta", source: "solar", region: "SE", capacity_mw: 110 },
];

const OVERVIEW = {
  rows: 24564,
  plants: DEMO_PLANTS.length,
  event_rate_pct: 18.7,
  curtailed_mwh: 18432.6,
  data_mode: "synthetic_demo_static",
};

const MODEL_METRICS = {
  model_version: "demo-logistic-v1",
  decision_threshold: 0.57,
  classifier: {
    pr_auc: 0.574,
    roc_auc: 0.8,
    recall: 0.79,
    precision: 0.46,
    f1: 0.582,
  },
  regressor: {
    mae_mwh: 13.8,
    rmse_mwh: 18.4,
  },
  data_mode: "synthetic_demo_static",
};

const PATTERNS = {
  hourly: Array.from({ length: 24 }, (_, hour) => {
    const wave = Math.sin((hour - 8) / 24 * Math.PI * 2);
    const eventRate = Math.max(4, 16 + wave * 9 + (hour >= 17 && hour <= 21 ? 7 : 0));
    return {
      hour,
      event_rate_pct: Number(eventRate.toFixed(1)),
      curtailed_mwh: Math.round(120 + eventRate * 18),
    };
  }),
  reasons: [
    { restriction_reason: "transmission_constraint", events: 412, mwh: 7810 },
    { restriction_reason: "system_security", events: 287, mwh: 5290 },
    { restriction_reason: "energy_balance", events: 204, mwh: 3515 },
    { restriction_reason: "other", events: 118, mwh: 1818 },
  ],
  regions: [
    { region: "NE", event_rate_pct: 22.4, mwh: 13120 },
    { region: "SE", event_rate_pct: 11.8, mwh: 3310 },
    { region: "S", event_rate_pct: 8.7, mwh: 2003 },
  ],
};

function plantSeed(code) {
  return [...code].reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

function forecastFor(code) {
  const seed = plantSeed(code);
  const risk = Math.min(0.93, 0.58 + (seed % 28) / 100);
  const magnitude = 45 + (seed % 75);
  const level = risk >= 0.8 ? "critical" : risk >= 0.65 ? "high" : "moderate";
  return {
    plant_code: code,
    risk_probability: Number(risk.toFixed(2)),
    risk_level: level,
    decision_threshold: MODEL_METRICS.decision_threshold,
    predicted_curtailed_mwh: Number(magnitude.toFixed(1)),
    data_mode: "synthetic_demo_static",
    explanation: [
      { feature: "network_stress_index", label: "Estresse recente da rede", effect: 0.21 },
      { feature: "recent_event_frequency", label: "Frequência recente de cortes", effect: 0.16 },
      { feature: "available_generation", label: "Geração disponível elevada", effect: 0.11 },
      { feature: "hour_pattern", label: "Padrão temporal", effect: -0.06 },
    ],
  };
}

function historyFor(code, limit = 168) {
  const seed = plantSeed(code);
  const end = Date.UTC(2026, 7, 24, 18, 0, 0);
  const plant = DEMO_PLANTS.find((item) => item.code === code) ?? DEMO_PLANTS[0];
  const points = Array.from({ length: Math.min(limit, 240) }, (_, index) => {
    const hourIndex = index - Math.min(limit, 240) + 1;
    const timestamp = new Date(end + hourIndex * 3600000);
    const hour = timestamp.getUTCHours();
    const solarFactor = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI));
    const windFactor = 0.58 + 0.24 * Math.sin((index + seed) / 8) + 0.12 * Math.sin(index / 3.5);
    const productionFactor = plant.source === "solar" ? solarFactor : Math.max(0.18, windFactor);
    const available = Math.max(0, plant.capacity_mw * productionFactor);
    const stress = Math.min(0.98, Math.max(0.08, 0.38 + 0.3 * Math.sin((index + seed) / 11) + (index % 29 > 23 ? 0.24 : 0)));
    const event = stress > 0.72 && available > plant.capacity_mw * 0.45;
    const curtailed = event ? available * (0.14 + (seed % 7) / 100) : 0;
    return {
      timestamp: timestamp.toISOString(),
      available_generation_mw: Number(available.toFixed(2)),
      actual_generation_mw: Number(Math.max(0, available - curtailed).toFixed(2)),
      network_stress_index: Number(stress.toFixed(3)),
      curtailment_event: event ? 1 : 0,
      curtailed_energy_mwh: Number(curtailed.toFixed(2)),
    };
  });
  return { plant_code: code, points };
}

function optimizeStatic(payload) {
  const profile = payload.curtailed_profile_mwh ?? [];
  let batteryRemaining = Math.max(0, Number(payload.battery_capacity_mwh || 0) - Number(payload.battery_initial_soc_mwh || 0));
  let flexRemaining = Math.max(0, Number(payload.flexible_load_total_mwh || 0));
  const batteryPower = Math.max(0, Number(payload.battery_max_charge_mw || 0));
  const flexPower = Math.max(0, Number(payload.flexible_load_capacity_mw || 0));
  const efficiency = Math.min(1, Math.max(0.01, Number(payload.battery_roundtrip_efficiency || 0.9)));

  const dispatch = profile.map((energy, hour) => {
    const available = Math.max(0, Number(energy));
    const batteryInput = Math.min(available, batteryPower, batteryRemaining / efficiency);
    const batteryRecovered = batteryInput * efficiency;
    batteryRemaining -= batteryRecovered;
    const afterBattery = available - batteryInput;
    const flexible = Math.min(afterBattery, flexPower, flexRemaining);
    flexRemaining -= flexible;
    const recovered = batteryRecovered + flexible;
    return {
      hour,
      available_mwh: Number(available.toFixed(3)),
      battery_mwh: Number(batteryRecovered.toFixed(3)),
      flexible_load_mwh: Number(flexible.toFixed(3)),
      recovered_mwh: Number(recovered.toFixed(3)),
      lost_mwh: Number(Math.max(0, available - recovered).toFixed(3)),
    };
  });

  const total = profile.reduce((sum, value) => sum + Math.max(0, Number(value)), 0);
  const recovered = dispatch.reduce((sum, row) => sum + row.recovered_mwh, 0);
  const lost = Math.max(0, total - recovered);
  const recoveryRate = total > 0 ? (recovered / total) * 100 : 0;
  const energyValue = Number(payload.energy_value_brl_mwh || 220);
  const gridFactor = Number(payload.grid_factor_tco2_mwh || 0.08);

  return {
    plant_code: payload.plant_code ?? "DEMO",
    total_available_mwh: Number(total.toFixed(3)),
    recovered_mwh: Number(recovered.toFixed(3)),
    lost_mwh: Number(lost.toFixed(3)),
    recovery_rate_pct: Number(recoveryRate.toFixed(2)),
    estimated_value_preserved_brl: Number((recovered * energyValue).toFixed(2)),
    estimated_avoided_emissions_tco2: Number((recovered * gridFactor).toFixed(3)),
    strategy_summary: "battery + flexible load",
    dispatch,
    optimizer_status: "github_pages_static_demo",
    notes: [
      "Static GitHub Pages simulation using the same public contract as the backend optimizer.",
      "Technical feasibility must be validated with official data and the thematic specialist.",
    ],
  };
}

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

function staticApi() {
  return {
    overview: async () => OVERVIEW,
    plants: async () => DEMO_PLANTS,
    forecast: async (plantCode) => forecastFor(plantCode),
    history: async (plantCode, limit = 168) => historyFor(plantCode, limit),
    patterns: async () => PATTERNS,
    modelMetrics: async () => MODEL_METRICS,
    scenarios: async () => [],
    optimize: async (payload) => optimizeStatic(payload),
  };
}

const liveApi = {
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

export const api = isGitHubPages ? staticApi() : liveApi;
export const apiMode = isGitHubPages ? "github-pages-static-demo" : "live-backend";
