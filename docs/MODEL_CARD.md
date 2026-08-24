# Model Card — modelo demo

## Finalidade

Modelo de integração pré-hackathon com horizonte de **6 horas**. Ele existe para validar o fluxo completo de dados, API, previsão, explicação e dashboard antes da disponibilidade dos dados oficiais.

Não é um modelo treinado com dados do ONS.

## Dados de treinamento atuais

- modo: sintético;
- linhas: aproximadamente 24,5 mil;
- fontes: eólica e solar simuladas;
- target de classificação: pelo menos um evento de curtailment em `T+1 ... T+6`;
- target de magnitude: MWh restringidos acumulados em `T+1 ... T+6`;
- split: cronológico `70/15/15`.

## Modelos comparados

### Baseline

`LogisticRegression`

### Candidato não linear

`HistGradientBoostingClassifier`

O modelo escolhido é o que obtém maior **PR-AUC no conjunto de validação**, não o modelo mais complexo por definição.

## Regressão de magnitude

`RandomForestRegressor` treinado nos exemplos com magnitude positiva.

## Métricas demo de referência

Os valores abaixo pertencem exclusivamente ao gerador sintético original e podem mudar se o demo for regenerado/reconfigurado.

| Métrica | Referência demo |
|---|---:|
| PR-AUC | ~0,57 |
| ROC-AUC | ~0,80 |
| Recall | ~0,79 |
| F1 | ~0,58 |

Use `GET /api/v1/model/metrics` para consultar o artefato efetivamente carregado.

## Explicabilidade

A implementação atual usa perturbação local de uma variável por vez e mede a mudança na probabilidade prevista.

Isso serve para interpretação do comportamento do modelo, mas **não representa efeito causal**.

## Limitações

- dados sintéticos;
- sistema elétrico simplificado;
- ausência de topologia real da rede;
- ausência de ativos reais de mitigação;
- distribuição demo não representa a distribuição real do ONS;
- probabilidade prevista não está validada operacionalmente.

## Obrigatório antes da submissão final

- definir formalmente o instante `T` e horizonte `H`;
- auditar leakage feature por feature;
- documentar missingness e revisões do dataset;
- comparar com baseline ingênuo/histórico;
- avaliar calibração;
- avaliar por fonte, região e usina;
- revisar falsos positivos e falsos negativos;
- documentar failure modes;
- atualizar este Model Card com dados e métricas oficiais.
