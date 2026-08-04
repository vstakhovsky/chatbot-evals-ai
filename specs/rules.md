Extends CLAUDE.md. Never overrides it; never duplicates it. Checkpoint pattern, cost gate,
"keep everything explicit", and file locations remain defined in CLAUDE.md only.

## Spec-driven flow
- `specs/` holds one spec per stage (stage6_dataset_rag.md, stage7_judges.md, stage8_gepa.md,
  stage9_arize.md, ...) plus this file. The active stage spec is the single source of truth for
  scope, acceptance criteria, and status.
- Session start: read this file and the active stage spec; run the stage's acceptance command
  before starting and before finishing.
- Acceptance for a stage = its verify script exits 0. Verify scripts are read-only oracles:
  never modify one; if a check looks wrong, stop and report to the user.
- Deviating from a spec requires editing that spec first (log under "Accepted deviations",
  own commit), then writing code.
- A closed stage's spec and verify script are frozen forever.
- Status semantics: ✅ only for a gate executed in this session with raw output shown.
  Anything waiting on an external event is ⛔ BLOCKED/WAITING. "Code written" is never "done".

## Engineering rules
- Simplicity first: stdlib before custom, half the code if possible, no speculative
  abstractions. Prefer deleting to adding.
- Every new file states — in its docstring or commit message — which spec criterion or rule
  requires it. Can't state it: don't create it. Each stage spec carries a file-inventory
  whitelist; off-list files are deleted or defended in writing.
- One-shot scripts are deleted in the same commit that applies their result.
- Resumable jobs extend the CLAUDE.md checkpoint pattern with a single-writer lockfile
  (O_CREAT|O_EXCL holding the pid) and atomic writes (tmp + os.replace).
- Any job longer than ~10 minutes runs detached (`nohup ... >> log &`), never tied to an
  agent session. The agent does one health check, then stops with WAITING. No sleep-polling.
- Never simulate the output of an external tool or model; a missing tool is reported SKIPPED.
- No `git push --force`; history is append-only. Never delete executed notebooks or other
  run evidence.

## Proactive tooling
At the start of each task, check whether a built-in skill (/code-review, /simplify,
/security-review), an installed plugin, or a subagent does the job better than ad-hoc work;
if yes, propose it to the user in one line (tool + why) before proceeding. Use a read-only
Explore subagent for search-heavy work to keep the main context clean. Suggest installing a
plugin only when it maps directly to the current task.
