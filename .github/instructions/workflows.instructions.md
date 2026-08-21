---
description: "Enforce safety and clarity conventions for the LIVE gate workflows that implement the three-gate auto-merge airlock. Use when: editing, creating, or reviewing files in .github/workflows/. Ensures explicit permissions, pinned actions, a workflow_dispatch escape hatch alongside every schedule, and a paths filter that keeps gates from firing on curriculum-content PRs. Auto-applies to all workflow YAML."
applyTo: ".github/workflows/*.yml"
---

# Live Workflow Conventions

Unlike every other file in this repo, files here **execute for real** against the sandbox repo.
A mistake here doesn't just teach a wrong lesson — it can merge something, run on an unintended
schedule, or leak a secret. Treat these rules as load-bearing, not stylistic.

## Required on Every Workflow File

1. **Header comment naming the gate it implements:**

   ```yaml
   # Gate 3 — PR Risk Scoring
   # Reads PR diff metadata, computes a risk score, publishes a check run.
   # Chapter: learning_modules/chapter_15_gate3_risk_scoring.md
   ```

2. **Explicit `permissions:` block on every job — never inherit the repo default:**

   ```yaml
   permissions:
     contents: read
     pull-requests: write   # only if the job actually comments/labels
     checks: write          # only if the job actually publishes a check run
   ```

3. **A `paths:` filter on every gate workflow, scoped to `sandbox/**`** — this repo is both the
   curriculum and the live lab, and the gates must never act on a PR that edits
   `learning_modules/`, `labs/`, or `notebooks/`:

   ```yaml
   on:
     pull_request:
       paths:
         - 'sandbox/**'
   ```

4. **`workflow_dispatch:` alongside any `schedule:`** — cron-only workflows are untestable on
   demand and `schedule:` silently stops firing after 60 days of repo inactivity:

   ```yaml
   on:
     schedule:
       - cron: '0 6 * * 1'   # weekly, Monday 06:00 UTC
     workflow_dispatch: {}   # trigger manually to test without waiting a week
   ```

5. **Pin actions to a major version tag at minimum** (`actions/checkout@v4`), not `@main` or an
   unpinned floating tag.

## Token Discipline

- Default to the workflow's own `GITHUB_TOKEN`. Only reach for `PRA_BOT_TOKEN` (a fine-grained
  PAT, stored as a repo secret) when a step must trigger a *downstream* workflow — see
  Chapter 10. Never name a secret `GITHUB_*`; that prefix is reserved.
- Never `echo` or `run: | echo ${{ secrets.* }}` a secret value, even for debugging.

## Job Summaries

- Every gate job writes a human-readable verdict to `$GITHUB_STEP_SUMMARY` — this is the fastest
  way to see *why* a gate passed or failed without opening logs (taught in Chapter 12).

## What Belongs Here vs `capstone` Content

- These files are the **only** workflows that execute in this repository. Anything meant purely
  as reading material (an illustrative YAML snippet) belongs inline in a chapter's Appendix A,
  never dropped into this directory even temporarily — an inert-looking YAML file here is not
  inert; GitHub will parse and run it.
