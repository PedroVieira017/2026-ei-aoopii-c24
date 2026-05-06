# Content Pipeline Agent

- **Nome:** Pedro Rodrigues Vieira
- **Numero:** n31389
- **Email:** vieira.pedro@ipvc.pt

## Objetivo

Desenvolver um agente que recebe uma unica fonte de conteudo e gera varias versoes adaptadas a plataformas diferentes.

O projeto segue a ideia do enunciado: escrever uma vez e obter conteudo adequado ao local onde vai ser publicado, sem fazer apenas uma reformulacao generica.

## Input

O MVP recebe texto introduzido manualmente pelo utilizador. Esse texto pode representar, por exemplo:

- excerto de entrevista;
- artigo curto;
- nota de investigacao;
- transcricao de voice memo.

## Outputs

A aplicacao gera quatro formatos:

- blog post, mais desenvolvido e estruturado;
- LinkedIn post, profissional e curto;
- tweet thread, informal e envolvente;
- email newsletter section, muito sintetica.

## Decisao tecnica principal

O agente nao gera os formatos diretamente a partir do texto original.

Primeiro, extrai uma lista de factos explicitos do input. Depois, cada formato e gerado apenas a partir desses factos. Esta etapa reduz alucinacoes, evita conclusoes inventadas e torna mais facil validar se os outputs respeitam a fonte inicial.

Pipeline:

```text
Input do utilizador
  -> Extracao de factos
  -> Geracao por formato
  -> Revisao de conformidade
  -> Reparacao factual final
  -> Validacao rapida na interface
  -> Outputs finais
```

## Tecnologias

- Python
- Streamlit
- OpenAI Python SDK
- Groq API, usando endpoint compativel com OpenAI
- python-dotenv

## Como executar

1. Criar e ativar ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Criar ficheiro `.env` na raiz do projeto:

```text
GROQ_API_KEY=colocar_a_chave_aqui
```

4. Executar a aplicacao:

```powershell
streamlit run app.py
```

## Estrutura

```text
app.py                         Aplicacao Streamlit e pipeline de geracao
prompts/facts_extraction.txt   Prompt para extrair factos
prompts/blog_post.txt          Prompt do blog post
prompts/linkedin_post.txt      Prompt do LinkedIn
prompts/tweet_thread.txt       Prompt da tweet thread
prompts/newsletter_section.txt Prompt da newsletter
prompts/compliance_review.txt  Prompt de revisao de conformidade
data/                          Exemplos de input para demonstracao
docs/                          Documentacao tecnica do projeto
```

## Validacao

A interface mostra uma validacao rapida para cada output:

- numero de palavras, frases e paragrafos;
- repeticoes obvias;
- marcadores Markdown indevidos;
- termos comuns de portugues do Brasil;
- verbos fortes de garantia ou comprovacao;
- limites especificos por formato, como 280 caracteres por tweet e 60 palavras no corpo da newsletter.

## Limites atuais

- O MVP recebe texto manualmente; ainda nao processa audio real.
- A publicacao nas plataformas nao esta automatizada.
- A validacao local ajuda a detetar problemas formais, mas a fidelidade factual continua a depender da qualidade da extracao de factos e da revisao por LLM.
