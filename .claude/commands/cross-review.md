---
description: Independent cross-model review of the current milestone by Codex and Gemini
---
Run an independent cross-model review. $ARGUMENTS describes the milestone (optional).

1. Build the review bundle:
   - git diff main...HEAD > /tmp/review.diff (if the diff is empty, use git show HEAD > /tmp/review.diff)
   - git diff --name-only main...HEAD > /tmp/review_files.txt
2. Compose the reviewer instruction (same text for both models):
   "You are an independent adversarial code reviewer. You receive a unified diff at /tmp/review.diff and the file list at /tmp/review_files.txt inline below. Milestone: $ARGUMENTS. For each acceptance-relevant aspect output PASS or FAIL with concrete evidence (file, line, reason). Hunt specifically for: fabricated artifacts (hand-written .ipynb outputs: non-sequential execution_count, tiny base64 PNGs, placeholder stdout), tests weakened to pass, claims not backed by code, missing error handling on the changed paths. Do not praise. Do not fix. End with one line: CROSS-VERDICT: PASS or CROSS-VERDICT: FAIL."
3. Check availability: command -v codex; command -v gemini. Run `codex exec --help` / `gemini --help` once if unsure of the exact non-interactive flag and adapt.
4. Codex: cat /tmp/review.diff | codex exec "<instruction>"
5. Gemini: cat /tmp/review.diff | gemini -p "<instruction>"
6. Print both outputs VERBATIM under headers "=== CODEX VERDICT ===" and "=== GEMINI VERDICT ===". Never summarize, soften, or merge them into your own words.
7. If either verdict is FAIL, or a CLI is missing, state plainly: the milestone is NOT accepted; list the blockers.
