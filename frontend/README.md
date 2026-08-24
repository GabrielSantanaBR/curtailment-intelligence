# Frontend React/Vite

Este diretório é o workspace visual do **Curtailment Intelligence**. Ele foi separado do backend para permitir que uma pessoa de frontend trabalhe na experiência do produto sem precisar alterar código de Machine Learning, otimização ou banco de dados.

> O dashboard zero-build servido diretamente pelo FastAPI continua em `/web`. O React é a interface evolutiva para desenvolvimento visual e futura publicação como SPA.

## Executar

Mantenha o backend ativo em `http://127.0.0.1:8000` e, em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

Para validar antes de um Pull Request:

```bash
npm run build
```

O `vite.config.js` possui proxy para `/api` e `/health`, então o frontend deve usar caminhos relativos:

```js
fetch("/api/v1/overview")
```

Não hardcode `http://localhost:8000` dentro de componentes.

## Organização atual

```text
src/
├── App.jsx       fluxo e composição do dashboard
├── api.js        único ponto de comunicação com FastAPI
├── main.jsx      bootstrap React
└── styles.css    design system e responsividade
```

À medida que a interface crescer, extraia blocos de `App.jsx` para `src/components/` por domínio, por exemplo:

```text
components/
├── overview/
├── prediction/
├── mitigation/
├── patterns/
└── model/
```

Evite criar componentes muito genéricos cedo demais. Primeiro mantenha cada componente ligado a uma responsabilidade clara do produto.

## Fluxo de dados

```text
React
  ↓
frontend/src/api.js
  ↓
/api/v1/*
  ↓
FastAPI
  ↓
services
  ├── ML
  ├── optimizer
  └── database
```

O navegador não deve:

- carregar artefatos `.joblib`;
- executar regras de otimização;
- consultar o banco diretamente;
- duplicar lógica de feature engineering;
- inferir métricas que o backend já calcula.

## Views

O dashboard está dividido em cinco áreas:

1. **Visão geral** — risco, energia em risco, histórico e explicabilidade.
2. **Predição** — leitura temporal e threshold de decisão.
3. **Mitigação** — formulário de cenário, otimização e despacho.
4. **Padrões** — comportamento por horário e categorias.
5. **Modelo** — métricas e avisos de validação.

## Design system

A interface utiliza um visual escuro orientado a operação e análise de dados. As principais variáveis ficam no topo de `styles.css`:

```css
--bg
--panel
--line
--text
--muted
--accent
--lime
--danger
--warn
```

Prefira reutilizar essas variáveis em vez de inserir novas cores isoladas.

## Dados sintéticos

Enquanto os dados oficiais do desafio não forem integrados, a interface deve continuar exibindo claramente que os números vêm do modo de demonstração. Não remova esses avisos apenas por estética.

## Branch de trabalho

O desenvolvimento visual deve acontecer em `develop` ou em branches criadas a partir dela. A `main` deve receber mudanças somente após revisão e CI verde.
