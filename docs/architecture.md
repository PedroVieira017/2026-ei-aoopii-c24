# Arquitetura do Content Pipeline Agent

## Objetivo funcional

O agente recebe uma unica fonte de conteudo e produz varias versoes adaptadas a plataformas diferentes. O objetivo nao e apenas resumir ou reformular: cada output deve respeitar as convencoes do formato onde vai ser publicado.

Neste projeto, o termo agente e usado como orquestrador de uma pipeline com passos e ferramentas internas: transcricao, extracao de factos, geracao por formato, revisao, reparacao factual, validacao local e exportacao. Nao foi implementado um agente autonomo com publicacao externa porque essa parte nao e obrigatoria no enunciado e depende de credenciais de plataformas externas.

## Fluxo de execucao

1. O utilizador escolhe uma fonte na interface Streamlit.
2. A fonte pode ser texto escrito manualmente, um exemplo da pasta `data/`, um ficheiro `.txt`/`.md` ou um ficheiro de audio.
3. A aplicacao valida se existe input.
4. A aplicacao cria um cliente para a Groq API atraves do SDK `openai`.
5. Se a fonte for audio, a aplicacao transcreve o ficheiro com `whisper-large-v3-turbo`.
6. O texto fonte e enviado para o prompt de extracao de factos.
7. A lista de factos passa a ser a unica base para os restantes outputs.
8. Cada formato tem um prompt proprio.
9. Cada rascunho passa por um prompt de revisao de conformidade.
10. Cada texto passa por uma reparacao factual final, que remove frases sem suporte direto nos factos.
11. A newsletter pode passar por uma reparacao extra se nao cumprir o formato curto.
12. A interface apresenta o resultado, o prompt usado, uma validacao rapida e uma exportacao em Markdown.

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

A validacao implementada em `app.py` nao substitui avaliacao humana, mas ajuda a detetar problemas frequentes:

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

Para audio, a aplicacao usa o endpoint de transcricao da Groq atraves do mesmo cliente OpenAI-compativel. O resultado da transcricao passa a ser a fonte textual unica da pipeline.

## Decisao sobre publicacao

As publishing APIs foram consideradas fora do MVP porque o enunciado as apresenta como opcionais e a sua demonstracao depende de credenciais externas. Para manter a demo funcional, a aplicacao exporta todos os resultados em Markdown, permitindo publicacao manual nas plataformas.
