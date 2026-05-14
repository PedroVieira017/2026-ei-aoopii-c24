# Content Pipeline Agent

- **Nome:** Pedro Rodrigues Vieira
- **Numero:** n31389
- **Email:** vieira.pedro@ipvc.pt

## Objetivo

Desenvolver um agente conversacional que recebe uma unica fonte de conteudo e gera varias versoes adaptadas a plataformas diferentes.

O projeto segue a ideia do enunciado: escrever uma vez e obter conteudo adequado ao local onde vai ser publicado, sem fazer apenas uma reformulacao generica.

O modo principal do projeto e um agente conversacional para uma aplicacao/rede social. O nucleo do agente esta separado da interface, por isso pode ser ligado a canais como WhatsApp, Telegram, Discord, Slack ou outra plataforma com API. Neste projeto, o Telegram fica como adaptador funcional de exemplo. Existe tambem um painel web profissional em HTML/CSS/JS com backend Flask, usado apenas para demonstracao e debug.

## Input

O agente recebe uma unica fonte por pedido. A fonte e usada diretamente quando ja e texto, ou transcrita primeiro quando e audio. Pode ser:

- texto enviado numa mensagem da aplicacao/rede social;
- ficheiro `.txt` ou `.md` enviado ao bot;
- voice memo/audio enviado ao bot, transcrito antes de entrar na pipeline;
- exemplo pre-carregado da pasta `data/`, no painel web de demonstracao.

Esse texto pode representar, por exemplo:

- excerto de entrevista;
- artigo curto;
- nota de investigacao;
- voice memo.

O projeto nao processa imagens. No caso de audio, o agente transcreve primeiro e depois usa a transcricao como fonte unica da pipeline.

## Outputs

O agente gera quatro formatos:

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
  -> Validacao formal local
  -> Resposta na aplicacao/rede social e exportacao Markdown
  -> Outputs finais
```

## Tecnologias

- Python
- Nucleo de agente conversacional independente do canal
- Telegram Bot API
- Flask
- HTML/CSS/JavaScript
- OpenAI Python SDK
- Groq API, usando endpoint compativel com OpenAI
- Groq Speech to Text para transcricao de audio
- python-dotenv
- requests

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
TELEGRAM_BOT_TOKEN=colocar_o_token_do_bot_aqui
```

O `TELEGRAM_BOT_TOKEN` e obtido ao criar um bot no BotFather do Telegram.

4. Executar o adaptador Telegram de exemplo:

```powershell
python telegram_agent.py
```

5. Opcionalmente, executar o painel web profissional:

```powershell
python web_demo.py
```

Depois abrir:

```text
http://127.0.0.1:5000
```

## Estrutura

```text
telegram_agent.py              Agente conversacional para Telegram
conversation_agent.py          Nucleo do agente independente do canal
content_pipeline.py            Pipeline reutilizavel de geracao
web_demo.py                    Backend Flask do painel web
web_demo/templates/index.html  Interface HTML do painel web
web_demo/static/               CSS e JavaScript do painel web
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
.env.example                   Exemplo das variaveis de ambiente necessarias
```

## Validacao

A validacao local verifica cada output, e o painel web mostra esses resultados de forma visual:

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

## Resposta e exportacao

Depois de gerar conteudos, o agente responde no canal de conversa com os formatos principais e envia tambem um ficheiro Markdown com:

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

- As publishing APIs foram deixadas fora por exigirem credenciais e configuracao especifica de plataformas externas. Em vez disso, o agente envia os conteudos ao utilizador e exporta Markdown para publicacao manual.
- Nao foi usado LangGraph/CrewAI porque o enunciado exige LLM com prompting especifico por formato; a arquitetura foi mantida simples, mas com um nucleo de agente conversacional e um adaptador funcional para Telegram.
