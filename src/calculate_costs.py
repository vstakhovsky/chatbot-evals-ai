"""Calculate cost estimates for OpenAI API usage."""

# OpenAI pricing (as of 2024)
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # per 1M tokens
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.02}  # per 1M tokens
}

# Approximate token counts
AVG_TOKENS = {
    "generation": {"input": 500, "output": 150},  # query generation
    "vibe_check": {"input": 600, "output": 200},  # 6 binary checks
    "rag": {"input": 800, "output": 300},  # RAG with context
    "judge": {"input": 700, "output": 100},  # single judge evaluation
    "gold": {"input": 1200, "output": 300}  # gold label with richer rubric
}

def calculate_stage_cost(model, num_calls, stage_type):
    """Calculate cost for a stage."""
    pricing = PRICING[model]
    tokens = AVG_TOKENS[stage_type]
    input_cost = (num_calls * tokens["input"] / 1_000_000) * pricing["input"]
    output_cost = (num_calls * tokens["output"] / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def calculate_pipeline_cost(num_queries=1500, vibe_acceptance_rate=0.75):
    """Calculate total pipeline cost estimate."""

    costs = {}

    # Stage 1: Query generation
    costs["query_generation"] = calculate_stage_cost("gpt-4o-mini", num_queries, "generation")

    # Stage 2: Vibe check validation (with regeneration)
    # 1.5x calls for regeneration
    vibe_calls = int(num_queries * 1.5)
    costs["vibe_check"] = calculate_stage_cost("gpt-4o-mini", vibe_calls, "vibe_check")

    # Stage 3: RAG pipeline
    # Embeddings: 786 corpus + num_queries
    embed_calls = 786 + num_queries
    costs["embeddings"] = calculate_stage_cost("text-embedding-3-small", embed_calls, "generation")

    # RAG answers (75% pass vibe check)
    rag_calls = int(num_queries * vibe_acceptance_rate)
    costs["rag_answers"] = calculate_stage_cost("gpt-4o-mini", rag_calls, "rag")

    # Stage 4: Six binary judges
    # 6 criteria × rag_calls
    judge_calls = rag_calls * 6
    costs["six_judges"] = calculate_stage_cost("gpt-4o-mini", judge_calls, "judge")

    # Total
    costs["total"] = sum(costs.values())

    return costs


if __name__ == "__main__":
    import sys
    num_queries = int(sys.argv[1]) if len(sys.argv) > 1 else 1500

    costs = calculate_pipeline_cost(num_queries)

    print("=" * 60)
    print("OPENAI API COST ESTIMATE")
    print("=" * 60)
    print(f"\nFor {num_queries:,} queries generated:")
    print(f"\nStage breakdown:")
    for stage, cost in costs.items():
        if stage != "total":
            print(f"  {stage:<20}: ${cost:.2f}")

    print(f"\n  {'Total':>20} ${costs['total']:.2f}")
    print("\n⚠ This is an estimate. Actual cost will vary by:")
    print("  - Real token usage per call")
    print("  - Vibe check acceptance rate (affects regeneration)")
    print("  - Model pricing changes")
    print("=" * 60)