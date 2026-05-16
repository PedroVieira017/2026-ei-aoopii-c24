# Arquitetura do Content Pipeline Agent

## Objetivo funcional

O agente recebe uma unica fonte de conteudo por conversa e produz varias versoes adaptadas a plataformas diferentes. O objetivo nao e apenas resumir ou reformular: cada output deve respeitar as convencoes do formato onde vai ser publicado.

Neste projeto, o agente foi separado em duas partes: um nucleo conversacional independente do canal e adaptadores de interface. Isto significa que o mesmo agente pode ser ligado a uma aplicacao ou rede social com API, como WhatsApp, Telegram, Discord, Slack ou outro canal. Telegram, Discord e Slack sao adaptadores funcionais de exemplo. O painel Flask/HTML e apenas uma demo visual profissional para apresentacao e debug.

## Fluxo de execucao

1. O utilizador envia uma mensagem ao agente numa aplicacao/rede social.
2. A fonte pode ser texto, um ficheiro `.txt`/`.md`, uma nota de voz ou um ficheiro de audio.
3. O agente valida se existe input utilizavel.
4. O agente cria um cliente para a Groq API atraves do SDK `openai`.
5. Se a fonte for audio, o agente transcreve o ficheiro com `whisper-large-v3-turbo`.
6. O texto fonte e enviado para o prompt de extracao de factos.
7. A lista de factos passa a ser a unica base para os restantes outputs.
8. Cada formato tem um prompt proprio.
9. Cada rascunho passa por um prompt de revisao de conformidade.
10. Cada texto passa por uma reparacao factual final, que remove frases sem suporte direto nos factos.
11. A newsletter pode passar por uma reparacao extra se nao cumprir o formato curto.
12. O agente responde no canal de conversa com os outputs e envia um ficheiro Markdown com o pacote completo.

## Adaptadores conversacionais

O nucleo `ConversationContentAgent` nao conhece Telegram, Discord, Slack nem Flask. Cada adaptador transforma eventos do canal numa fonte textual e depois chama o mesmo nucleo.

```text
Telegram Bot API
Discord Bot API
Slack Bolt / Socket Mode
Painel Flask
        -> ConversationContentAgent
        -> content_pipeline.py
        -> Groq/OpenAI-compatible API
```

Esta separacao e a principal defesa tecnica do projeto: trocar ou adicionar um canal nao obriga a reescrever a pipeline.

## Razao para a extracao de factos

Gerar diretamente a partir do texto original aumentava o risco de o modelo acrescentar ideias, conclusoes, emocoes ou promessas que nao existiam na fonte.

A extracao de factos cria uma camada intermedia mais controlada:

- reduz alucinacoes;
- preserva a ordem e a perspetiva do texto original;
- facilita a revisao de conformidade;
- torna os outputs mais consistentes entre si.

## Formatos suportados

- **Blog post:** formato mais desenvolvido, com titulo, introducao e secoes.
- **LinkedIn post:** publicacao profissional, curta, em paragrafos.
- **Tweet thread:** sequencia de 3 a 6 tweets numerados, com limite de 280 caracteres por linha.
- **Newsletter section:** titulo curto e um paragrafo muito sintetico.

## Validacao local

A validacao implementada em `validation.py` nao substitui avaliacao humana, mas ajuda a detetar problemas frequentes:

- texto demasiado longo;
- excesso de frases ou paragrafos;
- Markdown indesejado;
- repeticoes;
- termos de portugues do Brasil;
- verbos fortes como "garante" ou "comprova";
- tweets acima de 280 caracteres;
- newsletter fora do formato pedido.

## Decisao sobre API

O projeto usa o SDK `openai` porque a Groq disponibiliza uma API compativel com OpenAI. A chamada foi implementada com Chat Completions para maximizar compatibilidade e previsibilidade no contexto de apresentacao academica.

Para audio, o agente usa o endpoint de transcricao da Groq atraves do mesmo cliente OpenAI-compativel. O resultado da transcricao passa a ser a fonte textual unica da pipeline.

## Decisao sobre publicacao

As publishing APIs foram consideradas fora do MVP porque o enunciado as apresenta como opcionais e a sua demonstracao depende de credenciais externas. Para manter a demo funcional, o agente envia todos os resultados ao utilizador e exporta Markdown, permitindo publicacao manual nas plataformas.

## Decisao sobre o painel web

O painel web nao substitui o agente. Ele existe para demonstrar a pipeline de forma visual e profissional. O frontend HTML/CSS/JavaScript comunica com um backend Flask local; a chave da API fica apenas no backend e nunca e exposta no browser.
