# API Contract

Base URL local: `http://127.0.0.1:8000`

A documentação interativa completa fica em `/docs`.

## Convenções

- JSON em UTF-8.
- Timestamps preferencialmente em ISO-8601/UTC.
- Potência em MW.
- Energia em MWh.
- Probabilidades em `0..1`.
- Percentuais exibidos pela API que terminam em `_pct` usam `0..100`.

## Health

```http
GET /health
```

Exemplo:

```json
{
  "status": "ok",
  "app": "Curtailment Intelligence API",
  "version": "1.0.0",
  "environment": "development"
}
```

## Plants

```http
GET /api/v1/plants
```

Retorna o catálogo de usinas atualmente carregado no banco.

## Histórico

```http
GET /api/v1/plants/{plant_code}/history?limit=168
```

O limite é normalizado entre 24 e 1000 registros.

## Forecast

```http
GET /api/v1/plants/{plant_code}/forecast
```

Usa a linha mais recente disponível para a usina no dataset carregado.

## Predict

```http
POST /api/v1/predict
Content-Type: application/json
```

O payload mínimo pode fornecer apenas a usina e usar as features atuais do dataset:

```json
{
  "plant_code": "DEMO-WIND-01"
}
```

Ou pode fornecer `features` explicitamente conforme `FeaturePayload` em `app/schemas.py`.

Resposta principal:

```json
{
  "plant_code": "DEMO-WIND-01",
  "risk_probability": 0.72,
  "risk_level": "high",
  "decision_threshold": 0.43,
  "predicted_curtailed_mwh": 18.4,
  "explanation": [],
  "model_version": "demo-...",
  "data_mode": "synthetic_demo"
}
```

## Optimize

```http
POST /api/v1/optimize
```

Veja payload completo em `reference/optimization_request.json`.

O resultado retorna:

- energia total do perfil;
- energia recuperada;
- energia perdida;
- percentual recuperado;
- impacto econômico parametrizado;
- estimativa parametrizada de emissões;
- despacho por hora;
- premissas do cenário.

## Scenarios

```http
GET /api/v1/scenarios?limit=20
```

Lista os cenários de otimização persistidos mais recentemente.

## Analytics

```http
GET /api/v1/overview
GET /api/v1/analytics/patterns
```

No estado atual, essas rotas descrevem o dataset sintético.

## Model metrics

```http
GET /api/v1/model/metrics
```

Retorna `metrics.json` do artefato carregado.

## Inspect CSV

```http
POST /api/v1/data/inspect-csv
Content-Type: multipart/form-data
```

Campo: `file`.

Limite atual: 25 MB.

O endpoint não treina modelo. Ele apenas tenta interpretar o arquivo e identificar colunas conhecidas.
