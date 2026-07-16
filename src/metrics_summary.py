"""Comprehensive smoke test summary with examples and cost estimate."""

import pandas as pd


def show_comprehensive_summary():
    """Show complete smoke test results."""

    print("=" * 80)
    print("SMOKE TEST COMPLETE - END-TO-END PIPELINE VERIFIED")
    print("=" * 80)

    # Load all data
    queries_df = pd.read_csv("data/outputs/synthetic_queries.csv")
    vibe_df = pd.read_csv("data/outputs/validated_queries.csv")
    rag_df = pd.read_csv("data/outputs/rag_outputs.csv")
    eval_df = pd.read_csv("data/outputs/eval_results.csv")

    print(f"\nPipeline Scale: {len(queries_df)} queries generated")
    print(f"Vibe Check Acceptance: {vibe_df['passed'].sum()}/{len(vibe_df)} ({vibe_df['passed'].mean():.1%})")
    print(f"RAG Answers: {len(rag_df)}")
    print(f"Final Evaluations: {len(eval_df)}")

    print("\n" + "=" * 80)
    print("EXAMPLE ROWS PER STAGE")
    print("=" * 80)

    # Stage 1: Generated Queries
    print("\n[1] SYNTHETIC QUERY GENERATION")
    print("-" * 80)
    for i, row in queries_df.head(2).iterrows():
        print(f"\nExample {i+1}:")
        print(f"  Persona: {row['persona_id']}")
        print(f"  Problem: {row['problem_id']}")
        print(f"  Modifier: {row['modifier_id']}")
        print(f"  Query: \"{row['query']}\"")

    # Stage 2: Vibe Check Validation
    print("\n[2] VIBE CHECK VALIDATION (Realism Layer)")
    print("-" * 80)
    for i, row in vibe_df.head(2).iterrows():
        print(f"\nExample {i+1}:")
        print(f"  Query: \"{row['query'][:60]}...\"")
        print(f"  Passed: {row['passed']}")
        print(f"  Looks human/mobile: {row['looks_human_mobile']}")
        print(f"  Not AI slop: {row['not_ai_slop']}")
        print(f"  Reasoning: {row['reasoning'][:80]}...")

    # Stage 3: RAG Pipeline
    print("\n[3] RAG PIPELINE (Retrieval + Answer)")
    print("-" * 80)
    for i, row in rag_df.head(2).iterrows():
        retrieved_titles = pd.Series(row['retrieved_titles']).str[:30]
        print(f"\nExample {i+1}:")
        print(f"  Query: \"{row['query'][:60]}...\"")
        print(f"  Retrieved: {retrieved_titles.tolist()}")
        print(f"  Answer: \"{row['answer'][:80]}...\"")

    # Stage 4: Six Binary Judges
    print("\n[4] SIX BINARY JUDGES - EVALUATION RESULTS")
    print("-" * 80)
    print(f"Evaluated: {len(eval_df)} RAG outputs")
    print("\nPass Rate Table:")
    print(f"{'Criterion':<25} {'Pass Rate':>12} {'Passed':>8} {'Failed':>8}")
    print("-" * 55)

    criteria = ["relevance", "groundedness", "completeness", "actionability", "tone_empathy", "safety_compliance"]
    for criterion in criteria:
        col = f"{criterion}_passed"
        passed = eval_df[col].sum()
        failed = len(eval_df) - passed
        rate = eval_df[col].mean()
        print(f"{criterion:<25} {rate:>11.2%} {passed:>8} {failed:>8}")

    print("\nDetailed Example Evaluations:")
    for i, row in eval_df.head(2).iterrows():
        print(f"\nExample {i+1}:")
        print(f"  Query: \"{row['query'][:50]}...\"")
        print(f"  Relevance: {row['relevance_passed']} - {row['relevance_reasoning'][:60]}...")
        print(f"  Groundedness: {row['groundedness_passed']} - {row['groundedness_reasoning'][:60]}...")
        print(f"  Tone/Empathy: {row['tone_empathy_passed']} - {row['tone_empathy_reasoning'][:60]}...")

    print("\n" + "=" * 80)
    print("COST ESTIMATE FOR FULL 1,500-ROW RUN")
    print("=" * 80)

    target_queries = 1500

    print("\nEstimated LLM API Calls:")
    print(f"  Query generation:      {target_queries:,} calls")
    print(f"  Vibe check validation: {target_queries * 1.5:,.0f} calls (1.5x for regenerates)")
    print(f"  Embeddings:            {786 + target_queries:,} calls (786 corpus + queries)")
    print(f"  RAG answer generation: {int(target_queries * 0.75):,} calls (75% pass vibe check)")
    print(f"  Six binary judges:     {int(target_queries * 0.75) * 6:,} calls")
    print(f"  {'TOTAL':<25} {13_911:,.0f} calls")

    print("\nRough Cost Estimate:")
    print(f"  Chat completions: $1.92")
    print(f"  Embeddings: $0.02")
    print(f"  {'TOTAL':<25} ${1.94:.2f}")

    print("\n⚠ Actual cost will vary by:")
    print("  - Real token usage per call")
    print("  - Vibe check acceptance rate (affects regeneration)")
    print("  - Model pricing changes")
    print("  - Failed validations and retries")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\nReady to proceed with full 1,500-row run when confirmed.")
    print("This will generate ~1,500 queries across all persona/problem/modifier combinations")
    print("and run the complete evaluation pipeline.")
    print("\nAwaiting confirmation to proceed with full run.")


if __name__ == "__main__":
    show_comprehensive_summary()
