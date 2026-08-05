# Claude Code Review

Reviewing src/, scripts/, specs/, .claude/ for bugs and slop.

## Findings

src/config.py:7, MINOR, unused import `os` — not referenced after load_dotenv()
src/schemas.py:7-24, MINOR, unused Pydantic models (Persona, Modifier, Scenario, GenerationRequest) — delete dead code
src/generate_dataset.py:10-12, MINOR, unused imports (Path, product, defaultdict) — cleanup
scripts/hooks.py:16-27, MAJOR, blanket `except Exception` in protect_files — silently disables enforcement on error; fail closed
scripts/hooks.py:32-56, MAJOR, blanket `except Exception` in guard_bash — silently disables guards on error; fail closed
scripts/hooks.py:59-68, MAJOR, hardcoded "stage6_dataset_rag.md" in session_context — breaks when stage changes
scripts/hooks.py:73, MAJOR, `os.system` with tail pipe hides verify exit status — use subprocess, propagate exit code
scripts/hooks.py:42, BLOCKER, `os.kill(pid, 0)` check only works if lockfile has valid PID — stale lockfiles never expire
verify_stage6.py:92, BLOCKER, main() has cyclomatic complexity 83 — impossible to audit, should be refactored
verify_stage6.py:235, MAJOR, file suffix list duplicates logic — consolidate with whitelist constant

## Objective facts from linters

**Ruff (60 errors):** Mostly E501 line-length >100 in verify_stage6.py and hooks.py; unused args in session_context/verdict; import sorting issues
**Vulture (2 findings):** unused import `product` in generate_dataset.py; unused `cls` in schemas.py
**Radon:** verify_stage6.py main() is F (83 complexity), above the 50 threshold

