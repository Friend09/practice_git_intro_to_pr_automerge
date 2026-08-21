# Chapter 08: Actions Anatomy

**Reading Time:** ~40 minutes
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

## 7. Reading `ci.yml` as a Worked Example

This repo's actual `.github/workflows/ci.yml` — the workflow Gate 2 (Chapter 15) reads the
conclusion of — has exactly one job (`test`) with five steps: checkout, set up Python, install
pytest, run the sandbox app's test suite, and write a job summary. Reading it against this
chapter's vocabulary:

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
something's missing, that's a gap in your parsing, not the file.

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
