# Plano de Implementação — Pull, Otimização e Avaliação de Prompts (Bug → User Story)

> Documento de planejamento técnico para o desafio do MBA em Engenharia de IA. Elaborado a partir da leitura integral do `README.md` do desafio, do código já existente neste repositório (`src/`, `prompts/`, `tests/`, `utils.py`, `metrics.py`, `evaluate.py`) e do projeto de referência da disciplina (`C:\git\aulas\02-mba-ia-prompt-engineering`, com foco em `7-evaluation`).

---

## 0. Decisões já confirmadas com o solicitante

| Decisão | Escolha | Justificativa |
|---|---|---|
| **Provider de LLM** | Google Gemini (`gemini-2.5-flash`) para geração e avaliação | Já configurado como default, chave já disponível, camada gratuita (limites: 15 req/min, 1500 req/dia — ver seção de Riscos) |
| **Técnicas de prompt** (além de Few-shot, que é obrigatório) | **Role Prompting** + **Chain of Thought (CoT)** | Role Prompting fixa persona e vocabulário (ajuda Clarity/Helpfulness); CoT interno reduz perda de detalhes técnicos em bugs médios/complexos (ajuda F1/Precision/Correctness) |
| **Credenciais** | Movidas para `.env` local (git-ignored); `.env.example` restaurado ao template vazio | O `.env.example` está versionado e o repositório final precisa ser público — chaves reais nunca podem estar nesse arquivo |
| **Execução das etapas** | Eu implemento todo o código e posso rodar o `pull` sozinho (é somente leitura, sem efeito colateral). Push, avaliação e iteração serão feitos com você "copilotando" | Push cria um prompt **público** na sua conta do LangSmith Hub e consome sua cota de API — ação com efeito em sistema externo e visível para terceiros, deve ser feita com sua presença |

### ⚠️ Ação obrigatória sua antes de qualquer `push`/`evaluate`

O `.env` que criei localmente ainda tem **`USERNAME_LANGSMITH_HUB` vazio** — eu não posso adivinhar seu usuário do LangSmith Hub. Além disso, o `Client.push_prompt(..., is_public=True)` da LangSmith **falha se sua conta ainda não tiver um "handle" público configurado** (mensagem oficial da lib: *"Cannot create a public prompt without first creating a LangChain Hub handle"*). Antes de rodarmos `push_prompts.py`, você precisa:

1. Acessar https://smith.langchain.com/prompts e, se ainda não tiver, criar/confirmar seu handle público (username).
2. Preencher `USERNAME_LANGSMITH_HUB=<seu-usuario>` no `.env` local.

Isso não bloqueia a implementação do código nem o `pull`, apenas o `push`/`evaluate` reais.

---

## 1. Diagnóstico do prompt v1 (o que está errado)

Lendo `prompts/bug_to_user_story_v1.yml`:

- **`{bug_report}` duplicado**: aparece embutido no `system_prompt` *e* de novo como `user_prompt`. Isso confunde o modelo sobre qual é a instrução e qual é o dado de entrada, e desperdiça contexto.
- **Sem persona**: começa com "Você é um assistente que ajuda a...", vago demais — nenhuma especialização, tom ou nível de experiência definidos.
- **Sem few-shot**: zero exemplos de entrada/saída — o modelo não tem referência de formato, nível de detalhe ou tom esperado.
- **Sem formato de saída exigido**: não há especificação de Markdown, template "Como um... Eu quero... Para que...", nem de Critérios de Aceitação.
- **Sem tratamento de edge cases**: bugs simples, médios e complexos (ver `datasets/bug_to_user_story.jsonl`, que já os classifica em `metadata.complexity`) recebem exatamente o mesmo tratamento raso.
- **Instrução final vaga**: "Analise o relato de bug abaixo e crie uma user story a partir dele" não diz *como* pensar sobre o problema nem *o que* obrigatoriamente incluir.

Isso explica os scores baixos do exemplo ilustrativo no README (~0.45–0.52 em todas as métricas).

---

## 2. Arquitetura da solução v2

### 2.1 Schema do `prompts/bug_to_user_story_v2.yml` — atenção a um detalhe não óbvio

`utils.validate_prompt_structure(prompt_data)` (arquivo que **não deve ser alterado**) espera os campos **no nível raiz** do dicionário carregado do YAML:

```python
required_fields = ['description', 'system_prompt', 'version']
...
techniques = prompt_data.get('techniques_applied', [])
```

Só que `bug_to_user_story_v1.yml` **não segue esse formato** — ele aninha tudo sob uma chave `bug_to_user_story_v1:`. Se `prompts/bug_to_user_story_v2.yml` repetir esse aninhamento (`bug_to_user_story_v2: {...}`), `validate_prompt_structure()` receberia esse dict aninhado, faria `.get('system_prompt')` no nível errado e retornaria **todos os campos como "faltando"**, mesmo estando tudo preenchido corretamente. Isso quebraria silenciosamente tanto os testes obrigatórios de `tests/test_prompts.py` quanto qualquer validação em `push_prompts.py` que reutilize essa função.

**Decisão de arquitetura:** `prompts/bug_to_user_story_v2.yml` será **plano (flat)** no nível raiz:

```yaml
description: "..."
system_prompt: |
  ...
user_prompt: "{bug_report}"
version: "v2"
created_at: "2026-07-07"
tags: [...]
techniques_applied:
  - "Few-shot Learning"
  - "Role Prompting"
  - "Chain of Thought (CoT)"
```

### 2.2 Design do `system_prompt` (Role Prompting + CoT + Few-shot)

**Persona (Role Prompting):** definir o modelo como um Product Manager/Business Analyst sênior, especializado em transformar relatos de bug em User Stories ágeis prontas para backlog — com anos de prática em Discovery, priorização e escrita de Critérios de Aceitação testáveis.

**Regras explícitas de formato (obrigatório pelo README):**
- Markdown.
- Template padrão: `Como um [persona], eu quero [ação], para que [benefício]`.
- Seção separada de **Critérios de Aceitação** em formato Given/When/Then.
- Seções condicionais por complexidade (edge cases):
  - Bug simples → apenas User Story + Critérios de Aceitação.
  - Bug médio/complexo com contexto técnico (logs, endpoints, stack traces) → incluir seção **Contexto Técnico**.
  - Bug com impacto/severidade mencionados → incluir observação de **Impacto**.

  *(Essas seções condicionais não são pontuadas pelas 3 métricas hoje conectadas em `evaluate.py`, mas alinham o prompt com `evaluate_completeness_score` em `metrics.py` — métrica de referência não usada no pipeline atual, mas que documenta a expectativa "oficial" da disciplina para esse tipo de tarefa, então vale seguir por robustez.)*

**Chain of Thought (oculto):** instruir o modelo a raciocinar internamente em etapas antes de responder — (1) identificar o tipo de usuário afetado, (2) identificar a ação impedida pelo bug, (3) identificar o valor de negócio perdido, (4) derivar os critérios de aceite testáveis — mas **exibir somente o resultado final formatado**, nunca o raciocínio passo a passo cru. Isso é importante: um CoT "vazado" na resposta prejudicaria diretamente a métrica **Clarity** (penaliza verbosidade/ambiguidade) e a **Precision** (penaliza texto fora do que foi pedido).

**Few-shot (obrigatório):** 2–3 exemplos completos de entrada/saída embutidos diretamente no `system_prompt` (texto estático, não os 15 exemplos do dataset de avaliação — usar exemplos *sintéticos* próprios para não contaminar a avaliação, já que o dataset existente é a régua de teste, não o material de treino do prompt). Cobrir pelo menos um caso simples, um médio (com contexto técnico) e idealmente um complexo, espelhando a taxonomia de `metadata.complexity` do dataset real.

### 2.3 `src/pull_prompts.py`

1. `hub.pull("leonanluppi/bug_to_user_story_v1")` → retorna um `ChatPromptTemplate`.
2. Extrair as mensagens (`system` / `human`) do objeto retornado.
3. Serializar para o mesmo formato YAML já usado em `prompts/bug_to_user_story_v1.yml` (usando `utils.save_yaml`).
4. Tratar erro de forma clara caso `LANGSMITH_API_KEY` esteja ausente ou o prompt não seja encontrado (mesmo padrão de mensagens de erro já usado em `evaluate.py`).

Executarei este script eu mesmo assim que implementado — é somente leitura de um prompt público de terceiros, sem custo relevante nem efeito colateral em conta.

### 2.4 `src/push_prompts.py`

1. `utils.load_yaml("prompts/bug_to_user_story_v2.yml")`.
2. Validar com `utils.validate_prompt_structure()` — abortar com mensagem clara se inválido (nunca dar push de um prompt malformado).
3. Montar `ChatPromptTemplate.from_messages([("system", data["system_prompt"]), ("user", data["user_prompt"])])`.
4. `client.push_prompt(f"{username}/bug_to_user_story_v2", object=prompt_obj, is_public=True, description=data["description"], tags=data.get("techniques_applied", []) + data.get("tags", []))`.
5. Ler `USERNAME_LANGSMITH_HUB` do `.env` (via `check_env_vars`) e falhar cedo com mensagem acionável se estiver vazio.

Padrão extraído diretamente de `7-evaluation/3-pairwise/create_prompts.py` e do docstring de `Client.push_prompt` na lib instalada — é o mesmo idioma usado pelo professor no restante da disciplina.

### 2.5 `tests/test_prompts.py` — mapeamento dos 6 testes obrigatórios

| Teste | Verificação |
|---|---|
| `test_prompt_has_system_prompt` | `system_prompt` existe, não é `None`, `.strip()` não vazio |
| `test_prompt_has_role_definition` | `system_prompt` contém marcador de persona (ex.: regex por `"Você é um"` / `"Product Manager"` / `"Business Analyst"`) |
| `test_prompt_mentions_format` | `system_prompt` menciona `Markdown` **e** o template `Como um`/`User Story` |
| `test_prompt_has_few_shot_examples` | `system_prompt` contém pelo menos 2 blocos de exemplo (ex.: contagem de ocorrências de marcador `"Exemplo"` ou de pares bug/user-story) |
| `test_prompt_no_todos` | `"[TODO]"` (e variações) **não** aparece em nenhum campo de texto |
| `test_minimum_techniques` | `len(prompt_data.get("techniques_applied", [])) >= 2` — reaproveitando `utils.validate_prompt_structure` quando possível, para não duplicar lógica |

Todos são estáticos (YAML/regex), sem chamadas de rede ou LLM — coerente com `pytest tests/test_prompts.py` rodando em segundos.

### 2.6 Atualização do `README.md`

Adicionar, ao final do README existente, as 3 seções exigidas pelo desafio:
- **"Técnicas Aplicadas (Fase 2)"** — Role Prompting + CoT + Few-shot, com justificativa e um trecho de exemplo real do `system_prompt` v2 para cada técnica.
- **"Resultados Finais"** — tabela comparativa v1 vs v2 (as 5 métricas), link do dashboard público do LangSmith e espaço para os screenshots que você vai capturar.
- **"Como Executar"** — passo a passo (setup, pull, editar, push, evaluate, testes), praticamente já coberto pelo `CLAUDE.md`, mas reescrito em tom de entrega para quem for avaliar o desafio.

---

## 3. Ordem de execução (cronograma)

1. Implementar `src/pull_prompts.py` → eu executo (`python src/pull_prompts.py`), confirmando que `prompts/bug_to_user_story_v1.yml` é reproduzido a partir do Hub.
2. Escrever `prompts/bug_to_user_story_v2.yml` completo (persona + CoT oculto + few-shot + formato + techniques_applied).
3. Implementar `src/push_prompts.py`.
4. **Pausa para você**: preencher `USERNAME_LANGSMITH_HUB` no `.env` e confirmar handle público no LangSmith.
5. Implementar os 6 testes em `tests/test_prompts.py` e rodar `pytest tests/test_prompts.py` (sem custo, sem rede) — corrigir o YAML até passar 100%.
6. Rodar `python src/push_prompts.py` **junto com você** (ação pública, visível na sua conta).
7. Rodar `python src/evaluate.py` **junto com você** — analisar as 5 métricas.
8. Iterar sobre `prompts/bug_to_user_story_v2.yml` conforme métricas abaixo de 0.8 → repetir passos 6–7 (README espera 3–5 iterações).
9. Atualizar `README.md` com as 3 seções obrigatórias, incluindo os números finais reais.
10. Entregar um **checklist de testes manuais** para você validar tudo de ponta a ponta (será o TODO final, gerado ao término da implementação, conforme combinado).

---

## 4. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| **Rate limit do Gemini free tier** (15 req/min, 1500/dia) | Cada rodada de `evaluate.py` faz ~60 chamadas de LLM (15 exemplos × [1 geração + 3 juízes]). `metrics.py` **zera silenciosamente o score** (`0.0`) em qualquer exceção — inclusive erro 429 —, o que pode mascarar um prompt bom como reprovado | Rodar `evaluate.py` de forma isolada (sem paralelismo — já é sequencial), observar o console para mensagens `❌ Erro ao avaliar`; se aparecerem, aguardar ~1 min e rodar de novo antes de concluir que o prompt precisa mudar |
| **Handle público não configurado no LangSmith** | `push_prompt(..., is_public=True)` falha com erro claro da própria lib | Passo 4 do cronograma — pré-requisito antes do push |
| **Contaminação do few-shot com dados de avaliação** | Usar os mesmos 15 exemplos do dataset como few-shot infla artificialmente as métricas (o modelo "decora" a resposta esperada) | Few-shot usa exemplos sintéticos próprios, nunca uma cópia dos 15 do `datasets/bug_to_user_story.jsonl` |
| **Schema aninhado incorreto no YAML v2** (ver seção 2.1) | Quebra silenciosa de `validate_prompt_structure()` e dos testes | YAML v2 será flat desde o início; teste unitário cobre isso |

---

## 5. Critérios de aceite (Definition of Done)

- [ ] `pytest tests/test_prompts.py` — 6/6 testes passando, sem chamadas de rede.
- [ ] `python src/evaluate.py` — as 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision) todas **≥ 0.8** simultaneamente (não só a média).
- [ ] Prompt publicado como **público** em `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` no LangSmith Hub.
- [ ] `README.md` com as 3 seções exigidas preenchidas com dados reais (não placeholders).
- [ ] Nenhuma credencial real em arquivos versionados (`.env.example` permanece com placeholders vazios).

---

## 6. Próximos passos imediatos

Após sua aprovação deste plano, eu:
1. Implemento `src/pull_prompts.py` e já executo o pull.
2. Escrevo `prompts/bug_to_user_story_v2.yml`.
3. Implemento `src/push_prompts.py` e `tests/test_prompts.py`.
4. Aviso você para o passo de configuração do handle do LangSmith Hub antes de qualquer push/evaluate real.
