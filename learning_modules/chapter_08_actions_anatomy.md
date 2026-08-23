# Chapter 08: Actions Anatomy

**Reading Time:** ~50 minutes
**Prerequisites:** Chapter 07 (The GitHub API & Apps)
**Practice Notebook:** `notebooks/practice_08.ipynb`
**Reference Notebook:** `notebooks/lab_08_actions_anatomy.ipynb`
**Script:** `labs/lab_08_actions_anatomy.py`
**Doc Reference:** GitHub Docs "Understanding GitHub Actions"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 — the four-layer anatomy and how it maps onto real YAML.

**What to SKIP on first read:** Section 10 (self-hosted vs GitHub-hosted runner trade-offs).
Return once you're actually choosing a runner type for a real workflow.

**Key concepts in plain English:**

- **Workflow:** One `.yml` file under `.github/workflows/`, with a name, a trigger, and one or more
  jobs. This is the top-level unit — everything else nests inside it.
- **Job:** A group of steps that all run together on the *same* runner instance. Different jobs in
  the same workflow get different, fresh runners by default.
- **Step:** One action within a job — either `run:` (a shell command) or `uses:` (a reusable,
  packaged action). Steps in a job execute in order, on the same runner, sharing filesystem state.
- **Runner:** The actual virtual machine (or self-hosted machine) that executes a job's steps.
  Every job starts on a *fresh* runner — nothing persists between jobs unless you explicitly pass
  it along (Chapter 10's `needs`/outputs).
- **Action:** A packaged, reusable unit of automation (`actions/checkout@v4` is one) that a step can
  `uses:` instead of writing raw shell.

**Your prior knowledge connection:** If you've ever written a Jenkinsfile or a `.gitlab-ci.yml`,
this four-layer structure (pipeline → stage → job → step, in various naming) will feel immediately
familiar — Actions' specific vocabulary is the only new part.

---

> **🔬 Automation Engineer's Lens:** The most common "why didn't my step run" confusion isn't a
> trigger problem — it's forgetting that each *job* gets a fresh runner. A file written in job A's
> `run:` step doesn't exist in job B unless you explicitly persist it (an artifact, or a shared
> volume) — job B starts from a clean checkout, every time. Debugging this as if it were "one big
> script" instead of "several isolated machines" wastes far more time than reading this chapter
> once.

---

> **🚦 Native vs Custom:** The entire execution model — jobs, steps, runners, the fresh-VM-per-job
> guarantee — is 100% native GitHub Actions infrastructure. What you build is the YAML describing
> *what* to run and *when* — this repo's five gate workflows are exactly that: declarative
> descriptions of jobs and steps, with all the actual scheduling and isolation handled natively.

---

## What You'll Learn

- The four-layer structure every workflow follows: workflow → job(s) → step(s) → runner
- Why each job gets a fresh runner, and what that means for state between jobs
- The difference between a `run:` step and a `uses:` step
- How to read this repo's real `ci.yml` as a worked example of the anatomy
- What `permissions:` at the workflow level actually restricts
- Where jobs and steps sit relative to Chapter 09's events and Chapter 10's contexts

---

## Table of Contents

- [Chapter 08: Actions Anatomy](#chapter-08-actions-anatomy)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Four Layers, One Direction](#1-four-layers-one-direction)
  - [2. The Workflow File Itself](#2-the-workflow-file-itself)
  - [3. Jobs: Independent, Parallel by Default](#3-jobs-independent-parallel-by-default)
  - [4. Steps: Ordered, Shared State Within a Job](#4-steps-ordered-shared-state-within-a-job)
  - [5. `run:` vs `uses:`](#5-run-vs-uses)
  - [6. Runners: What Actually Executes a Job](#6-runners-what-actually-executes-a-job)
  - [7. Reading `ci.yml` as a Worked Example](#7-reading-ciyml-as-a-worked-example)
  - [8. Workflow-Level `permissions:`](#8-workflow-level-permissions)
  - [9. ⚠️ ADVANCED: `if:` Conditions on Jobs and Steps](#9-️-advanced-if-conditions-on-jobs-and-steps)
  - [10. ⚠️ ADVANCED: Self-Hosted vs GitHub-Hosted Runners](#10-️-advanced-self-hosted-vs-github-hosted-runners)
  - [11. ⚠️ ADVANCED: Matrix Builds](#11-️-advanced-matrix-builds)
  - [12. Case Study: A Step That "Disappeared" Between Jobs](#12-case-study-a-step-that-disappeared-between-jobs)
  - [13. Case Study: This Repo's Five Workflows, At a Glance](#13-case-study-this-repos-five-workflows-at-a-glance)
  - [14. Practical Tips: Reading Any Workflow File Fast](#14-practical-tips-reading-any-workflow-file-fast)
  - [15. Your First Project: Parse a Workflow Programmatically](#15-your-first-project-parse-a-workflow-programmatically)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 09 — The Event Model](#18-whats-next-chapter-09--the-event-model)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Parsing a Workflow's Anatomy (from Section 15)](#a1--parsing-a-workflows-anatomy-from-section-15)
    - [A.2 — The Real `ci.yml`, Line-Numbered (from Section 7)](#a2--the-real-ciyml-line-numbered-from-section-7)

---

## 1. Four Layers, One Direction

```
Workflow (one .yml file)
    └── Job (one or more; parallel by default, own fresh runner each)
            └── Step (ordered; run: or uses:; shares the job's runner and filesystem)
                    └── Runner (the actual VM executing that job's steps)
```

Every workflow you'll ever read decomposes into exactly this shape. Nothing skips a layer — a step
always belongs to a job, a job always belongs to a workflow.

## 2. The Workflow File Itself

A workflow is one YAML file under `.github/workflows/`, with a top-level `name:`, a trigger (`on:`,
Chapter 09's whole subject), an optional `permissions:` block (Section 8), and one or more `jobs:`.
GitHub discovers every file in that directory automatically — there's no registration step beyond
committing the file.

## 3. Jobs: Independent, Parallel by Default

Each key under `jobs:` is a separate job with its own `runs-on:` (which runner image) and its own
`steps:`. Unless one job declares `needs: [other_job]` (Chapter 10), every job in a workflow starts
**in parallel**, on **separate, fresh runners** — job A cannot see a file job B wrote, because
they're different machines entirely.

```
jobs:
  test: ...        ─┐
  lint: ...          ├─▶  all start at roughly the same time, on 3 SEPARATE runners
  build: ...        ─┘
```

## 4. Steps: Ordered, Shared State Within a Job

Within a single job, steps run **in order**, on the **same** runner — so, unlike jobs, steps *do*
share filesystem state. A `run:` step that writes a file is readable by the next `run:` step in the
same job, because they're literally the same machine.

## 5. `run:` vs `uses:`

```yaml
- name: Run tests
  run: python -m pytest sandbox/app -v      # raw shell, executed on the runner

- name: Checkout
  uses: actions/checkout@v4                 # a packaged, reusable action
```

`run:` executes shell directly. `uses:` invokes a pre-built action — code someone else packaged
(or you did, Chapter 21) — that GitHub downloads and runs, optionally configured with `with:`
inputs. Almost every workflow needs at least one `uses:` step (`actions/checkout@v4` is close to
universal — without it, the runner has no copy of your repo's code at all).

## 6. Runners: What Actually Executes a Job

`runs-on: ubuntu-latest` requests a GitHub-hosted virtual machine, freshly provisioned for this job
alone, torn down when the job finishes. Nothing about the runner persists across jobs, or even
across separate runs of the same job — every run starts from the same clean image. This is the
mechanical reason job-to-job state sharing needs an explicit mechanism (artifacts, or
`needs`-passed outputs, Chapter 10) rather than "just being there."

### What's Actually in the Image, and How Labels Match

"Clean image" does not mean "bare OS." A GitHub-hosted runner image is a fully stocked
development machine: Python, Node.js, Go, Java (all LTS versions), Docker, `git`, `git-lfs`,
and the `gh` CLI are all preinstalled on the Ubuntu image, with platform-appropriate additions
elsewhere (Xcode on macOS, for example). That's why `ci.yml` never installs Python or git —
only `pytest`, the one tool the image doesn't ship. It still runs `actions/setup-python@v5`
anyway, to pin *exactly* `'3.12'` rather than trusting whichever versions the image happens to
carry this month. The authoritative per-image inventory lives in the
`actions/runner-images` repository (each image links an "Included Software" README), also
linked from every run's log under "Set up job."

`runs-on:` selects an image by **label**. `ubuntu-latest`, `windows-latest`, and
`macos-latest` are aliases GitHub re-points to newer OS versions over time — "latest" means
"newest *supported*," not newest released — while version-pinned labels (`ubuntu-22.04`-style)
freeze the OS at the cost of eventual deprecation. `runs-on:` also accepts an array of labels,
in which case the job runs only on a runner matching **all** of them — the mechanism Section
10's self-hosted runners use for targeting (e.g. `[self-hosted, linux, gpu]`).

## 7. Reading `ci.yml` as a Worked Example

This repo's actual `.github/workflows/ci.yml` — the workflow Gate 2 (Chapter 15) reads the
conclusion of — has exactly one job (`test`) with five steps: checkout, set up Python, install
pytest, run the sandbox app's test suite, and write a job summary. The full 45-line file is
quoted, line-numbered, in
[Appendix A.2](#a2--the-real-ciyml-line-numbered-from-section-7); here is the excerpt where
the anatomy's top three layers all appear:

```text
10. name: CI
11.
12. on:
13.   pull_request:
14.     paths:
15.       - 'sandbox/**'
16.   workflow_dispatch: {}
17.
18. permissions:
19.   contents: read
20.
21. jobs:
22.   test:
23.     runs-on: ubuntu-latest
24.     steps:
```

Breaking the file down block by block (line numbers match Appendix A.2):

- **Lines 1–8** *(A.2)*: a comment block for humans — never executed. It documents which
  workflow reads this one's conclusion and which chapters reference it.
- **Line 10**: the **workflow** layer (Section 2). "CI" is this workflow's display name in the
  Actions tab, and the name branch protection's required-check list knows it by (Chapter 05).
- **Lines 12–16**: the trigger — `pull_request`, path-filtered to `sandbox/**`, plus a manual
  `workflow_dispatch`. This is the `on:` block Chapter 09 spends a whole chapter on.
- **Lines 18–19**: the workflow-level `permissions:` ceiling (Section 8) — `contents: read`
  and nothing else.
- **Lines 21–24**: the **job** layer (Section 3). One job, id `test`, requesting a
  GitHub-hosted `ubuntu-latest` runner (Section 6); line 24 opens its ordered **step** list
  (Section 4).
- **Lines 25–31** *(A.2)*: two `uses:` steps (Section 5) — `actions/checkout@v4`, then
  `actions/setup-python@v5` configured with a `with:` input pinning Python `'3.12'`.
- **Lines 33–39** *(A.2)*: two `run:` steps — `pip install pytest`, then
  `python -m pytest sandbox/app -v`, the command whose pass/fail becomes this workflow's
  conclusion.
- **Lines 41–45** *(A.2)*: the job-summary step, guarded by `if: always()` (Section 9) so it
  writes to `$GITHUB_STEP_SUMMARY` even when the test step fails.

**What to notice:**

- Lines 10, 12, 21, and 24 are the four structural keys — `name:`, `on:`, `jobs:`, `steps:` —
  that Section 14's fast-reading checklist tells you to find first in *any* workflow file.
- Indentation *is* the anatomy: `test:` nests under `jobs:`, `runs-on:` and `steps:` nest
  under `test:` — the YAML tree and the four-layer diagram in Section 1 are the same tree.
- `workflow_dispatch: {}` on line 16 is an empty mapping — the event needs no configuration,
  but the key must still be present for the manual "Run workflow" button to exist.

Reading the same file against this chapter's vocabulary as a summary tree:

```
workflow: "CI"
  trigger: pull_request (path-filtered to sandbox/**), workflow_dispatch
  permissions: contents: read
  job "test":  runs-on: ubuntu-latest
    step 1: uses: actions/checkout@v4
    step 2: uses: actions/setup-python@v5
    step 3: run: pip install pytest
    step 4: run: python -m pytest sandbox/app -v
    step 5: run: (write $GITHUB_STEP_SUMMARY), if: always()
```

Every field in that real file maps onto a name from Sections 2–6 with nothing left over — that's
the whole point of the anatomy.

## 8. Workflow-Level `permissions:`

`permissions:` at the top of a workflow (or per-job) sets the ceiling on what `GITHUB_TOKEN` can do
for that run — `ci.yml` declares `contents: read` and nothing else, meaning even if a step tried to
post a PR comment, it would be rejected: no `pull-requests: write` was granted. Chapter 11 covers
this mechanism and every scope in depth; this chapter only establishes *where* the setting lives
structurally (workflow-level, optionally overridden per-job).

## 9. ⚠️ ADVANCED: `if:` Conditions on Jobs and Steps

> ⚠️ **ADVANCED TOPIC:** Conditionally running (or skipping) a job or step.
> **Skip on first read** — return once you need a step that should run even after a failure.

`ci.yml`'s last step uses `if: always()` — without it, a step is skipped by default the moment any
earlier step in the same job fails. `always()` is one of several special functions (`success()`,
`failure()`, `cancelled()`) available inside `if:` expressions, evaluated against the job's
in-progress status. Chapter 10 covers the full expression syntax these conditions are built from.

## 10. ⚠️ ADVANCED: Self-Hosted vs GitHub-Hosted Runners

> ⚠️ **ADVANCED TOPIC:** When a GitHub-hosted runner isn't enough.
> **Skip on first read** — GitHub-hosted runners (`ubuntu-latest`, etc.) cover everything this
> curriculum builds.

`runs-on: ubuntu-latest` (or `windows-latest`, `macos-latest`) requests a runner GitHub manages
entirely — provisioning, teardown, and security isolation are GitHub's problem. `runs-on:
[self-hosted, ...]` instead targets a machine *you* register and maintain — necessary for
specialized hardware, air-gapped environments, or workloads too large/long for hosted runner
limits, but it shifts patching, isolation between jobs, and secret exposure risk onto you entirely.
This repo never needs self-hosted runners; every gate workflow runs on `ubuntu-latest`.

The middle path is an **ephemeral, just-in-time (JIT) runner**: a self-hosted runner created
through the REST API, started with `./run.sh --jitconfig <encoded_config>`, that performs **at
most one job before being automatically removed** from the repo or organization. That restores
the fresh-machine-per-job property GitHub-hosted runners give you for free — provided your
automation actually hands each JIT runner a clean environment, since reused hardware can leak
state from the previous job.

## 11. ⚠️ ADVANCED: Matrix Builds

> ⚠️ **ADVANCED TOPIC:** Running the same job across multiple parameter combinations.
> **Skip on first read.**

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

A `strategy: matrix:` block turns one job definition into N parallel jobs, one per combination of
the listed values (here, two Python versions) — each gets its own fresh runner, same as any other
job. Useful for testing across multiple language versions or OSes; this repo's own CI doesn't need
it since the sandbox app targets exactly one Python version.

### A Worked Expansion: 3 × 2 → 6 Jobs

**Before** — one job definition, `test`, carrying a two-variable matrix:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
        os: [ubuntu-latest, macos-latest]
```

**After** — the run triggers, and the run's job list shows **six** entries. With no `name:`
set, the UI's default label is the job name plus that combination's values (a UI default,
not documented syntax):

```
test (3.11, ubuntu-latest)
test (3.11, macos-latest)
test (3.12, ubuntu-latest)
test (3.12, macos-latest)
test (3.13, ubuntu-latest)
test (3.13, macos-latest)
```

**What to notice:**

- 3 versions × 2 OSes = 6 **jobs** — the matrix multiplies jobs (each on its own fresh
  runner), never steps within a job.
- Each label lists the values in the order the matrix variables were defined:
  `python-version` first, then `os`.
- A matrix generates at most **256 jobs per workflow run** — hosted or self-hosted alike.

Four knobs adjust the expansion:

- `include:` — add a variant: a combination not produced by the cross-product, or extra
  properties merged onto matching existing combinations.
- `exclude:` — remove specific combinations (e.g. drop `{python-version: "3.11", os:
  macos-latest}` to skip one of the six).
- `fail-fast:` — defaults to `true`: one failing job cancels all in-progress and queued
  sibling jobs in the matrix.
- `max-parallel:` — caps how many of the generated jobs run simultaneously (default: as many
  as runner availability allows).

## 12. Case Study: A Step That "Disappeared" Between Jobs

An early draft workflow (not this repo's, but a common real mistake) had a `build` job write a
compiled artifact to disk, then a separate `deploy` job try to read that same path — and got "file
not found." The `build` job's write happened on one fresh runner; the `deploy` job started on an
entirely different one with a clean filesystem. The fix requires an explicit mechanism —
`actions/upload-artifact` + `actions/download-artifact`, or restructuring into one job with two
steps if separate runners genuinely aren't needed. This repo's own workflows sidestep the issue
entirely: every gate is a single-job workflow, precisely to avoid needing artifact-passing
machinery for a task that doesn't require it.

## 13. Case Study: This Repo's Five Workflows, At a Glance

| Workflow | Trigger | Jobs | Purpose |
| --- | --- | --- | --- |
| `ci.yml` | `pull_request` (sandbox-scoped), `workflow_dispatch` | 1 (`test`) | Builds/tests `sandbox/app` — the required check Gate 2 reads |
| `gate1-repo-health.yml` | `schedule` (weekly cron), `workflow_dispatch` | 1 | Repo-readiness check, publishes a badge |
| `gate2-pr-health.yml` | `workflow_run` (off CI) | 1 | Reads CI's conclusion, publishes a fail-closed check run |
| `gate3-score.yml` | `pull_request` (sandbox-scoped) | 1 | Computes and publishes the risk score |
| `automerge.yml` | `pull_request` (sandbox-scoped) | 1 | Calls `gh pr merge --auto --squash` |

Every one of this repo's five real workflows is a **single-job** workflow — a deliberate
simplicity choice matching Section 12's lesson: fewer jobs means less inter-job state-passing
machinery to get wrong.

## 14. Practical Tips: Reading Any Workflow File Fast

```
Reading an unfamiliar workflow file
──────────────────────────────────────
[ ] name: and on: first -- what triggers this, and what's it called in the Actions UI?
[ ] permissions: -- what's the ceiling on what this run's GITHUB_TOKEN can do?
[ ] jobs: -- how many, do any have `needs:` (implying an order)?
[ ] Within each job: runs-on, then read steps top to bottom
[ ] Any `if:` conditions -- do they change what actually executes?
```

## 15. Your First Project: Parse a Workflow Programmatically

Load any workflow file (this repo's `ci.yml` is a good start) with `yaml.safe_load` and print its
four-layer anatomy — name, triggers, permissions, and each job's steps — exactly as this chapter's
lab script does. Confirm every field you see in the raw YAML shows up in your printed summary; if
something's missing, that's a gap in your parsing, not the file. Your expected result is the
anatomy already printed in Section 7 (and the full line-numbered listing in Appendix A.2 is the
ground truth to diff your output against, line by line).

## 16. Common Pitfalls & Misconceptions

1. **"All the jobs in a workflow run on the same machine."** No — each job gets its own fresh
   runner by default. Only steps *within* one job share a runner.

2. **"A workflow file with a syntax error just doesn't run that step."** No — a YAML/schema error
   in a workflow file typically means the *entire workflow* fails to register or run at all;
   Chapter 13 covers diagnosing this.

3. **"`run:` and `uses:` are interchangeable ways to write the same thing."** No — `run:` executes
   raw shell; `uses:` invokes a packaged action. You can't put shell commands under `uses:`.

4. **"Permissions set inside a step apply to that step only."** No — `permissions:` is set at the
   workflow or job level, applying to every step in scope; there's no per-step permission grant.

5. **"If job B needs job A's output, it'll just be there."** No — job-to-job data passing requires
   an explicit mechanism (artifacts, or `needs` + declared `outputs`, Chapter 10) — nothing persists
   automatically between separate runners.

## 17. Key Takeaways

- **Four layers, always: workflow → job(s) → step(s) → runner** — every workflow file decomposes
  into exactly this shape.
- **Jobs are isolated by default** — separate, fresh runners, running in parallel unless `needs:`
  imposes an order.
- **Steps within one job share a runner** — ordered, same filesystem, same machine.
- **`run:` is raw shell; `uses:` is a packaged action** — not interchangeable syntax for the same
  thing.
- **This repo's five real workflows are all single-job** — a deliberate simplicity choice that
  avoids needing inter-job state-passing machinery.

## 18. What's Next: Chapter 09 — The Event Model

Chapter 09 goes deep on the `on:` trigger this chapter treated as a black box — every event type
that can start a workflow, which ones expose secrets, and which ones fork PRs can and can't reach.

[→ Chapter 09: The Event Model](chapter_09_event_model.md)

## 19. Additional Resources

- **GitHub Docs, "Understanding GitHub Actions"** — https://docs.github.com/en/actions/get-started/understanding-github-actions (fetched 2026-08)
- **GitHub Docs, "Workflow syntax for GitHub Actions"** — https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions (fetched 2026-08)
- **GitHub Docs, "Choosing the runner for a job"** — https://docs.github.com/en/actions/using-jobs/choosing-the-runner-for-a-job (fetched 2026-08)
- **GitHub Docs, "Running variations of jobs in a workflow"** — https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs (fetched 2026-08)
- **GitHub Docs, "Workflow syntax for GitHub Actions"** (reference: `strategy.fail-fast` default, 256-job matrix cap, `runs-on` label matching) — https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (fetched 2026-08)
- **`actions/runner-images` repository** (per-image "Included Software" inventories) — https://github.com/actions/runner-images (fetched 2026-08)
- **GitHub Docs, "Security hardening for GitHub Actions"** (ephemeral/JIT runners) — https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Parsing a Workflow's Anatomy (from Section 15)

**What the code does:** Parses a workflow YAML document (a stable fixture example, or this repo's
real `ci.yml` in live mode) and reduces it to name, triggers, permissions, and each job's ordered
step list.

**ASCII flowchart:**

```
parse_workflow(yaml_text) → raw dict
        │
        ▼
summarize_workflow(raw) → {name, triggers, permissions, jobs: [{job_id, runs_on, steps}]}
```

See `labs/lab_08_actions_anatomy.py` for the full runnable version, including
`load_real_ci_workflow()` for live mode.

### A.2 — The Real `ci.yml`, Line-Numbered (from Section 7)

**What the code does:** This is this repo's actual `.github/workflows/ci.yml`, quoted verbatim
with line numbers added for the commentary in Section 7. On any `pull_request` touching
`sandbox/**` (or a manual dispatch), one job on a GitHub-hosted `ubuntu-latest` runner checks
out the PR head, pins Python 3.12, installs pytest, runs the sandbox app's test suite, and
writes a job summary even on failure.

**ASCII flowchart:**

```
pull_request touching sandbox/** (or workflow_dispatch)
        │
        ▼
job "test" on ubuntu-latest  (permissions: contents: read)
  checkout ─▶ setup-python 3.12 ─▶ pip install pytest ─▶ python -m pytest sandbox/app -v
        │
        ▼
write $GITHUB_STEP_SUMMARY   (if: always() — runs even when the tests failed)
```

```text
 1. # CI — builds and tests sandbox/app/
 2. # This is the workflow that Gate 2 (gate2-pr-health.yml) reads the conclusion of.
 3. # It is registered as a required status check in branch protection (Chapter 05),
 4. # and its completion is what gate2-pr-health.yml listens for via workflow_run
 5. # (Chapter 10 — workflow_run is the sanctioned way to react to another workflow's
 6. # completion regardless of which token that workflow used internally).
 7. # Chapter: learning_modules/chapter_04_actions_anatomy.md (built here),
 8. #          learning_modules/chapter_05_branch_protection.md (registered here)
 9.
10. name: CI
11.
12. on:
13.   pull_request:
14.     paths:
15.       - 'sandbox/**'
16.   workflow_dispatch: {}
17.
18. permissions:
19.   contents: read
20.
21. jobs:
22.   test:
23.     runs-on: ubuntu-latest
24.     steps:
25.       - name: Checkout PR head
26.         uses: actions/checkout@v4
27.
28.       - name: Set up Python
29.         uses: actions/setup-python@v5
30.         with:
31.           python-version: '3.12'
32.
33.       - name: Install test dependencies
34.         run: pip install pytest
35.
36.       - name: Run sandbox app tests
37.         # `python -m pytest` (not bare `pytest`) so the repo root lands on sys.path
38.         # and `from sandbox.app...` resolves as a namespace package.
39.         run: python -m pytest sandbox/app -v
40.
41.       - name: Write job summary
42.         if: always()
43.         run: |
44.           echo "## CI Result" >> "$GITHUB_STEP_SUMMARY"
45.           echo "sandbox/app test suite ran — see the step above for pass/fail detail." >> "$GITHUB_STEP_SUMMARY"
```
