# Chatbot Evals AI

## Project Overview

This is a project for building evaluation for simple RAG pipeline of Revolut bank. The pipeline itself is a simple RAG chatbot over Revolut help articles. The articles database can be found in `data/revolut_help_articles.jsonl`. How RAG pipeline works can be found in `notebooks/faq_rag_chatbot.ipynb`.

## Where Config Lives

All models and settings in `src/config.py` — single source of truth.

## Implementation guidelines and rules

- **Keep it simple**: don't overcomplicate implementation, keep it clear and easy to review ande read. Don't overload code with verbose comments.
- **Security**: never expose keys or sensitive data in the codebase
- **Follow Python coding standarts**: Follow zen of Python, PEP8, DRY
- **Prompts in files**: Every multi-line LLM prompt lives in `prompts/` as a .txt file loaded at runtime. Never inline.
- **Binary judges**: All judges output binary {passed: bool, reasoning: str} — no 0-5 scales.
- **No frameworks**: Plain functions, numpy in-memory retrieval. No LangChain, no LlamaIndex, no vector DB.
- **Checkpoint pattern**: Every batch LLM stage checkpoints to CSV incrementally, resumes on restart with printed "resume: X done, Y missing".
- **Cost gate**: Before any stage making >2K LLM calls, print estimated count and stop for confirmation.
- **Keep everything excplicit**: All implementation steps should land in the codebase, no "outside" results or data.

## File Locations

- Data: `data/*.jsonl|csv`
- Prompts: `prompts/*.txt` and `prompts/{judges,gold}/*.txt`
- Notebooks: `notebooks/*.ipynb`
- Source implementation code: `src`
