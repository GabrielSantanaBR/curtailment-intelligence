# Transição para os dados oficiais da competição

A base de software já existe. Quando o dataset oficial chegar, o trabalho principal deve ser **validar o problema e os dados**, não reconstruir a aplicação.

## 1. Congelar os arquivos brutos

Coloque arquivos intactos em `data/raw/`. Registre fonte, data de download/recebimento, período coberto e versão/dicionário associado. Não edite o CSV bruto manualmente.

## 2. Auditar o arquivo

```bash
python scripts/audit_dataset.py data/raw/ARQUIVO.csv
```

A auditoria fornece uma primeira visão de schema, missingness, duplicatas, faixa temporal e nomes potencialmente perigosos para leakage.

## 3. Definir o instante de previsão

Antes de criar features, escreva uma frase inequívoca:

> No instante T, o sistema prevê se a unidade P sofrerá curtailment no horizonte H usando somente informações disponíveis em ou antes de T.

Se uma variável só fica conhecida depois do evento começar, ela não pode ser usada para prever aquele evento.

## 4. Definir o target

Possibilidades a testar conforme a granularidade oficial:

- evento na próxima 1 hora;
- evento nas próximas 3 horas;
- evento nas próximas 6 horas;
- MWh restringidos no horizonte;
- risco agregado por conjunto/região.

Não assumir granularidade horária sem confirmar os dados.

## 5. Construir baseline primeiro

Antes de modelos sofisticados, medir soluções simples: taxa histórica por usina, taxa por hora/período, Logistic Regression e regra baseada em histórico recente. O modelo final precisa superar um baseline defensável.

## 6. Features candidatas

Somente se disponíveis e permitidas: calendário/sazonalidade, tecnologia/capacidade, geração disponível ou previsão, estatísticas móveis estritamente passadas, carga do sistema, participação renovável, indicadores de rede/sistema e meteorologia permitida.

## 7. Validação

Manter ordem temporal. Preferir, conforme o target: PR-AUC, Recall, Precision, F1, Brier/calibração e MAE/RMSE para magnitude. Accuracy isolada não é suficiente para um evento desbalanceado.

## 8. Integrar sem quebrar o produto

A API deve continuar retornando, idealmente:

```text
risk_probability
risk_level
predicted_curtailed_mwh
explanation
model_version
data_mode
```

Assim o frontend continua funcionando enquanto o motor interno evolui.

## 9. Validar mitigação

Revisar com o especialista localização do recurso, capacidade em MWh, potência em MW, eficiência, SOC, restrições de conexão, carga flexível e regras operacionais/mercado.

## 10. Evidência final

Na apresentação, separar claramente:

- **observado**: aconteceu nos dados históricos;
- **previsto**: estimativa do modelo;
- **simulado**: cenário do otimizador;
- **estimado**: impacto econômico/ambiental parametrizado.
