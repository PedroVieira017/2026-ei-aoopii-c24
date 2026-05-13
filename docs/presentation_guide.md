# Guia de apresentacao ao professor

## Explicacao curta

Este projeto implementa um agente de pipeline de conteudo. A ideia principal e receber uma unica fonte, como uma entrevista, artigo, nota de investigacao ou audio, e transformar essa fonte em varios conteudos adaptados a plataformas diferentes.

O agente nao faz apenas copy-paste com palavras diferentes. Primeiro transforma a fonte numa lista de factos explicitos. Depois usa prompts especificos para criar quatro formatos: blog post, post de LinkedIn, tweet thread e secao de newsletter. Cada formato tem regras proprias de estrutura, tom, tamanho e uso.

## O que foi construido

- Uma aplicacao Streamlit com interface para escolher a fonte.
- Entrada por texto manual, exemplo local, ficheiro `.txt`/`.md` ou audio.
- Transcricao de audio antes da geracao, para manter uma fonte unica em texto.
- Extracao de factos antes da escrita dos outputs.
- Quatro prompts especificos, um por formato final.
- Revisao de conformidade para remover informacao sem suporte nos factos.
- Reparacao factual final para reduzir alucinacoes.
- Validacao local dos outputs na interface.
- Exportacao final em Markdown.

## Como a pipeline funciona

```text
Fonte unica
  -> Transcricao, se for audio
  -> Extracao de factos explicitos
  -> Geracao do blog post
  -> Geracao do LinkedIn post
  -> Geracao da tweet thread
  -> Geracao da newsletter
  -> Revisao e reparacao factual
  -> Validacao formal por formato
  -> Exportacao em Markdown
```

## Como cumpre o enunciado

| Requisito | Como foi cumprido |
| --- | --- |
| Receber um unico input | A aplicacao usa apenas uma fonte por execucao. Se for audio, primeiro transcreve e depois usa essa transcricao como fonte unica. |
| Aceitar fontes como entrevista, artigo, nota ou voice memo | Ha texto manual, exemplos em `data/`, upload de texto e upload de audio. |
| Gerar pelo menos 3 formatos | Gera 4 formatos: blog, LinkedIn, Twitter/X e newsletter. |
| Adaptar cada formato ao canal | Cada output tem prompt proprio com regras de tom, tamanho, estrutura e finalidade. |
| Evitar reformulacao generica | A pipeline usa extracao de factos, prompts por formato, revisao de conformidade e validacao local. |
| Usar LLM e prompts especificos | Usa modelo LLM via Groq com SDK OpenAI-compativel e ficheiros de prompt separados. |
| APIs opcionais de publicacao | Nao foram integradas porque sao opcionais e exigem credenciais externas; em alternativa, o projeto exporta Markdown para publicacao manual. |

## Diferencas entre outputs

Blog post:
Tem titulo, introducao e secoes. E o formato mais desenvolvido e organizado.

LinkedIn post:
E curto, profissional e direto. Usa paragrafos breves e parece uma atualizacao profissional.

Tweet thread:
Divide a informacao em 3 a 6 tweets numerados, com limite de 280 caracteres por tweet. O tom e mais leve e rapido.

Newsletter:
E o formato mais sintetico. Tem um titulo curto e um paragrafo pequeno pronto a entrar num email.

## Pontos tecnicos fortes

- A fonte original nao e usada diretamente para todos os outputs; primeiro passa por extracao de factos.
- Cada frase final deve estar suportada pelos factos extraidos.
- Existe uma revisao automatica apos cada rascunho.
- A newsletter tem uma reparacao extra quando fica demasiado longa.
- A interface mostra os prompts usados, o que ajuda a explicar o funcionamento.
- A validacao local verifica limites, estrutura, repeticoes, Markdown indevido, termos de portugues do Brasil e verbos fortes como "garante" ou "comprova".
- Existem testes unitarios para a logica de validacao.

## Como demonstrar na aula

1. Abrir a aplicacao com `streamlit run app.py`.
2. Escolher o exemplo de entrevista.
3. Mostrar que existe apenas uma fonte de entrada.
4. Clicar em `Gerar conteudos`.
5. Abrir cada separador e comparar os formatos.
6. Mostrar os factos extraidos no blog post.
7. Mostrar o prompt carregado em cada separador.
8. Mostrar a validacao rapida de cada output.
9. Descarregar o Markdown final para provar que a pipeline gera um pacote completo de conteudo.

## Frase para defender a decisao tecnica

Usei uma arquitetura simples mas controlada: em vez de pedir ao modelo para escrever quatro textos diretamente a partir da fonte original, primeiro extraio factos explicitos e depois uso esses factos como base unica para cada formato. Isto reduz invencoes do modelo e ajuda a garantir que as versoes sao diferentes pela estrutura e pelo canal, nao apenas por sinonimos.

## Limites assumidos

- A publicacao automatica em plataformas externas ficou fora do projeto porque o enunciado diz que e opcional e porque exige contas, tokens e aprovacoes de APIs.
- Como qualquer sistema com LLM, os resultados devem ser revistos por uma pessoa.
- A validacao local nao prova verdade factual absoluta, mas deteta erros formais e ajuda a controlar os outputs.
