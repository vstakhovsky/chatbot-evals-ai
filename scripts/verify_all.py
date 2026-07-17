"""Aggregate gate: pytest plus artifact verifiers. Exit non-zero on any failure."""
import subprocess
import sys
from pathlib import Path

fails = []

def run(name, cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        print((r.stdout + r.stderr)[-2000:])
        fails.append(name)

run("pytest", ["uv", "run", "pytest", "-q"])
nb = Path("notebooks/01_rag_evals.ipynb")
if nb.exists():
    run("notebook verifier", ["uv", "run", "python", "scripts/verify_notebook.py", str(nb)])
print("GATE:", "FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
