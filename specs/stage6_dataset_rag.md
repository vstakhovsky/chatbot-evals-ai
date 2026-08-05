# Stage 6 — Synthetic dataset + RAG evaluation run

## Goal
1500 synthetic queries (15 personas × 10 scenarios × 10 modifiers, seeds in
data/synthetic_data_seeds/) answered by the RAG assistant; answers and contexts persisted.

## Acceptance
`python verify_stage6.py` exits 0. Open WARNs are listed in Status until closed.

## Status (evidence-based)
| Item | State | Evidence |
|---|---|---|
| queries dataset (1500 rows) | ⛔ FAIL | verify G3: row count == 1500 PASS; verify exits 1 on G4 |
| RAG outputs (1500 rows, 7 columns) | ⛔ FAIL | verify G4: columns == 7 expected, got ['persona','scenario','modifier','query','answer','retrieved_articles','hits'] |
| notebook Section 6 executed | ⛔ FAIL | verify NB: 5/6 cells unexecuted (execution_count is None) |
| open WARNs | ⛔ WARN | verify G2: every persona spans >= 6 topic groups (min=5) |

## File inventory (whitelist; anything off-list is deleted or must justify itself)
Product (mirrors ArTeria21/llm-eval-course/hw1):
  notebooks/faq_rag_chatbot.ipynb
  src/generate_dataset.py · src/schemas.py · src/config.py
  prompts/rag_system.txt · prompts/generate_query.txt   (deviation: reference inlines prompts)
  data/revolut_help_articles.jsonl · data/synthetic_revolut_queries.csv
  data/synthetic_revolut_rag_outputs.csv · data/synthetic_data_seeds/{personas,modifiers,scenarios}.json
Trust layer (price of agent delegate, capped, may not grow):
  CLAUDE.md · specs/rules.md · specs/stage6_dataset_rag.md · verify_stage6.py
  scripts/hooks.py · .claude/settings.json
Infra: pyproject.toml · uv.lock · .env.example · .gitignore
Stage 7 budget (for later): src/judges.py (reference bar: 220 LOC, one file)
  + prompts/judges/*.txt · specs/stage7_judges.md · verify_stage7.py

## Accepted deviations
- RAG loop lives in notebook Section 6 (reference shape); the script detour is reverted — the bulk of rows is already answered, the remaining run is short. <2025-01-05>
- Scenario ids are descriptive snake_case; the 9 golden ids preserved for benchmark joins. <2025-01-XX>

## Out of scope
Judges, metrics, GEPA, Arize → their own specs when those stages start.
