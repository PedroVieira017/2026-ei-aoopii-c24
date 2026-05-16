# Configurar o agente Slack

Este adaptador usa Slack Bolt for Python em Socket Mode. Assim, o bot corre no teu computador e liga-se ao Slack por WebSocket, sem ser necessario criar um webhook publico.

## 1. Criar a aplicacao

1. Abrir `https://api.slack.com/apps`.
2. Escolher `Create New App`.
3. Escolher `From scratch`.
4. Dar um nome, por exemplo `Content Pipeline Agent`.
5. Escolher o workspace de teste.

## 2. Ativar Socket Mode

1. Abrir `Socket Mode`.
2. Ativar `Enable Socket Mode`.
3. Criar um app-level token com o scope:

```text
connections:write
```

4. Copiar o token `xapp-...` para o `.env`:

```text
SLACK_APP_TOKEN=colocar_o_token_xapp_aqui
```

## 3. Configurar permissoes do bot

Em `OAuth & Permissions`, adicionar estes Bot Token Scopes:

```text
app_mentions:read
channels:history
chat:write
commands
files:read
files:write
im:history
im:write
```

Scopes opcionais, se quiseres testar tambem em canais privados ou mensagens de grupo:

```text
groups:history
mpim:history
```

Depois clicar em `Install to Workspace` ou `Reinstall to Workspace`.

Copiar o `Bot User OAuth Token`, que comeca por `xoxb-`, para o `.env`:

```text
SLACK_BOT_TOKEN=colocar_o_token_xoxb_aqui
```

Tambem deve existir:

```text
GROQ_API_KEY=colocar_a_chave_aqui
```

## 4. Configurar eventos

Em `Event Subscriptions`, ativar eventos e adicionar em `Subscribe to bot events`:

```text
app_mention
message.im
message.channels
```

Se tiveres adicionado os scopes opcionais, tambem podes adicionar:

```text
message.groups
message.mpim
```

Guardar as alteracoes e reinstalar a app no workspace se o Slack pedir.

## 5. Configurar slash command opcional

Em `Slash Commands`, criar:

```text
/pipeline
```

Como a app usa Socket Mode, nao e preciso configurar um servidor publico para a demo local. O comando e opcional; o bot tambem funciona por mensagem direta, mencao ou `!pipeline`.

## 6. Atualizar o ambiente local

No terminal do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No `.env`:

```text
GROQ_API_KEY=colocar_a_chave_aqui
TELEGRAM_BOT_TOKEN=colocar_o_token_do_bot_aqui
DISCORD_BOT_TOKEN=colocar_o_token_do_bot_aqui
SLACK_BOT_TOKEN=colocar_o_token_xoxb_aqui
SLACK_APP_TOKEN=colocar_o_token_xapp_aqui
```

## 7. Executar

```powershell
python slack_agent.py
```

## 8. Testar no Slack

Mensagem privada ao bot:

```text
Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas. O teste envolveu 12 participantes. No final, 9 participantes afirmaram que a aplicacao ajudou a organizar melhor as sessoes de estudo. A equipa ainda nao avaliou impacto nas notas.
```

Num canal onde o bot esteja presente:

```text
!pipeline Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas. O teste envolveu 12 participantes. No final, 9 participantes afirmaram que a aplicacao ajudou a organizar melhor as sessoes de estudo. A equipa ainda nao avaliou impacto nas notas.
```

Ou com mencao:

```text
@Content Pipeline Agent Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas...
```

Se configuraste o slash command:

```text
/pipeline Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas...
```

O bot deve responder com:

- factos extraidos;
- blog post;
- LinkedIn post;
- tweet thread;
- newsletter section;
- ficheiro Markdown final.

## 9. Parar

No terminal:

```text
Ctrl+C
```
