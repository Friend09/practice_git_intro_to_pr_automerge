# Chapter 10: Contexts, Expressions, Outputs & `needs`

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 09 (The Event Model)
**Practice Notebook:** `notebooks/practice_10.ipynb`
**Reference Notebook:** `notebooks/lab_10_job_outputs.ipynb`
**Script:** `labs/lab_10_job_outputs.py`
**Doc Reference:** GitHub Docs "Understanding GitHub Actions" (contexts, expressions)
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8 — contexts, `${{ }}` expressions, and the `needs`/outputs
mechanism, in that order.

**What to SKIP on first read:** Section 11 (the full context object list beyond `github` and
`needs`). Return once you need `runner.*` or `matrix.*` specifically.

**Key concepts in plain English:**

- **Context:** A structured object (`github`, `needs`, `steps`, `env`, ...) Actions exposes inside
  `${{ }}` expressions, populated with information about the current run.
- **Expression (`${{ }}`):** GitHub Actions' own small expression language — comparisons, boolean
  logic, string functions — evaluated wherever it appears in a workflow file, not real code.
- **Status function:** `success()`, `failure()`, `cancelled()`, `always()` — four built-in functions
  that answer "what's the job's status so far," usable inside `if:` conditions.
- **`needs`:** A job-level declaration that this job must wait for one or more other jobs, and (as
  a side effect) grants access to `needs.<job_id>.outputs.<name>`.
- **Job output:** A named value one job explicitly publishes (via `$GITHUB_OUTPUT`) so a downstream
  job can read it through `needs` — the *only* way jobs pass data to each other (Chapter 08 §12).

**Your prior knowledge connection:** If you've ever used template interpolation in Jinja2, Go
templates, or a CI system's own `${VAR}` substitution, `${{ }}` expressions will feel structurally
familiar — GitHub Actions' vocabulary and function set are just its own.

---

> **🔬 Automation Engineer's Lens:** `github.sha` inside a `pull_request`-triggered workflow is the
> single most common "which commit is this actually testing" bug source in this entire domain — it
> resolves to the synthetic merge commit (Chapter 02 §13), not the PR author's own commit. Any gate
> that logs, comments on, or scores "commit `github.sha`" without knowing this is reporting the
> wrong SHA to a human reading that output later.

---

> **🚦 Native vs Custom:** Contexts, expressions, and the `needs`/outputs mechanism are 100% native
> — GitHub populates and evaluates all of it; you write no interpreter. What you build is correct
> *usage*: choosing the right context field, writing an `if:` condition that means what you think it
> means, and deciding what data actually needs to cross the job boundary via `needs`.

---

## What You'll Learn

- What a context is, and the difference between `github`, `needs`, `steps`, and `env`
- How `${{ }}` expressions are evaluated, and that they are not Python or JavaScript
- The four status functions and exactly when each one runs
- Why `github.sha` in a `pull_request` trigger is the merge commit, not the author's commit
- How a job publishes an output and a downstream job reads it via `needs.<job>.outputs.<name>`
- How this repo's own gates would compose their outputs into a single merge decision

---

## Table of Contents

- [Chapter 10: Contexts, Expressions, Outputs \& `needs`](#chapter-10-contexts-expressions-outputs--needs)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What a Context Actually Is](#1-what-a-context-actually-is)
  - [2. The `github` Context](#2-the-github-context)
  - [3. `${{ }}`: A Small Expression Language, Not Real Code](#3--a-small-expression-language-not-real-code)
  - [4. The Four Status Functions](#4-the-four-status-functions)
  - [5. Where Expressions Are Allowed](#5-where-expressions-are-allowed)
  - [6. Job Outputs: Publishing a Value](#6-job-outputs-publishing-a-value)
  - [7. `needs`: Ordering Plus Data Access](#7-needs-ordering-plus-data-access)
  - [8. Putting It Together: A Two-Job Pipeline](#8-putting-it-together-a-two-job-pipeline)
  - [9. ⚠️ ADVANCED: Expression Type Coercion Surprises](#9-️-advanced-expression-type-coercion-surprises)
  - [10. ⚠️ ADVANCED: `env` Context vs Shell Environment Variables](#10-️-advanced-env-context-vs-shell-environment-variables)
  - [11. ⚠️ ADVANCED: The Full Context List](#11-️-advanced-the-full-context-list)
  - [12. Case Study: A Comment Posted Against the Wrong SHA](#12-case-study-a-comment-posted-against-the-wrong-sha)
  - [13. Case Study: Composing Three Gates' Outputs Into One Decision](#13-case-study-composing-three-gates-outputs-into-one-decision)
  - [14. Practical Tips: Debugging an Expression](#14-practical-tips-debugging-an-expression)
  - [15. Your First Project: Print Every Context Field You'll Actually Use](#15-your-first-project-print-every-context-field-youll-actually-use)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 11 — Tokens \& Permissions](#18-whats-next-chapter-11--tokens--permissions)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Contexts, Status Functions, and Needs/Outputs (from Section 15)](#a1--contexts-status-functions-and-needsoutputs-from-section-15)

---

## 1. What a Context Actually Is

A context is a structured, read-only object GitHub populates for the duration of a run, accessible
from `${{ }}` expressions anywhere a workflow file allows them. `github`, `needs`, `steps`, `env`,
`job`, `runner`, and `matrix` are the contexts this curriculum touches; each one holds a different
slice of "what's true about this run right now."

## 2. The `github` Context

`github` carries event and run metadata: `github.sha`, `github.event` (the full webhook payload for
whatever triggered this run), `github.actor`, `github.run_id`, and dozens more. For a
`pull_request`-triggered run specifically, `github.event.pull_request` holds the entire PR object
from Chapter 02 — `github.event.pull_request.head.sha`, `.base.ref`, `.number`, all directly
addressable.

```
github.sha                              → the SYNTHETIC MERGE COMMIT (pull_request trigger)
github.event.pull_request.head.sha      → the PR AUTHOR'S actual commit
github.event.pull_request.base.ref      → "main"
```

## 3. `${{ }}`: A Small Expression Language, Not Real Code

```yaml
if: ${{ github.event.pull_request.base.ref == 'main' }}
```

`${{ }}` expressions support comparisons (`==`, `!=`, `<`, `>`), boolean operators (`&&`, `||`,
`!`), a handful of built-in functions (`contains()`, `startsWith()`, `format()`, the four status
functions in Section 4), and literal values. It is **not** Python, JavaScript, or any general-
purpose language — there's no loop construct, no arbitrary function definition, nothing beyond this
fixed, deliberately small vocabulary. Note also that inside an `if:` at the top level, the `${{ }}`
wrapper is optional — `if: github.event.pull_request.base.ref == 'main'` means the same thing.

## 4. The Four Status Functions

| Function | Runs when | Setup Effort |
| --- | --- | --- |
| `success()` | Every previous step/job in scope succeeded (this is the **default** condition when no `if:` is present at all) | Minimal — implicit unless overridden |
| `failure()` | Any previous step/job in scope failed | Minimal — explicit opt-in to run on failure |
| `cancelled()` | The run was cancelled | Minimal |
| `always()` | Unconditionally — regardless of prior status | Minimal — but be deliberate, this bypasses the implicit success-only default |

A step with no `if:` at all behaves as though `if: success()` were present — this is why a failed
step normally skips everything after it, and why `ci.yml`'s job-summary step (Chapter 08 §9) needs
`if: always()` explicitly to still run after a test failure.

## 5. Where Expressions Are Allowed

Expressions can appear in `if:`, `env:` values, `with:` input values, job/step `name:` fields, and
matrix definitions — essentially anywhere a workflow needs a value computed from run-time
information rather than hardcoded at authoring time. They are evaluated by GitHub's own workflow
engine before the relevant step runs, not by the runner's shell.

## 6. Job Outputs: Publishing a Value

A step publishes an output by writing to the `$GITHUB_OUTPUT` file:

```bash
echo "risk_score=66.0" >> "$GITHUB_OUTPUT"
```

The job then re-exposes that step's output at the job level:

```yaml
jobs:
  gate3:
    outputs:
      risk_score: ${{ steps.score.outputs.risk_score }}
    steps:
      - id: score
        run: echo "risk_score=66.0" >> "$GITHUB_OUTPUT"
```

Without this explicit two-step re-exposure (step output → job output), the value never leaves the
job's own runner — this is the mechanism Chapter 08 §12 promised existed for passing data between
otherwise-isolated jobs.

## 7. `needs`: Ordering Plus Data Access

```yaml
jobs:
  gate3:
    outputs:
      risk_score: ${{ steps.score.outputs.risk_score }}
    steps: [...]

  automerge:
    needs: gate3
    if: needs.gate3.outputs.risk_score <= 70
    steps: [...]
```

`needs: gate3` does two things at once: it makes `automerge` wait until `gate3` finishes (jobs
without `needs` run in parallel, Chapter 08 §3), and it grants `automerge` read access to
`needs.gate3.outputs.risk_score` — the value `gate3` published in Section 6. Neither effect happens
without the other; `needs` is the single declaration that buys both ordering and data access.

## 8. Putting It Together: A Two-Job Pipeline

```
job "gate3"                                  job "automerge"  (needs: gate3)
    │                                                 │
    step "score" writes $GITHUB_OUTPUT               waits for gate3 to finish
        risk_score=66.0                                │
    │                                                 │
    job output: risk_score = 66.0  ────────────▶  needs.gate3.outputs.risk_score = "66.0"
                                                        │
                                                    if: needs.gate3.outputs.risk_score <= 70
                                                        → true → this job's steps run
```

Note the value arrives as a **string** (`"66.0"`, not the float `66.0`) — Section 9 covers why this
matters.

## 9. ⚠️ ADVANCED: Expression Type Coercion Surprises

> ⚠️ **ADVANCED TOPIC:** Why `needs.*.outputs.*` values are always strings, and what that does to
> comparisons.
> **Skip on first read** — return the first time a numeric comparison in `if:` behaves oddly.

Every job output and every `github.event.*` field arriving through JSON is, structurally, a string
once inside expression evaluation — GitHub Actions' expression language does perform numeric
coercion for comparisons like `<=`, so `needs.gate3.outputs.risk_score <= 70` does work as expected
for well-formed numeric strings. But a subtly malformed value (empty string, or a value with
trailing whitespace from a careless `echo`) can silently fail to coerce the way you'd expect,
producing a comparison result that's neither obviously true nor obviously false in the workflow
log. Always test a numeric job output against edge-case values (empty, zero, negative) before
trusting it downstream.

## 10. ⚠️ ADVANCED: `env` Context vs Shell Environment Variables

> ⚠️ **ADVANCED TOPIC:** Two different things that look similar: the `env` context and actual shell
> environment variables.
> **Skip on first read.**

`${{ env.MY_VAR }}` (the `env` *context*, evaluated by GitHub's expression engine before the step
runs) and `$MY_VAR` (a real shell environment variable, expanded by the runner's shell *while* the
step runs) are populated from the same `env:` block but resolved at different times by different
systems. A workflow that mixes them inconsistently — using `${{ env.X }}` where `$X` was needed, or
vice versa — is a frequent source of "why is this blank" confusion, because one resolves before the
step starts and the other resolves during it.

## 11. ⚠️ ADVANCED: The Full Context List

> ⚠️ **ADVANCED TOPIC:** Contexts beyond `github` and `needs`.
> **Skip on first read** — return once a workflow you're writing needs `matrix.*` or `runner.*`
> specifically.

Beyond `github`, `needs`, `steps`, and `env` (this chapter's focus), GitHub Actions also exposes
`job` (the current job's own status/services), `jobs` (reusable-workflow context, Chapter 21),
`runner` (OS, architecture, temp directory of the current runner), `secrets` (declared secret
values, never logged), `strategy` and `matrix` (Chapter 08 §11's matrix build parameters), and
`inputs` (values passed to a reusable workflow or `workflow_dispatch`). None of this repo's five
real workflows need `matrix` or reusable-workflow contexts; they're documented here for
completeness.

## 12. Case Study: A Comment Posted Against the Wrong SHA

A gate publishes a PR comment using `github.sha` to identify "the commit this result is for,"
inside a `pull_request`-triggered workflow. A reviewer, checking that SHA against the PR's own
commit list, can't find it — because `github.sha` here is the synthetic merge commit (Section 2),
which never appears in the PR's actual commit history at all. The fix is one field:
`github.event.pull_request.head.sha` — this repo's own Gate 3 workflow uses exactly this field when
identifying which commit its risk score applies to, specifically to avoid this confusion.

## 13. Case Study: Composing Three Gates' Outputs Into One Decision

This chapter's `needs`/outputs mechanism is exactly how a real multi-job airlock *could* be
structured: Gate 1, Gate 2, and Gate 3 each as jobs with `outputs: {status: ...}`, and a final
`decide` job with `needs: [gate1, gate2, gate3]` reading all three via
`needs.gate1.outputs.status`, `needs.gate2.outputs.status`, `needs.gate3.outputs.status`. This
repo's actual design (Chapter 17) instead uses required status checks plus native auto-merge rather
than a single composing job — but the `needs`/outputs pattern shown here is the general-purpose
tool for any pipeline that *does* want to compose multiple jobs' verdicts inside one workflow run.

## 14. Practical Tips: Debugging an Expression

```
An if: condition isn't behaving as expected
──────────────────────────────────────────────
[ ] Add a debug step: run: echo "value is '${{ needs.job.outputs.x }}'"
    -- quote it, so an empty/whitespace value is visible in the log
[ ] Check: is this the FIRST hop or a later one, if it's a workflow_run chain? (Ch 09 §8)
[ ] Confirm the producing job actually re-exposed the step output at the job level (Section 6)
[ ] Remember: no if: at all means an implicit if: success() -- a failed prior step silently
    skips everything after it unless always()/failure() is explicit
```

## 15. Your First Project: Print Every Context Field You'll Actually Use

For any workflow you're about to write, list every `${{ }}` expression you expect to need *before*
writing the YAML, and confirm each field's exact path against the GitHub Docs context reference.
This chapter's lab script does the same exercise against a representative `github` context —
resolve each path and confirm the value is what Section 2's table predicts.

## 16. Common Pitfalls & Misconceptions

1. **"`${{ }}` expressions are just JavaScript."** No — it's a small, fixed, purpose-built language
   with no loops, no arbitrary function definitions, and specific coercion rules of its own.

2. **"`github.sha` is always the commit I actually care about."** Not in a `pull_request` trigger —
   it's the synthetic merge commit. Use `github.event.pull_request.head.sha` for the author's real
   commit.

3. **"A step runs unless I add `if: false`."** No — a *failed* prior step silently skips every
   subsequent step by default (the implicit `if: success()`), with no explicit `if:` needed to
   cause that skip.

4. **"Job outputs are typed the way I wrote them."** No — everything crossing the `needs.*.outputs`
   boundary is a string; comparisons coerce, but malformed values can fail silently (Section 9).

5. **"`env.X` and `$X` are the same thing, evaluated the same way."** No — one is a context resolved
   by GitHub's engine before the step runs; the other is a real shell variable expanded during the
   step (Section 10).

## 17. Key Takeaways

- **A context is a structured, read-only object populated per-run** — `github`, `needs`, `steps`,
  `env` are the ones this curriculum uses.
- **`${{ }}` is a small expression language**, not a general-purpose one — comparisons, booleans, a
  fixed function set.
- **`github.sha` in a `pull_request` trigger is the merge commit, not the author's commit** — the
  single most common source of "wrong SHA" bugs in this domain.
- **The implicit condition on any step with no `if:` is `success()`** — a failure upstream silently
  skips everything after it unless `always()`/`failure()` says otherwise.
- **`needs` buys both ordering and data access at once** — a job can only read another job's
  outputs if it also declares `needs` on it.

## 18. What's Next: Chapter 11 — Tokens & Permissions

Chapter 11 covers the identity every one of these context values and expressions runs *as* —
`GITHUB_TOKEN`'s scoped permissions, the no-downstream-trigger rule from Chapter 09 §9 in full
depth, and when a PAT or App token is actually required.

[→ Chapter 11: Tokens & Permissions](chapter_11_tokens_and_permissions.md)

## 19. Additional Resources

- **GitHub Docs, "Accessing contextual information about workflow runs"** — https://docs.github.com/en/actions/learn-github-actions/contexts (fetched 2026-08)
- **GitHub Docs, "Evaluate expressions in workflows and actions"** — https://docs.github.com/en/actions/learn-github-actions/expressions (fetched 2026-08)
- **GitHub Docs, "Defining outputs for jobs"** — https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs (fetched 2026-08)
- **GitHub Docs, "Workflow syntax for GitHub Actions"** — https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idneeds (fetched 2026-08) — see `needs`

## 20. Appendix A — Code Index

### A.1 — Contexts, Status Functions, and Needs/Outputs (from Section 15)

**What the code does:** Resolves dotted paths against a representative `github` context, evaluates
the four status functions against a simulated job status, and simulates a job publishing an output
a downstream job reads via `needs`.

**ASCII flowchart:**

```
resolve_context_path(github_context, "event.pull_request.head.sha") → the author's real SHA

evaluate_status_function("failure", job_status="failure") → True
evaluate_status_function("success", job_status="failure") → False

simulate_needs_output_passing(risk_score=66.0, threshold=70.0)
    → {"gate3_outputs": {"risk_score": "66.0"}, "downstream_would_run": True}
```

See `labs/lab_10_job_outputs.py` for the full runnable version.
