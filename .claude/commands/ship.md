---
description: Close out the current milestone end to end - gate, simplify, review, cross-review, commit, blob verify, push, probes
---
Close out the current milestone: $ARGUMENTS

1. `uv run python scripts/verify_all.py` paste full output. On FAIL: stop and report, do not continue.
2. Invoke the code-simplifier subagent on this milestone's changed files; paste its diffstat; re-run the gate.
3. Invoke the milestone-reviewer subagent with the acceptance criteria; paste its verdict table.
4. Execute the procedure from .claude/commands/cross-review.md; include both verdicts verbatim.
5. All green: git add the changed files, conventional commit, then verify the committed blob (`git show HEAD:<key artifact>` to /tmp, re-run its verifier), paste output.
6. `git push origin <current branch>`; paste push output and `curl -s -o /dev/null -w "%{http_code}"` on the key artifact's raw URL.
7. STOP for human review. Never start the next milestone.
