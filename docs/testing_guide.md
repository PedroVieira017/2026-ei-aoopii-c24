# Guia rapido de testes

## 1. Testes automaticos

Executar:

```powershell
python -m unittest discover -s tests
```

Resultado esperado:

```text
OK
```

Estes testes nao chamam a API da Groq. Servem para confirmar:

- validacao local dos formatos;
- pagina web e endpoints basicos;
- nucleo do agente conversacional;
- helpers do adaptador Discord;
- rejeicao de inputs invalidos antes de criar cliente LLM.

## 2. Testar painel web sem gastar API

Executar:

```powershell
python web_demo.py
```

Abrir:

```text
http://127.0.0.1:5000
```

Confirmar:

- a pagina abre;
- o seletor de exemplos mostra inputs da pasta `data/`;
- se carregares em gerar sem texto nem ficheiro, aparece erro de input;
- se carregares um ficheiro nao suportado, aparece erro de formato.

Estes passos validam a interface sem gerar conteudo.

## 3. Testar geracao real no painel web

Garantir que o `.env` tem:

```text
GROQ_API_KEY=colocar_a_chave_aqui
```

Executar:

```powershell
python web_demo.py
```

Depois:

1. Abrir `http://127.0.0.1:5000`.
2. Escolher um exemplo.
3. Clicar em `Gerar conteudos`.
4. Confirmar que aparecem:
   - factos extraidos;
   - blog post;
   - LinkedIn post;
   - tweet thread;
   - newsletter section.
5. Clicar em `Exportar Markdown`.

## 4. Testar o agente Telegram

Garantir que o `.env` tem:

```text
GROQ_API_KEY=colocar_a_chave_aqui
TELEGRAM_BOT_TOKEN=colocar_o_token_do_bot_aqui
```

Executar:

```powershell
python telegram_agent.py
```

No Telegram:

1. Abrir conversa com o bot.
2. Enviar `/start`.
3. Enviar uma fonte de texto.
4. Confirmar que o bot responde com factos e os quatro formatos.
5. Enviar uma nota de voz, se quiseres testar transcricao.

## 5. Testar o agente Discord

Garantir que o `.env` tem:

```text
GROQ_API_KEY=colocar_a_chave_aqui
DISCORD_BOT_TOKEN=colocar_o_token_do_bot_aqui
```

No Discord Developer Portal:

1. Criar uma aplicacao.
2. Criar/adicionar um bot.
3. Copiar o token do bot para `DISCORD_BOT_TOKEN`.
4. Ativar `Message Content Intent` na pagina do bot.
5. Convidar o bot para um servidor com permissao de enviar mensagens e anexar ficheiros.

Executar:

```powershell
python discord_agent.py
```

No Discord:

1. Num canal onde o bot esteja presente, enviar `!help`.
2. Enviar:

```text
!pipeline Uma pequena equipa de estudantes testou uma aplicacao de estudo durante duas semanas. O teste envolveu 12 participantes. No final, 9 participantes afirmaram que a aplicacao ajudou a organizar melhor as sessoes de estudo. A equipa ainda nao avaliou impacto nas notas.
```

3. Confirmar que o bot responde com factos, os quatro formatos e o Markdown final.

## 6. Parar servidores

No terminal onde o servidor esta a correr, usar:

```text
Ctrl+C
```
