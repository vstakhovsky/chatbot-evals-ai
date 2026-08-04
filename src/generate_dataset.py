#!/usr/bin/env python3
"""Generate synthetic queries dataset.

15 personas × 10 scenarios × 10 modifiers = 1500 queries
"""

import asyncio
import json
import argparse
from pathlib import Path
from itertools import product
from collections import defaultdict
from typing import List

import pandas as pd
from openai import AsyncOpenAI
from tqdm import tqdm
from pydantic import ValidationError

from src.config import *
from src.schemas import GeneratedQuery

# Load generation prompt
with open(GENERATE_QUERY_PROMPT_PATH, 'r') as f:
    GENERATE_PROMPT_TEMPLATE = f.read()

# Load seeds
def load_seeds():
    with open(PERSONAS_PATH) as f:
        personas = {p['persona']: p for p in json.load(f)}
    with open(MODIFIERS_PATH) as f:
        modifiers = {m['modifier']: m for m in json.load(f)}
    with open(SCENARIOS_PATH) as f:
        scenarios = json.load(f)
    return personas, modifiers, scenarios

# Format prompt for generation
def format_prompt(persona, scenario, modifier):
    """Format generation prompt with persona, scenario, modifier."""
    # Get scenario intent
    scenario_obj = next(s for s in load_seeds()[2] if s['scenario'] == scenario)
    intent = scenario_obj['intent_summary']
    articles = scenario_obj['target_articles']

    return GENERATE_PROMPT_TEMPLATE.format(
        persona_description=persona['description'],
        english_level=persona['english'],
        scenario_intent=intent,
        target_articles='\n'.join(f'- {a}' for a in articles),
        modifier_instructions=modifier['style_instructions']
    )

# Generate single query with structured output
async def generate_query(client, persona, scenario, modifier, semaphore):
    async with semaphore:
        prompt = format_prompt(persona, scenario, modifier)

        try:
            resp = await client.chat.completions.create(
                model=GENERATION_MODEL,
                messages=[
                    {'role': 'system', 'content': 'You are an expert at writing realistic user support queries. Output valid JSON only.'},
                    {'role': 'user', 'content': prompt + '\n\nOutput your response as a JSON object with key "query" containing the generated text.'}
                ],
                temperature=0.9,
                response_format={'type': 'json_object'}
            )

            result = json.loads(resp.choices[0].message.content)

            # Validate with pydantic
            validated = GeneratedQuery(**result)
            return validated.query

        except (ValidationError, json.JSONDecodeError, KeyError) as e:
            print(f"Validation error for {persona['persona']}/{scenario}/{modifier['modifier']}: {e}")
            return None
        except Exception as e:
            print(f"Generation error for {persona['persona']}/{scenario}/{modifier['modifier']}: {e}")
            return None

# Main generation function
async def generate_dataset(max_rows=None, concurrency=8, confirm=True):
    """Generate synthetic queries dataset."""
    personas, modifiers, scenarios = load_seeds()

    # Build full grid of combinations
    combinations = []
    for scenario_obj in scenarios:
        persona = personas[scenario_obj['persona']]
        scenario = scenario_obj['scenario']
        for modifier in modifiers.values():
            combinations.append((persona, scenario, modifier))

    if max_rows:
        combinations = combinations[:max_rows]

    print(f'Total combinations to generate: {len(combinations)}')

    # Check for existing results
    existing = set()
    if SYNTHETIC_QUERIES_PATH.exists():
        try:
            df = pd.read_csv(SYNTHETIC_QUERIES_PATH)
            existing = set(zip(df['persona'], df['scenario'], df['modifier']))
            print(f'Resume: {len(existing)} done, {len(combinations) - len(existing)} missing')
        except Exception as e:
            print(f'Could not load existing file: {e}')

    # Filter out existing combinations
    todo = [c for c in combinations if (c[0]['persona'], c[1], c[2]['modifier']) not in existing]
    print(f'Generating {len(todo)} new queries')

    if not todo:
        print('All queries already generated!')
        return

    # Estimate calls and cost gate (1 call per combo, not counting retries)
    estimated_calls = len(todo)
    print(f'\\nEstimated API calls: {estimated_calls}')

    if estimated_calls > 2000:
        if confirm:
            response = input('This will make >2000 API calls. Continue? (yes/no): ')
            if response.lower() != 'yes':
                print('Aborted.')
                return
        else:
            print('Skipping confirmation (--yes flag set)')

    # Generate with semaphore
    semaphore = asyncio.Semaphore(concurrency)
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    results = []
    checkpoint_interval = SAVE_EVERY

    async def generate_with_progress(combo):
        persona, scenario, modifier = combo
        query = await generate_query(client, persona, scenario, modifier, semaphore)
        if query:
            results.append({
                'persona': persona['persona'],
                'scenario': scenario,
                'modifier': modifier['modifier'],
                'query': query
            })
        return query is not None

    # Process with progress bar
    successes = 0
    for combo in tqdm(todo, desc='Generating'):
        if await generate_with_progress(combo):
            successes += 1

        # Checkpoint
        if len(results) % checkpoint_interval == 0:
            save_checkpoint(results, existing)
            print(f'Checkpoint: {len(results)} queries saved')

    # Final save
    save_checkpoint(results, existing)
    print(f'\\nGenerated {successes}/{len(todo)} queries successfully')
    print(f'Saved to {SYNTHETIC_QUERIES_PATH}')

def save_checkpoint(new_results, existing_keys):
    """Save results incrementally, combining with existing data."""
    new_df = pd.DataFrame(new_results)

    if SYNTHETIC_QUERIES_PATH.exists() and existing_keys:
        existing_df = pd.read_csv(SYNTHETIC_QUERIES_PATH)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    # Dedup
    key_cols = ['persona', 'scenario', 'modifier']
    combined = combined.drop_duplicates(subset=key_cols, keep='last')

    combined.to_csv(SYNTHETIC_QUERIES_PATH, index=False)

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic queries dataset')
    parser.add_argument('--max-rows', type=int, default=None, help='Max rows to generate (for testing)')
    parser.add_argument('--concurrency', type=int, default=8, help='Concurrent API calls')
    parser.add_argument('--model', type=str, default=None, help='Override generation model')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompts')

    args = parser.parse_args()

    if args.model:
        global GENERATION_MODEL
        GENERATION_MODEL = args.model

    asyncio.run(generate_dataset(max_rows=args.max_rows, concurrency=args.concurrency, confirm=not args.yes))

if __name__ == '__main__':
    main()
