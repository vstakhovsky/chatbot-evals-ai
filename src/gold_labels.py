"""Generate gold labels for LLM judge evaluation.

Stratified sampling of ~150 rows per criterion from eval_results,
balanced across judge verdict × modifier combinations.
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
import numpy as np
from openai import AsyncOpenAI

from src.config import GOLD_MODEL, BASE_URL, SEED

load_dotenv()

CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("OPENAI_API_KEY"), timeout=60.0)
    return CLIENT


async def create_gold_label(row, criterion, prompt_file):
    """Create a gold label for a single row and criterion."""
    prompt = Path(prompt_file).read_text()

    # Format prompt with row data
    formatted_prompt = prompt.format(
        query=row["query"],
        answer=row["answer"],
        context=row.get("context", ""),
        persona=row.get("persona", "")
    )

    client = get_client()
    response = await client.chat.completions.create(
        model=GOLD_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert evaluator. Output JSON with passed (bool) and reasoning (str)."},
            {"role": "user", "content": formatted_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1500
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "criterion": criterion,
        "gold_passed": result["passed"],
        "gold_reasoning": result["reasoning"],
        "judge_passed": row[f"{criterion}_passed"],
        "judge_reasoning": row[f"{criterion}_reasoning"]
    }


def stratified_sample(eval_df, criterion, n_samples=150, random_seed=SEED):
    """Stratified sample balanced across judge verdict × modifier."""
    np.random.seed(random_seed)

    # Get unique modifiers
    modifiers = eval_df["modifier_id"].unique()

    # Calculate samples per stratum
    samples = []
    for modifier in modifiers:
        modifier_data = eval_df[eval_df["modifier_id"] == modifier]

        # Split by judge verdict for this criterion
        judge_col = f"{criterion}_passed"
        passed = modifier_data[modifier_data[judge_col] == True]
        failed = modifier_data[modifier_data[judge_col] == False]

        # Sample equal numbers of pass/fail from this modifier
        n_per_verdict = min(
            len(passed),
            len(failed),
            max(1, n_samples // (2 * len(modifiers)))  # At least 1 per stratum
        )

        if n_per_verdict > 0:
            samples.extend(passed.sample(n_per_verdict, random_state=random_seed).to_dict('records'))
            samples.extend(failed.sample(n_per_verdict, random_state=random_seed).to_dict('records'))

    # Shuffle and limit to n_samples
    np.random.shuffle(samples)
    return samples[:n_samples]


async def generate_gold_labels_for_criterion(eval_df, criterion, prompt_file, output_file, n_samples=150):
    """Generate gold labels for a single criterion."""
    print(f"\nGenerating {n_samples} gold labels for {criterion}...")

    # Stratified sample
    sampled_rows = stratified_sample(eval_df, criterion, n_samples)

    print(f"Sampled {len(sampled_rows)} rows (stratified by judge verdict × modifier)")

    # Generate labels
    results = []
    for i, row in enumerate(sampled_rows):
        result = await create_gold_label(row, criterion, prompt_file)
        result.update({
            "query": row["query"],
            "answer": row["answer"],
            "persona_id": row["persona_id"],
            "problem_id": row["problem_id"],
            "modifier_id": row["modifier_id"]
        })
        results.append(result)

        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(sampled_rows)} completed")

    # Save to CSV
    df = pd.DataFrame(results)
    df["human_override"] = "none"
    df = df[[
        "persona_id", "problem_id", "modifier_id", "query", "answer",
        "criterion", "gold_passed", "gold_reasoning",
        "judge_passed", "judge_reasoning", "human_override"
    ]]
    df.to_csv(output_file, index=False)

    print(f"  Saved {len(df)} gold labels to {output_file}")

    return df


async def main():
    """Generate gold labels for all criteria."""
    eval_file = Path("data/outputs/eval_results.csv")
    if not eval_file.exists():
        print(f"Error: {eval_file} not found. Run judges first.")
        return

    eval_df = pd.read_csv(eval_file)

    # Define criteria and their prompt files
    criteria = {
        "relevance": "prompts/gold/relevance.txt",
        "groundedness": "prompts/gold/groundedness.txt",
        "completeness": "prompts/gold/completeness.txt",
        "actionability": "prompts/gold/actionability.txt",
        "tone_empathy": "prompts/gold/tone_empathy.txt",
        "safety_compliance": "prompts/gold/safety_compliance.txt"
    }

    output_dir = Path("data/outputs/gold_labels")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for criterion, prompt_file in criteria.items():
        output_file = output_dir / f"gold_labels_{criterion}.csv"

        # Skip if exists
        if output_file.exists():
            print(f"Skipping {criterion} (already exists)")
            results[criterion] = pd.read_csv(output_file)
            continue

        # Check prompt file exists
        if not Path(prompt_file).exists():
            print(f"Warning: {prompt_file} not found, skipping {criterion}")
            continue

        df = await generate_gold_labels_for_criterion(
            eval_df, criterion, prompt_file, output_file, n_samples=150
        )
        results[criterion] = df

    print(f"\n{'='*60}")
    print(f"Gold label generation complete!")
    print(f"{'='*60}")
    for criterion, df in results.items():
        agreement_rate = (df["gold_passed"] == df["judge_passed"]).mean()
        print(f"{criterion}: {len(df)} labels, agreement: {agreement_rate:.2%}")


if __name__ == "__main__":
    asyncio.run(main())
