---
description: "Enforce Python lab script conventions for the Intro to PR Auto-Merge hands-on exercises. Use when: editing, creating, or reviewing files in labs/. Ensures module docstrings, import ordering, type hints, PRA_ environment variable patterns, pathlib usage, and fixture/live dual-mode discipline. Auto-applies to all Python files under labs/."
applyTo: "labs/**/*.py"
---

# Python Lab Script Conventions

These rules apply to every Python file under `labs/`. They enforce guardrails on **any** edit —
small fixes, refactors, or additions.

## Required File Structure

Every lab script must follow this order:

```
1. Module docstring (purpose, chapter link, gh commands used, usage example)
2. Imports: stdlib → sys.path insertion (see below) → pr_automerge
3. Constants / Configuration (PRA_ env vars, thresholds, paths)
4. Helper Functions / Classes (each with docstring + type hints)
5. Main experiment / demo logic
6. if __name__ == "__main__": entrypoint with argparse or direct call
```

## sys.path Insertion (Required)

Labs run standalone (`python labs/lab_XX_*.py`, and via `make lab-XX`), not as an installed
package. Because the `pr_automerge` package lives at the repo root, not under `labs/`, every lab
that imports from it must insert the repo root into `sys.path` before that import — verified
necessary: omitting this raises `ModuleNotFoundError: No module named 'pr_automerge'` the moment
the script is run directly rather than via pytest (which inserts the root itself).

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_automerge.models import GateResult  # noqa: E402
```

## Environment Variables

Use `PRA_` prefix for all configuration:

```python
import os
output_dir = os.environ.get("PRA_OUTPUT_DIR", "./output")
repo       = os.environ.get("PRA_REPO", "")          # "owner/name"
log_level  = os.environ.get("PRA_LOG_LEVEL", "INFO")
threshold  = float(os.environ.get("PRA_THRESHOLD", "70.0"))
```

## Python Standards

- **Docstrings**: Required on all functions and classes (also required by the user's global
  CLAUDE.md for every `.py` file)
- **Type hints**: Required on all function signatures
- **Imports**: `stdlib` → `third-party` → `pr_automerge`
- **File paths**: `pathlib.Path` — never f-string or `os.path` concatenation
- **No hardcoded paths**: Use env vars or `pathlib.Path` relative to script location
- **Subprocess calls to `gh`**: Never `shell=True`; always pass args as a list; always request
  `--jq` or parse JSON with `json.loads`, never dump raw payloads

## Domain-Specific Patterns

Lab scripts demonstrate PR auto-merge concepts through hands-on code. Common patterns include:

- **Fixture / live dual mode**: Every lab that talks to GitHub must support both
  `PRA_MODE=fixture` (reads from `fixtures/*.json`, fully offline, deterministic) and
  `PRA_MODE=live` (calls `gh` against `PRA_REPO`). Default to `fixture` so `make test` never
  needs network.
- **`gh` wrapper**: Route all GitHub calls through a shared `run_gh()` helper (in the shared
  `pr_automerge` package) rather than ad hoc `subprocess.run` calls scattered per lab.
- **Never log tokens**: Do not print `PRA_BOT_TOKEN`, `GITHUB_TOKEN`, or any secret value, even at
  DEBUG level.
- **Decision objects**: Gate logic returns a typed `GateResult`/`Decision` dataclass, never a bare
  bool or string — the chapter's teaching point is *why* a gate decided what it decided.

## Output Requirements

- Print clear section headers (e.g., `print("=" * 60)`, `print("Phase 1: Fetching PR data")`)
- Use descriptive output — not raw dicts or unformatted JSON
- Print a **summary table** at the end: check/rule name, result, rationale
- Write output artifacts (reports, decision JSON) to `PRA_OUTPUT_DIR`
- Scripts must run standalone: `python labs/lab_XX_<topic>.py`

## Code Quality Rules

**DO:**

- Use the `pr_automerge` namespace for any shared utilities
- Support `PRA_MODE=fixture` for offline, deterministic runs
- Print section progress headers
- Include type hints on function signatures
- Use `pathlib.Path` for file paths
- Add docstrings to all functions and classes
- Make scripts runnable standalone
- Include `if __name__ == "__main__":` block

**DON'T:**

- Call `gh` or the GitHub API with `shell=True`
- Hard-code file paths, thresholds, or magic numbers — read from `PRA_` env vars or `gates.yml`
- Omit docstrings on functions or classes
- Print secrets or full API tokens
- Skip error handling at system boundaries (missing `gh` binary, network failure, malformed JSON)
- Require network access for `make test` to pass
