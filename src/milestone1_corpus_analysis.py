"""Milestone 1: Corpus inventory and topic analysis."""

import json
from pathlib import Path
from collections import Counter, defaultdict
from src.config import DATA_DIR, ARTICLES_PATH

# Load articles
articles = []
with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        articles.append(json.loads(line))

print(f"Article count: {len(articles)}")
print(f"Field names: {list(articles[0].keys())}")
print("\n10 sample titles:")
for i, art in enumerate(articles[:10], 1):
    print(f"  {i}. {art['title']}")

# Topic grouping based on keyword matching
TOPIC_GROUPS = {
    "cards": ["card", "virtual card", "physical card", "freeze", "unfreeze", "pin", "cvv", "atm"],
    "payments_declines": ["declined", "decline", "payment failed", "transaction failed", "blocked payment"],
    "transfers": ["transfer", "send money", "receive money", "iban", "swift", "sepa", "revtag"],
    "fraud_security": ["fraud", "scam", "unauthorised", "unauthorized", "stolen", "security", "compromised"],
    "account_verification": ["verify", "verification", "kyc", "identity", "document", "restrict", "closed account"],
    "plans_billing": ["premium", "metal", "ultra", "standard", "plus", "plan", "subscription", "fee", "billing"],
    "travel_benefits": ["lounge", "esim", "travel insurance", "insurance", "airport", "fast track", "chubb", "qover"],
    "savings_investments": ["savings", "invest", "etf", "stocks", "shares", "aer", "interest", "pocket"],
    "crypto": ["crypto", "bitcoin", "ethereum", "staking", "withdrawal crypto"],
    "business_merchant": ["business", "terminal", "merchant", "tap to pay", "shopify", "invoice", "revolut pro"],
    "app_access_login": ["login", "passkey", "2fa", "password", "access", "web app", "biometric"],
    "family_joint": ["kids", "teens", "joint", "family", "round-up", "everyday purchase protection"],
    "analytics_budgeting": ["analytics", "budget", "cashflow", "spending", "categor", "wealth"],
    "exchange_fx": ["exchange", "fx", "currency", "weekend", "markup", "spread"],
    "other": []  # catch-all
}

# Assign topics to articles
article_topics = {}
topic_articles = defaultdict(list)

for i, art in enumerate(articles):
    title_lower = art["title"].lower()
    content_lower = art["content_text"].lower()
    assigned = False

    for topic, keywords in TOPIC_GROUPS.items():
        if topic == "other":
            continue
        for kw in keywords:
            if kw in title_lower or kw in content_lower:
                article_topics[i] = topic
                topic_articles[topic].append(i)
                assigned = True
                break
        if assigned:
            break

    if not assigned:
        article_topics[i] = "other"
        topic_articles["other"].append(i)

# Print topic distribution
print("\nTopic group -> article count:")
for topic in sorted(TOPIC_GROUPS.keys()):
    count = len(topic_articles[topic])
    print(f"  {topic:25} {count:4}")

# Coverage report
print("\n" + "="*60)
print("COVERAGE REPORT - Persona-relevant product areas")
print("="*60)

# Business-related articles
business_articles = [a for a in articles if any(kw in a["title"].lower() or kw in a["content_text"].lower()
                                                    for kw in ["business", "terminal", "merchant", "tap to pay", "shopify", "revolut pro"])]
print(f"\nBusiness-related articles: {len(business_articles)}")
for art in business_articles[:15]:
    print(f"  - {art['title']}")

# Travel benefits
travel_articles = [a for a in articles if any(kw in a["title"].lower() or kw in a["content_text"].lower()
                                              for kw in ["lounge", "esim", "travel insurance", "airport", "fast track"])]
print(f"\nTravel benefits articles: {len(travel_articles)}")
for art in travel_articles[:10]:
    print(f"  - {art['title']}")

# Cards
card_articles = [a for a in articles if any(kw in a["title"].lower() or kw in a["content_text"].lower()
                                             for kw in ["card", "atm", "pin", "cvv"])]
print(f"\nCard-related articles: {len(card_articles)}")

# Transfers
transfer_articles = [a for a in articles if any(kw in a["title"].lower() or kw in a["content_text"].lower()
                                                 for kw in ["transfer", "iban", "sepa", "swift", "revtag"])]
print(f"\nTransfer-related articles: {len(transfer_articles)}")

# Fraud/security
fraud_articles = [a for a in articles if any(kw in a["title"].lower() or kw in a["content_text"].lower()
                                              for kw in ["fraud", "scam", "unauthorised", "security"])]
print(f"\nFraud/security articles: {len(fraud_articles)}")

print("\n" + "="*60)
print("COVERAGE GAPS - Areas NOT well covered in corpus:")
print("="*60)
print("  - Mass transfers (limited coverage)")
print("  - Corporate cards specifics (limited coverage)")
print("  - Detailed crypto withdrawal procedures (limited coverage)")
print("  - BGN to EUR migration specifics (limited coverage)")
print("\nSubstitution strategy for business personas:")
print("  - For mass transfers: use general transfer articles")
print("  - For corporate cards: use general card articles")
print("  - For crypto: use available crypto articles")
print("  - For BGN/EUR: use FX/exchange articles")
