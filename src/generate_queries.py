"""Generate synthetic customer queries from seed data."""

import asyncio
import csv
import json
import os
from pathlib import Path
from itertools import product
from dotenv import load_dotenv

from openai import AsyncOpenAI
from tqdm import tqdm

from src.config import GEN_MODEL, BASE_URL, MAX_ROWS, CONCURRENCY, SEED, MAX_TOKENS_GENERATION
from src.schemas import SyntheticQuery

load_dotenv()

CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = AsyncOpenAI(base_url=BASE_URL, api_key=os.getenv("OPENAI_API_KEY"))
    return CLIENT


def load_seeds():
    """Load all seed data."""
    personas = [json.loads(line) for line in Path("seeds/personas.jsonl").read_text().strip().split("\n")]
    problems = [json.loads(line) for line in Path("seeds/problems.jsonl").read_text().strip().split("\n")]
    modifiers = [json.loads(line) for line in Path("seeds/modifiers.jsonl").read_text().strip().split("\n")]
    return personas, problems, modifiers


def generate_grid(personas, problems, modifiers):
    """Generate the full grid of combinations."""
    if MAX_ROWS:
        personas = personas[:MAX_ROWS // (len(problems) * len(modifiers)) + 1]
        problems = problems[:MAX_ROWS // (len(personas) * len(modifiers)) + 1]
        modifiers = modifiers[:MAX_ROWS // (len(personas) * len(problems)) + 1]

    return list(product(personas, problems, modifiers))


async def generate_query(persona, problem, modifier):
    """Generate a single query."""
    prompt = Path("prompts/query_generation.txt").read_text().format(
        persona=persona["description"],
        problem=problem["description"],
        modifier=modifier["description"]
    )

    client = get_client()
    response = await client.chat.completions.create(
        model=GEN_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=MAX_TOKENS_GENERATION
    )

    query = response.choices[0].message.content().strip('"\'`')

    return {
        "persona_id": persona["id"],
        "problem_id": problem["id"],
        "modifier_id": modifier["id"],
        "query": query
    }


async def generate_queries_with_resume(grid, output_file):
    """Generate queries with checkpoint/resume capability."""
    # Load existing if any
    existing = {}
    if output_file.exists():
        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row["persona_id"], row["problem_id"], row["modifier_id"])
                existing[key] = row

    # Find what's missing
    missing = [g for g in grid if (g[0]["id"], g[1]["id"], g[2]["id"]) not in existing]

    if existing:
        print(f"resume: {len(existing)} done, {len(missing)} missing")

    if not missing:
        print("All queries already generated")
        return list(existing.values())

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def generate_with_semaphore(pers, prob, mod):
        async with semaphore:
            return await generate_query(pers, prob, mod)

    # Generate missing ones
    results = []
    for pers, prob, mod in tqdm(missing, desc="Generating queries"):
        result = await generate_with_semaphore(pers, prob, mod)
        results.append(result)

        # Checkpoint incrementally
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["persona_id", "problem_id", "modifier_id", "query"])
            if f.tell() == 0:
                f.write("")  # Empty file, write header
                f.seek(0)
                writer.writeheader()
            else:
                # File has content, seek to end before write
                f.seek(0, 2)

            writer.writerow(result)

    return list(existing.values()) + results


async def main():
    """Generate all synthetic queries."""
    personas, problems, modifiers = load_seeds()
    grid = generate_grid(personas, problems, modifiers)

    project_root = Path.cwd()
    while not (project_root / "src").exists() and project_root.parent != project_root:
        project_root = project_root.parent

    output_file = project_root / "data/outputs/synthetic_queries.csv"
    results = await generate_queries_with_resume(grid, output_file)

    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)

    print(f"\nGenerated {len(df)} queries")
    print(f"Output: {output_file}")
    print(f"\nSample queries:")
    print(df.head(3))

    return df


if __name__ == "__main__":
    asyncio.run(main())
