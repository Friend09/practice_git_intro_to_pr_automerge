# Chapter 21: Reusable Workflows & Composite Actions

**Reading Time:** ~40 minutes
**Prerequisites:** Chapter 08 (Actions Anatomy)
**Practice Notebook:** `notebooks/practice_21.ipynb`
**Reference Notebook:** `notebooks/lab_21_reusable_workflows.ipynb`
**Script:** `labs/lab_21_reusable_workflows.py`
**Doc Reference:** GitHub Docs "Reusing workflows"
**Depth:** ⭐ Optional Deep-Dive

---

## Beginner's Guide

**What to focus on first:** Sections 3–6 — the two mechanisms and exactly where each is invoked
from, which is the detail people mix up most.

**What to SKIP on first read:** Section 10 (nested reusable workflows and the call-depth limit).
Return only if you're building a multi-layer reuse hierarchy.

**Key concepts in plain English:**

- **Composite action:** A bundle of *steps*, packaged with an `action.yml`, invoked with `uses:`
  from **inside** a job's `steps:` list — as if it were one step.
- **Reusable workflow:** An entire *workflow* (one or more jobs), invoked with `uses:` at the
  **job** level, triggered by a special `workflow_call` event, with typed inputs/secrets/outputs.
- **Scaffold duplication:** The specific, concrete kind of repetition this chapter targets — the
  same checkout + setup steps copy-pasted across multiple workflow files.
- **`workflow_call`:** The trigger a reusable workflow declares instead of `pull_request`/`schedule`
  — it means "this file is meant to be called by another workflow, not run directly."
- **Typed I/O:** Reusable workflows declare `inputs:`/`secrets:`/`outputs:` with real types
  (string, boolean, number) — composite actions' inputs are always plain strings.

**Your prior knowledge connection:** If you've ever extracted a shared function versus a shared
module in a codebase — a function for "this exact sequence of steps," a module for "this whole
piece of functionality with its own internal structure" — composite actions and reusable workflows
map onto roughly that same distinction, one level up.

---

> **🔬 Automation Engineer's Lens:** Duplicated workflow scaffolding isn't just an aesthetic
> complaint — it's a real maintenance liability. When `actions/checkout@v4` needs to bump to `@v5`
> across five workflow files that each hardcoded it separately, that's five edits, five chances to
> miss one, five separate PRs' worth of review. A single composite action makes it one edit,
> automatically applied everywhere it's used.

---

> **🚦 Native vs Custom:** Both mechanisms are entirely native — GitHub provides the `uses:`
> resolution, the typed I/O passing, the whole invocation machinery. What you build is the
> **extraction decision**: recognizing duplicated scaffolding (Section 7's real example) and
> choosing the right mechanism (step-level vs job-level) to eliminate it.

---

## What You'll Learn

- The precise difference between a composite action and a reusable workflow
- Exactly where each is invoked from in a workflow file — the detail that distinguishes them
- How to find real, concrete duplication in this repo's own workflow files
- What a minimal composite action (`action.yml`) and reusable workflow (`workflow_call`) look like
- The typed-I/O difference between the two mechanisms
- When extraction is worth the indirection cost, and when duplication is actually fine

---

## Table of Contents

- [Chapter 21: Reusable Workflows \& Composite Actions](#chapter-21-reusable-workflows--composite-actions)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Two Different Kinds of "Don't Repeat Yourself"](#1-two-different-kinds-of-dont-repeat-yourself)
  - [2. Composite Actions: Step-Level Reuse](#2-composite-actions-step-level-reuse)
  - [3. Reusable Workflows: Job-Level Reuse](#3-reusable-workflows-job-level-reuse)
  - [4. The Invocation-Point Distinction, Precisely](#4-the-invocation-point-distinction-precisely)
  - [5. `workflow_call` and Typed I/O](#5-workflow_call-and-typed-io)
  - [6. Side-by-Side Comparison](#6-side-by-side-comparison)
  - [7. Finding Real Duplication in This Repo](#7-finding-real-duplication-in-this-repo)
  - [8. What the Extraction Would Look Like](#8-what-the-extraction-would-look-like)
  - [9. ⚠️ ADVANCED: Composite Actions Can't Set Job-Level `permissions:`](#9-️-advanced-composite-actions-cant-set-job-level-permissions)
  - [10. ⚠️ ADVANCED: Nested Reusable Workflows](#10-️-advanced-nested-reusable-workflows)
  - [11. ⚠️ ADVANCED: Versioning a Shared Action or Workflow](#11-️-advanced-versioning-a-shared-action-or-workflow)
  - [12. Case Study: The `@v4`-to-`@v5` Bump, Five Times vs Once](#12-case-study-the-v4-to-v5-bump-five-times-vs-once)
  - [13. Case Study: Why This Repo Hasn't Extracted Anything (Yet)](#13-case-study-why-this-repo-hasnt-extracted-anything-yet)
  - [14. Practical Tips: Deciding What to Extract](#14-practical-tips-deciding-what-to-extract)
  - [15. Your First Project: Find Your Own Repo's Duplication](#15-your-first-project-find-your-own-repos-duplication)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 22 — Buy vs Build](#18-whats-next-chapter-22--buy-vs-build)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Finding Shared Steps and Comparing Mechanisms (from Section 15)](#a1--finding-shared-steps-and-comparing-mechanisms-from-section-15)

---

## 1. Two Different Kinds of "Don't Repeat Yourself"

Workflow duplication comes in two shapes: the same handful of *steps* repeated inside several
jobs' `steps:` lists (checkout, set up a language runtime), or the same *whole job pattern*
repeated across several workflow files or repositories (an entire "build, test, publish" sequence).
GitHub gives you a different mechanism for each.

## 2. Composite Actions: Step-Level Reuse

A composite action is a directory (usually under `.github/actions/<name>/`) containing an
`action.yml` with `runs: { using: composite, steps: [...] }` — a named bundle of steps, invoked
exactly like any other `uses:` step, from inside a job's `steps:` list:

```yaml
steps:
  - uses: ./.github/actions/setup-python-gate-env
  - run: python -m pytest
```

Everything the composite action's steps do runs on the *calling* job's own runner — it's not a
separate job, just a named shortcut for a sequence of steps.

## 3. Reusable Workflows: Job-Level Reuse

A reusable workflow is an ordinary-looking workflow file that declares `on: workflow_call` instead
of (or alongside) `pull_request`/`schedule`, and is invoked from a **job**, not a step:

```yaml
jobs:
  call-gate-publisher:
    uses: ./.github/workflows/reusable-gate-publisher.yml
    with:
      check_name: gate3-risk-score
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

The called workflow can define **multiple jobs** of its own, each running on its own runner — a
capability a composite action, confined to one job's steps, structurally cannot offer.

## 4. The Invocation-Point Distinction, Precisely

```
Composite action:  uses: INSIDE a job's steps: list      (one step, borrowed from elsewhere)
Reusable workflow: uses: ON the job itself (job-level)    (an entire separate workflow, invoked)
```

This is the single fact that resolves most confusion between the two: if you're writing `uses:`
under `steps:`, you're calling a composite action (or a plain marketplace action); if you're
writing `uses:` as a job's own top-level key (replacing `runs-on:`/`steps:` for that job), you're
calling a reusable workflow.

## 5. `workflow_call` and Typed I/O

A reusable workflow's `workflow_call` trigger declares `inputs:` (typed: `string`, `boolean`,
`number`), `secrets:` (explicitly passed through, never inherited implicitly unless
`secrets: inherit` is used), and `outputs:` a calling job can read via
`needs.<job>.outputs.<name>` (Chapter 10 §7) — the same job-output mechanism from Chapter 10,
extended across workflow boundaries. Composite actions' `inputs:` are always plain strings, with no
type declaration — a real capability gap between the two mechanisms.

## 6. Side-by-Side Comparison

| Property | Composite Action | Reusable Workflow | Setup Effort |
| --- | --- | --- | --- |
| Invoked from | Inside a job's `steps:` list | At the job level (`uses:` on the job itself) | Low (action) / Moderate (workflow) |
| Can define multiple jobs | No — confined to one job's steps | Yes | — |
| Input types | Always string | Typed (string/boolean/number) | — |
| Secret handling | Inherited from the calling job automatically | Explicit `secrets:` block, or `secrets: inherit` | Low (action) / Moderate (workflow, more deliberate) |
| Best fit | A shared sequence of steps within one job | An entire shared job pattern, possibly multi-job | — |

## 7. Finding Real Duplication in This Repo

`gate2-pr-health.yml` and `gate3-score.yml` each independently declare the identical checkout +
`actions/setup-python@v5` scaffold as their first two steps — verified by parsing both real files
(this chapter's lab does exactly this, read-only). This is precisely the kind of duplication
composite actions exist to eliminate: two files, same two steps, copy-pasted rather than shared.

## 8. What the Extraction Would Look Like

```yaml
# .github/actions/setup-python-gate-env/action.yml (illustrative -- NOT applied to this repo)
name: Setup Python Gate Environment
runs:
  using: composite
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
```

Both `gate2-pr-health.yml` and `gate3-score.yml` could then replace their first two steps with one:
`uses: ./.github/actions/setup-python-gate-env`. This curriculum deliberately doesn't apply this
extraction to the live workflows (Section 13 explains why) — it's presented here as a worked
example of the *pattern*, not a change made to this repo's actual `.github/workflows/`.

## 9. ⚠️ ADVANCED: Composite Actions Can't Set Job-Level `permissions:`

> ⚠️ **ADVANCED TOPIC:** A real limitation worth knowing before reaching for composite actions.
> **Skip on first read.**

A composite action's steps run with whatever `permissions:` the *calling job* already has — the
action itself cannot declare or expand permissions. If two workflows extract a shared composite
action but need different permission scopes (one needs `checks: write`, the other doesn't), each
calling job must still declare its own correct `permissions:` block independently; the extraction
only removes step duplication, not permission-declaration duplication.

## 10. ⚠️ ADVANCED: Nested Reusable Workflows

> ⚠️ **ADVANCED TOPIC:** Reusable workflows calling other reusable workflows.
> **Skip on first read** — return only if building a multi-layer reuse hierarchy.

A reusable workflow can itself call another reusable workflow, up to a maximum nesting depth
GitHub enforces (four levels, as of this writing). This enables genuinely layered reuse (a
top-level "deploy" reusable workflow calling a "build" reusable workflow calling a "test" reusable
workflow), at the cost of debugging complexity — tracing a failure through several layers of
`uses:` indirection is meaningfully harder than reading one flat file, a real cost to weigh against
the deduplication benefit.

## 11. ⚠️ ADVANCED: Versioning a Shared Action or Workflow

> ⚠️ **ADVANCED TOPIC:** Pinning a composite action or reusable workflow the same way as any other
> `uses:` reference.
> **Skip on first read.**

A composite action or reusable workflow referenced via a relative path (`./.github/actions/...`)
always uses whatever version exists at the calling workflow's own checked-out ref — no separate
pinning needed, since it's part of the same repo and commit. One referenced from a *different*
repository (`owner/repo/.github/workflows/file.yml@v1`) needs the same version-pinning discipline
as any other cross-repo `uses:` reference (Chapter 18 §11) — a tag can move; a commit SHA cannot.

## 12. Case Study: The `@v4`-to-`@v5` Bump, Five Times vs Once

If this repo's five workflows had each independently hardcoded `actions/checkout@v4`, bumping to
`@v5` when it releases means five separate edits across five files — five chances to miss one, and
five separate diffs a reviewer has to re-verify are all doing the same thing. With the extraction
from Section 8 in place, it's one edit to one `action.yml`, automatically applied everywhere that
composite action is used. This is the concrete payoff Section 1's "maintenance liability" framing
promises, made specific.

## 13. Case Study: Why This Repo Hasn't Extracted Anything (Yet)

Two duplicated steps, across two workflow files, is a small enough amount of duplication that the
extra indirection of a composite action (a new file, a new relative path to remember, one more
thing to understand when reading either gate workflow) arguably isn't worth it yet at this repo's
current scale — five total workflows, two of which share this one scaffold. The crossover point
(Section 14) is about *how much* duplication and *how often* it needs synchronized changes, not
about duplication existing at all. This repo's own restraint here is itself an illustration of that
judgment call, not an oversight.

## 14. Practical Tips: Deciding What to Extract

```
Is this duplication worth extracting?
──────────────────────────────────────────
[ ] Does the SAME sequence appear in 3+ places, not just 2? (weak signal at 2, strong at 3+)
[ ] Has it needed a synchronized change before (a version bump, a config tweak)?
[ ] Is the sequence itself stable, or does it change per-caller in ways that'd need many inputs?
[ ] Would the indirection cost (a new file to open, understand) outweigh the dedup benefit?
```

If most of these point toward "extract," a composite action (step-level) or reusable workflow
(job-level, per Section 4's distinction) is the right native mechanism — never hand-rolled
duplication-detection tooling or a templating system layered on top of YAML.

## 15. Your First Project: Find Your Own Repo's Duplication

Run this chapter's lab against two of your own repo's workflow files (or reuse this repo's own
`gate2-pr-health.yml`/`gate3-score.yml` pair) and confirm `find_shared_scaffold_steps` correctly
identifies the duplicated `uses:` values. Then sketch — on paper, not applied — what the composite
action extraction would look like for your own case.

## 16. Common Pitfalls & Misconceptions

1. **"Composite actions and reusable workflows are basically interchangeable."** No — they're
   invoked from structurally different places (step-level vs job-level, Section 4) and have
   different capabilities (multi-job, typed I/O).

2. **"A composite action can grant a job extra permissions."** No — it inherits whatever
   permissions the calling job already has (Section 9); it can't expand them.

3. **"Extracting shared scaffolding is always worth doing."** Not necessarily — two occurrences of
   a two-step sequence, as in this repo's own case, may not clear the bar (Section 13–14).

4. **"A reusable workflow referenced by relative path needs the same SHA-pinning discipline as a
   cross-repo action."** No — same-repo relative references always resolve to the calling
   workflow's own checked-out commit; only cross-repository references need separate pinning
   (Section 11).

5. **"Nesting reusable workflows has no practical limit."** GitHub enforces a maximum call depth
   (Section 10) — deep nesting also has a real debugging cost independent of any hard limit.

## 17. Key Takeaways

- **Composite actions are step-level reuse**, invoked inside a job's `steps:` list, confined to one
  job's runner.
- **Reusable workflows are job-level reuse**, invoked via `uses:` on the job itself, and can define
  multiple jobs with typed inputs/secrets/outputs.
- **The invocation point is the fact that disambiguates them** — under `steps:` vs as the job's own
  `uses:` key.
- **This repo has real, findable duplication** (checkout + setup-python across Gate 2 and Gate 3)
  — a genuine worked example, not a hypothetical.
- **Extraction is a judgment call weighed against indirection cost** — this repo's own restraint
  at two occurrences is a deliberate illustration of that trade-off, not an oversight.

## 18. What's Next: Chapter 22 — Buy vs Build

Chapter 22 (also optional) zooms out from GitHub's own native mechanisms to ask a different
question: for teams that don't want to build any of this curriculum's three gates themselves, what
do the existing third-party PR-automation tools (Mergify, Kodiak, Renovate) actually offer, and
when does building your own still win?

[→ Chapter 22: Buy vs Build](chapter_22_buy_vs_build.md)

## 19. Additional Resources

- **GitHub Docs, "Reusing workflows"** — https://docs.github.com/en/actions/using-workflows/reusing-workflows (fetched 2026-08)
- **GitHub Docs, "Creating a composite action"** — https://docs.github.com/en/actions/creating-actions/creating-a-composite-action (fetched 2026-08)
- **This repo's own** `.github/workflows/gate2-pr-health.yml` and `gate3-score.yml` — the real duplication this chapter's case study is drawn from

## 20. Appendix A — Code Index

### A.1 — Finding Shared Steps and Comparing Mechanisms (from Section 15)

**What the code does:** Parses two real workflow files to find `uses:`/`name:` values shared
across their first job's steps, and describes the two reuse mechanisms' defining properties.

**ASCII flowchart:**

```
find_shared_scaffold_steps(gate2_path, gate3_path)
    → parse each file's first job's steps → intersect the identifier sets
    → ["actions/checkout@v4", "actions/setup-python@v5"]

describe_reuse_mechanism("composite_action")   → invoked from steps:, no jobs, untyped I/O
describe_reuse_mechanism("reusable_workflow")  → invoked from job uses:, multi-job, typed I/O
```

See `labs/lab_21_reusable_workflows.py` for the full runnable version.
