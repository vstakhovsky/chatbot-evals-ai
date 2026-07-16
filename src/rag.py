"""Simple RAG pipeline with numpy-based retrieval."""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
import pandas as pd
from openai import AsyncOpenAI
from tqdm import tqdm

from src.config import EMBED_MODEL_OPENAI, BASE_URL, STUDENT_MODEL, TOP_K, CONCURRENCY
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


def get_embedding_client():
    """Get client for embeddings - use direct OpenAI."""
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def embed_texts(texts, model=EMBED_MODEL_OPENAI):
    """Embed a list of texts."""
    client = get_embedding_client()

    results = []
    for i in range(0, len(texts), CONCURRENCY):
        batch = texts[i:i + CONCURRENCY]
        responses = await asyncio.gather(*[
            client.embeddings.create(model=model, input=text)
            for text in batch
        ])
        results.extend([r.data[0].embedding for r in responses])

    return np.array(results)


async def build_corpus_embeddings():
    """Build and cache corpus embeddings."""
    cache_file = Path("data/outputs/corpus_emb.npz")
    articles_file = Path("data/revolut_help_articles.jsonl")

    if cache_file.exists():
        print(f"Loading cached embeddings from {cache_file}")
        data = np.load(cache_file, allow_pickle=True)
        return data["embeddings"], data["articles"]

    print("Building corpus embeddings...")
    articles = [json.loads(line) for line in articles_file.read_text().strip().split("\n")]

    # Embed title + content
    texts = [f"{a['title']}\n{a['content_text']}" for a in articles]
    embeddings = await embed_texts(texts)

    # Cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache_file, embeddings=embeddings, articles=articles)

    return embeddings, articles


def retrieve(query_embedding, corpus_embeddings, articles, top_k=TOP_K):
    """Retrieve top-k articles using dot product."""
    # L2-normalize for dot product similarity
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    corpus_norm = corpus_embeddings / np.linalg.norm(corpus_embeddings, axis=1, keepdims=True)

    # Dot product scores
    scores = corpus_norm @ query_norm

    # Top-k
    top_indices = np.argsort(scores)[-top_k:][::-1]

    return [
        {
            "index": int(idx),
            "title": articles[idx]["title"],
            "content": articles[idx]["content_text"],
            "score": float(scores[idx])
        }
        for idx in top_indices
    ]


async def answer_query(query, retrieved_articles, problem_id):
    """Generate answer using retrieved articles."""
    # Build context
    context = "\n\n".join([
        f"Article: {r['title']}\n{r['content']}"
        for r in retrieved_articles
    ])

    # Check if gold article was retrieved
    # This is a simple check - in real system you'd track article IDs
    gold_retrieved = False  # ponytail: would need source_article_ids from problem seed

    prompt = f"""You are a Revolut customer support agent. Answer the customer's question using ONLY the provided articles.

If the answer is not in the articles, say "I don't have enough information to help with that."

Be concise and practical. Reference specific steps when relevant.

Customer question:
{query}

Relevant articles:
{context}

Answer:"""

    client = get_client()
    response = await client.chat.completions.create(
        model=STUDENT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "retrieved_ids": json.dumps([r["index"] for r in retrieved_articles]),
        "retrieved_titles": json.dumps([r["title"] for r in retrieved_articles]),
        "retrieved_scores": json.dumps([r["score"] for r in retrieved_articles]),
        "gold_article_retrieved": gold_retrieved
    }


async def run_rag(df):
    """Run RAG pipeline on all queries."""
    print("Building corpus embeddings...")
    corpus_embeddings, articles = await build_corpus_embeddings()

    print("Embedding queries...")
    query_embeddings = await embed_texts(df["query"].tolist())

    print("Retrieving and answering...")
    results = []
    for i, (idx, row) in enumerate(tqdm(df.iterrows(), total=len(df))):
        retrieved = retrieve(query_embeddings[i], corpus_embeddings, articles)

        # Find problem ID from row
        problem_id = row.get("problem_id", "")
        result = await answer_query(row["query"], retrieved, problem_id)

        combined = {**row.to_dict(), **result}
        results.append(combined)

    return pd.DataFrame(results)


async def main():
    """Run RAG pipeline on validated queries."""
    input_file = Path("data/outputs/validated_queries.csv")

    if not input_file.exists():
        print(f"Error: {input_file} not found. Run vibe_check.py first.")
        return

    df = pd.read_csv(input_file)

    # Filter to only passed queries
    df = df[df["passed"] == True]

    print(f"Running RAG on {len(df)} validated queries...")
    results_df = await run_rag(df)

    output_file = Path("data/outputs/rag_outputs.csv")
    results_df.to_csv(output_file, index=False)

    print(f"\nOutput: {output_file}")
    print(f"\nSample RAG outputs:")
    print(results_df.head(3))

    return results_df


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
