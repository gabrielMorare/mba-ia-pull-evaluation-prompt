# Iteração 1 — versão inicial otimizada

**Data:** 14/09/2026
**Commit do prompt no Hub:** `7783acb3` — https://smith.langchain.com/prompts/gabrielmorare/bug_to_user_story_v2
**Modelo (geração e avaliação):** `gemini-2.5-flash` (`LLM_PROVIDER=google`)

## O que foi aplicado

Primeira refatoração completa do prompt `v1`, com as 3 técnicas declaradas em
`techniques_applied`:

- **Role Prompting** — persona de Product Manager / Business Analyst sênior (10+ anos),
  substituindo o "assistente" genérico do v1.
- **Chain of Thought (oculto)** — raciocínio interno em 4 passos (persona afetada → ação
  bloqueada → valor de negócio → critérios testáveis), com instrução explícita de **não**
  exibir esses passos na resposta.
- **Few-shot Learning** — 3 exemplos sintéticos de entrada/saída: um bug simples, um médio
  com contexto técnico e um complexo com impacto.

Além disso: formato Markdown obrigatório, template `Como um... eu quero... para que...`,
Critérios de Aceitação em Dado/Quando/Então, e seções condicionais `### Contexto Técnico`
e `### Impacto`.

## Resultado

```
Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.85 ✓

Métricas Base:
  - F1-Score: 0.77 ✗
  - Clarity: 0.94 ✓
  - Precision: 0.94 ✓

📊 MÉDIA GERAL: 0.8869
❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.8: f1_score
```

## Diagnóstico

Reprovou **apenas em F1-Score** (0.77 contra o mínimo de 0.8). Clarity e Precision já
ficaram altas (0.94), o que indica que o problema não é ruído nem alucinação — é
**recall**: falta conteúdo que a referência espera.

Cruzando o F1 por exemplo com a complexidade do dataset, o padrão é inequívoco — **os 3
bugs complexos são exatamente os 3 piores F1**:

| F1 | Complexidade | Tamanho da referência | Bug |
|---|---|---|---|
| 0.46 | complex | 5.756 chars | App de produtividade offline-first com bugs críticos |
| 0.53 | complex | 3.605 chars | Sistema de checkout com múltiplas falhas críticas |
| 0.67 | medium | 664 chars | Webhook de pagamento aprovado não é chamado |
| 0.70 | medium | 873 chars | Modal de confirmação aparece atrás do overlay |
| 0.71 | complex | 4.649 chars | Sistema de relatórios gerenciais com problemas severos |
| ... | | | |
| 1.00 | simple | 425 chars | Layout quebra em landscape no iOS |
| 1.00 | simple | 408 chars | Botão de adicionar ao carrinho não funciona |

As referências dos bugs complexos têm de 3.605 a 5.756 caracteres — **8 a 14 vezes maiores**
que as dos bugs simples (~400 chars), que pontuaram 0.8 a 1.0. Elas contêm seções que o
prompt atual sequer menciona: sub-cenários separados por problema, critérios técnicos e
tasks técnicas sugeridas.

O prompt trata todo bug com a mesma estrutura enxuta (User Story + Critérios + Contexto
Técnico + Impacto). Para um relato com 3 problemas distintos, isso produz uma resposta
curta que perde a maior parte do conteúdo esperado — recall baixo, logo F1 baixo.

## Próximo passo (iteração 2)

Ensinar o prompt a escalar a resposta com a complexidade do relato: decompor múltiplos
problemas em sub-itens, e adicionar as seções `### Critérios Técnicos` e
`### Tasks Técnicas Sugeridas` que as referências complexas apresentam.

## Output bruto da execução

```
==================================================
AVALIAÇÃO DE PROMPTS OTIMIZADOS
==================================================
Provider: google
Modelo Principal: gemini-2.5-flash
Modelo de Avaliação: gemini-2.5-flash
Criando dataset de avaliação: mba-evaluation-prompt-eval...
   ✓ Carregados 15 exemplos do arquivo datasets/bug_to_user_story.jsonl
   ✓ Dataset 'mba-evaluation-prompt-eval' já existe, usando existente
======================================================================
PROMPTS PARA AVALIAR
======================================================================
Este script irá puxar prompts do LangSmith Hub.
Certifique-se de ter feito push dos prompts antes de avaliar:
  python src/push_prompts.py
🔍 Avaliando: gabrielmorare/bug_to_user_story_v2
   Puxando prompt do LangSmith Hub: gabrielmorare/bug_to_user_story_v2
   ✓ Prompt carregado com sucesso
   Dataset: 15 exemplos
   Avaliando exemplos...
      [1/15] F1:0.46 Clarity:0.88 Precision:0.97
      [2/15] F1:0.71 Clarity:0.95 Precision:0.93
      [3/15] F1:0.53 Clarity:0.95 Precision:0.97
      [4/15] F1:0.70 Clarity:0.98 Precision:0.93
      [5/15] F1:0.77 Clarity:0.95 Precision:0.97
      [6/15] F1:0.73 Clarity:0.83 Precision:0.80
      [7/15] F1:0.82 Clarity:0.98 Precision:0.97
      [8/15] F1:0.87 Clarity:0.98 Precision:0.97
      [9/15] F1:0.75 Clarity:0.98 Precision:0.93
      [10/15] F1:0.67 Clarity:1.00 Precision:0.90
      [11/15] F1:0.80 Clarity:0.95 Precision:0.90
      [12/15] F1:0.82 Clarity:0.90 Precision:0.90
      [13/15] F1:1.00 Clarity:0.88 Precision:0.93
      [14/15] F1:0.91 Clarity:0.93 Precision:1.00
      [15/15] F1:1.00 Clarity:0.95 Precision:0.97
==================================================
Prompt: gabrielmorare/bug_to_user_story_v2
==================================================
Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.85 ✓
Métricas Base:
  - F1-Score: 0.77 ✗
  - Clarity: 0.94 ✓
  - Precision: 0.94 ✓
--------------------------------------------------
📊 MÉDIA GERAL: 0.8869
--------------------------------------------------
❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.8: f1_score
⚠️  Média atual: 0.8869 | Necessário: 0.8000
==================================================
RESUMO FINAL
==================================================
Prompts avaliados: 1
Aprovados: 0
Reprovados: 1
⚠️  Alguns prompts não atingiram todas as métricas >= 0.8
Próximos passos:
1. Refatore os prompts com score baixo
2. Faça push novamente: python src/push_prompts.py
3. Execute: python src/evaluate.py novamente
```
