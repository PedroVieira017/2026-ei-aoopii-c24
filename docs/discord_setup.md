# Configurar o agente Discord

## 1. Criar a aplicacao

1. Abrir o Discord Developer Portal.
2. Criar uma nova aplicacao.
3. Dar um nome, por exemplo `Content Pipeline Agent`.

## 2. Criar o bot

1. Abrir a seccao `Bot`.
2. Criar/adicionar o bot.
3. Copiar o token do bot.
4. Colocar o token no ficheiro `.env`:

```text
DISCORD_BOT_TOKEN=colocar_o_token_do_bot_aqui
```

Tambem deve existir:

```text
GROQ_API_KEY=colocar_a_chave_aqui
```

## 3. Ativar permissao de conteudo

Na pagina do bot, ativar:

```text
Message Content Intent
```

Esta permissao e necessaria para o bot conseguir ler mensagens de texto enviadas pelos utilizadores.

## 4. Convidar o bot para um servidor

No OAuth2/URL Generator:

1. Selecionar o scope `bot`.
2. Dar permissoes para enviar mensagens e anexar ficheiros.
3. Abrir o link gerado.
4. Escolher o servidor de teste.

## 5. Executar

No terminal do projeto:

```powershell
python discord_agent.py
```

## 6. Testar no Discord

Num canal onde o bot esteja presente:

```text
!help
```

Depois:

```text
!pipeline Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas. O teste envolveu 12 participantes. No final, 9 participantes afirmaram que a aplicacao ajudou a organizar melhor as sessoes de estudo. A equipa ainda nao avaliou impacto nas notas.
```

O bot deve responder com:

- factos extraidos;
- blog post;
- LinkedIn post;
- tweet thread;
- newsletter section;
- ficheiro Markdown final.
