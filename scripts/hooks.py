#!/usr/bin/env python3
"""
Hook guards for spec-driven development.
Required by specs/rules.md: protect-files, guard-bash, session-context, verdict.
Reads JSON from stdin; exit 2 blocks, exit 0 allows — never exit 1.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def protect_files(data: dict) -> int:
    """Block edits to verify_stage6.py (read-only oracle) or CLAUDE.md (user-frozen)."""
    path = data.get("tool_input", {}).get("file_path", "")
    if path.endswith("verify_stage6.py"):
        print("BLOCKED: verify scripts are read-only oracles; if a check looks wrong, stop and report", file=sys.stderr)
        return 2
    if path.endswith("CLAUDE.md"):
        # This line is removable by user later — they own CLAUDE.md
        print("BLOCKED: user has frozen CLAUDE.md; propose changes in chat instead", file=sys.stderr)
        return 2
    return 0


def guard_bash(data: dict) -> int:
    """Block: concurrent rag_evaluate, git push --force, deleting executed notebooks."""
    cmd = data.get("tool_input", {}).get("command", "")

    # Single-writer lock for rag_evaluate and nbconvert on this notebook
    if "rag_evaluate" in cmd or ("nbconvert" in cmd and "faq_rag_chatbot.ipynb" in cmd):
        lockfile = Path("data/.rag_eval.lock")
        if lockfile.exists():
            try:
                pid = int(lockfile.read_text().strip())
                os.kill(pid, 0)  # Check if process is alive
                print("BLOCKED: RAG evaluation already running (live lockfile)", file=sys.stderr)
                return 2
            except (OSError, ValueError):
                pass  # Lock stale or invalid

    if "push --force" in cmd or ("push" in cmd and "-f" in cmd):
        print("BLOCKED: history is append-only", file=sys.stderr)
        return 2

    if "rm" in cmd and ".ipynb" in cmd:
        print("BLOCKED: executed notebooks are evidence", file=sys.stderr)
        return 2
    return 0


def session_context(data: dict) -> int:
    """Print rules.md and active spec at session start."""
    try:
        rules = Path("specs/rules.md")
        if rules.exists():
            print(rules.read_text())
        print("Active spec: specs/stage6_dataset_rag.md — read it before working")
    except Exception:
        pass
    return 0


def verdict(data: dict) -> int:
    """Run verify before session ends — real verdict on screen."""
    result = subprocess.run(["python3", "verify_stage6.py"], capture_output=True, text=True)
    # Show last 20 lines of output
    lines = result.stdout.split("\n") + result.stderr.split("\n")
    print("\n".join(lines[-20:]))
    return result.returncode


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    mode = sys.argv[1]

    handlers = {
        "protect-files": protect_files,
        "guard-bash": guard_bash,
        "session-context": session_context,
        "verdict": verdict,
    }

    if mode not in handlers:
        sys.exit(1)

    # session-context and verdict don't need stdin
    if mode in ("session-context", "verdict"):
        sys.exit(handlers[mode]({}))

    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        data = {}

    sys.exit(handlers[mode](data))


if __name__ == "__main__":
    main()
