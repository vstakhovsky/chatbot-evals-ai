"""Validate generated queries for realism using LLM-as-a-judge."""

import asyncio
import csv
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from openai import AsyncOpenAI
from tqdm import tqdm
import pandas as pd

from src.config import VIBE_MODEL, BASE_URL, CONCURRENCY
from src.schemas import VibeCheckValidation

load_dotenv()

CLIENT = None


def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = AsyncOpenAI(
            base_url=BASE_URL,
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    return CLIENT


async def validate_query(row, persona_desc, problem_desc, modifier_desc):
    """Validate a single query."""
    prompt = Path("prompts/vibe_check.txt").read_text().format(
        query=row["query"],
        persona=persona_desc,
        problem=problem_desc,
        modifier=modifier_desc
    )

    client = get_client()
    response = await client.chat.completions.create(
        model=VIBE_MODEL,
        messages=[
            {"role": "system", "content": "You validate synthetic queries for realism. Output JSON with all checks as booleans, passed (bool), and reasoning (str)."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    result = json.loads(response.choices[0].message.content)
    return {**row, **result}


async def validate_queries_with_resume(input_file, output_file, personas, problems, modifiers):
    """Validate queries with checkpoint/resume capability."""

    # Load queries
    df = pd.read_csv(input_file)

    # Load existing validations if any
    existing = {}
    if output_file.exists():
        existing_df = pd.read_csv(output_file)
        for _, row in existing_df.iterrows():
            key = (row["persona_id"], row["problem_id"], row["modifier_id"])
            existing[key] = row

    # Find what's missing
    missing = []
    for _, row in df.iterrows():
        key = (row["persona_id"], row["problem_id"], row["modifier_id"])
        if key not in existing:
            missing.append(row)

    if existing:
        print(f"resume: {len(existing)} done, {len(missing)} missing")

    if not missing:
        print("All queries already validated")
        return pd.read_csv(output_file)

    # Build lookup dicts
    persona_lookup = {p["id"]: p["description"] for p in personas}
    problem_lookup = {p["id"]: p["description"] for p in problems}
    modifier_lookup = {m["id"]: m["description"] for m in modifiers}

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def validate_with_semaphore(row):
        async with semaphore:
            p_desc = persona_lookup[row["persona_id"]]
            pr_desc = problem_lookup[row["problem_id"]]
            m_desc = modifier_lookup[row["modifier_id"]]
            return await validate_query(row, p_desc, pr_desc, m_desc)

    # Validate missing ones
    results = []
    for row in tqdm(missing, desc="Validating queries"):
        result = await validate_with_semaphore(row)
        results.append(result)

        # Checkpoint incrementally
        output_file.parent.mkdir(parents=True, exist_ok=True)
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file, index=False)

    # Combine and return
    all_results = pd.DataFrame(list(existing.values()) + results)
    all_results.to_csv(output_file, index=False)

    return all_results


async def main():
    """Validate all generated queries."""
    # Load seeds
    personas = [json.loads(line) for line in Path("seeds/personas.jsonl").read_text().strip().split("\n")]
    problems = [json.loads(line) for line in Path("seeds/problems.jsonl").read_text().strip().split("\n")]
    modifiers = [json.loads(line) for line in Path("seeds/modifiers.jsonl").read_text().strip().split("\n")]

    input_file = Path("data/outputs/synthetic_queries.csv")
    output_file = Path("data/outputs/validated_queries.csv")

    if not input_file.exists():
        print(f"Error: {input_file} not found. Run generate_queries.py first.")
        return

    results_df = await validate_queries_with_resume(input_file, output_file, personas, problems, modifiers)

    print(f"\nValidated {len(results_df)} queries")
    print(f"Output: {output_file}")
    print(f"\nAcceptance rate: {results_df['passed'].mean():.2%}")
    print(f"\nSample validated queries:")
    print(results_df.head(3))

    return results_df


if __name__ == "__main__":
    asyncio.run(main())
