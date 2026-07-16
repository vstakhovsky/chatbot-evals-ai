"""Analyze evaluation results and show smoke test summary."""

import pandas as pd
import json


def analyze_smoke_results():
    """Show smoke test results with examples."""

    print("=" * 60)
    print("SMOKE TEST RESULTS - MAX_ROWS=24")
    print("=" * 60)

    # Load final results
    df = pd.read_csv("data/outputs/eval_results.csv")

    # Show sample queries
    print("\n=== STAGE 1: SYNTHETIC QUERIES (Sample) ===")
    queries_df = pd.read_csv("data/outputs/synthetic_queries.csv")
    print(f"Generated: {len(queries_df)} queries")
    print("\nSample queries:")
    for i, row in queries_df.head(3).iterrows():
        print(f"\n{i+1}. Persona: {row['persona_id']}")
        print(f"   Problem: {row['problem_id']}")
        print(f"   Modifier: {row['modifier_id']}")
        print(f"   Query: {row['query'][:100]}...")

    # Show validation results
    print("\n=== STAGE 2: VIBE CHECK VALIDATION ===")
    vibe_df = pd.read_csv("data/outputs/validated_queries.csv")
    print(f"Acceptance rate: {vibe_df['passed'].mean():.2%}")
    print(f"Accepted: {vibe_df['passed'].sum()}/{len(vibe_df)}")
    print("\nSample validated queries:")
    for i, row in vibe_df.head(3).iterrows():
        print(f"\n{i+1}. Passed: {row['passed']}")
        print(f"   Query: {row['query'][:80]}...")
        print(f"   Reasoning: {row['reasoning'][:60]}...")

    # Show RAG results
    print("\n=== STAGE 3: RAG PIPELINE ===")
    rag_df = pd.read_csv("data/outputs/rag_outputs.csv")
    print(f"RAG answers generated: {len(rag_df)}")
    print("\nSample RAG outputs:")
    for i, row in rag_df.head(2).iterrows():
        print(f"\n{i+1}. Query: {row['query'][:80]}...")
        print(f"   Answer: {row['answer'][:120]}...")

    # Show pass rates per criterion
    print("\n=== STAGE 4: SIX BINARY JUDGES ===")
    print(f"Rows evaluated: {len(df)}")
    print("\nPass rates per criterion:")
    criteria = ["relevance", "groundedness", "completeness", "actionability", "tone_empathy", "safety_compliance"]
    pass_rates = []
    for criterion in criteria:
        col = f"{criterion}_passed"
        pass_rate = df[col].mean()
        pass_rates.append((criterion, pass_rate))
        print(f"  {criterion:20s}: {pass_rate:6.2%}")

    # Calculate estimated call count and cost for full run
    print("\n" + "=" * 60)
    print("COST ESTIMATE FOR FULL 1,500-ROW RUN")
    print("=" * 60)

    # Current scale
    current_queries = len(queries_df)
    target_queries = 1500
    scale_factor = target_queries / current_queries

    # Estimate calls per stage for full run
    print("\nEstimated LLM calls:")

    # Stage 1: Query generation (10 personas × 25 problems × 6 modifiers = 1500)
    gen_calls = target_queries
    print(f"  Query generation: {gen_calls:,} calls")

    # Stage 2: Vibe check validation (assuming ~50% acceptance, 1 regenerate)
    vibe_calls = target_queries * 1.5  # 1.5x for regeneration
    print(f"  Vibe check: {vibe_calls:,} calls")

    # Stage 3: RAG (embeddings + answer generation)
    # Embeddings: corpus (786) + queries (1500)
    embed_calls = 786 + target_queries
    # Answers: 1 call per validated query (assume 75% pass vibe check)
    answer_calls = int(target_queries * 0.75)
    print(f"  Embeddings: {embed_calls:,} calls")
    print(f"  Answer generation: {answer_calls:,} calls")

    # Stage 4: Six judges (6 criteria × answer_calls)
    judge_calls = answer_calls * 6
    print(f"  Six judges: {judge_calls:,} calls")

    total_calls = gen_calls + vibe_calls + embed_calls + answer_calls + judge_calls
    print(f"\n  TOTAL: {total_calls:,} calls")

    # Cost estimate (rough)
    print("\nRough cost estimate:")
    # GPT-4o-mini pricing: $0.15/M input, $0.60/M output
    # text-embedding-3-small: $0.02/1M tokens

    avg_input_tokens = 500  # conservative estimate
    avg_output_tokens = 150

    chatgpt_calls = gen_calls + vibe_calls + answer_calls + judge_calls
    embed_calls_only = embed_calls

    chatgpt_cost = (chatgpt_calls * avg_input_tokens / 1_000_000 * 0.15 +
                    chatgpt_calls * avg_output_tokens / 1_000_000 * 0.60)
    embed_cost = embed_calls_only * avg_input_tokens / 1_000_000 * 0.02

    total_cost = chatgpt_cost + embed_cost

    print(f"  Chat completions: ${chatgpt_cost:.2f}")
    print(f"  Embeddings: ${embed_cost:.2f}")
    print(f"  TOTAL: ${total_cost:.2f}")

    print("\n⚠ This is a rough estimate. Actual cost will vary by:")
    print("  - Actual token usage per call")
    print("  - Vibe check acceptance rate")
    print("  - Model pricing changes")

    return df, pass_rates


if __name__ == "__main__":
    analyze_smoke_results()
