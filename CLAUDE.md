# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Desafio de MBA: fazer pull de um prompt ruim do LangSmith Prompt Hub (`leonanluppi/bug_to_user_story_v1`), otimizá-lo em YAML local, fazer push da v2 para o Hub sob o username do aluno, e avaliá-lo contra um dataset de 15 bugs até que **todas** as 5 métricas fiquem >= 0.8.

O LangSmith Hub é a **fonte única de verdade** na avaliação: `evaluate.py` não lê o YAML local — ele faz `hub.pull(f"{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2")`. Editar o YAML sem rodar `push_prompts.py` não muda nada na avaliação.

## Comandos

```bash
# Ambiente (Windows / PowerShell)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Ciclo completo
python src/pull_prompts.py      # baixa v1 do Hub -> prompts/bug_to_user_story_v1.yml
python src/push_prompts.py      # sobe prompts/bug_to_user_story_v2.yml -> Hub (público)
python src/evaluate.py          # puxa v2 do Hub, roda contra o dataset, imprime as 5 métricas

# Testes
pytest tests/test_prompts.py
pytest tests/test_prompts.py::TestPrompts::test_minimum_techniques   # teste único

# Smoke test das métricas isoladamente (faz chamadas reais ao LLM)
python src/metrics.py
```

Todos os scripts devem ser rodados **da raiz do projeto**: os módulos em `src/` usam imports flat (`from utils import ...`, `from metrics import ...`), que só resolvem porque Python adiciona o diretório do script ao `sys.path`. `python -m src.evaluate` quebra. Os caminhos de dataset também são relativos à raiz (`datasets/bug_to_user_story.jsonl`).

## Arquitetura

**Camada de provider** (`src/utils.py`): `get_llm()` e `get_eval_llm()` centralizam a escolha OpenAI vs. Google a partir de `LLM_PROVIDER`. Duas variáveis de modelo distintas: `LLM_MODEL` (gera as user stories) e `EVAL_MODEL` (o LLM-as-judge). `get_eval_llm()` é só `get_llm(model=EVAL_MODEL)`. `LLM_PROVIDER=google` no `.env.example` — o valor aceito é `google`, não `gemini` (embora `evaluate.py` aceite ambos ao checar as env vars obrigatórias).

**Métricas** (`src/metrics.py`): todas são LLM-as-judge — montam um prompt de avaliação pedindo JSON estrito e passam pelo `extract_json_from_response()`, que tem fallback tolerante (procura o primeiro `{` e o último `}`). Erro em qualquer avaliador retorna score 0.0 em vez de propagar exceção, então uma queda súbita para 0.0 costuma significar falha de API/parse, não prompt ruim.

O módulo exporta 7 funções de avaliação, mas **`evaluate.py` só usa 3**: `evaluate_f1_score`, `evaluate_clarity`, `evaluate_precision`. As outras 4 (`tone`, `acceptance_criteria`, `user_story_format`, `completeness`) são específicas de bug→user story e estão disponíveis mas não ligadas ao pipeline.

**As 5 métricas do relatório são derivadas de apenas 3 medições reais** (`src/evaluate.py:220-221`):
```
helpfulness = (clarity + precision) / 2
correctness = (f1_score + precision) / 2
```
Consequência prática ao iterar: `precision` entra em 3 das 5 métricas — é a alavanca de maior impacto. Não existe forma de melhorar helpfulness/correctness diretamente.

**Pipeline de avaliação** (`src/evaluate.py`): carrega o `.jsonl` → cria (ou reusa) um dataset no LangSmith chamado `{LANGSMITH_PROJECT}-eval` → `hub.pull` da v2 → encadeia `prompt | llm` por exemplo → roda os 3 avaliadores → média → status APROVADO/REPROVADO. O dataset é criado **apenas se ainda não existir**; alterar o `.jsonl` depois não atualiza o dataset remoto (seria preciso apagá-lo no LangSmith ou mudar `LANGSMITH_PROJECT`).

O prompt da v2 recebe os `inputs` do exemplo como variáveis de template. O dataset usa a chave `bug_report`, então **as variáveis do prompt v2 devem incluir `{bug_report}`** ou o `chain.invoke` falha silenciosamente (o erro é capturado, o exemplo vira resposta vazia e é pulado do cálculo).

**Contrato do YAML de prompt — a v2 é FLAT, sem chave-mãe.** `validate_prompt_structure()` (`src/utils.py:119`) lê os campos direto na raiz do dict:

```python
required_fields = ['description', 'system_prompt', 'version']
techniques = prompt_data.get('techniques_applied', [])
```

O `bug_to_user_story_v1.yml` aninha tudo sob a chave `bug_to_user_story_v1:` — se a v2 copiasse esse formato, `prompt_data.get('system_prompt')` leria o nível errado e a validação acusaria **todos os campos como faltando** em um prompt completo, quebrando silenciosamente os 6 testes obrigatórios e o `push_prompts.py`. Por isso `prompts/bug_to_user_story_v2.yml` tem `description`, `system_prompt`, `user_prompt`, `version`, `tags` e `techniques_applied` na raiz. Os requisitos: system_prompt não vazio, sem a string `TODO`, e **>= 2 itens em `techniques_applied`** — é esse campo que `test_minimum_techniques` consulta.

## Suítes de teste

- `tests/test_prompts.py` — os 6 testes obrigatórios do desafio, todos estáticos sobre `prompts/bug_to_user_story_v2.yml` (regex/YAML, sem rede).
- `tests/test_pull_prompts.py` e `tests/test_push_prompts.py` — testes unitários de `pull_prompts.py`/`push_prompts.py` com `hub.pull` e `langsmith.Client` mockados; nenhuma chamada real ao LangSmith acontece neles.

`pytest tests/ -v` roda tudo em segundos e sem custo de API.

## Registro das iterações

`docs/evidencias/iteracao-N.md` guarda, por rodada de otimização, o output bruto de `evaluate.py`, o que mudou no prompt e o diagnóstico da métrica que reprovou. Serve como prova auditável da jornada mesmo depois que os traces expiram no LangSmith (free tier retém traces por 14 dias — os prompts e datasets persistem, os traces não). `docs/output/plano-implementacao.md` é o plano técnico original.

## Não alterar

`src/evaluate.py`, `src/metrics.py`, `src/utils.py`, `datasets/bug_to_user_story.jsonl` e `prompts/bug_to_user_story_v1.yml` — material fornecido pelo desafio.

## Requisitos do desafio que restringem o código

- A v2 precisa aplicar **Few-shot obrigatoriamente** + pelo menos uma entre CoT, Tree of Thought, Skeleton of Thought, ReAct e Role Prompting; as técnicas escolhidas devem estar listadas em `techniques_applied`.
- O push precisa ser **público** (`is_public=True`), pois a entrega inclui link público do LangSmith.
- Espera-se de 3 a 5 iterações de push/evaluate até bater 0.8 em todas as métricas.
- O `README.md` é a entrega documental: precisa das seções "Técnicas Aplicadas", "Resultados Finais" (tabela v1 vs v2 + link/screenshots do dashboard) e "Como Executar".
