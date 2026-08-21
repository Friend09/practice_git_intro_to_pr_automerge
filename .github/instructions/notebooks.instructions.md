---
description: "Enforce Jupyter notebook conventions for the Intro to PR Auto-Merge learning labs. Use when: editing, creating, or reviewing files in notebooks/. Ensures required cell sequence (objectives -> env/auth check -> fixture-vs-live toggle -> narrated gh calls -> takeaways), markdown narration cadence, and clean output policy. Auto-applies to all .ipynb files under notebooks/."
applyTo: "notebooks/**/*.ipynb"
---

# Jupyter Notebook Conventions

These rules apply to every `.ipynb` file under `notebooks/`. They ensure all practice notebooks
are reproducible, well-narrated, and safe to run without leaking credentials.

## Required Cell Sequence

Every notebook must follow this section order:

```
Cell 1: Markdown — # Chapter XX: Title (notebook edition)
Cell 2: Markdown — ## Learning Objectives (4-6 bullets)
Cell 3: Code    — imports + PRA_ env vars + PRA_MODE toggle + auth check
Cell 4: Markdown — ## 1. <first concept>
Cell 5: Code    — the first gh/API call or local demo
[...additional sections matching chapter structure...]
Last-2: Markdown — ## Takeaways & Next Steps
Last-1: Code    — optional: save artifacts to PRA_OUTPUT_DIR
Last:   Markdown — ## Chapter Link (link back to learning_modules/chapter_XX_*.md)
```

## Cell-Level Rules

### Markdown Narration Cadence

Every code cell must be immediately preceded by a markdown cell that:

- States **what** the next code does (1-2 sentences)
- States **why** it matters (1 sentence)
- Optionally previews the expected output ("You should see…")

### Code Cells

- First code cell always: imports + constants + the `PRA_MODE` toggle (`fixture` | `live`) + a
  one-line auth check (`gh auth status`) when in live mode
- Use `PRA_` prefix env vars matching lab scripts
- Never print a token, even in live mode — assert its presence, don't display its value
- Print output at end of each code cell (don't rely on Jupyter's implicit last-line display for
  anything important)

## Fixture vs Live Discipline

```python
import os

PRA_MODE = os.environ.get("PRA_MODE", "fixture")   # "fixture" | "live"
PRA_REPO = os.environ.get("PRA_REPO", "")

if PRA_MODE == "live":
    assert PRA_REPO, "Set PRA_REPO=owner/name to run against a real repo"
    # gh auth status is assumed; do not print token values
```

- This toggle must appear in the **setup cell** (Cell 3) of every notebook
- Reference notebooks default to `PRA_MODE=fixture` so they run identically for every reader
- If a cell requires `live` mode (e.g. watching a real trigger fire), say so explicitly in the
  preceding markdown cell and show the expected fixture-mode output as a fallback

## Output Policy

- **Commit notebooks with cleared outputs** — run `make run-notebooks` to regenerate locally
- No large output blobs (a full `gh api` payload, 100+ line JSON dumps)
- Use `json.dumps(data, indent=2)[:500]` or a rendered table instead of raw payloads
- Never commit output containing a real token, PR URL with sensitive content, or account details
  beyond the public sandbox repo name

## Optional Deep-Dive Notebooks

For chapters marked ⭐ Optional Deep-Dive in README.md:

- Include a `> ⭐ **Optional section** — feel free to skip on first pass.` callout before advanced
  cells
- Group advanced cells under a clearly labeled `## Advanced: ...` section header

## Chapter Link Format

The final markdown cell must include:

```markdown
---

📖 **Reading companion:** [Chapter XX: Title](../learning_modules/chapter_XX_<topic>.md)
🔬 **Try it live:** Re-run this notebook with `PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge`
```
