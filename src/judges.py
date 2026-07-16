"""Six binary LLM judges for RAG evaluation."""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
from openai import AsyncOpenAI
from tqdm import tqdm

from src.config import JUDGE_MODEL, BASE_URL, MAX_TOKENS_JUDGES
from src.schemas import JudgeResult

load_dotenv()

CLIENT = None
# ponytail: conservative concurrency to avoid connection failures
JUDGE_CONCURRENCY = 4
MAX_RETRIES = 3
RETRY_DELAY = 2


def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = AsyncOpenAI(
            base_url=BASE_URL,
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=60.0,
            max_retries=0  # we handle retries manually
        )
    return CLIENT


JUDGES = {
    "relevance": {
        "prompt_file": "prompts/judges/relevance.txt",
        "inputs": ["query", "answer"]
    },
    "groundedness": {
        "prompt_file": "prompts/judges/groundedness.txt",
        "inputs": ["context", "answer"]
    },
    "completeness": {
        "prompt_file": "prompts/judges/completeness.txt",
        "inputs": ["gold_article", "answer"]
    },
    "actionability": {
        "prompt_file": "prompts/judges/actionability.txt",
        "inputs": ["query", "answer"]
    },
    "tone_empathy": {
        "prompt_file": "prompts/judges/tone_empathy.txt",
        "inputs": ["query", "modifier", "answer"]
    },
    "safety_compliance": {
        "prompt_file": "prompts/judges/safety_compliance.txt",
        "inputs": ["query", "context", "answer"]
    }
}


async def judge_criterion(row, criterion, judge_config):
    """Judge a single row on a single criterion with retry logic."""
    prompt = Path(judge_config["prompt_file"]).read_text()

    # Build input dict from row
    inputs = {}
    for input_key in judge_config["inputs"]:
        if input_key == "context":
            # Build context from retrieved articles
            titles = json.loads(row.get("retrieved_titles", "[]"))
            contents = []
            for i, title in enumerate(titles):
                contents.append(f"Article: {title}")
            inputs["context"] = "\n".join(contents)
        elif input_key == "gold_article":
            # In real system, you'd fetch the actual gold article
            # For now, use the retrieved articles as proxy
            inputs["gold_article"] = "See retrieved articles above"
        elif input_key == "modifier":
            # Get modifier description from seeds
            modifiers = [json.loads(line) for line in Path("seeds/modifiers.jsonl").read_text().strip().split("\n")]
            modifier_lookup = {m["id"]: m["description"] for m in modifiers}
            inputs["modifier"] = modifier_lookup.get(row.get("modifier_id", ""), "")
        else:
            inputs[input_key] = row.get(input_key, "")

    # Format prompt
    formatted_prompt = prompt.format(**inputs)

    client = get_client()

    # Retry with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": "You evaluate RAG outputs. Output JSON with passed (bool) and reasoning (str)."},
                    {"role": "user", "content": formatted_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=MAX_TOKENS_JUDGES
            )
            result = json.loads(response.choices[0].message.content)
            return criterion, result
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait_time = RETRY_DELAY * (2 ** attempt)
            print(f"  Retry {attempt + 1}/{MAX_RETRIES} for {criterion} after {wait_time}s (error: {e})")
            await asyncio.sleep(wait_time)


async def judge_row(row, criteria=JUDGES.keys()):
    """Judge a single row on all criteria - ALL SIX in parallel."""
    tasks = [judge_criterion(row, criterion, JUDGES[criterion]) for criterion in criteria]
    results = await asyncio.gather(*tasks)

    # Flatten results into dict
    flat = {}
    for criterion, result in results:
        flat[f"{criterion}_passed"] = result["passed"]
        flat[f"{criterion}_reasoning"] = result["reasoning"]

    return {**row, **flat}


async def judge_with_resume(input_file, output_file):
    """Judge all rows with checkpoint/resume capability and throughput reporting."""

    # Load RAG outputs
    df = pd.read_csv(input_file)

    # Load existing judgments if any
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
        print("All rows already judged")
        return pd.read_csv(output_file)

    semaphore = asyncio.Semaphore(JUDGE_CONCURRENCY)

    async def judge_with_semaphore(idx):
        async with semaphore:
            row = df.loc[idx]
            return idx, await judge_row(row)

    # Throughput tracking
    start_time = time.time()
    batch_size = 100

    print(f"\nJudging {len(missing_indices)} rows with CONCURRENCY={JUDGE_CONCURRENCY}...")
    print(f"Estimated time: {len(missing_indices) / JUDGE_CONCURRENCY * 2.5 / 60:.1f} minutes")

    # Judge missing rows in batches with progress tracking
    results = {}
    batch_count = 0

    for i in range(0, len(missing_indices), batch_size):
        batch_indices = missing_indices[i:i + batch_size]

        # Process batch in parallel
        batch_tasks = [judge_with_semaphore(idx) for idx in batch_indices]
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
        eta = (len(missing_indices) - (total_done - len(existing))) / throughput if throughput > 0 else 0
        eta_min = eta / 60

        print(f"[{current_time.strftime('%H:%M:%S')}] {total_done}/{len(df)} judged | "
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
    """Judge all RAG outputs."""
    input_file = Path("data/outputs/rag_outputs.csv")
    output_file = Path("data/outputs/eval_results.csv")

    if not input_file.exists():
        print(f"Error: {input_file} not found. Run rag.py first.")
        return

    print(f"Judging RAG outputs...")
    results_df = await judge_with_resume(input_file, output_file)

    print(f"\n{'='*60}")
    print(f"Judging complete: {len(results_df)} rows")
    print(f"Output: {output_file}")

    # Calculate pass rates
    criteria = [c for c in JUDGES.keys()]
    print(f"\nPass rates per criterion:")
    for criterion in criteria:
        col = f"{criterion}_passed"
        pass_rate = results_df[col].mean()
        passed = results_df[col].sum()
        print(f"  {criterion}: {pass_rate:.2%} ({passed}/{len(results_df)})")
    print(f"{'='*60}")

    return results_df


if __name__ == "__main__":
    asyncio.run(main())
