# Demo Model Card

## Purpose

Pre-hackathon integration model for a **6-hour curtailment-risk horizon**. It exists to validate the end-to-end software, model API, explanation layer and dashboard before official competition data is available.

## Training data

- Mode: synthetic demo
- Rows: 24,564
- Target: at least one curtailment event in T+1 ... T+6 hours
- Magnitude target: total curtailed MWh in T+1 ... T+6 hours
- Split: chronological 70/15/15
- Test positive rate: 26.3%

## Selected classifier

`logistic_baseline`

The simpler model won the validation PR-AUC comparison in this synthetic dataset. This is intentional: the project selects the better validated candidate rather than assuming a more complex algorithm must be better.

## Test metrics

| Metric | Value |
|---|---:|
| PR-AUC | 0.574 |
| ROC-AUC | 0.800 |
| Precision | 0.461 |
| Recall | 0.790 |
| F1 | 0.582 |
| Brier score | 0.230 |
| Decision threshold | 0.57 |
| Energy MAE | 33.6 MWh |
| Energy RMSE | 48.7 MWh |

## Limitations

These numbers **must not** be quoted as competition performance or ONS-data performance. They only describe the synthetic generator shipped with this repository. The model must be retrained and fully revalidated with the challenge dataset.

## Required before final submission

- define the official prediction horizon;
- audit leakage field by field;
- quantify missingness and data revisions;
- compare against historical-rate/naive baselines;
- inspect calibration;
- validate performance by source, region and plant;
- document model failure modes.
