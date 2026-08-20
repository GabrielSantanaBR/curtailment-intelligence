# API contract

The dashboard depends on stable REST endpoints so ML and frontend can evolve independently.

## Prediction

`POST /api/v1/predict`

When `features` is omitted, the demo uses the latest synthetic row for the selected plant. During the competition, the backend can replace that data source without changing the response shape.

## Optimization

`POST /api/v1/optimize` receives an hourly curtailed-energy profile plus resource constraints. It returns an hour-by-hour dispatch and aggregate impact.

## CSV inspection

`POST /api/v1/data/inspect-csv` accepts a CSV and reports column normalization/mapping without persisting or training on it.
