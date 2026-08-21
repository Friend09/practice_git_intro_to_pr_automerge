# Project Guidelines

> Conventions and code standards are in [CLAUDE.md](../CLAUDE.md). This file covers
> agent-specific workflow guidance.

## Learning Sources

This curriculum is anchored to GitHub's own documentation plus one book. Every chapter cites
which:

| Tag | Resource | Focus |
| --- | -------- | ----- |
| **GH Docs** | [docs.github.com/actions](https://docs.github.com/en/actions) | Canonical, but changes fast — always cite a dated fetch |
| **Pro Git** | Scott Chacon & Ben Straub, *Pro Git* 2nd Ed. (free, git-scm.com/book) | Refs, merge mechanics, the Git-level truth in Phase 1 |
| **REST API** | [docs.github.com/rest](https://docs.github.com/en/rest) | Every `gh api` call names its endpoint |

## Content Generation Rules

When writing or updating chapters:

1. **Doc Reference tag** — every chapter header must include `**Doc Reference:**` citing the
   relevant GitHub Docs page or Pro Git section
2. **Two callouts required** — every chapter must include at least one
   `> **🔬 Automation Engineer's Lens:**` and one `> **🚦 Native vs Custom:**` callout
3. **Don't paraphrase the docs wholesale** — summarize in our own voice; link out for exhaustive
   detail
4. **Concrete numbers** — rate limits, cron expressions, page sizes, timeouts, thresholds — never
   vague qualifiers like "fast" or "usually"
5. **Trade-off thinking** — every approach comparison needs a qualitative trade-off table (see
   `chapter-content.instructions.md` for the exact vocabulary)
6. **The Airlock Principle is the one metaphor** — reuse it; don't introduce a second competing
   analogy

## Chapter Structure

Every chapter follows this skeleton (see completed Ch 01, 06, 15 for examples):

```
# Chapter XX: Title
Reading Time / Prerequisites / Notebook / Script / Doc Reference / Depth
---
## Beginner's Guide (what to focus on, what to skip, key terms)
## 🔬 Automation Engineer's Lens callout
## 🚦 Native vs Custom callout
## What You'll Learn (bullet list)
## Table of Contents (20 sections)
## Sections 1-16 (core content)
## Sections 17-20 (takeaways, what's next, resources, appendix)
```

## Build and Test

```bash
# Install dependencies
uv pip compile requirements.in -o requirements.txt && uv pip install -r requirements.txt

# Run a lab script (offline, fixture mode by default)
python labs/lab_XX_<topic>.py

# Run a lab against the real sandbox repo
PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge python labs/lab_XX_<topic>.py

# Run all notebooks (execute + strip outputs)
make run-notebooks

# Run tests (must pass offline, no network)
pytest tests/ -v --tb=short

# Generate a throwaway sandbox PR of a known size
make pr LINES=120 FILES=6
```

## Safety Rule for This Repo Specifically

This repository is **both** the curriculum you are writing **and** the live lab the gate
workflows run against. Any workflow under `.github/workflows/` executes for real. Before adding
or editing one, read `.github/instructions/workflows.instructions.md` — in particular, every
gate must carry a `paths: ['sandbox/**']` filter so it never fires on a PR that only edits
`learning_modules/`, `labs/`, or `notebooks/`.

## Standard Workflow

For each new or updated chapter: draft against the instruction files → write the paired lab
script and notebook pair → verify the lab runs in fixture mode with `make test` → if the chapter
claims a live behavior, verify it against the real sandbox repo → log the chapter in
`notes/THINGS_TASK_TRACKER.md` and `notes/IMPROVEMENTS_SUMMARY.md`.

## Notebook/Code Generation

When generating notebooks or scripts, be careful with escape sequences (write real newlines, not
literal `\n`), and verify the generated file renders/runs before finishing. Never write a real
token or credential into a notebook output cell.
