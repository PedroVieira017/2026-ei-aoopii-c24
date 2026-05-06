# Arquitetura do Content Pipeline Agent

## Objetivo funcional

O agente recebe uma unica fonte de conteudo e produz varias versoes adaptadas a plataformas diferentes. O objetivo nao e apenas resumir ou reformular: cada output deve respeitar as convencoes do formato onde vai ser publicado.

## Fluxo de execucao

1. O utilizador escreve o texto fonte na interface Streamlit.
2. A aplicacao valida se existe input.
3. A aplicacao cria um cliente para a Groq API atraves do SDK `openai`.
4. O texto fonte e enviado para o prompt de extracao de factos.
5. A lista de factos passa a ser a unica base para os restantes outputs.
6. Cada formato tem um prompt proprio.
7. Cada rascunho passa por um prompt de revisao de conformidade.
8. Cada texto passa por uma reparacao factual final, que remove frases sem suporte direto nos factos.
9. A newsletter pode passar por uma reparacao extra se nao cumprir o formato curto.
10. A interface apresenta o resultado, o prompt usado e uma validacao rapida.

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
