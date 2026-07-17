import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
if data.get("stop_hook_active") or not os.path.exists(".claude/gate_on"):
    sys.exit(0)
r = subprocess.run(
    ["uv", "run", "python", "scripts/verify_all.py"],
    capture_output=True, text=True,
)
if r.returncode != 0:
    print(
        "Completion blocked: verification gate failed.\n" + r.stdout + r.stderr,
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
