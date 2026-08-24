# Ambiente de desenvolvimento

Este documento é o ponto de entrada para quem vai programar no projeto.

## 1. Pré-requisitos

- Git
- Python 3.11 ou 3.12
- Node.js 20+ apenas se você for mexer em `frontend/`
- Docker Desktop opcional

## 2. Clone e instalação

```bash
git clone https://github.com/GabrielSantanaBR/curtailment-intelligence.git
cd curtailment-intelligence
python -m venv .venv
```

Ative o ambiente:

```bat
:: Windows
.venv\Scripts\activate
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## 3. Diagnóstico do ambiente

```bash
python scripts/dev.py doctor
```

O comando verifica Python, módulos essenciais, estrutura do projeto e artefatos necessários para rodar o demo.

## 4. Preparar o demo

```bash
python scripts/dev.py bootstrap
```

O bootstrap é idempotente: se dataset e modelos já existirem, eles são reutilizados. Para regenerar intencionalmente:

```bash
python scripts/bootstrap_demo.py --force-data --force-models
```

Para também limpar históricos de previsões/cenários:

```bash
python scripts/bootstrap_demo.py --reset-history
```

## 5. Rodar backend + dashboard

```bash
python scripts/dev.py run
```

- Dashboard: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## 6. Rodar o frontend React

Terminal 1:

```bash
python scripts/dev.py run
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

O Vite encaminha `/api` e `/health` para o backend local, portanto o frontend pode usar caminhos relativos.

## 7. Testes e qualidade

Antes de commit/PR:

```bash
python scripts/dev.py check
```

O comando executa compilação Python, Ruff quando disponível e Pytest.

Individualmente:

```bash
pytest
ruff check app ml scripts tests
```

Frontend:

```bash
cd frontend
npm run build
```

## 8. Onde mexer

| Quero alterar... | Diretório principal |
|---|---|
| Endpoint/API | `app/api/` |
| Schemas de entrada/saída | `app/schemas.py` |
| Banco | `app/models/`, `app/core/db.py` |
| Previsão | `app/services/model_service.py`, `ml/` |
| Features | `ml/features.py` |
| Treinamento | `ml/modeling.py` |
| Adapter ONS | `ml/ons_adapter.py` |
| Otimização | `app/services/optimizer.py` |
| Dashboard atual | `web/` |
| React | `frontend/` |
| Testes | `tests/` |
| Integração com dados oficiais | `scripts/`, `docs/COMPETITION_TRANSITION.md` |

## 9. Regra de ouro do ML

Antes de adicionar uma feature, pergunte:

> Essa informação já existia no instante em que a previsão seria feita?

Se a resposta for não, ela pode causar data leakage.

## 10. Fluxo Git recomendado

```bash
git checkout main
git pull
git checkout -b feat/nome-curto
# desenvolvimento
python scripts/dev.py check
git add .
git commit -m "feat: describe the change"
git push -u origin feat/nome-curto
```

Abra um Pull Request e evite trabalhar diretamente na `main` durante a competição.

## 11. Problemas comuns

### O app diz que os modelos não existem

```bash
python scripts/dev.py bootstrap
```

### Quero limpar todo o demo

```bash
python scripts/bootstrap_demo.py --reset
```

### Banco PostgreSQL não está disponível

Para desenvolvimento local, deixe `DATABASE_URL=sqlite:///./curtailment.db`. Docker Compose usa PostgreSQL.

### Mudei o ML e o resultado não mudou

Force o retreinamento:

```bash
python scripts/bootstrap_demo.py --force-models
```
