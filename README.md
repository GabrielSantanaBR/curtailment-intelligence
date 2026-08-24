# Curtailment Intelligence

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/GabrielSantanaBR/curtailment-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/GabrielSantanaBR/curtailment-intelligence/actions/workflows/ci.yml)

Plataforma de **apoio à decisão para curtailment de geração renovável**, criada como base técnica para o **Hackathon IA 2026 — COPPE/UFRJ, Desafio 1**.

O objetivo não é apenas prever um possível corte de geração. O sistema foi estruturado para percorrer o ciclo completo:

> **Entender o problema → prever o risco → explicar a previsão → simular respostas → medir o impacto.**

> [!IMPORTANT]
> O repositório funciona hoje com **dados sintéticos de demonstração**. Esses dados servem para validar arquitetura, integração, UX, testes e fluxo de Machine Learning antes da entrada dos dados oficiais. Nenhum resultado demo deve ser apresentado como dado ou conclusão do ONS.

## O que o projeto faz

### 1. Diagnóstico

Organiza e analisa frequência de eventos, energia restringida, padrões horários, diferenças entre regiões/fontes, motivos de restrição e usinas com maior incidência.

### 2. Previsão

O pipeline de ML estima probabilidade de curtailment nas próximas horas, nível de risco, energia esperada em risco e fatores associados à previsão.

### 3. Mitigação

Simula recursos como bateria e carga flexível sob limites explícitos de capacidade, potência e energia disponível.

### 4. Impacto

Mostra MWh potencialmente recuperados, MWh restantes, percentual de aproveitamento e estimativas parametrizadas de valor econômico e emissões.

Essas métricas são **estimativas de cenário**, não resultados operacionais oficiais.

## Arquitetura

```text
                         ┌─────────────────────┐
                         │    Dashboard Web    │
                         │  /web ou React/Vite │
                         └──────────┬──────────┘
                                    │ HTTP / JSON
                                    ▼
┌──────────────────────────────────────────────────────────┐
│                       FastAPI                            │
│  /overview  /plants  /predict  /optimize  /analytics   │
└───────────────┬──────────────────┬───────────────────────┘
                │                  │
                ▼                  ▼
      ┌──────────────────┐   ┌────────────────────┐
      │ Machine Learning │   │ Otimizador Linear │
      │ classificação +  │   │ bateria + carga   │
      │ regressão + XAI  │   │ flexível          │
      └────────┬─────────┘   └─────────┬──────────┘
               │                       │
               └───────────┬───────────┘
                           ▼
                 ┌───────────────────┐
                 │ SQLAlchemy / DB   │
                 │ SQLite/PostgreSQL │
                 └───────────────────┘
                           ▲
                           │
                 ┌─────────┴─────────┐
                 │ Pipeline de Dados │
                 │ demo / ONS / CSV  │
                 └───────────────────┘
```

A separação entre API, ML, dados, otimização e interface permite que os desenvolvedores trabalhem em paralelo.

Mais detalhes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Stack

| Área | Tecnologia |
|---|---|
| Backend | Python + FastAPI |
| Validação | Pydantic |
| Banco | SQLAlchemy + SQLite/PostgreSQL |
| Dados | Pandas + NumPy |
| Machine Learning | scikit-learn |
| Otimização | SciPy `linprog` |
| Model artifacts | Joblib |
| Dashboard principal | HTML + CSS + JavaScript servido pelo FastAPI |
| Frontend de evolução | React + Vite |
| Testes | Pytest + TestClient |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

## Começando rápido

Requisitos: Python **3.11+** e Git.

```bash
git clone https://github.com/GabrielSantanaBR/curtailment-intelligence.git
cd curtailment-intelligence
python -m venv .venv
```

**Windows:**

```bat
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/bootstrap_demo.py
uvicorn app.main:app --reload
```

**Linux/macOS:**

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/bootstrap_demo.py
uvicorn app.main:app --reload
```

Acesse:

- Dashboard: `http://127.0.0.1:8000`
- Swagger/OpenAPI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

Também existem `start_demo.bat` e `start_demo.sh`.

### Docker

```bash
docker compose up --build
```

O stack Docker usa PostgreSQL e expõe a aplicação em `http://localhost:8000`.

## Para quem vai desenvolver

```bash
pip install -r requirements-dev.txt
python scripts/dev.py doctor
python scripts/dev.py bootstrap
python scripts/dev.py check
```

Comandos disponíveis:

```bash
python scripts/dev.py doctor
python scripts/dev.py bootstrap
python scripts/dev.py run
python scripts/dev.py test
python scripts/dev.py check
```

Guia completo: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Estrutura do repositório

```text
curtailment-intelligence/
├── app/                        # FastAPI, banco e regras de aplicação
├── ml/                         # features, treino, adapter ONS e dados sintéticos
├── web/                        # dashboard principal sem build
├── frontend/                   # workspace React/Vite
├── scripts/                    # CLI, bootstrap, auditoria, treino e download
├── tests/                      # testes automatizados
├── docs/                       # documentação técnica
├── reference/                  # payloads de exemplo
├── notebooks/                  # exploração de dados
├── data/
│   ├── raw/                    # dados brutos — não versionar
│   ├── processed/              # dados processados — não versionar
│   └── demo/                   # gerado localmente — não versionar
├── artifacts/                  # modelos/métricas gerados — não versionar
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

Regras de dados: [`docs/DATA_GUIDE.md`](docs/DATA_GUIDE.md).

## API

```text
GET  /health
GET  /api/v1/overview
GET  /api/v1/plants
GET  /api/v1/plants/{plant_code}/history
GET  /api/v1/plants/{plant_code}/forecast
POST /api/v1/predict
POST /api/v1/optimize
GET  /api/v1/scenarios
GET  /api/v1/analytics/patterns
GET  /api/v1/model/metrics
POST /api/v1/data/inspect-csv
```

Contrato detalhado: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

## Machine Learning

O demo compara `LogisticRegression` e `HistGradientBoostingClassifier` e escolhe o melhor candidato por **PR-AUC de validação**. Um `RandomForestRegressor` estima a magnitude condicional do curtailment.

A medida de energia esperada em risco combina:

```text
probabilidade do evento × magnitude condicional prevista
```

A validação é cronológica:

```text
70% treino → 15% validação → 15% teste
```

A camada de explicabilidade atual usa perturbações locais e **não representa causalidade**.

Leia [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

## Otimização

O otimizador maximiza o aproveitamento da energia sujeita a restrições de bateria e carga flexível. Ele respeita balanço energético, capacidade, potência, eficiência e orçamento total de carga flexível.

> [!WARNING]
> Uma recomendação não significa que um recurso real exista naquele local. Localização, conexão, segurança elétrica, regras operacionais e mercado precisam ser validados pelo especialista temático.

## Transição para dados oficiais

Quando os arquivos oficiais forem liberados:

```text
arquivo oficial
    ↓
auditoria de schema
    ↓
validação com especialista
    ↓
definição do instante de previsão
    ↓
remoção de leakage
    ↓
EDA
    ↓
features
    ↓
baseline
    ↓
modelos candidatos
    ↓
validação temporal
    ↓
integração na API existente
```

Primeiro comando:

```bash
python scripts/audit_dataset.py data/raw/arquivo.csv
```

Leia [`docs/COMPETITION_TRANSITION.md`](docs/COMPETITION_TRANSITION.md) antes de modelar.

## Testes e qualidade

```bash
pytest
python scripts/dev.py check
```

O GitHub Actions executa validações de backend/ML e build do frontend em `push` para `main` e Pull Requests.

## Documentação

| Documento | Uso |
|---|---|
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | onboarding de desenvolvimento |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | componentes e responsabilidades |
| [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) | integração frontend/backend/ML |
| [`docs/DATA_GUIDE.md`](docs/DATA_GUIDE.md) | organização e segurança dos dados |
| [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) | limites e avaliação do modelo |
| [`docs/COMPETITION_TRANSITION.md`](docs/COMPETITION_TRANSITION.md) | migração para dados oficiais |
| [`docs/TEAM_WORKFLOW.md`](docs/TEAM_WORKFLOW.md) | trabalho em equipe |
| [`docs/PITCH_STORY.md`](docs/PITCH_STORY.md) | narrativa inicial do pitch |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | pronto vs. demo vs. pendente |

## Roadmap

### Base pré-competição

- [x] arquitetura modular;
- [x] API FastAPI;
- [x] dashboard funcional;
- [x] workspace React;
- [x] SQLite/PostgreSQL;
- [x] dados sintéticos;
- [x] classificação + regressão;
- [x] explicabilidade demo;
- [x] otimização linear;
- [x] testes;
- [x] Docker;
- [x] CI;
- [x] adaptador inicial ONS;
- [x] documentação de onboarding.

### Durante a competição

- [ ] validar schema oficial;
- [ ] documentar target/horizonte;
- [ ] eliminar leakage;
- [ ] realizar EDA real;
- [ ] construir baseline oficial;
- [ ] testar features/modelos;
- [ ] calibrar threshold;
- [ ] validar mitigação;
- [ ] substituir métricas demo por oficiais;
- [ ] preparar demo e pitch.

## Como contribuir

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md).

Fluxo curto:

```bash
git checkout main
git pull
git checkout -b feat/minha-mudanca
python scripts/dev.py check
git add .
git commit -m "feat: descreve a mudança"
git push -u origin feat/minha-mudanca
```

## Integridade científica

1. **Sem leakage:** campos conhecidos só depois do corte não entram em uma previsão anterior.
2. **Sem falsa certeza:** probabilidade de risco não é garantia de evento.
3. **Sem mitigação fictícia:** cenários precisam declarar premissas e limites.

## Licença

Distribuído sob licença [MIT](LICENSE).
