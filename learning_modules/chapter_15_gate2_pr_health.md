# Chapter 15: Gate 2 — PR Health

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 12 (Status Checks), Chapter 08 (Actions Anatomy)
**Practice Notebook:** `notebooks/practice_15.ipynb`
**Reference Notebook:** `notebooks/lab_15_pr_health.ipynb`
**Script:** `labs/lab_15_pr_health.py`
**Doc Reference:** This repo's own design -- no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 — how Gate 2 reads CI's conclusion, and why the trigger
choice (`workflow_run`, not `pull_request`) is deliberate.

**What to SKIP on first read:** Section 10 (the fail-open POC comparison, in full code detail).
Chapter 01 §3 already gave you the concept; return here for the exact code contrast.

**Key concepts in plain English:**

- **Gate 2:** The second airlock door (Chapter 01 §4) — did *this specific PR's* CI build actually
  succeed?
- **Fail-closed:** A missing CI result is treated identically to a failed one — never as "skip this
  check."
- **`workflow_run` off CI:** Gate 2 doesn't run on `pull_request` directly — it listens for CI's own
  completion, so it always has a real conclusion to read, never a guess about whether CI has
  finished yet.
- **First-hop reliability:** Gate 2 is exactly one `workflow_run` hop deep (listening to CI, which
  is itself `pull_request`-triggered) — the one configuration where `head_sha` is guaranteed
  correct (Chapter 09 §8).
- **`evaluate_gate2`:** The pure function taking one nullable string (`ci_conclusion`) and returning
  a typed `GateResult` — already implemented and live-verified in `pr_automerge.gates`.

**Your prior knowledge connection:** If you've ever configured a deploy pipeline to block on "the
test stage passed," Gate 2 is exactly that gate, specialized to GitHub's status-check vocabulary and
made deliberately strict about what counts as "passed."

---

> **🔬 Automation Engineer's Lens:** Gate 2 is this curriculum's cleanest illustration of Chapter
> 01's whole thesis. `evaluate_gate2`'s entire behavior fits in one sentence: `success` passes,
> literally everything else — including `None` — fails. There's no branch, no exception, no
> "we'll assume it's fine" fallback anywhere in the logic. That's not a simplification; it's the
> point. An airlock door that asks a nuanced question is a door someone can talk their way through.

---

> **🚦 Native vs Custom:** CI running and reporting its own conclusion is 100% native GitHub
> Actions. `workflow_run` firing when CI completes is 100% native. What you build is the
> **interpretation**: `evaluate_gate2`'s fail-closed logic is the one piece of judgment in this
> entire gate, and it's a deliberate, documented departure from the fail-open prior art
> (Section 10).

---

## What You'll Learn

- What Gate 2 checks, and why it's scoped to exactly one PR's CI result
- Why Gate 2 triggers on `workflow_run` off CI rather than directly on `pull_request`
- The full fail-closed contract: `success` passes, everything else — including missing — fails
- How this inverts the prior-art POC's fail-open `skip` handling, concretely
- How `pr_automerge.gates.evaluate_gate2` composes with a real CI-conclusion fetch
- Why Gate 2 never needs to worry about the `workflow_run` second-hop collapse (Chapter 09 §8)

---

## Table of Contents

- [Chapter 15: Gate 2 — PR Health](#chapter-15-gate-2--pr-health)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What Question Gate 2 Answers](#1-what-question-gate-2-answers)
  - [2. The Fail-Closed Contract, Exactly](#2-the-fail-closed-contract-exactly)
  - [3. Why `workflow_run` Off CI, Not `pull_request` Directly](#3-why-workflow_run-off-ci-not-pull_request-directly)
  - [4. Gate 2 Is Exactly One Hop Deep](#4-gate-2-is-exactly-one-hop-deep)
  - [5. Reading the Conclusion](#5-reading-the-conclusion)
  - [6. `pr_automerge.gates.evaluate_gate2`, the Engine](#6-pr_automergegatesevaluate_gate2-the-engine)
  - [7. Publishing Gate 2's Own Check Run](#7-publishing-gate-2s-own-check-run)
  - [8. ⚠️ ADVANCED: The `if:` Filter on `workflow_run.event`](#8-️-advanced-the-if-filter-on-workflow_runevent)
  - [9. ⚠️ ADVANCED: What "Conclusion" Values Actually Arrive](#9-️-advanced-what-conclusion-values-actually-arrive)
  - [10. ⚠️ ADVANCED: The Fail-Open POC, Side by Side](#10-️-advanced-the-fail-open-poc-side-by-side)
  - [11. Case Study: A Crashed Scanner That Would Have Scored Higher](#11-case-study-a-crashed-scanner-that-would-have-scored-higher)
  - [12. Case Study: Gate 2 and Gate 3 Running in Parallel](#12-case-study-gate-2-and-gate-3-running-in-parallel)
  - [13. Practical Tips: Reading `gate2-pr-health.yml` End to End](#13-practical-tips-reading-gate2-pr-healthyml-end-to-end)
  - [14. Your First Project: Watch Gate 2 Fail-Closed, Live](#14-your-first-project-watch-gate-2-fail-closed-live)
  - [15. Your Second Project: Compose With Gate 1](#15-your-second-project-compose-with-gate-1)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 16 — Gate 3: Risk Scoring](#18-whats-next-chapter-16--gate-3-risk-scoring)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Fetching a Conclusion and Evaluating Gate 2 (from Section 14)](#a1--fetching-a-conclusion-and-evaluating-gate-2-from-section-14)

---

## 1. What Question Gate 2 Answers

Chapter 01 §4: "Did this specific PR's build succeed?" Unlike Gate 1 (repo-wide, checked
periodically), Gate 2 is inherently per-PR and per-commit — a new push means a new CI run means a
new question for Gate 2 to answer, every single time.

## 2. The Fail-Closed Contract, Exactly

```python
def evaluate_gate2(ci_conclusion: str | None) -> GateResult:
    if ci_conclusion == "success":
        return GateResult(..., status=GateStatus.PASS, ...)
    return GateResult(..., status=GateStatus.FAIL, ...)   # everything else, including None
```

There is no third branch. `"failure"` fails. `"cancelled"` fails. `"timed_out"` fails. `None` —
meaning no CI result has been published yet — fails, identically to an explicit failure. This is
Chapter 01's Airlock Principle rendered as the simplest possible function: one condition for pass,
everything else falls through to the same fail path.

## 3. Why `workflow_run` Off CI, Not `pull_request` Directly

If Gate 2 triggered directly on `pull_request`, it would need to somehow *wait* for CI to finish
before it could read a meaningful conclusion — CI and Gate 2 would be racing each other, both
firing on the same event, with no guarantee CI finishes first. Triggering on `workflow_run` off
CI's own completion (Chapter 09 §7) sidesteps the race entirely: Gate 2 only ever starts once CI
has already finished, so `github.event.workflow_run.conclusion` is always populated, never a guess
about timing.

## 4. Gate 2 Is Exactly One Hop Deep

Recall Chapter 09 §8's warning: `workflow_run`'s `head_sha` is reliable on the first hop, and
collapses on a second. Gate 2 is precisely one hop: CI is `pull_request`-triggered (hop zero, if you
like — the origin), and Gate 2 listens directly to CI's completion (hop one). Gate 2 never needs to
worry about the collapse, because nothing listens to *Gate 2's own* completion via a further
`workflow_run` — `automerge.yml` triggers independently on `pull_request` instead (Chapter 17), so
no second hop exists anywhere in this repo's actual chain.

## 5. Reading the Conclusion

```yaml
env:
  HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
  CI_CONCLUSION: ${{ github.event.workflow_run.conclusion }}
```

Both values come directly off the `workflow_run` event payload — no separate API call needed to
fetch them, since GitHub includes the triggering workflow's outcome directly in the event that
woke Gate 2 up. `HEAD_SHA` here is reliable per Section 4; `CI_CONCLUSION` is CI's own `conclusion`
field, using the exact vocabulary from Chapter 12 §4.

## 6. `pr_automerge.gates.evaluate_gate2`, the Engine

The real workflow's Python step imports and calls this function directly —
`from pr_automerge.gates import evaluate_gate2` — unlike Gate 1, whose shell-out script duplicates
its own inline logic (Chapter 14 §5). This means Gate 2's actual behavior *is* exactly what
`tests/test_gates.py` already verifies offline: `test_gate2_passes_on_success`,
`test_gate2_fails_on_explicit_failure`, `test_gate2_fails_closed_on_missing_conclusion` — the same
function, the same tests, the same guarantee, whether run in CI or in this chapter's lab.

## 7. Publishing Gate 2's Own Check Run

Gate 2 publishes its own verdict as a check run named `gate2-pr-health` (Chapter 12 §5's pattern
exactly), keyed against `HEAD_SHA` from Section 5 — never a guessed or recomputed SHA. This check
name is one of the three this repo's branch protection requires (Chapter 05 §3, Chapter 12 §12) —
renaming it without updating branch protection reproduces Chapter 12 §11's stuck-forever bug.

## 8. ⚠️ ADVANCED: The `if:` Filter on `workflow_run.event`

> ⚠️ **ADVANCED TOPIC:** Why Gate 2's job has `if: github.event.workflow_run.event == 'pull_request'`.
> **Skip on first read** — return once you're wiring `workflow_run` to a workflow with more than
> one possible upstream trigger.

CI itself can run from more than one trigger (`pull_request` and `workflow_dispatch`, per Chapter
08 §7). Gate 2 only cares about CI runs that were *themselves* triggered by a PR — a manually
dispatched CI run has no PR to score. The `if:` condition filters on
`github.event.workflow_run.event`, which names the ORIGINAL trigger that started the upstream
workflow, letting Gate 2 skip cleanly for non-PR CI runs instead of erroring on a missing PR
context.

## 9. ⚠️ ADVANCED: What "Conclusion" Values Actually Arrive

> ⚠️ **ADVANCED TOPIC:** The full set of values `workflow_run.conclusion` can hold.
> **Skip on first read.**

Beyond `success`/`failure`, a `workflow_run`'s conclusion can be `cancelled`, `skipped` (if the
upstream workflow's own trigger conditions caused it to skip entirely), `timed_out`, or
`action_required` (for workflows needing manual approval, e.g. from a first-time fork contributor).
`evaluate_gate2`'s contract handles all of these identically — none of them equal the string
`"success"`, so all of them fail. This is a deliberate simplification: Gate 2 doesn't need to
distinguish *why* CI didn't succeed, only that it didn't.

## 10. ⚠️ ADVANCED: The Fail-Open POC, Side by Side

> ⚠️ **ADVANCED TOPIC:** The exact prior-art contrast, in code.
> **Skip on first read** — Chapter 01 §3 already covered the concept; this section is the promised
> code-level detail.

The prior-art POC's `engine.py` computes `score = earned / applicable`, where a rule with no data
is marked `skip` and removed from *both* the numerator and denominator. Applied to a CI-style
blocker rule, a crashed scanner (no result) is `skip`ped — invisible to the score, not a penalty.
`evaluate_gate2` makes the opposite choice deliberately: there is no `skip` state in its output at
all (Chapter 01 §16.3) — `None` maps to `FAIL`, full stop, with the rationale string literally
appending `"— fail-closed"` so the reason is visible in every job summary and PR comment Gate 2
produces.

## 11. Case Study: A Crashed Scanner That Would Have Scored Higher

This is Chapter 01 §3's worked example, made concrete for Gate 2 specifically: imagine CI itself
crashes before producing any conclusion at all (a runner provisioning failure, say — genuinely
possible, not a made-up edge case). Under the fail-open POC's model, a missing blocker signal
doesn't penalize the score; under Gate 2's actual `evaluate_gate2`, `ci_conclusion=None` fails,
identically to an explicit `failure`. The PR simply cannot merge until CI actually reports
something — which is exactly the behavior you want from a system whose entire job is catching
exactly this kind of infrastructure failure before it reaches `main`.

## 12. Case Study: Gate 2 and Gate 3 Running in Parallel

Gate 2 (this chapter) and Gate 3 (Chapter 16) have no dependency on each other — Gate 3 triggers
directly on `pull_request` and only needs the PR's own metadata (Chapter 16 §3), while Gate 2 waits
on CI. Both can and do run concurrently; neither blocks the other from starting. `automerge.yml`
(Chapter 17) doesn't wait on either explicitly either — it relies on branch protection's required-
check list to hold the PR until *all three* named checks report, regardless of their relative
timing.

## 13. Practical Tips: Reading `gate2-pr-health.yml` End to End

```
Reading this repo's real Gate 2 workflow
──────────────────────────────────────────
[ ] on: workflow_run, workflows: ["CI"], types: [completed]  -- Section 3-4
[ ] permissions: checks: write, pull-requests: read
[ ] if: github.event.workflow_run.event == 'pull_request'    -- Section 8
[ ] Read HEAD_SHA and CI_CONCLUSION straight off the event payload -- Section 5
[ ] Call evaluate_gate2(conclusion) directly -- Section 6
[ ] Publish a check run named gate2-pr-health against HEAD_SHA -- Section 7
```

## 14. Your First Project: Watch Gate 2 Fail-Closed, Live

Against the sandbox repo: open a PR that touches `sandbox/**`, then cancel the CI run before it
finishes. Watch Gate 2's published check run report `failure`, with a rationale mentioning
"fail-closed" — the exact behavior this chapter's lab reproduces offline with `evaluate_gate2(None)`.

## 15. Your Second Project: Compose With Gate 1

Run this chapter's lab and Chapter 14's lab back to back against the same repo, and manually
combine their two `GateResult`s into a `Decision` (Chapter 01 §11's model) — confirm the merge
verdict is `True` only when *both* pass, previewing exactly what Chapter 17's real composition
does across all three gates.

## 16. Common Pitfalls & Misconceptions

1. **"Gate 2 races CI to see who finishes first."** No — triggering on `workflow_run` off CI's own
   completion means Gate 2 only ever starts after CI has already finished (Section 3).

2. **"A cancelled CI run is treated more leniently than a failed one."** No —
   `evaluate_gate2` treats every non-`success` value identically, including `cancelled` (Section 2).

3. **"Gate 2 needs to worry about the workflow_run second-hop SHA collapse."** No — it's exactly one
   hop deep, the one configuration where `head_sha` is guaranteed reliable (Section 4).

4. **"A missing CI result just means Gate 2 waits and re-checks later."** No — Gate 2 doesn't poll;
   it evaluates the conclusion it received once, and `None` fails immediately, by design.

5. **"Gate 2 and Gate 3 run in a fixed order."** No — they trigger independently and can run
   concurrently; only branch protection's required-check list enforces that both must eventually
   report success.

## 17. Key Takeaways

- **Gate 2 answers a per-PR, per-commit question**: did this specific build succeed?
- **The fail-closed contract has no third state** — `success` passes; everything else, including
  `None`, fails, with no `skip`.
- **`workflow_run` off CI avoids a race** and guarantees a real conclusion is always available when
  Gate 2 runs.
- **Gate 2 is exactly one hop deep** — the one `workflow_run` configuration immune to the SHA
  collapse from Chapter 09 §8.
- **This is the sharpest inversion of the fail-open prior art in the whole curriculum** — no `skip`
  state exists in `evaluate_gate2`'s output at all.

## 18. What's Next: Chapter 16 — Gate 3: Risk Scoring

Chapter 16 covers the third and final door: even with a ready repo and a green build, is this
diff's *size and shape* something safe to merge without a human looking — the pure-risk scoring
model this curriculum builds and calibrates in depth.

[→ Chapter 16: Gate 3 — Risk Scoring](chapter_16_gate3_risk_scoring.md)

## 19. Additional Resources

- **This repo's own** `.github/workflows/gate2-pr-health.yml` — the live, executing implementation this chapter describes
- **This repo's own** `pr_automerge/gates.py` — `evaluate_gate2`'s full docstring and implementation
- **This repo's own** `tests/test_gates.py` — the offline tests verifying the fail-closed contract
- **GitHub Docs, "Events that trigger workflows"** — https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Fetching a Conclusion and Evaluating Gate 2 (from Section 14)

**What the code does:** Fetches a named check's conclusion for a SHA and evaluates Gate 2 against
it, then separately evaluates the fail-closed path with no conclusion at all.

**ASCII flowchart:**

```
fetch_ci_conclusion(repo, sha) → "success" | "failure" | ... | None
        │
        ▼
evaluate_gate2(conclusion) → GateResult(PASS only if conclusion == "success")
```

See `labs/lab_15_pr_health.py` for the full runnable version.
