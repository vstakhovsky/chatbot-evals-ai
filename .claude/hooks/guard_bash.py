import json
import re
import sys

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")
PATTERNS = [
    r"\brm\b[^\n]*\.ipynb",
    r"\brm\s+-rf\b",
    r"git\s+push[^\n]*--force",
    r"git\s+reset\s+--hard",
    r"git\s+checkout[^\n]*--force",
]
for pat in PATTERNS:
    if re.search(pat, cmd):
        print(
            f"Blocked by policy ({pat}). Destructive-op protocol: name the exact "
            f"victim and survivor with evidence, prefer mv to _trash/, wait for approval.",
            file=sys.stderr,
        )
        sys.exit(2)
sys.exit(0)
