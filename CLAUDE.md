# Chatbot Evals AI

## Project Overview

Two-part LLM evaluation project:
1. RAG evals: Simple RAG chatbot over Revolut help articles, stress-tested with synthetic queries and binary LLM judges
2. GEPA optimization: DSPy GEPA applied to weakest judges against gold labels

## Where Config Lives

All models and settings in `src/config.py` — single source of truth.

## Style Rules

- **Prompts in files**: Every multi-line LLM prompt lives in `prompts/` as a .txt file loaded at runtime. Never inline.
- **Binary judges**: All judges output binary {passed: bool, reasoning: str} — no 0-5 scales.
- **No frameworks**: Plain functions, numpy in-memory retrieval. No LangChain, no LlamaIndex, no vector DB.
- **Checkpoint pattern**: Every batch LLM stage checkpoints to CSV incrementally, resumes on restart with printed "resume: X done, Y missing".
- **Asyncio + semaphore**: All batch LLM stages use asyncio with semaphore (concurrency from config).
- **Fixed seed**: All sampling and splits use SEED=42 from config.
- **Cost gate**: Before any stage making >2K LLM calls, print estimated count and stop for confirmation.

## Running

Smoke run: MAX_ROWS=24 in config.py
Full run: MAX_ROWS=None

## Execution Order

Branch: feat/rag-evals-and-gepa

1. Seeds with self vibe-check
2. Synthetic query generation
3. Query realism validation layer
4. RAG pipeline over Revolut articles
5. Six binary LLM judges
6. Pass rates, slices, error clustering
7. Gold labels and baseline agreement
8. GEPA optimization with evolution log
9. README, Serge workflow, anti-slop pass

## File Locations

- Seeds: `seeds/*.jsonl` (personas, problems, modifiers)
- Data: `data/revolut_help_articles.jsonl` (source), `data/outputs/*.csv` (results)
- Prompts: `prompts/*.txt` and `prompts/{judges,gold}/*.txt`
- Source: `src/*.py` (keep each under ~150 lines)
- Notebooks: `notebooks/01_rag_evals.ipynb`, `notebooks/02_gepa_optimization.ipynb`
