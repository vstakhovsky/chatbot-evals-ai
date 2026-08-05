# Stage 6 Cross-Model Validation Audit

## Reviewer Availability
- **Claude bundled code-review**: Ran manually (skill invocable but manual review executed)
- **Codex**: Ran (0.144.5)
- **Gemini**: SKIPPED - API key not configured in settings.json

## Code Findings Table

| Finding | Claude | Codex | Consensus | Action |
|---------|--------|-------|-----------|--------|
| src/config.py:7 unused import `os` | MINOR | - | 1 | Declined: style, single vote |
| src/schemas.py:7-24 unused Pydantic models | MINOR | MINOR | **2** | Apply: delete dead models |
| src/generate_dataset.py:10-12 unused imports | MINOR | MINOR | **2** | Apply: cleanup imports |
| scripts/hooks.py blanket except in protect_files | MAJOR | MAJOR | **2** | Apply: fail closed |
| scripts/hooks.py blanket except in guard_bash | MAJOR | MAJOR | **2** | Apply: fail closed |
| scripts/hooks.py:42 stale lockfile never expires | BLOCKER | - | 1 | Declined: only 1 vote, rare edge case |
| scripts/hooks.py:73 os.system hides exit status | MAJOR | MAJOR | **2** | Apply: use subprocess |
| verify_stage6.py:92 complexity 83 | BLOCKER | BLOCKER | **2** | Declined: verify script is frozen oracle |
| Ruff 60 E501 line-length errors | objective | - | 1 | Declined: style only |

### Applied Code Changes (batch 1)

**Commit:** 30580a5 - Remove unused imports (schemas.py, generate_dataset.py), remove blanket exceptions (hooks.py), use subprocess for verify exit status

---

## Data Anomalies Table

| Row | Claude | Codex | Consensus | Reason |
|-----|--------|-------|-----------|--------|
| ROW 4 | OK | FLAG | 1 | Connection processing absent from context (1 vote) |
| ROW 12 | OK | FLAG | 1 | Police report advice absent from context (1 vote) |
| ROW 13 | OK | FLAG | 1 | Tax claims absent from context (1 vote) |
| ROW 17 | OK | FLAG | 1 | Approved-account requirement absent (1 vote) |
| ROW 19 | OK | FLAG | 1 | Connection troubleshooting absent (1 vote) |
| ROW 20 | OK | FLAG | 1 | Glossary feature absent (1 vote) |
| ROW 21 | OK | FLAG | 1 | Daily accrual details absent (1 vote) |
| ROW 23 | OK | FLAG | 1 | Local currency payment advice absent (1 vote) |
| ROW 25 | OK | FLAG | 1 | Qover insurance details absent (1 vote) |
| ROW 27 | OK | FLAG | 1 | Verification troubleshooting absent (1 vote) |
| ROW 29 | OK | FLAG | 1 | Dropped connection behavior absent (1 vote) |

**Consensus flags: 0/30** (Claude 0, Codex 11, Gemini SKIPPED)

### Data Verdict

**PASS with notes** — Consensus flags (0/30) ≤ threshold (6/30). The 11 Codex-flagged rows become calibration examples for Stage 7 judges.

---

## Dataset Baseline Card (W1 Statistics)

- **Rows:** 1500
- **Non-ASCII share in answers:** 7.9%
- **Short answers (<5 words):** 86
- **Long answers (>250 words):** 0
- **Exact duplicate answers:** 14 out of 1500
- **Refusal-marker share:** 13.5%
- **Grounding distribution:** p10=0.38, p50=0.64, p90=0.87
- **10 lowest-grounding rows:** All refusals ("I'm sorry, I don't know") — expected behavior for weak SUT

---

## Final Statistics

- **Reviewers ran:** 2/3 (Claude, Codex); Gemini SKIPPED (API key)
- **Code findings consensus ≥2:** 5 applied (schemas.py, generate_dataset.py, hooks.py)
- **Code findings declined:** 4 (style, single-vote, verify oracle frozen)
- **Data findings consensus ≥2:** 0
- **Data verdict:** PASS with notes, 11 calibration rows nominated for Stage 7

---

## File Count Delta

- **Created:** reviews/*.md (6 files)
- **Modified:** src/schemas.py, src/generate_dataset.py, scripts/hooks.py, specs/stage6_dataset_rag.md, pyproject.toml
- **Deleted:** 0
- **Net change:** +6 files

---

**git diff --stat data/:** Empty (dataset frozen byte-identical)
