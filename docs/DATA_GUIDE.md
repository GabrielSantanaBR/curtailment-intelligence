# Guia de dados

## Princípio

Dados oficiais e dados sintéticos nunca devem ser misturados de forma silenciosa. Todo output precisa ser rastreável até sua origem.

## Diretórios

```text
data/raw/        arquivos oficiais exatamente como recebidos
data/processed/  dados limpos/normalizados/feature tables
data/demo/       dados sintéticos gerados pelo projeto
artifacts/       modelos, métricas e metadados gerados
```

Esses diretórios são ignorados pelo Git, mantendo apenas `.gitkeep` quando aplicável.

## Regras para dados oficiais

1. Não altere o arquivo original em `data/raw/`.
2. Registre nome, data de obtenção, fonte e versão.
3. Se o ONS republicar o arquivo, preserve rastreabilidade da versão usada no modelo.
4. Gere dados tratados em `data/processed/`.
5. Não faça commit de arquivos oficiais sem confirmar licença e regras da competição.

## Auditoria inicial

```bash
python scripts/audit_dataset.py data/raw/arquivo.csv
```

O auditor procura separador/encoding, normaliza nomes, tenta mapear campos conhecidos e sinaliza potenciais riscos.

## Leakage

Uma coluna não pode entrar no modelo somente porque está disponível no dataset.

Para uma previsão feita em `T`, uma feature só é elegível se estivesse disponível em produção em `T` (ou antes). Informações geradas após o evento devem ficar fora dos preditores.

Documente para cada feature:

| Campo | Unidade | Fonte | Disponível em T? | Transformação | Observação |
|---|---|---|---|---|---|
| exemplo | MW | ONS | sim | lag 1h | exemplo apenas |

## Qualidade

Antes de modelar, avaliar pelo menos:

- cobertura temporal;
- granularidade;
- duplicatas;
- valores ausentes;
- timezone;
- unidades;
- outliers;
- mudanças de schema;
- distribuição do target;
- frequência por usina/região;
- possíveis revisões do dado.

## Dados sintéticos

`data/demo/` existe somente para manter produto, testes e integração funcionando enquanto o dataset oficial não está incorporado. Métricas de demo nunca devem ser apresentadas como resultado real.

## Artefatos de modelo

`artifacts/` deve conter localmente o classificador, regressor e métricas correspondentes. Na etapa final, registre também hash/versão do dataset, período de treino, features, threshold e data de treinamento.
