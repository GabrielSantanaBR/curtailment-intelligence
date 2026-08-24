# Arquitetura

## Objetivo

Permitir desenvolvimento paralelo durante o hackathon e evitar que alterações em ML obriguem o frontend a ser refeito.

## Componentes

```text
                        CLIENTES
                ┌──────────┴──────────┐
                │                     │
          Dashboard /web        React /frontend
                │                     │
                └──────────┬──────────┘
                           │ REST/JSON
                           ▼
                     app/api/routes.py
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   data_service       model_service      optimizer
          │                │                │
          │                ▼                │
          │             ml/*                │
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                     SQLAlchemy / DB
```

## `app/api`

Responsável por HTTP:

- validação de entrada;
- códigos de status;
- serialização;
- chamada dos services;
- persistência de logs/cenários.

Não deve conter algoritmo de ML nem formulação matemática complexa.

## `app/services`

Camada de aplicação:

- `data_service.py`: acesso aos dados usados pela demo;
- `model_service.py`: carregamento de modelos, previsão e explicação;
- `optimizer.py`: formulação de otimização;
- `analytics.py`: agregações do dashboard.

## `ml`

Camada de ciência de dados:

- `constants.py`: contrato de features/targets;
- `features.py`: engenharia de features;
- `modeling.py`: treino, seleção e métricas;
- `ons_adapter.py`: ingestão/adaptação de fontes externas;
- `synthetic.py`: somente demonstração.

## Persistência

SQLite é o padrão local por simplicidade. Em Docker, PostgreSQL é usado para deixar a arquitetura próxima de uma implantação real.

Atualmente `Base.metadata.create_all` é suficiente para o protótipo. Se a modelagem de banco começar a mudar com frequência, o próximo passo é introduzir Alembic.

## Frontends

### `/web`

Interface principal do demo. Não exige Node/npm e é servida pelo próprio FastAPI. Deve continuar sendo o plano de contingência offline.

### `/frontend`

Workspace React/Vite para evolução visual e trabalho independente do desenvolvedor frontend.

## Contrato estável

A fronteira mais importante do projeto é:

```text
frontend ← JSON → FastAPI ← Python → ML/otimizador
```

Durante a competição, tente manter os campos de resposta estáveis mesmo que o modelo interno mude completamente.
