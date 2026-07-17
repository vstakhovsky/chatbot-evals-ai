"""Enhanced notebook verifier with mandatory section checks."""
import sys
from pathlib import Path
import nbformat

notebook_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("notebooks/01_rag_evals.ipynb")
notebook = nbformat.read(notebook_path, as_version=4)

fails = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        fails.append(name)
        if detail:
            print(f"  {detail}")

# 1. nbformat validation
try:
    nbformat.validate(notebook)
    check("nbformat validation", True)
except Exception as e:
    check("nbformat validation", False, str(e))

# 2. nbformat 4
check("nbformat version 4", notebook.nbformat == 4)

# 3. No markdown cells with outputs
markdown_bad = [i for i, c in enumerate(notebook.cells)
                if c.cell_type == 'markdown' and 'outputs' in c]
check("markdown cells without outputs", not markdown_bad, f"cells: {markdown_bad}")

# 4. No markdown cells with execution_count
exec_bad = [i for i, c in enumerate(notebook.cells)
             if c.cell_type == 'markdown' and 'execution_count' in c]
check("markdown cells without execution_count", not exec_bad, f"cells: {exec_bad}")

# 5. No error outputs
error_cells = [i for i, c in enumerate(notebook.cells)
                if c.cell_type == 'code' and
                any(o.get('output_type') == 'error' for o in c.get('outputs', []))]
check("no error outputs", not error_cells, f"cells: {error_cells}")

# 6. All code cells executed
unexecuted = [i for i, c in enumerate(notebook.cells)
              if c.cell_type == 'code' and c.get('execution_count') is None]
skip_executed = [i for i, c in enumerate(notebook.cells)
                  if c.cell_type == 'code' and c.get('execution_count') is None and
                  'skip-execution' in c.get('metadata', {}).get('tags', [])]
unexecuted_required = len(unexecuted) - len(skip_executed)
check("all code cells executed", unexecuted_required == 0, f"unexecuted: {unexecuted_required}")

# 7. Required headings
all_text = ' '.join([''.join(c['source']) if isinstance(c['source'], list) else c['source']
                     for c in notebook.cells])
required_headings = ["retrieval", "judge", "evaluation", "failure", "attribution", "conclusions"]
missing_headings = [h for h in required_headings if h.lower() not in all_text.lower()]
check("required headings", not missing_headings, f"missing: {missing_headings}")

# 8. Five retrieval examples
retrieval_count = 0
for c in notebook.cells:
    if c.cell_type == 'code':
        source = ''.join(c['source']) if isinstance(c['source'], list) else c['source']
        if 'question' in source.lower() and 'retrieved' in source.lower():
            retrieval_count += 1
check("retrieval examples >= 5", retrieval_count >= 5, f"found: {retrieval_count}")

# 9. Judge registry
judge_registry = any('judge' in ''.join(c['source']).lower() and 'registry' in ''.join(c['source']).lower()
                      if isinstance(c['source'], list) else c['source'] for _ in [0]
                      for c in notebook.cells if c.cell_type == 'code')
check("judge registry", judge_registry)

# 10. Judge smoke test
smoke_test = any('smoke' in ''.join(c['source']).lower() and 'test' in ''.join(c['source']).lower()
                  if isinstance(c['source'], list) else c['source'] for _ in [0]
                  for c in notebook.cells if c.cell_type == 'code')
check("judge smoke test", smoke_test)

# 11. Data analysis charts
charts = sum(1 for c in notebook.cells
             if c.cell_type == 'code' and
             any('plt.' in ''.join(c['source']) if isinstance(c['source'], list) else c['source'] for _ in [0])
             for o in c.get('outputs', [])
             if o.get('output_type') == 'display_data')
check("data-analysis charts >= 1", charts >= 1, f"found: {charts}")

# 12. Failure taxonomy
taxonomy = any('taxonomy' in ''.join(c['source']).lower() or 'failure' in ''.join(c['source']).lower()
                if isinstance(c['source'], list) else c['source'] for _ in [0]
                for c in notebook.cells if c.cell_type == 'code')
check("failure taxonomy", taxonomy)

# 13. Attribution output
attribution = any('attribution' in ''.join(c['source']).lower()
                  if isinstance(c['source'], list) else c['source'] for _ in [0]
                  for c in notebook.cells if c.cell_type == 'code')
check("attribution output", attribution)

# 14. Conclusions
conclusions = any('conclusions' in ''.join(c['source']).lower()
                  if isinstance(c['source'], list) else c['source'] for _ in [0]
                  for c in notebook.cells if c.cell_type == 'markdown')
check("conclusions", conclusions)

# 15. No API keys
no_secrets = 'api_key' not in all_text.lower() and 'sk-' not in all_text.lower()
check("no obvious API keys", no_secrets)

# 16. File size
size_ok = notebook_path.stat().st_size < 10_000_000
check("file size < 10MB", size_ok, f"{notebook_path.stat().st_size / 1024:.1f} KB")

print(f"\nGATE: {'PASS' if not fails else 'FAIL'}")
if fails:
    print(f"Failed: {fails}")

sys.exit(1 if fails else 0)
