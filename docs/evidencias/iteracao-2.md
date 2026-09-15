# Iteração 2 — resposta proporcional à complexidade do bug

**Data:** 14/09/2026
**Commit do prompt no Hub:** `c5b8d743` — https://smith.langchain.com/prompts/gabrielmorare/bug_to_user_story_v2
**Modelo (geração e avaliação):** `gemini-2.5-flash`

## O que mudou em relação à iteração 1

Atacando o recall baixo nos bugs complexos diagnosticado na rodada anterior:

1. **Regra de decomposição de múltiplos problemas** — quando o relato descreve problemas
   distintos e separáveis (numerados, ou por categoria), cada um vira um sub-item com letra
   própria (A, B, C...) dentro de `### Critérios de Aceitação`, com seu próprio
   Dado/Quando/Então, em vez de virar uma lista única achatada.
2. **Novas seções para bugs complexos** — `### Critérios Técnicos` (solução técnica por
   problema) e `### Tasks Técnicas Sugeridas` (lista acionável prefixada por área, ex.
   `[BACKEND]`, `[SEGURANÇA]`), que são exatamente as seções presentes nas referências dos
   3 bugs complexos do dataset.
3. **Regra de proporcionalidade** — o tamanho e o nível de detalhe da resposta devem
   acompanhar a complexidade do relato; proibido resumir bug complexo em poucas linhas.
4. **`### Contexto do Bug`** como alternativa a `### Impacto` quando o relato também traz
   severidade.
5. **4º exemplo few-shot** — bug de agendamento de entregas com 3 problemas numerados e
   bloco de impacto, demonstrando na prática o formato A/B/C + Critérios Técnicos +
   Contexto do Bug + Tasks Técnicas.

## Resultado

```
Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.90 ✓

Métricas Base:
  - F1-Score: 0.85 ✓
  - Clarity: 0.93 ✓
  - Precision: 0.95 ✓

📊 MÉDIA GERAL: 0.9129
✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

## Análise

**F1-Score: 0.77 → 0.85** (+0.08), cruzando o limite de aprovação. Todas as 5 métricas
ficaram ≥ 0.8 já nesta rodada.

A hipótese da iteração 1 se confirmou de forma direta — os 3 bugs complexos, que eram os 3
piores exemplos, foram os que mais subiram:

| Exemplo | Complexidade | F1 iteração 1 | F1 iteração 2 | Δ |
|---|---|---|---|---|
| #1 App offline-first | complex | 0.46 | **0.76** | +0.30 |
| #3 Checkout multi-falhas | complex | 0.53 | **0.78** | +0.25 |
| #2 Relatórios gerenciais | complex | 0.71 | **0.79** | +0.08 |

Precision subiu junto (0.94 → 0.95), o que é importante: a resposta ficou mais longa sem
passar a inventar conteúdo. Clarity caiu marginalmente (0.94 → 0.93) — custo esperado e
aceitável de respostas mais extensas.

## Por que ainda houve uma iteração 3

A rodada já está aprovada, mas **6 dos 15 exemplos continuam com F1 individual abaixo de
0.8** — incluindo os próprios 3 bugs complexos (0.76, 0.78, 0.79), que passaram a depender
de a média compensá-los:

| Exemplo | Complexidade | F1 |
|---|---|---|
| #6 App Android trava ao carregar notificações | medium | 0.70 |
| #4 Modal de confirmação atrás do overlay | medium | 0.73 |
| #1 App offline-first | complex | 0.76 |
| #10 Webhook de pagamento não chamado | medium | 0.77 |
| #3 Checkout multi-falhas | complex | 0.78 |
| #2 Relatórios gerenciais | complex | 0.79 |

Aprovar com 0.85 em um agregado de 15 exemplos avaliados por LLM-as-judge — que é
não-determinístico — significa pouca margem: uma variação normal entre execuções poderia
derrubar o F1 abaixo de 0.8 de novo. A iteração 3 ataca as causas específicas desses
exemplos para ganhar margem de segurança, em vez de parar na primeira aprovação.

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
      [1/15] F1:0.76 Clarity:0.83 Precision:0.90
      [2/15] F1:0.79 Clarity:0.83 Precision:0.90
      [3/15] F1:0.78 Clarity:0.93 Precision:1.00
      [4/15] F1:0.73 Clarity:0.98 Precision:0.90
      [5/15] F1:0.83 Clarity:0.88 Precision:0.97
      [6/15] F1:0.70 Clarity:0.95 Precision:0.90
      [7/15] F1:0.84 Clarity:0.98 Precision:0.97
      [8/15] F1:0.89 Clarity:0.98 Precision:0.93
      [9/15] F1:0.84 Clarity:0.98 Precision:0.90
      [10/15] F1:0.77 Clarity:0.82 Precision:0.95
      [11/15] F1:0.91 Clarity:0.98 Precision:0.97
      [12/15] F1:0.97 Clarity:1.00 Precision:0.93
      [13/15] F1:1.00 Clarity:0.95 Precision:1.00
      [14/15] F1:0.91 Clarity:0.95 Precision:1.00
      [15/15] F1:1.00 Clarity:0.93 Precision:1.00
==================================================
Prompt: gabrielmorare/bug_to_user_story_v2
==================================================
Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.90 ✓
Métricas Base:
  - F1-Score: 0.85 ✓
  - Clarity: 0.93 ✓
  - Precision: 0.95 ✓
--------------------------------------------------
📊 MÉDIA GERAL: 0.9129
--------------------------------------------------
✅ STATUS: APROVADO - Todas as métricas >= 0.8
==================================================
RESUMO FINAL
==================================================
Prompts avaliados: 1
Aprovados: 1
Reprovados: 0
✅ Todos os prompts atingiram todas as métricas >= 0.8!
✓ Confira os resultados em:
  https://smith.langchain.com/projects/mba-evaluation-prompt
Próximos passos:
1. Documente o processo no README.md
2. Capture screenshots das avaliações
3. Faça commit e push para o GitHub
```
