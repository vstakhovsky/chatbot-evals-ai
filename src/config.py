"""Single source of truth for models and settings."""

BASE_URL = "https://openrouter.ai/api/v1"
EMBED_MODEL = "openai/text-embedding-3-small"
EMBED_MODEL_OPENAI = "text-embedding-3-small"  # ponytail: direct OpenAI for embeddings
STUDENT_MODEL = "openai/gpt-4o-mini"  # RAG answerer — weak on purpose
GEN_MODEL = "openai/gpt-4o-mini"  # synthetic query writer
VIBE_MODEL = "openai/gpt-4o-mini"  # realism validator
JUDGE_MODEL = "openai/gpt-4o-mini"  # the 6 graders
GOLD_MODEL = "openai/gpt-4o"  # gold labeler (strong)
REFLECTION_MODEL = "openai/gpt-4o"  # GEPA prompt rewriter (strong)

TOP_K = 4
MAX_ROWS = 24  # smoke run: test full pipeline with subset
CONCURRENCY = 8
GOLD_VOTES = 1  # 3 = majority vote for gold labels
SEED = 42

# Ponytail: all models via OpenRouter; fallback to direct OpenAI for embeddings if needed
