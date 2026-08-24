import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api";

const navItems = [
  ["overview", "Visão geral"],
  ["prediction", "Predição"],
  ["mitigation", "Mitigação"],
  ["patterns", "Padrões"],
  ["model", "Modelo"],
];

const formatNumber = (value, digits = 1) =>
  Number(value ?? 0).toLocaleString("pt-BR", { maximumFractionDigits: digits });

const formatMoney = (value) =>
  Number(value ?? 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });

function MetricCard({ label, value, detail, tone = "default" }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function Panel({ kicker, title, action, children, className = "" }) {
  return (
    <article className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          {kicker && <p className="eyebrow">{kicker}</p>}
          {title && <h2>{title}</h2>}
        </div>
        {action}
      </div>
      {children}
    </article>
  );
}

function RiskGauge({ probability = 0 }) {
  const percent = Math.round(probability * 100);
  return (
    <div
      className="risk-gauge"
      style={{ "--risk-angle": `${percent * 3.6}deg` }}
      aria-label={`Risco estimado de ${percent}%`}
    >
      <div className="risk-gauge-inner">
        <strong>{percent}%</strong>
        <span>risco</span>
      </div>
    </div>
  );
}

function LoadingBlock({ text = "Carregando dados…" }) {
  return <div className="loading-block">{text}</div>;
}

export default function App() {
  const [activeView, setActiveView] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [plants, setPlants] = useState([]);
  const [plantCode, setPlantCode] = useState("");
  const [forecast, setForecast] = useState(null);
  const [history, setHistory] = useState([]);
  const [patterns, setPatterns] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [error, setError] = useState("");
  const [loadingPlant, setLoadingPlant] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [profile, setProfile] = useState("35, 50, 42, 28, 18, 12");
  const [batteryCapacity, setBatteryCapacity] = useState(80);
  const [batterySoc, setBatterySoc] = useState(10);
  const [batteryPower, setBatteryPower] = useState(40);
  const [flexPower, setFlexPower] = useState(20);
  const [flexTotal, setFlexTotal] = useState(40);

  useEffect(() => {
    Promise.all([api.overview(), api.plants(), api.patterns(), api.modelMetrics()])
      .then(([overviewData, plantData, patternData, metricData]) => {
        setOverview(overviewData);
        setPlants(plantData);
        setPatterns(patternData);
        setModelMetrics(metricData);
        if (plantData.length) setPlantCode(plantData[0].code);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!plantCode) return;
    setLoadingPlant(true);
    setError("");
    Promise.all([api.forecast(plantCode), api.history(plantCode)])
      .then(([forecastData, historyData]) => {
        setForecast(forecastData);
        setHistory(historyData.points ?? []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoadingPlant(false));
  }, [plantCode]);

  const selectedPlant = useMemo(
    () => plants.find((plant) => plant.code === plantCode),
    [plants, plantCode],
  );

  const historyChart = useMemo(
    () =>
      history.slice(-96).map((point) => ({
        time: new Date(point.timestamp).toLocaleString("pt-BR", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
        }),
        available: Number(point.available_generation_mw ?? 0),
        actual: Number(point.actual_generation_mw ?? 0),
        stress: Number(point.network_stress_index ?? 0) * 100,
        event: point.curtailment_event ? 100 : 0,
      })),
    [history],
  );

  const hourlyPatterns = useMemo(
    () =>
      (patterns?.hourly ?? []).map((item) => ({
        hour: `${String(item.hour).padStart(2, "0")}h`,
        risk: Number(item.event_rate_pct ?? 0),
        curtailed: Number(item.curtailed_mwh ?? 0),
      })),
    [patterns],
  );

  const reasons = useMemo(
    () => [...(patterns?.reasons ?? [])].sort((a, b) => Number(b.mwh) - Number(a.mwh)),
    [patterns],
  );

  const runOptimization = async () => {
    const curtailedProfile = profile
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => Number.isFinite(value) && value >= 0);

    if (!curtailedProfile.length) {
      setError("Informe ao menos um valor válido no perfil de energia.");
      return;
    }

    setOptimizing(true);
    setError("");
    try {
      const result = await api.optimize({
        plant_code: plantCode || "DEMO-WIND-01",
        curtailed_profile_mwh: curtailedProfile,
        battery_capacity_mwh: Number(batteryCapacity),
        battery_initial_soc_mwh: Number(batterySoc),
        battery_max_charge_mw: Number(batteryPower),
        battery_roundtrip_efficiency: 0.9,
        flexible_load_capacity_mw: Number(flexPower),
        flexible_load_total_mwh: Number(flexTotal),
        energy_value_brl_mwh: 220,
        grid_factor_tco2_mwh: 0.08,
      });
      setOptimization(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setOptimizing(false);
    }
  };

  const riskPercent = Math.round((forecast?.risk_probability ?? 0) * 100);
  const riskLevel = forecast?.risk_level ?? "aguardando";
  const classifier = modelMetrics?.classifier;
  const regressor = modelMetrics?.regressor;

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">CI</div>
          <div>
            <strong>Curtailment</strong>
            <span>Intelligence</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Navegação principal">
          {navItems.map(([key, label], index) => (
            <button
              key={key}
              type="button"
              className={activeView === key ? "nav-item active" : "nav-item"}
              onClick={() => setActiveView(key)}
            >
              <span className="nav-index">0{index + 1}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-status">
          <span className="status-dot" />
          <div>
            <strong>Modo demonstração</strong>
            <small>Dados sintéticos</small>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">COPPE/UFRJ · Hackathon IA 2026 · Desafio 1</p>
            <h1>Antecipar o corte. Explicar o risco. Aproveitar a energia.</h1>
            <p className="lead">
              Plataforma de apoio à decisão para curtailment renovável com previsão,
              explicabilidade e simulação de mitigação.
            </p>
          </div>

          <div className="plant-control">
            <label htmlFor="plant-select">Usina analisada</label>
            <select
              id="plant-select"
              value={plantCode}
              onChange={(event) => setPlantCode(event.target.value)}
            >
              {plants.map((plant) => (
                <option key={plant.code} value={plant.code}>
                  {plant.name} · {plant.source.toUpperCase()} · {plant.region}
                </option>
              ))}
            </select>
            <small>{selectedPlant ? `${selectedPlant.capacity_mw} MW instalados` : "—"}</small>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {activeView === "overview" && (
          <section className="view-stack">
            <div className="hero-grid">
              <article className="risk-hero panel-glow">
                <div>
                  <p className="eyebrow">Risco nas próximas horas</p>
                  <div className="risk-title-row">
                    <strong>{loadingPlant ? "—" : `${riskPercent}%`}</strong>
                    <span className={`risk-pill ${riskLevel}`}>{riskLevel}</span>
                  </div>
                  <p>
                    Threshold de decisão: {forecast ? `${Math.round(forecast.decision_threshold * 100)}%` : "—"}
                    {forecast ? ` · ${forecast.data_mode}` : ""}
                  </p>
                </div>
                <RiskGauge probability={forecast?.risk_probability ?? 0} />
              </article>

              <article className="energy-hero panel-glow">
                <p className="eyebrow">Energia potencialmente em risco</p>
                <strong>{forecast ? `${formatNumber(forecast.predicted_curtailed_mwh)} MWh` : "—"}</strong>
                <span>estimativa condicionada ao cenário atual</span>
                <div className="hero-divider" />
                <small>
                  Probabilidade e magnitude ficam separadas para reduzir falsa precisão na leitura operacional.
                </small>
              </article>
            </div>

            <div className="metrics-grid">
              <MetricCard label="Taxa de eventos" value={overview ? `${overview.event_rate_pct}%` : "—"} detail="dataset sintético" />
              <MetricCard label="Energia restringida" value={overview ? `${formatNumber(overview.curtailed_mwh, 0)} MWh` : "—"} detail="histórico demo" />
              <MetricCard label="Plantas" value={overview?.plants ?? "—"} detail="eólica + solar" />
              <MetricCard label="Modelo" value={modelMetrics?.model_version ?? "—"} detail="artefato ativo" tone="accent" />
            </div>

            <div className="content-grid wide-left">
              <Panel kicker="Histórico operacional" title="Geração disponível vs. realizada">
                {historyChart.length ? (
                  <div className="chart-shell">
                    <ResponsiveContainer width="100%" height={320}>
                      <AreaChart data={historyChart}>
                        <defs>
                          <linearGradient id="availableFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="currentColor" stopOpacity={0.22} />
                            <stop offset="95%" stopColor="currentColor" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} />
                        <XAxis dataKey="time" minTickGap={40} />
                        <YAxis />
                        <Tooltip />
                        <Area type="monotone" dataKey="available" stroke="currentColor" fill="url(#availableFill)" strokeWidth={2.4} />
                        <Line type="monotone" dataKey="actual" stroke="#a7b9bd" dot={false} strokeWidth={1.8} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <LoadingBlock />
                )}
              </Panel>

              <Panel kicker="Explicabilidade" title="O que está puxando o risco">
                <div className="explanation-list">
                  {(forecast?.explanation ?? []).map((item) => (
                    <div className="explanation-item" key={item.feature}>
                      <div>
                        <strong>{item.label}</strong>
                        <span>{item.effect >= 0 ? "+" : ""}{(item.effect * 100).toFixed(1)} p.p.</span>
                      </div>
                      <div className="progress-track">
                        <span style={{ width: `${Math.min(100, Math.max(8, Math.abs(item.effect) * 240))}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="fine-print">Efeitos locais do modelo não significam causalidade.</p>
              </Panel>
            </div>
          </section>
        )}

        {activeView === "prediction" && (
          <section className="view-stack">
            <Panel
              kicker="Predição temporal"
              title="Estresse de rede e eventos de curtailment"
              action={<span className="soft-badge">últimos {historyChart.length} registros</span>}
            >
              <div className="chart-shell tall">
                <ResponsiveContainer width="100%" height={390}>
                  <LineChart data={historyChart}>
                    <CartesianGrid strokeDasharray="4 4" vertical={false} />
                    <XAxis dataKey="time" minTickGap={42} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="stress" stroke="currentColor" dot={false} strokeWidth={2.4} />
                    <Line type="stepAfter" dataKey="event" stroke="#ff9a82" dot={false} strokeWidth={1.6} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Panel>

            <div className="content-grid equal">
              <Panel kicker="Leitura operacional" title="Interpretação do cenário atual">
                <div className="narrative-number">{riskPercent}%</div>
                <p className="body-copy">
                  O modelo estima risco <strong>{riskLevel}</strong> para a usina selecionada e uma magnitude esperada de <strong>{formatNumber(forecast?.predicted_curtailed_mwh)} MWh</strong>.
                </p>
              </Panel>
              <Panel kicker="Regra de decisão" title="Threshold validado">
                <div className="threshold-card">
                  <span>Acionar alerta a partir de</span>
                  <strong>{forecast ? `${Math.round(forecast.decision_threshold * 100)}%` : "—"}</strong>
                </div>
                <p className="fine-print">O threshold final será recalibrado com os dados oficiais.</p>
              </Panel>
            </div>
          </section>
        )}

        {activeView === "mitigation" && (
          <section className="view-stack">
            <div className="content-grid equal">
              <Panel kicker="Cenário" title="Recursos disponíveis">
                <div className="form-grid">
                  <label className="full-field">Energia restringida por hora (MWh)
                    <input value={profile} onChange={(event) => setProfile(event.target.value)} />
                  </label>
                  <label>Capacidade da bateria (MWh)
                    <input type="number" value={batteryCapacity} onChange={(event) => setBatteryCapacity(event.target.value)} />
                  </label>
                  <label>SOC inicial (MWh)
                    <input type="number" value={batterySoc} onChange={(event) => setBatterySoc(event.target.value)} />
                  </label>
                  <label>Potência de carga (MW)
                    <input type="number" value={batteryPower} onChange={(event) => setBatteryPower(event.target.value)} />
                  </label>
                  <label>Carga flexível/hora (MW)
                    <input type="number" value={flexPower} onChange={(event) => setFlexPower(event.target.value)} />
                  </label>
                  <label className="full-field">Carga flexível total (MWh)
                    <input type="number" value={flexTotal} onChange={(event) => setFlexTotal(event.target.value)} />
                  </label>
                </div>
                <button className="primary-button" type="button" onClick={runOptimization} disabled={optimizing}>
                  {optimizing ? "Otimizando…" : "Otimizar aproveitamento"}
                </button>
              </Panel>

              <Panel kicker="Resultado" title="Melhor despacho no cenário" className="result-panel">
                {optimization ? (
                  <>
                    <div className="result-hero">
                      <strong>{formatNumber(optimization.recovery_rate_pct)}%</strong>
                      <span>da energia potencialmente recuperada</span>
                    </div>
                    <div className="result-list">
                      <div><span>Recuperada</span><strong>{formatNumber(optimization.recovered_mwh)} MWh</strong></div>
                      <div><span>Restante</span><strong>{formatNumber(optimization.lost_mwh)} MWh</strong></div>
                      <div><span>Valor preservado*</span><strong>{formatMoney(optimization.estimated_value_preserved_brl)}</strong></div>
                      <div><span>Emissões evitadas*</span><strong>{formatNumber(optimization.estimated_avoided_tco2)} tCO₂</strong></div>
                    </div>
                  </>
                ) : (
                  <LoadingBlock text="Execute uma otimização para ver o despacho recomendado." />
                )}
              </Panel>
            </div>

            {optimization && (
              <Panel kicker="Despacho horário" title="Alocação da energia restringida">
                <div className="chart-shell">
                  <ResponsiveContainer width="100%" height={330}>
                    <BarChart data={optimization.dispatch}>
                      <CartesianGrid strokeDasharray="4 4" vertical={false} />
                      <XAxis dataKey="hour" tickFormatter={(value) => `H${value}`} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="battery_charge_mwh" stackId="recovery" fill="currentColor" radius={[5, 5, 0, 0]} />
                      <Bar dataKey="flexible_load_mwh" stackId="recovery" fill="#b9f58c" radius={[5, 5, 0, 0]} />
                      <Bar dataKey="lost_mwh" fill="#ff9a82" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>
            )}
          </section>
        )}

        {activeView === "patterns" && (
          <section className="view-stack">
            <div className="content-grid wide-left">
              <Panel kicker="Padrão temporal" title="Taxa de eventos por hora">
                <div className="chart-shell">
                  <ResponsiveContainer width="100%" height={330}>
                    <BarChart data={hourlyPatterns}>
                      <CartesianGrid strokeDasharray="4 4" vertical={false} />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="risk" fill="currentColor" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Panel>

              <Panel kicker="Categorias" title="Energia por motivo simulado">
                <div className="reason-list">
                  {reasons.map((item) => (
                    <div className="reason-row" key={item.restriction_reason}>
                      <div>
                        <span>{String(item.restriction_reason).replaceAll("_", " ")}</span>
                        <small>{item.events} eventos</small>
                      </div>
                      <strong>{formatNumber(item.mwh, 0)} MWh</strong>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          </section>
        )}

        {activeView === "model" && (
          <section className="view-stack">
            <Panel kicker="Validação" title="Saúde do modelo de demonstração">
              <div className="metrics-grid model-metrics">
                <MetricCard label="PR-AUC" value={classifier ? classifier.pr_auc.toFixed(3) : "—"} detail="classificação" />
                <MetricCard label="ROC-AUC" value={classifier ? classifier.roc_auc.toFixed(3) : "—"} detail="classificação" />
                <MetricCard label="Recall" value={classifier ? classifier.recall.toFixed(3) : "—"} detail="eventos encontrados" />
                <MetricCard label="F1" value={classifier ? classifier.f1.toFixed(3) : "—"} detail="equilíbrio" />
                <MetricCard label="MAE energia" value={regressor ? `${formatNumber(regressor.mae_mwh)} MWh` : "—"} detail="magnitude" />
                <MetricCard label="Threshold" value={modelMetrics ? Number(modelMetrics.decision_threshold).toFixed(3) : "—"} detail="validação temporal" tone="accent" />
              </div>
              <div className="model-warning">
                Split cronológico 70/15/15. Métricas atuais pertencem ao dataset sintético e não devem ser apresentadas como desempenho final no ONS.
              </div>
            </Panel>
          </section>
        )}

        <footer>
          <span>Curtailment Intelligence · branch de desenvolvimento</span>
          <span>Dados atuais: demonstração sintética</span>
        </footer>
      </main>
    </div>
  );
}
