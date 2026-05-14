# Guia de apresentacao ao professor

## Explicacao curta

Este projeto implementa um agente conversacional de pipeline de conteudo para uma aplicacao/rede social. O utilizador envia uma unica fonte numa conversa, e o agente devolve automaticamente varios conteudos adaptados a plataformas diferentes. Telegram e Discord sao usados como adaptadores funcionais de demonstracao.

A parte importante e que o agente nao faz apenas copy-paste com outras palavras. Primeiro transforma a fonte numa lista de factos explicitos. Depois usa prompts especificos para criar quatro formatos: blog post, post de LinkedIn, tweet thread e secao de newsletter. Cada formato tem regras proprias de estrutura, tom, tamanho e uso.

## O que foi construido

- Nucleo de agente conversacional em `conversation_agent.py`.
- Adaptador Telegram de exemplo em `telegram_agent.py`.
- Adaptador Discord de exemplo em `discord_agent.py`.
- Pipeline reutilizavel em `content_pipeline.py`.
- Painel web profissional em `web_demo.py` e `web_demo/`, usado para demonstracao e debug.
- Entrada por mensagem de texto, ficheiro `.txt`/`.md` ou audio/nota de voz.
- Transcricao de audio antes da geracao, para manter uma fonte unica em texto.
- Extracao de factos antes da escrita dos outputs.
- Quatro prompts especificos, um por formato final.
- Revisao de conformidade para remover informacao sem suporte nos factos.
- Reparacao factual final para reduzir alucinacoes.
- Validacao local dos outputs.
- Exportacao final em Markdown enviada pelo agente.

## Como a pipeline funciona

```text
Mensagem numa aplicacao/rede social
  -> Texto, ficheiro ou audio
  -> Transcricao, se for audio
  -> Extracao de factos explicitos
  -> Geracao do blog post
  -> Geracao do LinkedIn post
  -> Geracao da tweet thread
  -> Geracao da newsletter
  -> Revisao e reparacao factual
  -> Resposta no canal de conversa
  -> Envio de ficheiro Markdown
```

## Como cumpre o enunciado

| Requisito | Como foi cumprido |
| --- | --- |
| Receber um unico input | O agente processa uma fonte por pedido. Se for audio, primeiro transcreve e depois usa essa transcricao como fonte unica. |
| Aceitar fontes como entrevista, artigo, nota ou voice memo | O agente aceita texto, ficheiros `.txt`/`.md` e notas de voz/audio, dependendo do adaptador do canal. |
| Gerar pelo menos 3 formatos | Gera 4 formatos: blog, LinkedIn, Twitter/X e newsletter. |
| Adaptar cada formato ao canal | Cada output tem prompt proprio com regras de tom, tamanho, estrutura e finalidade. |
| Evitar reformulacao generica | A pipeline usa extracao de factos, prompts por formato, revisao de conformidade e validacao local. |
| Usar LLM e prompts especificos | Usa modelo LLM via Groq com SDK OpenAI-compativel e ficheiros de prompt separados. |
| APIs opcionais de publicacao | Nao foram integradas porque sao opcionais e exigem credenciais externas; em alternativa, o agente envia os outputs e um Markdown final. |

## Diferencas entre outputs

Blog post:
Tem titulo, introducao e secoes. E o formato mais desenvolvido e organizado.

LinkedIn post:
E curto, profissional e direto. Usa paragrafos breves e parece uma atualizacao profissional.

Tweet thread:
Divide a informacao em 3 a 6 tweets numerados, com limite de 280 caracteres por tweet. O tom e mais leve e rapido.

Newsletter:
E o formato mais sintetico. Tem um titulo curto e um paragrafo pequeno pronto a entrar num email.

## Frase para defender a decisao tecnica

Transformei o projeto num agente conversacional: em vez de ser apenas um site, o utilizador envia a fonte numa aplicacao/rede social e recebe automaticamente os conteudos. A pipeline por tras do agente primeiro extrai factos explicitos e so depois gera os formatos com prompts especificos. Isto reduz invencoes do modelo e garante que cada versao e adaptada ao canal, nao apenas reformulada. Telegram e Discord demonstram que o mesmo nucleo pode ser ligado a canais diferentes.

O painel web em HTML/CSS/JavaScript nao e o produto principal. Ele e uma demo visual ligada ao mesmo agente, com backend Flask, para apresentar a pipeline de forma mais profissional sem expor a chave da API no browser.

## Como demonstrar na aula

1. Explicar que `conversation_agent.py` e o nucleo independente do canal.
2. Executar o adaptador de exemplo com `python telegram_agent.py`.
3. Abrir a conversa com o bot no Telegram.
4. Enviar um texto ou uma nota de voz.
5. Mostrar que o bot confirma a rececao da fonte.
6. Mostrar os factos extraidos.
7. Mostrar os quatro outputs enviados pelo bot.
8. Abrir o ficheiro Markdown recebido.
9. Executar `python discord_agent.py` e mostrar a mesma ideia no Discord com `!pipeline`.
10. Opcionalmente, abrir o painel web com `python web_demo.py`.
11. Explicar que o painel web e apenas demo/debug; o centro do projeto continua a ser o agente.

## Limites assumidos

- A publicacao automatica em LinkedIn, X ou email ficou fora porque o enunciado diz que e opcional e porque exige contas, tokens e aprovacoes de APIs.
- Como qualquer sistema com LLM, os resultados devem ser revistos por uma pessoa.
- A validacao local nao prova verdade factual absoluta, mas deteta erros formais e ajuda a controlar os outputs.
