"""Configuration - single source of truth for models, paths, and settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Repository root
REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
PROMPTS_DIR = REPO_ROOT / "prompts"

# Models
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-3.5-turbo"  # Weak model for RAG (intentionally weak for evals)
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gpt-4o")  # Stronger model for dataset generation

# RAG settings
TOP_K = 4
RAG_CONCURRENCY = 8

# Checkpoint/evaluation settings
SAVE_EVERY = 25

# File paths
ARTICLES_PATH = DATA_DIR / "revolut_help_articles.jsonl"
SYNTHETIC_QUERIES_PATH = DATA_DIR / "synthetic_revolut_queries.csv"
RAG_OUTPUT_PATH = DATA_DIR / "synthetic_revolut_rag_outputs.csv"
PERSONAS_PATH = DATA_DIR / "synthetic_data_seeds" / "personas.json"
MODIFIERS_PATH = DATA_DIR / "synthetic_data_seeds" / "modifiers.json"
SCENARIOS_PATH = DATA_DIR / "synthetic_data_seeds" / "scenarios.json"

# Prompt files
RAG_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "rag_system.txt"
GENERATE_QUERY_PROMPT_PATH = PROMPTS_DIR / "generate_query.txt"

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment. Please set it in .env file.")
