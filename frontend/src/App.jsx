import { useEffect, useState } from "react";
import { api } from "./api";

function Metric({ label, value, detail }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export default function App() {
  const [overview, setOverview] = useState(null);
  const [plants, setPlants] = useState([]);
  const [plantCode, setPlantCode] = useState("");
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.overview(), api.plants()])
      .then(([overviewData, plantData]) => {
        setOverview(overviewData);
        setPlants(plantData);
        if (plantData.length) setPlantCode(plantData[0].code);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!plantCode) return;
    api.forecast(plantCode)
      .then(setForecast)
      .catch((err) => setError(err.message));
  }, [plantCode]);

  return (
    <main className="shell">
      <header>
        <div>
          <p className="eyebrow">React workspace</p>
          <h1>Curtailment Intelligence</h1>
          <p className="subtitle">
            Base desacoplada para o DEV Front evoluir sem tocar no código de ML.
          </p>
        </div>
        <select value={plantCode} onChange={(event) => setPlantCode(event.target.value)}>
          {plants.map((plant) => (
            <option key={plant.code} value={plant.code}>
              {plant.name}
            </option>
          ))}
        </select>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="metrics">
        <Metric
          label="Risco atual"
          value={forecast ? `${Math.round(forecast.risk_probability * 100)}%` : "—"}
          detail={forecast?.risk_level ?? "carregando"}
        />
        <Metric
          label="Energia esperada em risco"
          value={forecast ? `${forecast.predicted_curtailed_mwh.toLocaleString("pt-BR")} MWh` : "—"}
          detail="demo sintético"
        />
        <Metric
          label="Plantas no demo"
          value={overview?.plants ?? "—"}
          detail="eólica + solar"
        />
        <Metric
          label="Taxa de eventos"
          value={overview ? `${overview.event_rate_pct}%` : "—"}
          detail="dataset demo"
        />
      </section>

      <section className="panel">
        <p className="eyebrow">Contrato</p>
        <h2>Frontend consome apenas `/api/v1/*`</h2>
        <p>
          Mantenha modelagem, regras de negócio e otimização no backend. Isso permite trocar o
          modelo final sem reescrever a interface.
        </p>
      </section>
    </main>
  );
}
