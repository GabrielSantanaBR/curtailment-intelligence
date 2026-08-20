# Team workflow

## Suggested technical ownership

- **Dev Data/ML:** `ml/`, experiments, model card, validation.
- **Dev Backend/Data:** `app/`, database, ingestion, deployment.
- **Dev Frontend:** `web/` or `frontend/`, dashboard and pitch demo flow.
- **Scrum Master / PM:** backlog, acceptance criteria, integration windows, final demo checklist.
- **Thematic specialist:** domain assumptions, operational feasibility, terminology, mitigation constraints.

## Branches

```text
main
feat/data-*
feat/ml-*
feat/api-*
feat/frontend-*
feat/optimizer-*
docs/*
fix/*
```

Use short pull requests and keep `main` demoable. Avoid one huge branch that is merged hours before the pitch.

## Integration checkpoints

1. Data contract frozen.
2. First real EDA published.
3. Baseline model connected to API.
4. Final candidate model connected.
5. Optimizer assumptions signed off by specialist.
6. Full demo rehearsed on another computer.
7. Repository/README/pitch evidence frozen.
