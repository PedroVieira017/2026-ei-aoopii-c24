# Content Pipeline Agent

- **Nome:** Pedro Rodrigues Vieira
- **Numero:** n31389
- **Email:** vieira.pedro@ipvc.pt

## Objetivo

Desenvolver um agente que recebe uma unica fonte de conteudo e gera varias versoes adaptadas a plataformas diferentes.

O projeto segue a ideia do enunciado: escrever uma vez e obter conteudo adequado ao local onde vai ser publicado, sem fazer apenas uma reformulacao generica.

## Input

A aplicacao recebe uma unica fonte por execucao. A fonte e usada diretamente quando ja e texto, ou transcrita primeiro quando e audio. Pode ser:

- texto introduzido manualmente pelo utilizador;
- exemplo pre-carregado da pasta `data/`;
- ficheiro `.txt` ou `.md` carregado pelo utilizador;
- voice memo/audio carregado pelo utilizador, transcrito antes de entrar na pipeline.

Esse texto pode representar, por exemplo:

- excerto de entrevista;
- artigo curto;
- nota de investigacao;
- voice memo.

O projeto nao processa imagens. No caso de audio, a aplicacao transcreve primeiro e depois usa a transcricao como fonte unica da pipeline.

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
Input unico
  -> Transcricao, se a fonte for audio
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
- Groq Speech to Text para transcricao de audio
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
validation.py                  Funcoes locais de validacao formal
prompts/facts_extraction.txt   Prompt para extrair factos
prompts/blog_post.txt          Prompt do blog post
prompts/linkedin_post.txt      Prompt do LinkedIn
prompts/tweet_thread.txt       Prompt da tweet thread
prompts/newsletter_section.txt Prompt da newsletter
prompts/compliance_review.txt  Prompt de revisao de conformidade
data/                          Exemplos de input para demonstracao
docs/                          Documentacao tecnica e exemplo de outputs
docs/presentation_guide.md     Guia curto para apresentar e defender o projeto
tests/                         Testes unitarios da validacao local
```

## Validacao

A interface mostra uma validacao rapida para cada output:

- numero de palavras, frases e paragrafos;
- repeticoes obvias;
- marcadores Markdown indevidos;
- termos comuns de portugues do Brasil;
- verbos fortes de garantia ou comprovacao;
- limites especificos por formato, como 280 caracteres por tweet e 60 palavras no corpo da newsletter.

Os testes unitarios podem ser executados com:

```powershell
python -m unittest discover -s tests
```

## Exportacao

Depois de gerar conteudos, a interface permite descarregar um ficheiro Markdown com:

- fonte final usada;
- factos extraidos;
- blog post;
- LinkedIn post;
- tweet thread;
- newsletter section.

## Limites atuais

- O MVP trabalha com texto e audio; ainda nao processa imagens.
- A publicacao nas plataformas nao esta automatizada.
- A validacao local ajuda a detetar problemas formais, mas a fidelidade factual continua a depender da qualidade da extracao de factos e da revisao por LLM.

## Decisoes fora do MVP

- As publishing APIs foram deixadas fora por exigirem credenciais e configuracao especifica de plataformas externas. Em vez disso, o projeto exporta os resultados em Markdown para publicacao manual.
- Nao foi usado LangGraph/CrewAI porque o enunciado exige LLM com prompting especifico por formato; a arquitetura foi mantida simples e demonstravel em Streamlit.
