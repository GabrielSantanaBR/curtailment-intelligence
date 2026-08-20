# Architecture

```mermaid
flowchart LR
    ONS[ONS / competition data] --> ADAPTER[Ingestion & schema adapter]
    ADAPTER --> FEAT[Feature engineering]
    FEAT --> CLF[Risk classifier]
    FEAT --> REG[Curtailed-energy regressor]
    CLF --> API[FastAPI]
    REG --> API
    API --> XAI[Local explanation]
    API --> OPT[Scenario optimizer]
    OPT --> IMPACT[Impact metrics]
    API --> UI[Dashboard]
    API --> DB[(PostgreSQL / SQLite)]
```

## Separation of concerns

- **Prediction** answers: how likely is a curtailment event under currently available information?
- **Magnitude** answers: if the event occurs, what magnitude is plausible?
- **Optimization** answers: under explicitly declared hypothetical assets/constraints, how much energy can be absorbed?
- **Impact** translates recovered energy into scenario KPIs.

The separation is intentional. It prevents the UI from calling every downstream calculation “AI” and makes the pitch technically defensible.
