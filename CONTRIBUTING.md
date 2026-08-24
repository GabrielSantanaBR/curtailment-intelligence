# Contribuindo com o Curtailment Intelligence

O objetivo deste guia é permitir que qualquer integrante consiga fazer uma mudança segura sem precisar entender o projeto inteiro primeiro.

## Ambiente

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/dev.py bootstrap
python scripts/dev.py check
```

## Branches

Use uma branch por tarefa:

- `feat/nome-da-feature`
- `fix/nome-do-bug`
- `docs/nome-da-documentacao`
- `refactor/nome-da-area`
- `data/nome-do-pipeline`
- `ml/nome-do-experimento`

## Commits

Prefira commits pequenos e objetivos:

```text
feat: add risk history endpoint
fix: prevent invalid battery state of charge
docs: explain official data transition
refactor: split csv parsing from api route
test: cover invalid optimization payload
```

Evite mensagens como `update`, `final`, `final2` ou `arrumei`.

## Antes do Pull Request

```bash
python scripts/dev.py check
```

Se alterou `frontend/`:

```bash
cd frontend
npm install
npm run build
```

## Dados

Nunca faça commit de dados oficiais brutos, arquivos confidenciais da competição, credenciais, tokens, `.env`, bancos locais ou artefatos grandes sem decisão explícita da equipe.

Use:

- `data/raw/` para arquivos brutos locais;
- `data/processed/` para dados tratados;
- `data/demo/` para dados sintéticos;
- `artifacts/` para modelos e métricas gerados.

Leia `docs/DATA_GUIDE.md`.

## Machine Learning

Toda alteração de modelo deve responder:

- Qual é o target?
- Qual é o horizonte?
- A feature está disponível no instante da previsão?
- Qual split temporal foi usado?
- Qual baseline foi comparado?
- Quais métricas mudaram?
- Existe risco de leakage?

## Otimização

Toda estratégia nova precisa declarar função objetivo, variáveis de decisão, restrições, unidades e premissas técnicas.

## Pull Request

Inclua resumo, motivo, como testar, impacto em dados/modelos e screenshots quando houver mudança visual.
