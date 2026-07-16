"""Single source of truth for models and settings."""

# OpenAI direct routing (primary)
BASE_URL = "https://api.openai.com/v1"
EMBED_MODEL = "text-embedding-3-small"
STUDENT_MODEL = "gpt-4o-mini"  # RAG answerer — weak on purpose
GEN_MODEL = "gpt-4o-mini"  # synthetic query writer
VIBE_MODEL = "gpt-4o-mini"  # realism validator
JUDGE_MODEL = "gpt-4o-mini"  # the 6 graders
GOLD_MODEL = "gpt-4o"  # gold labeler (strong)
REFLECTION_MODEL = "gpt-4o"  # GEPA prompt rewriter (strong)

# Max tokens caps
MAX_TOKENS_VIBE_CHECK = 800
MAX_TOKENS_JUDGES = 800
MAX_TOKENS_RAG = 600
MAX_TOKENS_GENERATION = 800
MAX_TOKENS_GOLD = 1500

# OpenRouter alternative (commented out)
# BASE_URL = "https://openrouter.ai/api/v1"
# STUDENT_MODEL = "openai/gpt-4o-mini"
# GEN_MODEL = "openai/gpt-4o-mini"
# VIBE_MODEL = "openai/gpt-4o-mini"
# JUDGE_MODEL = "openai/gpt-4o-mini"
# GOLD_MODEL = "openai/gpt-4o"
# REFLECTION_MODEL = "openai/gpt-4o"

TOP_K = 4
MAX_ROWS = None  # full run: 1500 queries (10 personas × 25 problems × 6 modifiers)
CONCURRENCY = 16
GOLD_VOTES = 1  # 3 = majority vote for gold labels
SEED = 42

# Ponytail: explicit concurrency for batch stages to prevent rate limits

# Ponytail: all models via OpenRouter; fallback to direct OpenAI for embeddings if needed
