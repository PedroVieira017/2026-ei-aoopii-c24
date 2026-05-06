# Relatorio de testes de geracao

## Objetivo

Testar a pipeline com varios inputs para avaliar:

- cumprimento dos formatos pedidos;
- ausencia de Markdown indevido;
- limites de tamanho;
- portugues europeu;
- ausencia de verbos fortes nao suportados;
- fidelidade aos factos extraidos.

## Casos testados

Foram usados seis inputs:

- `data/exemplo_entrevista.txt`;
- `data/exemplo_nota_investigacao.txt`;
- `data/exemplo_voice_memo.txt`;
- input curto sobre uma sala de estudo;
- input com a palavra "ajudou", para verificar se o modelo nao transforma ajuda em garantia;
- input em ingles, para observar preservacao ou traducao do idioma.

## Resultado da primeira bateria

A primeira bateria correu a pipeline completa e revelou falhas factuais importantes:

- o LinkedIn acrescentou sentimentos nao presentes na fonte, como felicidade;
- a tweet thread acrescentou agradecimentos e generosidade;
- alguns textos usaram inferencias como "sugere", "potenciais vantagens" e "resultados iniciais";
- alguns outputs explicaram beneficios provaveis, como uma sala de estudo "oferecer espaco para estudar";
- alguns textos transformaram "disseram que ajudou" numa afirmacao geral de ajuda;
- houve repeticoes em alguns outputs curtos.

As regras formais estavam geralmente bem: os limites de newsletter, estrutura da tweet thread e ausencia de Markdown passaram na maioria dos casos.

## Correcoes aplicadas

Depois da bateria inicial foram feitas melhorias:

- prompts de blog, LinkedIn, tweet thread e newsletter foram reforcados para exigir suporte direto em factos;
- `compliance_review.txt` passou a tratar os factos como fonte completa e exaustiva;
- foi adicionada uma etapa final de reparacao factual em `app.py`;
- a validacao de repeticoes passou a ignorar o titulo em formatos com titulo, para reduzir falsos positivos;
- foi definido `MODEL_MAX_TOKENS` para limitar outputs excessivos.

## Limite encontrado

A segunda bateria foi interrompida por limite de tokens da Groq:

```text
Rate limit reached for model llama-3.3-70b-versatile
Limit 100000 tokens/day
Used approximately 99641 tokens
```

Por isso, a bateria completa pos-correcao deve ser repetida quando o limite da API voltar a estar disponivel.

## Conclusao

Nao e correto afirmar que a saida fica sempre 100% correta. A pipeline ficou mais robusta, mas outputs gerados por LLM devem continuar a ser validados. O projeto agora inclui mecanismos para reduzir os erros principais: extracao de factos, revisao de conformidade, reparacao factual final e validacao local por formato.
