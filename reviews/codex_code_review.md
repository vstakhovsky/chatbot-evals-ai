src/generate_dataset.py:82, MAJOR, replace substring typo detection with token/regex checks; ordinary text ending in “u ”, including “you ”, falsely passes `rushing_with_typos`.

src/generate_dataset.py:96, MINOR, pass the already-loaded scenario object into `format_prompt`; it currently reloads all seed files per query and duplicates the lookup at line 214.

src/generate_dataset.py:192, MAJOR, estimate worst-case calls including five retries; the 1,500-row job can make 7,500 calls while never triggering the required >2,000-call cost gate.

src/generate_dataset.py:211, MINOR, delete the single-use `generate_with_progress` wrapper and inline its body into the processing function.

src/generate_dataset.py:229, MAJOR, execute bounded tasks concurrently or delete the semaphore and `--concurrency`; awaiting each row serially makes both nonfunctional.

src/generate_dataset.py:234, MAJOR, checkpoint on nonzero processed milestones; using `len(results) % SAVE_EVERY` rewrites after every failure at the same count and can attempt to deduplicate an empty columnless frame.

src/generate_dataset.py:257, MAJOR, acquire the required O_EXCL PID lock and write via a temporary file plus `os.replace`; direct CSV writes violate `specs/rules.md:25-26` and permit corruption or concurrent writers.

src/config.py:41, MAJOR, move API-key validation to API-calling entry points; importing shared paths and settings currently fails for offline consumers without credentials.

src/schemas.py:7, MINOR, delete the unused `Persona`, `Modifier`, `Scenario`, and `GenerationRequest` models; no repository code imports them.

scripts/hooks.py:16, MAJOR, remove the blanket exception handler and fail closed on invalid hook input; unexpected errors silently disable protected-file enforcement.

scripts/hooks.py:32, MAJOR, remove the blanket exception handler and fail closed; unexpected errors silently disable every Bash guard.

scripts/hooks.py:47, MAJOR, parse Git arguments and reject every forced-push form, including `--force-with-lease` and `--force-if-includes`, instead of substring matching.

scripts/hooks.py:51, MAJOR, replace substring matching with target-aware command validation; notebook deletion through commands such as `unlink` bypasses the evidence guard.

scripts/hooks.py:65, MAJOR, derive or configure the active stage instead of hard-coding Stage 6; session startup becomes incorrect as soon as another stage is active.

scripts/hooks.py:73, MAJOR, run verification with `subprocess`, show its complete raw output, and propagate its exit status; piping through `tail` violates `specs/rules.md:15` and line 74 reports success after verifier failure.

specs/stage6_dataset_rag.md:14, MAJOR, state the actual G4 mismatch—missing `extracted_context` and unexpected `hits`; the current evidence says seven columns were expected and then lists seven columns without identifying the failure.