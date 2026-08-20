# Transition to official competition data

## 1. Freeze the raw files

Store untouched files in `data/raw/`. Record source, download date and any challenge-specific version. ONS says its open constrained-off data may be revised during recurring consistency processes, so reproducibility matters.

## 2. Confirm the prediction timestamp

Before creating features, write one sentence:

> At time T, the system predicts whether plant P will be curtailed in horizon H using only information that would have been available at or before T.

Any field that is only known after the restriction starts must be excluded from predictors.

## 3. Build the target deliberately

Possible targets to test, depending on the official data:

- event in the next 1/3/6 hours;
- curtailed MWh in the next H hours;
- risk category by plant/region.

Do not assume hourly data unless the challenge data supports it.

## 4. Feature groups

Candidates, only if available/allowed:

- calendar and seasonality;
- plant technology/capacity;
- generation available/forecast;
- historical rolling curtailment statistics computed strictly from past rows;
- system load and renewable penetration;
- network/system indicators;
- weather variables if supplied/allowed.

## 5. Validation

Use chronological holdouts. Prefer PR-AUC/recall/F1 over accuracy for an imbalanced event target. Compare against a naive historical-rate baseline.

## 6. Mitigation model

The optimization module is already usable, but its inputs must be presented as scenarios unless the competition provides real storage/flexible-load assets. Confirm with the thematic specialist:

- connection location;
- MW/MWh limits;
- charge efficiency;
- dispatch feasibility;
- grid constraints;
- market/operational rules.

## 7. Final evidence

The pitch should clearly separate:

- observed historical results;
- model-estimated risk;
- simulated mitigation;
- scenario-estimated economic/environmental impact.

## Fast data audit command

As soon as a CSV arrives, run:

```bash
python scripts/audit_dataset.py data/raw/FILE.csv
```

The report flags missingness, duplicates, time parsing, detected ONS-style fields and **potential leakage/post-event columns** for manual review. The leakage list is a warning system, not an automatic verdict.
