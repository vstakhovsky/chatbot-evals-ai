"""Validate generated queries for realism using LLM-as-a-judge."""

import asyncio
import csv
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

from openai import AsyncOpenAI
from tqdm import tqdm
import pandas as pd

from src.config import VIBE_MODEL, BASE_URL, CONCURRENCY, MAX_TOKENS_VIBE_CHECK
from src.schemas import VibeCheckValidation

load_dotenv()

CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("OPENAI_API_KEY"))
    return CLIENT


async def validate_query(row, persona_desc, problem_desc, modifier_desc):
    """Validate a single query - ONE structured call with all checks."""
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
            {"role": "system", "content": "You validate synthetic queries for realism. Output JSON with six boolean checks (looks_human_mobile, not_ai_slop, single_language, matches_problem, matches_persona, no_pii), passed (bool, AND of all), and reasoning (str)."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=MAX_TOKENS_VIBE_CHECK
    )

    result = json.loads(response.choices[0].message.content)
    return {**row, **result}


async def validate_queries_with_resume(input_file, output_file, personas, problems, modifiers):
    """Validate queries with checkpoint/resume capability and throughput reporting."""

    # Load queries
    df = pd.read_csv(input_file)

    # Load existing validations if any
    existing = {}
    if output_file.exists():
        existing_df = pd.read_csv(output_file)
        for _, row in existing_df.iterrows():
            # Use index as key
            existing[row.name] = row

    # Find what's missing
    missing_indices = [i for i in df.index if i not in existing]

    if existing:
        print(f"resume: {len(existing)} done, {len(missing_indices)} missing")

    if not missing_indices:
        print("All queries already validated")
        return pd.read_csv(output_file)

    # Build lookup dicts
    persona_lookup = {p["id"]: p["description"] for p in personas}
    problem_lookup = {p["id"]: p["description"] for p in problems}
    modifier_lookup = {m["id"]: m["description"] for m in modifiers}

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def validate_with_semaphore(idx):
        async with semaphore:
            row = df.loc[idx]
            p_desc = persona_lookup[row["persona_id"]]
            pr_desc = problem_lookup[row["problem_id"]]
            m_desc = modifier_lookup[row["modifier_id"]]
            return idx, await validate_query(row, p_desc, pr_desc, m_desc)

    # Throughput tracking
    start_time = time.time()
    batch_size = 100

    print(f"\nValidating {len(missing_indices)} queries with CONCURRENCY={CONCURRENCY}...")
    print(f"Estimated time: {len(missing_indices) / CONCURRENCY * 2.5 / 60:.1f} minutes")

    # Validate missing rows in batches with progress tracking
    results = {}
    batch_count = 0

    for i in range(0, len(missing_indices), batch_size):
        batch_indices = missing_indices[i:i + batch_size]

        # Process batch in parallel
        batch_tasks = [validate_with_semaphore(idx) for idx in batch_indices]
        batch_results = await asyncio.gather(*batch_tasks)

        # Store results
        for idx, result in batch_results:
            results[idx] = result

        batch_count += 1
        elapsed = time.time() - start_time
        total_done = len(existing) + len(results)
        throughput = total_done / elapsed if elapsed > 0 else 0

        # Print progress every batch
        current_time = datetime.now()
        elapsed_min = elapsed / 60
        eta = (len(missing_indices) - total_done + len(existing)) / throughput if throughput > 0 else 0
        eta_min = eta / 60

        print(f"[{current_time.strftime('%H:%M:%S')}] {total_done}/{len(df)} validated | "
              f"throughput: {throughput:.1f} rows/min | "
              f"ETA: {eta_min:.1f} min | "
              f"elapsed: {elapsed_min:.1f} min")

    # Combine and save
    all_results = []
    for idx in df.index:
        if idx in existing:
            all_results.append(existing[idx].to_dict())
        else:
            all_results.append(results[idx])

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(output_file, index=False)

    return results_df


async def main():
    """Validate all generated queries."""
    personas = [json.loads(line) for line in Path("seeds/personas.jsonl").read_text().strip().split("\n")]

    project_root = Path.cwd()
    while not (project_root / "src").exists() and project_root.parent != project_root:
        project_root = project_root.parent

    problems = [json.loads(line) for line in (project_root / "seeds/problems.jsonl").read_text().strip().split("\n")]
    modifiers = [json.loads(line) for line in (project_root / "seeds/modifiers.jsonl").read_text().strip().split("\n")]

    input_file = project_root / "data/outputs/synthetic_queries.csv"
    output_file = project_root / "data/outputs/validated_queries.csv"

    if not input_file.exists():
        print(f"Error: {input_file} not found. Run generate_queries.py first.")
        return

    results_df = await validate_queries_with_resume(input_file, output_file, personas, problems, modifiers)

    print(f"\n{'='*60}")
    print(f"Validation complete: {len(results_df)} queries")
    print(f"Output: {output_file}")
    print(f"\nAcceptance rate: {results_df['passed'].mean():.2%}")
    print(f"Passed: {results_df['passed'].sum()}/{len(results_df)}")
    print(f"{'='*60}")

    return results_df


if __name__ == "__main__":
    asyncio.run(main())
