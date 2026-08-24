# Frontend React/Vite

O dashboard principal de demonstração fica em `/web` e é servido diretamente pelo FastAPI. Esta pasta é o workspace do desenvolvedor frontend para evoluir uma SPA React sem alterar a camada de ML.

## Executar

Primeiro, em outro terminal, mantenha o backend em `http://127.0.0.1:8000`.

Depois:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

O `vite.config.js` possui proxy para `/api` e `/health`, portanto componentes React devem usar caminhos relativos:

```js
fetch("/api/v1/overview")
```

Evite hardcodar `http://localhost:8000` nos componentes.

## Regra de arquitetura

O navegador não deve importar nem reproduzir lógica de ML, otimização ou acesso direto ao banco.

```text
React → FastAPI → services/ML/optimizer/database
```
