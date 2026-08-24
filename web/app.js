const $ = (id) => document.getElementById(id);

const state = {
  plants: [],
  plant: null,
  forecast: null,
  history: [],
  metrics: null,
  patterns: null,
};

const formatNumber = (value, digits = 1) =>
  Number(value ?? 0).toLocaleString("pt-BR", { maximumFractionDigits: digits });

const formatMoney = (value) =>
  Number(value ?? 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });

async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error((await response.text()) || `HTTP ${response.status}`);
  }
  return response.json();
}

function drawLineChart(target, series) {
  const element = $(target);
  if (!element || !series.length) return;

  const width = 900;
  const height = 280;
  const padding = 34;
  const x = series.map(
    (_, index) => padding + (index * (width - 2 * padding)) / Math.max(1, series.length - 1),
  );
  const values = series.flatMap((item) => [item.a, item.b ?? item.a]).filter(Number.isFinite);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(1, max - min);
  const y = (value) => height - padding - ((value - min) * (height - 2 * padding)) / span;

  let grid = "";
  for (let index = 0; index < 5; index += 1) {
    const yy = padding + (index * (height - 2 * padding)) / 4;
    grid += `<line class="gridline" x1="${padding}" y1="${yy}" x2="${width - padding}" y2="${yy}"/>`;
  }

  const pathA = series
    .map((item, index) => `${index ? "L" : "M"}${x[index].toFixed(1)},${y(item.a).toFixed(1)}`)
    .join(" ");

  const hasSecondSeries = series.some((item) => Number.isFinite(item.b));
  const pathB = hasSecondSeries
    ? series
        .map((item, index) => `${index ? "L" : "M"}${x[index].toFixed(1)},${y(item.b).toFixed(1)}`)
        .join(" ")
    : "";

  element.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img">
      ${grid}
      <path class="line-a" d="${pathA}" />
      ${pathB ? `<path class="line-b" d="${pathB}" />` : ""}
    </svg>
  `;
}

function drawBarChart(target, series) {
  const element = $(target);
  if (!element || !series.length) return;

  const width = 900;
  const height = 280;
  const padding = 34;
  const max = Math.max(...series.map((item) => item.v), 1);
  const barWidth = (width - 2 * padding) / series.length;
  let bars = "";
  let labels = "";

  series.forEach((item, index) => {
    const barHeight = ((height - 2 * padding) * item.v) / max;
    const x = padding + index * barWidth + 2;
    const y = height - padding - barHeight;
    bars += `<rect class="bar" x="${x}" y="${y}" width="${Math.max(2, barWidth - 5)}" height="${barHeight}" rx="3"/>`;
    if (index % 3 === 0) {
      labels += `<text class="axis-label" x="${x}" y="${height - 10}">${item.label}</text>`;
    }
  });

  element.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img">
      ${bars}${labels}
    </svg>
  `;
}

function renderOverview(overview) {
  $("eventRate").textContent = `${formatNumber(overview.event_rate_pct)}%`;
  $("totalCurtailed").textContent = `${formatNumber(overview.curtailed_mwh, 0)} MWh`;
  $("plantCount").textContent = overview.plants;
}

function renderPlantMeta() {
  if (!state.plant) return;
  $("plantMeta").textContent = `${state.plant.capacity_mw} MW instalados · ${state.plant.source.toUpperCase()} · ${state.plant.region}`;
}

function renderForecast() {
  const forecast = state.forecast;
  if (!forecast) return;

  const probability = Math.round(forecast.risk_probability * 100);
  $("riskValue").textContent = `${probability}%`;
  $("ringText").textContent = `${probability}%`;
  $("riskRing").style.setProperty("--p", `${probability * 3.6}deg`);
  $("riskLevel").textContent = forecast.risk_level;
  $("riskSubtitle").textContent = `Threshold de decisão: ${Math.round(
    forecast.decision_threshold * 100,
  )}% · ${forecast.data_mode}`;
  $("energyRisk").textContent = `${formatNumber(forecast.predicted_curtailed_mwh)} MWh`;
  $("thresholdValue").textContent = `${Math.round(forecast.decision_threshold * 100)}%`;
  $("predictionNarrative").textContent = `O modelo estima ${probability}% de risco e ${formatNumber(
    forecast.predicted_curtailed_mwh,
  )} MWh esperados para o cenário atual.`;

  renderExplanation();
}

function renderExplanation() {
  const items = state.forecast?.explanation ?? [];
  const maxEffect = Math.max(...items.map((item) => Math.abs(item.effect)), 0.01);

  $("explanationList").innerHTML = items
    .map(
      (item) => `
        <div class="explain-row">
          <div class="explain-top">
            <span>${item.label}</span>
            <span>${item.effect >= 0 ? "+" : ""}${(item.effect * 100).toFixed(1)} p.p.</span>
          </div>
          <div class="explain-track">
            <div class="explain-fill" style="width:${Math.max(
              6,
              (Math.abs(item.effect) / maxEffect) * 100,
            )}%"></div>
          </div>
        </div>
      `,
    )
    .join("");
}

function renderHistory() {
  const recent = state.history.slice(-72);
  drawLineChart(
    "generationChart",
    recent.map((point) => ({
      a: Number(point.available_generation_mw ?? 0),
      b: Number(point.actual_generation_mw ?? 0),
    })),
  );

  drawLineChart(
    "riskChart",
    recent.map((point) => ({
      a: Number(point.network_stress_index ?? 0) * 100,
      b: point.curtailment_event ? 100 : 0,
    })),
  );
}

function renderPatterns() {
  if (!state.patterns) return;

  drawBarChart(
    "hourlyChart",
    state.patterns.hourly.map((item) => ({
      label: `${String(item.hour).padStart(2, "0")}h`,
      v: Number(item.event_rate_pct ?? 0),
    })),
  );

  $("reasonList").innerHTML = [...state.patterns.reasons]
    .sort((a, b) => Number(b.mwh) - Number(a.mwh))
    .map(
      (item) => `
        <div class="reason-row">
          <span>${String(item.restriction_reason).replaceAll("_", " ")}</span>
          <strong>${formatNumber(item.mwh, 0)} MWh</strong>
        </div>
      `,
    )
    .join("");
}

function renderMetrics() {
  const classifier = state.metrics?.classifier;
  const regressor = state.metrics?.regressor;
  if (!classifier || !regressor) return;

  const items = [
    ["PR-AUC", classifier.pr_auc],
    ["ROC-AUC", classifier.roc_auc],
    ["Recall", classifier.recall],
    ["F1", classifier.f1],
    ["MAE energia", `${regressor.mae_mwh} MWh`],
    ["Threshold", state.metrics.decision_threshold],
  ];

  $("modelMetrics").innerHTML = items
    .map(
      ([label, value]) => `
        <article class="metric">
          <span>${label}</span>
          <strong>${typeof value === "number" ? value.toFixed(3) : value}</strong>
          <small>demo validation</small>
        </article>
      `,
    )
    .join("");
}

async function loadPlant(code) {
  const select = $("plantSelect");
  select.disabled = true;
  try {
    state.plant = state.plants.find((plant) => plant.code === code) ?? null;
    renderPlantMeta();

    const [forecast, history] = await Promise.all([
      request(`/api/v1/plants/${code}/forecast`),
      request(`/api/v1/plants/${code}/history?limit=168`),
    ]);

    state.forecast = forecast;
    state.history = history.points ?? [];
    renderForecast();
    renderHistory();
  } finally {
    select.disabled = false;
  }
}

async function loadBase() {
  const [plants, overview, metrics, patterns] = await Promise.all([
    request("/api/v1/plants"),
    request("/api/v1/overview"),
    request("/api/v1/model/metrics"),
    request("/api/v1/analytics/patterns"),
  ]);

  state.plants = plants;
  state.metrics = metrics;
  state.patterns = patterns;

  $("plantSelect").innerHTML = plants
    .map(
      (plant) =>
        `<option value="${plant.code}">${plant.name} · ${plant.source.toUpperCase()} · ${plant.region}</option>`,
    )
    .join("");

  $("modelVersion").textContent = metrics.model_version;
  renderOverview(overview);
  renderPatterns();
  renderMetrics();

  if (plants.length) {
    await loadPlant(plants[0].code);
  }
}

async function optimize() {
  const profile = $("profileInput")
    .value.split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isFinite(value) && value >= 0);

  if (!profile.length) {
    $("optMessage").textContent = "Informe ao menos um valor válido de energia.";
    return;
  }

  const payload = {
    plant_code: $("plantSelect").value,
    curtailed_profile_mwh: profile,
    battery_capacity_mwh: Number($("batteryCap").value),
    battery_initial_soc_mwh: Number($("batterySoc").value),
    battery_max_charge_mw: Number($("batteryPower").value),
    battery_roundtrip_efficiency: 0.9,
    flexible_load_capacity_mw: Number($("flexPower").value),
    flexible_load_total_mwh: Number($("flexTotal").value),
    energy_value_brl_mwh: 220,
    grid_factor_tco2_mwh: 0.08,
  };

  const button = $("runOptimization");
  const previousLabel = button.textContent;
  button.disabled = true;
  button.textContent = "Otimizando...";
  $("optMessage").textContent = "Resolvendo o melhor despacho dentro das restrições...";

  try {
    const output = await request("/api/v1/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    $("recoveryPct").textContent = `${formatNumber(output.recovery_rate_pct)}%`;
    $("recoveredMwh").textContent = `${formatNumber(output.recovered_mwh)} MWh`;
    $("lostMwh").textContent = `${formatNumber(output.lost_mwh)} MWh`;
    $("valuePreserved").textContent = formatMoney(output.estimated_value_preserved_brl);
    $("optMessage").textContent = "Cenário otimizado e salvo no histórico.";

    drawBarChart(
      "dispatchChart",
      output.dispatch.map((item) => ({
        label: `H${item.hour}`,
        v: Number(item.recovered_mwh ?? 0),
      })),
    );
  } catch (error) {
    $("optMessage").textContent = `Erro: ${error.message}`;
  } finally {
    button.disabled = false;
    button.textContent = previousLabel;
  }
}

function activateView(viewName) {
  document.querySelectorAll(".nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${viewName}`);
  });

  history.replaceState(null, "", `#${viewName}`);
}

document.querySelectorAll(".nav").forEach((button) => {
  button.addEventListener("click", () => activateView(button.dataset.view));
});

$("plantSelect").addEventListener("change", (event) => loadPlant(event.target.value));
$("refreshForecast").addEventListener("click", () => loadPlant($("plantSelect").value));
$("runOptimization").addEventListener("click", optimize);

const initialView = window.location.hash.replace("#", "");
if (["overview", "prediction", "mitigation", "patterns", "model"].includes(initialView)) {
  activateView(initialView);
}

loadBase()
  .then(optimize)
  .catch((error) => {
    console.error(error);
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div style="position:fixed;bottom:20px;right:20px;max-width:360px;background:#3b1d1b;border:1px solid #7b3932;padding:12px 14px;border-radius:12px;z-index:200">Falha ao iniciar: ${error.message}</div>`,
    );
  });
