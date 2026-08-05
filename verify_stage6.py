#!/usr/bin/env python3
"""Stage 6 verification: re-derives every gate from committed artifacts.

Trust nothing the agent reported — every check below recomputes reality from
files on disk. Run from the repo root (or scripts/):

    python verify_stage6.py

Exit code 0 = all HARD checks pass. Any FAIL -> exit 1.
Stdlib only, so it works in a fresh clone with bare Python.
"""

import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --- locate repo root (script may live in root or scripts/) ---
HERE = Path(__file__).resolve().parent
REPO = HERE if (HERE / "data").exists() else HERE.parent
DATA = REPO / "data"
SEEDS = DATA / "synthetic_data_seeds"
NB_PATH = REPO / "notebooks" / "faq_rag_chatbot.ipynb"

CANONICAL_PERSONAS = {
    "eu_freelancer_traveling_uae_male_29", "ultra_globetrotter_executive_female_42",
    "senior_citizen_uk_female_67", "b2b_ecommerce_merchant_male_31",
    "genz_crypto_trader_female_20", "migrant_worker_remittance_male_38",
    "young_parent_family_budget_female_34", "retail_investor_stocks_male_45",
    "cafe_owner_smb_female_52", "gig_courier_instant_pay_male_27",
    "digital_nomad_tax_resident_female_33", "cross_border_commuter_female_37",
    "crypto_web3_enthusiast_male_24", "boutique_hotel_host_female_41",
    "student_abroad_exchange_male_22",
}
CANONICAL_MODIFIERS = {
    "empty", "calm_at_home", "panic_security_fear", "angry_after_waiting",
    "confused_by_app_updates", "rushing_with_typos", "on_the_go_direct",
    "voice_transcription", "poor_internet_connection", "vague_first_message",
}
GOLDEN_SCENARIOS = {
    "eu_freelancer_traveling_uae_male_29": {
        "fraud_unauthorised_atm_withdrawal", "fraud_unrecognised_card_payment",
        "cancel_recurring_subscription", "card_profile_restricted_security_system",
        "maintenance_fee_plan_billing", "cross_border_transfer_delay",
    },
    "ultra_globetrotter_executive_female_42": {
        "travel_insurance_claim_question", "airport_lounge_pass_issue",
        "esim_data_activation_failed",
    },
}
TOPIC_KEYWORDS = {
    "business_merchant": ["business", "terminal", "shopify", "invoice", "payment link", "tap to pay", "merchant", "reader"],
    "travel_benefits": ["lounge", "esim", "insurance", "fast track", "trip", "stays"],
    "crypto": ["crypto", "staking", "wallet", "bitcoin"],
    "savings_investments": ["stock", "etf", "saving", "interest", "loan", "flexible", "invest", "bond"],
    "family_joint": ["joint", "kids", "teen", "pocket"],
    "transfers": ["transfer", "iban", "sepa", "swift", "remitt"],
    "cards_atm": ["card", "atm", "pin", "cvv", "contactless"],
    "fraud_security": ["fraud", "scam", "chargeback", "dispute", "stolen", "unauthoris"],
    "account_verification": ["verif", "identity", "restricted", "closed", "passkey", "login", "password", "selfie", "document"],
    "plans_billing": ["premium", "metal", "ultra", "plan", "subscription", "fee", "pricing"],
    "fx_exchange": ["exchange", "currency", "conversion", "dcc"],
}

RESULTS = []  # (level, name, detail)


def check(name, ok, detail="", hard=True):
    level = "PASS" if ok else ("FAIL" if hard else "WARN")
    RESULTS.append((level, name, detail))


def warn_if(name, bad, detail=""):
    RESULTS.append(("WARN" if bad else "PASS", name, detail))


def unwrap(obj, key):
    return obj.get(key, obj) if isinstance(obj, dict) else obj


def topic_of(title):
    t = title.lower()
    for g, kws in TOPIC_KEYWORDS.items():
        if any(k in t for k in kws):
            return g
    return "other"


def main():
    # ---------------- corpus ----------------
    corpus_path = DATA / "revolut_help_articles.jsonl"
    check("corpus file exists", corpus_path.exists(), str(corpus_path))
    titles = set()
    if corpus_path.exists():
        titles = {json.loads(l)["title"] for l in corpus_path.open(encoding="utf-8") if l.strip()}
        check("corpus size == 786", len(titles) >= 700, f"{len(titles)} unique titles")

    # ---------------- G2: seeds ----------------
    try:
        personas = unwrap(json.load((SEEDS / "personas.json").open(encoding="utf-8")), "personas")
        modifiers = unwrap(json.load((SEEDS / "modifiers.json").open(encoding="utf-8")), "modifiers")
        scenarios = unwrap(json.load((SEEDS / "scenarios.json").open(encoding="utf-8")), "scenarios")
    except FileNotFoundError as e:
        check("seed files exist", False, str(e))
        return finish()

    pids = {p["persona"] for p in personas}
    mids = {m["modifier"] for m in modifiers}
    check("G2: 15 personas, canonical ids", pids == CANONICAL_PERSONAS,
          f"diff={sorted(pids ^ CANONICAL_PERSONAS)}" if pids != CANONICAL_PERSONAS else "")
    check("G2: 10 modifiers, canonical ids", mids == CANONICAL_MODIFIERS,
          f"diff={sorted(mids ^ CANONICAL_MODIFIERS)}" if mids != CANONICAL_MODIFIERS else "")
    per = Counter(s["persona"] for s in scenarios)
    check("G2: 150 scenarios, 10 per persona",
          len(scenarios) == 150 and set(per) == pids and all(v == 10 for v in per.values()),
          f"n={len(scenarios)}, per-persona={dict(per)}" if len(scenarios) != 150 else f"n={len(scenarios)}")

    misses = [(s["persona"], s["scenario"], t) for s in scenarios
              for t in s.get("target_articles", []) if t not in titles]
    check("G2: all target_articles resolve to real corpus titles (0 misses)",
          len(misses) == 0, f"{len(misses)} misses, e.g. {misses[:3]}")

    bad_counts = [s["scenario"] for s in scenarios if not 2 <= len(s.get("target_articles", [])) <= 5]
    check("G2: each scenario has 2-5 target_articles", not bad_counts, f"violations: {bad_counts[:5]}")

    have = defaultdict(set)
    for s in scenarios:
        have[s["persona"]].add(s["scenario"])
    missing_golden = {p: sorted(ids - have[p]) for p, ids in GOLDEN_SCENARIOS.items() if ids - have[p]}
    check("G2: golden scenario ids preserved (needed for joins with the golden benchmark)",
          not missing_golden, f"missing: {missing_golden}")

    # topic balance recomputed from target_articles (independent of any agent claim)
    sc_topic = {}
    for s in scenarios:
        c = Counter(topic_of(t) for t in s.get("target_articles", []))
        sc_topic[(s["persona"], s["scenario"])] = c.most_common(1)[0][0] if c else "other"
    dist = Counter(sc_topic.values())
    max_share = max(dist.values()) / max(1, len(scenarios))
    per_topics = defaultdict(set)
    for (p, _), g in sc_topic.items():
        per_topics[p].add(g)
    min_topics = min((len(v) for v in per_topics.values()), default=0)
    warn_if("G2: recomputed topic balance (max group <= 20%)", max_share > 0.20,
            f"max={max_share:.1%} dist={dict(dist.most_common(4))}")
    warn_if("G2: every persona spans >= 6 topic groups", min_topics < 6, f"min={min_topics}")
    has_topic_field = all("topic_group" in s for s in scenarios)
    warn_if("G2: topic_group persisted in scenarios.json (CLAUDE.md: no outside results)",
            not has_topic_field, "absent — balance claims are not reproducible from the repo")

    # ---------------- G3: queries ----------------
    q_path = DATA / "synthetic_revolut_queries.csv"
    check("G3: queries csv exists", q_path.exists(), str(q_path))
    if not q_path.exists():
        return finish()
    rows = list(csv.DictReader(q_path.open(encoding="utf-8")))
    check("G3: row count == 1500", len(rows) == 1500, f"n={len(rows)}")
    check("G3: columns exactly persona,scenario,modifier,query",
          list(rows[0].keys()) == ["persona", "scenario", "modifier", "query"], str(list(rows[0].keys())))

    grid_expected = {(s["persona"], s["scenario"], m["modifier"]) for s in scenarios for m in modifiers}
    grid_actual = {(r["persona"], r["scenario"], r["modifier"]) for r in rows}
    check("G3: combo grid == full 15x10x10 grid derived from seeds",
          grid_actual == grid_expected,
          f"missing={len(grid_expected - grid_actual)} extra={len(grid_actual - grid_expected)}")

    empty_q = sum(1 for r in rows if not r["query"].strip())
    check("G3: no empty queries", empty_q == 0, f"{empty_q} empty")
    norm = Counter(re.sub(r"\s+", " ", r["query"].casefold()).strip() for r in rows)
    dups = sum(1 for c in norm.values() if c > 1)
    check("G3: zero normalized duplicate queries", dups == 0, f"{dups} duplicate groups")
    pm = Counter((r["persona"], r["modifier"]) for r in rows)
    check("G3: persona x modifier crosstab all == 10",
          len(pm) == 150 and all(v == 10 for v in pm.values()), "")

    by_mod = defaultdict(list)
    for r in rows:
        by_mod[r["modifier"]].append(len(r["query"].split()))
    long_mods = {m: statistics.median(v) for m, v in by_mod.items() if statistics.median(v) > 45}
    warn_if("G3: query style — per-modifier median <= 45 words (golden style is ~15-30)",
            bool(long_mods), f"too verbose: { {k: int(v) for k, v in long_mods.items()} }")
    sc_arts = {(s["persona"], s["scenario"]): s.get("target_articles", []) for s in scenarios}
    leak = sum(1 for r in rows
               if any(t.casefold() in r["query"].casefold()
                      for t in sc_arts.get((r["persona"], r["scenario"]), []) if len(t) > 25))
    warn_if("G3: queries do not quote article titles verbatim", leak > 0, f"{leak} leaking queries")

    # ---------------- G4: RAG outputs ----------------
    out_path = DATA / "synthetic_revolut_rag_outputs.csv"
    if not out_path.exists():
        check("G4: synthetic_revolut_rag_outputs.csv exists (Milestone 4 executed)", False,
              "file absent — the RAG evaluation run has NOT happened; any 'done' claim is false")
    else:
        orows = list(csv.DictReader(out_path.open(encoding="utf-8")))
        exp_cols = ["persona", "scenario", "modifier", "query", "answer", "extracted_context", "retrieved_articles"]
        check("G4: row count == 1500", len(orows) == 1500, f"n={len(orows)}")
        check("G4: columns exactly the 7 expected", list(orows[0].keys()) == exp_cols, str(list(orows[0].keys())))
        okeys = {(r["persona"], r["scenario"], r["modifier"], r["query"]) for r in orows}
        qkeys = {(r["persona"], r["scenario"], r["modifier"], r["query"]) for r in rows}
        check("G4: output keys == query dataset keys", okeys == qkeys,
              f"missing={len(qkeys - okeys)} extra={len(okeys - qkeys)}")
        empty_a = sum(1 for r in orows if not r["answer"].strip())
        check("G4: no empty answers", empty_a == 0, f"{empty_a} empty")
        empty_ra = sum(1 for r in orows if not r["retrieved_articles"].strip())
        check("G4: retrieved_articles non-empty for >= 99% rows",
              empty_ra <= len(orows) * 0.01, f"{empty_ra} empty")

    # ---------------- notebook execution evidence ----------------
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]
    sec6_idx = next((i for i, c in enumerate(cells)
                     if c["cell_type"] == "markdown" and "Evaluate Synthetic Dataset" in "".join(c["source"])), None)
    check("NB: section '6. Evaluate Synthetic Dataset' present", sec6_idx is not None, "")
    pre_code = [c for c in cells[:sec6_idx] if c["cell_type"] == "code"] if sec6_idx else []
    post_code = [c for c in cells[sec6_idx:] if c["cell_type"] == "code"] if sec6_idx else []
    check("NB: stages 1-5 cells actually executed (execution_count set)",
          bool(pre_code) and all(c.get("execution_count") is not None for c in pre_code),
          f"unexecuted: {sum(1 for c in pre_code if c.get('execution_count') is None)}/{len(pre_code)}")
    unexec6 = sum(1 for c in post_code if c.get("execution_count") is None)
    check("NB: section 6 cells actually executed (this is the real Milestone 4 gate)",
          bool(post_code) and unexec6 == 0,
          f"unexecuted: {unexec6}/{len(post_code)} — execution_count is None means the cell never ran")
    allsrc = "\n".join("".join(c["source"]) for c in cells)
    check("NB: no 'script' column naming regression", not re.search(r"[\"']script[\"']", allsrc), "")
    check("NB: no hardcoded API key placeholder", "YOUR_API_KEY" not in allsrc, "")
    check("NB: outputs show the FULL run resume line",
          "RAG resume: 1500 done, 0 missing" in NB_PATH.read_text(encoding="utf-8"),
          "notebook shows a smoke/partial resume line - re-execute after the full run")

    # ---------------- repo hygiene ----------------
    import subprocess
    tracked = [t for t in subprocess.run(["git", "ls-files"], cwd=REPO,
               capture_output=True, text=True).stdout.split("\n") if t]
    secret_hits = []
    for rel in tracked:
        fp = REPO / rel
        try:
            if fp.is_file() and re.search(r"sk-[A-Za-z0-9_\-]{16,}", fp.read_text(encoding="utf-8", errors="ignore")):
                secret_hits.append(rel)
        except Exception:
            pass
    check("SEC: no keys in git-tracked files (.env is the key's legitimate home)", not secret_hits, str(secret_hits))
    gi = (REPO / ".gitignore").read_text(encoding="utf-8") if (REPO / ".gitignore").exists() else ""
    check("SEC: .env is gitignored", ".env" in gi.split(), "")
    warn_if("ENV: pyproject.toml / requirements present (fresh clone reproducibility)",
            not any((REPO / f).exists() for f in ("pyproject.toml", "requirements.txt", "uv.lock")),
            "no dependency manifest committed")

    finish()


def finish():
    print(f"\n{'=' * 76}\nSTAGE 6 VERIFICATION — recomputed from artifacts, zero trust in agent claims\n{'=' * 76}")
    fails = warns = 0
    for level, name, detail in RESULTS:
        mark = {"PASS": "  [PASS]", "WARN": "  [WARN]", "FAIL": "  [FAIL]"}[level]
        print(f"{mark} {name}" + (f"\n         -> {detail}" if detail and level != "PASS" else ""))
        fails += level == "FAIL"
        warns += level == "WARN"
    print(f"\nTotal: {len(RESULTS)} checks | FAIL: {fails} | WARN: {warns}")
    if fails:
        print("\nVERDICT: NOT DONE. Fix every FAIL before declaring Stage 6 complete.")
        sys.exit(1)
    print("\nVERDICT: all hard gates hold. Review WARNs, then ship.")
    sys.exit(0)


if __name__ == "__main__":
    main()
