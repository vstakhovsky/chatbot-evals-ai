"""Six binary LLM judges for RAG evaluation."""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
from openai import AsyncOpenAI
from tqdm import tqdm

from src.config import JUDGE_MODEL, BASE_URL, CONCURRENCY
from src.schemas import JudgeResult

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
    """Judge a single row on a single criterion."""
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
    response = await client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "You evaluate RAG outputs. Output JSON with passed (bool) and reasoning (str)."},
            {"role": "user", "content": formatted_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    result = json.loads(response.choices[0].message.content)
    return result


async def judge_row(row, criteria=JUDGES.keys()):
    """Judge a single row on all criteria."""
    results = {}
    for criterion in criteria:
        result = await judge_criterion(row, criterion, JUDGES[criterion])
        results[f"{criterion}_passed"] = result["passed"]
        results[f"{criterion}_reasoning"] = result["reasoning"]
    return {**row, **results}


async def judge_with_resume(input_file, output_file):
    """Judge all rows with checkpoint/resume capability."""

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

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def judge_with_semaphore(idx):
        async with semaphore:
            row = df.loc[idx]
            return await judge_row(row)

    # Judge missing rows
    results = {}
    for idx in tqdm(missing_indices, desc="Judging rows"):
        result = await judge_with_semaphore(idx)
        results[idx] = result

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

    print(f"\nOutput: {output_file}")
    print(f"\nSample evaluated rows:")
    print(results_df.head(3))

    # Calculate pass rates
    criteria = [c for c in JUDGES.keys()]
    print(f"\nPass rates per criterion:")
    for criterion in criteria:
        col = f"{criterion}_passed"
        pass_rate = results_df[col].mean()
        print(f"  {criterion}: {pass_rate:.2%}")

    return results_df


if __name__ == "__main__":
    asyncio.run(main())
