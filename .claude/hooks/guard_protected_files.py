import json
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "") or ""
PROTECTED = ("scripts/verify_", "tests/", ".claude/")
if any(seg in path for seg in PROTECTED):
    print(
        "Verifiers, tests and harness config are read-only for the builder "
        "(gate integrity). Propose the change and wait for explicit approval.",
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
