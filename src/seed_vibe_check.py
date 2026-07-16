"""Validate seed data for realism using LLM-as-a-judge."""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from openai import AsyncOpenAI
from tqdm import tqdm

from src.config import VIBE_MODEL, BASE_URL, MAX_ROWS
from src.schemas import VibeCheckResult

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


async def validate_seed(seed: dict, seed_type: str) -> dict:
    """Validate a single seed for realism."""
    prompt = Path("prompts/seed_vibe_check.txt").read_text().format(
        seed=json.dumps(seed, indent=2),
        seed_type=seed_type
    )

    client = get_client()
    response = await client.chat.completions.create(
        model=VIBE_MODEL,
        messages=[
            {"role": "system", "content": "You evaluate whether support query seeds feel realistic. Output JSON with passed (bool) and reasoning (str)."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "seed_id": seed["id"],
        "seed_type": seed_type,
        "passed": result["passed"],
        "reasoning": result["reasoning"],
        "seed": seed
    }


async def validate_seeds(seeds_file: Path, seed_type: str) -> list[dict]:
    """Validate all seeds of one type."""
    seeds = [json.loads(line) for line in seeds_file.read_text().strip().split("\n")]

    if MAX_ROWS:
        seeds = seeds[:MAX_ROWS]

    semaphore = asyncio.Semaphore(8)

    async def validate_with_semaphore(seed):
        async with semaphore:
            return await validate_seed(seed, seed_type)

    results = await asyncio.gather(*[
        validate_with_semaphore(seed) for seed in seeds
    ])

    return results


async def main():
    """Run seed validation on personas and problems."""
    print("Validating seeds for realism...")

    personas_results = await validate_seeds(
        Path("seeds/personas.jsonl"),
        "persona"
    )

    problems_results = await validate_seeds(
        Path("seeds/problems.jsonl"),
        "problem"
    )

    all_results = personas_results + problems_results

    # Save results
    Path("data/outputs/seed_vibe_check.csv").parent.mkdir(parents=True, exist_ok=True)

    import pandas as pd
    df = pd.DataFrame(all_results)
    df.to_csv("data/outputs/seed_vibe_check.csv", index=False)

    # Print summary
    print("\n=== Seed Vibe Check Results ===")
    print(f"Total seeds: {len(df)}")
    print(f"Passed: {df['passed'].sum()}")
    print(f"Failed: {(~df['passed']).sum()}")

    print("\nFailed seeds:")
    failed = df[~df['passed']]
    for _, row in failed.iterrows():
        print(f"  - {row['seed_id']} ({row['seed_type']}): {row['reasoning']}")

    return df


if __name__ == "__main__":
    asyncio.run(main())
