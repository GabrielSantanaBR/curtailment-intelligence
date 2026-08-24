# Security Policy

## Escopo

Este repositório é um protótipo de hackathon e uma plataforma de apoio à decisão. Ele **não é** um componente SCADA/EMS e não deve ser conectado diretamente a sistemas de controle operacional.

## Dados e segredos

Nunca versionar chaves de API, senhas, tokens, `.env`, dados privados/restritos da competição ou dumps de banco contendo informações sensíveis.

## Upload de CSV

O endpoint de inspeção de CSV deve ser tratado como entrada não confiável. Existe limite de tamanho, mas uma implantação pública deve adicionar autenticação, rate limit, proxy e observabilidade.

## Dependências

Atualizações de dependências devem ser testadas antes de integração. Antes de uma demonstração pública, revise versões e vulnerabilidades conhecidas.

## Relato de vulnerabilidade

Durante o hackathon, reporte uma possível falha diretamente aos mantenedores da equipe antes de abrir uma issue pública contendo detalhes exploráveis.
