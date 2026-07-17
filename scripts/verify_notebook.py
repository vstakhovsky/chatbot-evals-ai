import base64, json, sys
p = sys.argv[1] if len(sys.argv) > 1 else "notebooks/01_rag_evals.ipynb"
raw = open(p, "rb").read()
nb = json.loads(raw)
fails = []
def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok: fails.append(name)

md_bad = [i for i,c in enumerate(nb["cells"]) if c["cell_type"]!="code" and ("outputs" in c or "execution_count" in c)]
check("markdown cells carry no outputs/execution_count", not md_bad, f"bad: {md_bad}")
code = [c for c in nb["cells"] if c["cell_type"]=="code"]
try:
    import nbformat
    nbformat.validate(nbformat.reads(raw.decode("utf-8"), as_version=4))
    check("nbformat schema valid", True)
except ImportError:
    print("[WARN] nbformat not installed; schema check partial")
except Exception as e:
    check("nbformat schema valid", False, str(e))
no_out = [i for i,c in enumerate(code) if not c.get("outputs")]
errs = [i for i,c in enumerate(code) if any(o.get("output_type")=="error" for o in c.get("outputs",[]))]
check("all code cells have outputs", bool(code) and not no_out, f"missing: {no_out}")
check("zero error outputs", not errs, f"errors: {errs}")

counts = [c.get("execution_count") for c in code]
seq = all(isinstance(x,int) for x in counts) and counts == list(range(1, len(counts)+1))
check("execution_count sequential 1..N (real top-to-bottom run)", seq, f"counts={counts}")

pngs = []
for c in code:
    for o in c.get("outputs", []):
        d = o.get("data", {}).get("image/png")
        if d:
            try: pngs.append(base64.b64decode(d))
            except Exception: pngs.append(b"")
real = [b for b in pngs if b.startswith(b"\x89PNG") and len(b) > 5000]
check("plots: >=5 real PNGs over 5KB each", len(real) >= 5, f"found={len(pngs)}, real={len(real)}, sizes={[len(b) for b in pngs]}")
check("file size plausible for executed notebook (>150KB)", len(raw) > 150_000, f"size={len(raw)}")
missing = [s for s in ["Loaded","resume","pass_rate"] if s not in raw.decode("utf-8","ignore")]
check("required strings present", not missing, f"missing={missing}")
print("VERDICT:", "FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
