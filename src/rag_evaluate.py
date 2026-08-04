#!/usr/bin/env python3
"""RAG evaluation for synthetic dataset. Faster than notebook execution."""

import asyncio
import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
import numpy as np
from openai import OpenAI, AsyncOpenAI
from tqdm.asyncio import tqdm

# Load env
load_dotenv()

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import *

# Clients
client = OpenAI(api_key=OPENAI_API_KEY)
async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Load system prompt
with open(RAG_SYSTEM_PROMPT_PATH, 'r') as f:
    SYSTEM_PROMPT = f.read().strip()

# Load articles
with open(ARTICLES_PATH) as f:
    articles = [json.loads(line) for line in f if line.strip()]

# Build embedding index
print(f"Loading {len(articles)} articles and building index...")
titles = [a['title'] for a in articles]
contents = [f"{a['title']}\n\n{a.get('content_text', '')}" for a in articles]

# Check for cached embeddings
embed_cache_path = Path("data/article_embeddings.npy")
if embed_cache_path.exists():
    print(f"Loading cached embeddings from {embed_cache_path}")
    article_embeddings = np.load(embed_cache_path)
else:
    print("Generating article embeddings...")
    article_embeddings = np.array([
        client.embeddings.create(
            model=EMBED_MODEL,
            input=content[:2000]  # Truncate for speed
        ).data[0].embedding
        for content in tqdm(contents, desc="Articles")
    ])
    np.save(embed_cache_path, article_embeddings)
    print(f"Saved embeddings to {embed_cache_path}")

def search(query: str, k: int = TOP_K):
    """Search articles by query embedding."""
    query_emb = client.embeddings.create(
        model=EMBED_MODEL,
        input=query[:500]
    ).data[0].embedding

    scores = np.dot(article_embeddings, query_emb)
    top_idx = np.argsort(-scores)[:k]

    return [articles[i] for i in top_idx]

async def answer_with_context(query: str):
    """Answer query with RAG context."""
    hits = search(query)
    context = "\n\n".join([f"Article: {a['title']}\n{a.get('content_text', '')[:300]}" for a in hits])

    prompt = f"""Context:
{context}

Query: {query}

Answer:"""

    resp = await async_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=500
    )

    answer = resp.choices[0].message.content
    return answer, [h['title'] for h in hits], len(hits)

async def evaluate_row(row):
    """Evaluate a single query."""
    answer, retrieved, hits = await answer_with_context(row['query'])
    return {
        'persona': row['persona'],
        'scenario': row['scenario'],
        'modifier': row['modifier'],
        'query': row['query'],
        'answer': answer,
        'retrieved_articles': ','.join(retrieved),
        'hits': hits
    }

async def run_evaluation(df, max_rows=None):
    """Run evaluation with checkpointing."""
    if max_rows:
        df = df.head(max_rows)

    # Check for existing results
    existing = set()
    if RAG_OUTPUT_PATH.exists():
        existing_df = pd.read_csv(RAG_OUTPUT_PATH)
        existing = set(zip(existing_df['persona'], existing_df['scenario'], existing_df['modifier']))
        print(f"RAG resume: {len(existing)} done, {len(df) - len(existing)} missing")

    # Filter out existing
    todo = [row for _, row in df.iterrows()
            if (row['persona'], row['scenario'], row['modifier']) not in existing]

    if not todo:
        print("All queries already evaluated!")
        return pd.read_csv(RAG_OUTPUTS_PATH)

    print(f"Evaluating {len(todo)} queries...")

    results = []
    checkpoint_interval = 50

    for row in tqdm(todo, desc="RAG eval"):
        result = await evaluate_row(row)
        results.append(result)

        # Checkpoint
        if len(results) % checkpoint_interval == 0:
            save_checkpoint(results, existing)
            print(f"Checkpoint: {len(results)} saved")

    # Final save
    save_checkpoint(results, existing)
    print(f"Saved {len(results)} results to {RAG_OUTPUT_PATH}")

    # Return combined results
    expected = 1500 if max_rows is None else max_rows
    return load_results(expected_rows=expected)

def save_checkpoint(new_results, existing_keys):
    """Save incremental results."""
    new_df = pd.DataFrame(new_results)

    if RAG_OUTPUT_PATH.exists() and existing_keys:
        existing_df = pd.read_csv(RAG_OUTPUT_PATH)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(RAG_OUTPUT_PATH, index=False)

def load_results(expected_rows=1500):
    """Load and validate results."""
    df = pd.read_csv(RAG_OUTPUT_PATH)

    # Validate
    assert len(df) <= expected_rows, f"Expected {expected_rows} results, got {len(df)}"
    assert list(df.columns) == ['persona', 'scenario', 'modifier', 'query', 'answer', 'retrieved_articles', 'hits']

    # Check no empty answers
    empty = df[df['answer'].isna() | (df['answer'] == '')]
    assert len(empty) == 0, f"Empty answers: {len(empty)}"

    # Check retrieved articles
    df['retrieved_count'] = df['retrieved_articles'].apply(lambda x: len(x.split(',')) if pd.notna(x) else 0)
    assert (df['retrieved_count'] >= 1).all(), "Some queries have no retrieved articles"

    print(f"✅ Results validated: {len(df)} rows, 7 columns, {df['retrieved_count'].median():.1f} median retrieves")
    return df

async def main():
    parser = argparse.ArgumentParser(description='RAG evaluation')
    parser.add_argument('--max-rows', type=int, default=None, help='Max rows for smoke test')
    args = parser.parse_args()

    # Load queries
    df = pd.read_csv(SYNTHETIC_QUERIES_PATH)
    print(f"Loaded {len(df)} queries from {SYNTHETIC_QUERIES_PATH}")

    # Run evaluation
    results = await run_evaluation(df, max_rows=args.max_rows)

    # Print summary
    print(f"\n=== Evaluation complete ===")
    print(f"Total results: {len(results)}")
    print(f"Columns: {list(results.columns)}")
    print(f"Sample answers:")
    for i, row in results.head(3).iterrows():
        print(f"\n[{i+1}] {row['query'][:60]}...")
        print(f"  Answer: {row['answer'][:80]}...")
        print(f"  Retrieved ({row['hits']}): {row['retrieved_articles'][:60]}...")

if __name__ == '__main__':
    asyncio.run(main())
