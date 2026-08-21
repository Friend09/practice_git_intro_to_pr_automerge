# Chapter 12: Status Checks, Check Runs & Commit Statuses

**Reading Time:** ~40 minutes
**Prerequisites:** Chapter 11 (Tokens & Permissions)
**Practice Notebook:** `notebooks/practice_12.ipynb`
**Reference Notebook:** `notebooks/lab_12_check_runs.ipynb`
**Script:** `labs/lab_12_check_runs.py`
**Doc Reference:** GitHub Docs "About status checks"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–6 — the two publishing APIs and how each connects back to
required-check matching from Chapter 05.

**What to SKIP on first read:** Section 10 (check-run annotations). Return once you're publishing
line-level feedback, not just a pass/fail verdict.

**Key concepts in plain English:**

- **Status check:** The umbrella term for "a named pass/fail signal attached to a commit" — the
  thing branch protection actually requires (Chapter 05).
- **Commit Status API:** The older of the two ways to publish a status check — one state, one short
  description, matched by a `context` string.
- **Checks API (check runs):** The newer, richer way — a title, a Markdown summary, optional
  line-level annotations, matched by a `name` string.
- **`status` vs `conclusion`:** Two separate fields on a check run — `status` tracks *progress*
  (`queued`/`in_progress`/`completed`); `conclusion` only has meaning once `status` is `completed`
  (`success`/`failure`/etc.).
- **Name matching:** Both APIs' published checks are matched against required-check names purely by
  string (Chapter 05 §2) — there's no structural link to a workflow file or job ID.

**Your prior knowledge connection:** If you've ever seen a green checkmark or red X next to a
commit on any Git hosting platform, you've seen a status check rendered — this chapter is about the
two APIs that produce that checkmark on GitHub specifically.

---

> **🔬 Automation Engineer's Lens:** A check run's `name` field is the single most silently
> breakable string in this entire curriculum. Rename a job in a workflow file, and the check it
> publishes gets a new name — branch protection's required-check list still references the *old*
> name, which now never reports again, and the PR is stuck "waiting" on a check that will never
> arrive. Nothing errors. Nothing warns you. The PR just never becomes mergeable, for a reason
> that isn't visible anywhere except "this required check has been pending forever."

---

> **🚦 Native vs Custom:** Both publishing APIs are entirely native — you call an endpoint, GitHub
> renders the result in the PR's UI and evaluates it against required-check requirements. What you
> build is the judgment: which API to use (Checks API, almost always, per Section 6), what SHA to
> publish against (always the real head SHA, Chapter 10 §12), and keeping the published name in
> sync with whatever string branch protection expects.

---

## What You'll Learn

- The difference between the Commit Status API and the Checks API, and why this repo uses the latter
- The `status` vs `conclusion` field distinction, and the full vocabulary of each
- How to publish a check run with `gh api`, matching this repo's actual gate workflows
- Why a job/workflow rename silently breaks required-check matching
- What check-run annotations are, for line-level feedback beyond a single title/summary
- How to diagnose a PR stuck "waiting" on a check that will never report

---

## Table of Contents

- [Chapter 12: Status Checks, Check Runs \& Commit Statuses](#chapter-12-status-checks-check-runs--commit-statuses)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. "Status Check" Is an Umbrella Term](#1-status-check-is-an-umbrella-term)
  - [2. Two APIs, One Job](#2-two-apis-one-job)
  - [3. The Commit Status API](#3-the-commit-status-api)
  - [4. The Checks API: `status` and `conclusion`](#4-the-checks-api-status-and-conclusion)
  - [5. Publishing a Check Run](#5-publishing-a-check-run)
  - [6. Why This Repo Uses the Checks API Exclusively](#6-why-this-repo-uses-the-checks-api-exclusively)
  - [7. Name Matching Ties Back to Chapter 05](#7-name-matching-ties-back-to-chapter-05)
  - [8. ⚠️ ADVANCED: In-Progress Check Runs](#8-️-advanced-in-progress-check-runs)
  - [9. ⚠️ ADVANCED: Who Can Publish a Check Run](#9-️-advanced-who-can-publish-a-check-run)
  - [10. ⚠️ ADVANCED: Annotations for Line-Level Feedback](#10-️-advanced-annotations-for-line-level-feedback)
  - [11. Case Study: A Renamed Job, A PR Stuck Forever](#11-case-study-a-renamed-job-a-pr-stuck-forever)
  - [12. Case Study: This Repo's Three Published Check Names](#12-case-study-this-repos-three-published-check-names)
  - [13. Practical Tips: Diagnosing a Perpetually-Pending Check](#13-practical-tips-diagnosing-a-perpetually-pending-check)
  - [14. Your First Project: Publish One Yourself](#14-your-first-project-publish-one-yourself)
  - [15. Your Second Project: Break the Name Match Deliberately](#15-your-second-project-break-the-name-match-deliberately)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 13 — Debugging Workflows That Didn't Fire](#18-whats-next-chapter-13--debugging-workflows-that-didnt-fire)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Publishing a Check Run (from Section 14)](#a1--publishing-a-check-run-from-section-14)

---

## 1. "Status Check" Is an Umbrella Term

"Status check" (as used throughout Chapter 05) refers to *any* named pass/fail signal attached to a
commit, regardless of which of the two publishing APIs produced it. Branch protection's required-
check list doesn't care which API a check came from — it matches on name, full stop.

## 2. Two APIs, One Job

```
Commit Status API (older)              Checks API / "check runs" (newer)
POST /repos/{o}/{r}/statuses/{sha}     POST /repos/{o}/{r}/check-runs
        │                                       │
        ▼                                       ▼
  state + short description string      status + conclusion + title + Markdown summary
  matched by "context"                   matched by "name"
```

Both end up rendered in the same place in GitHub's UI (the PR's checks list) and both are eligible
to be required checks. The Checks API is strictly richer.

## 3. The Commit Status API

```bash
gh api -X POST repos/owner/name/statuses/<sha> \
  -f state=success \
  -f context=my-check \
  -f description="Looks good"
```

One of four states (`error`, `failure`, `pending`, `success`), one short description string,
matched against required checks by the `context` field. This is the older, simpler API — still
fully supported, but with no equivalent to a Markdown summary or line annotations.

## 4. The Checks API: `status` and `conclusion`

The Checks API separates *progress* from *outcome* — two independent fields:

```
status:      queued  →  in_progress  →  completed
                                            │
conclusion (only meaningful once completed):
  success | failure | neutral | cancelled | skipped | timed_out | action_required
```

A check run can sit in `in_progress` for as long as the work takes, then transition to `completed`
with exactly one conclusion. Publishing `status=completed` and a `conclusion` in the same call (as
this repo's gates all do — Section 5) skips the `in_progress` phase entirely for a check that
finishes fast enough not to need it.

## 5. Publishing a Check Run

```bash
gh api repos/owner/name/check-runs \
  -f name=gate3-risk-score \
  -f head_sha=<the PR's real head sha> \
  -f status=completed \
  -f conclusion=success
```

Every gate workflow in this repo makes exactly this call (with richer `output.title` /
`output.summary` fields for the human-readable detail shown in the PR's checks tab). The `head_sha`
here must be the PR's actual head commit — Chapter 10 §12 already covered what goes wrong when a
gate accidentally publishes against `github.sha` (the synthetic merge commit) instead.

## 6. Why This Repo Uses the Checks API Exclusively

The Checks API's richer output (a Markdown summary, not just one short string) is what lets Gate 3
show its full worked risk-scoring math directly in the PR's checks tab rather than only in a
separate comment. The Commit Status API's one-line description simply can't carry that much
information. There's no scenario in this repo's design where the older API's simplicity is worth
losing that.

## 7. Name Matching Ties Back to Chapter 05

Recall from Chapter 05 §2: a required status check is matched purely by string name, not by
workflow file or job ID. That principle applies identically here — a check run's `name` field
(`"gate3-risk-score"`, in this repo's case) is exactly the string branch protection's
`required_status_checks.contexts` list must contain. Nothing about *how* the check was published
(Commit Status API or Checks API) changes this matching rule.

## 8. ⚠️ ADVANCED: In-Progress Check Runs

> ⚠️ **ADVANCED TOPIC:** Publishing a check run before the work finishes.
> **Skip on first read** — this repo's gates all publish `completed` in a single call.

For work that takes longer than a single API call's worth of time, a check run can be created with
`status=queued`, updated to `status=in_progress`, and finally updated to `status=completed` with a
`conclusion` — three separate calls against the same check run's `id`, giving a human watching the
PR live progress feedback rather than a single before/after jump. None of this repo's gates need
this pattern since each gate's own computation (reading PR metadata, scoring) completes well within
one workflow step.

## 9. ⚠️ ADVANCED: Who Can Publish a Check Run

> ⚠️ **ADVANCED TOPIC:** A permission detail that trips people up moving from statuses to checks.
> **Skip on first read.**

The Checks API historically required the publishing identity to be a GitHub App (not a plain PAT)
— `GITHUB_TOKEN` (which runs *as* a GitHub App-like identity internally) and App installation
tokens can publish check runs directly; a classic PAT acting as a human user has more restricted
check-run creation rights in some contexts. `checks: write` in a workflow's `permissions:` block is
what this repo's gates rely on — verified working with plain `GITHUB_TOKEN` throughout this repo's
own live testing.

## 10. ⚠️ ADVANCED: Annotations for Line-Level Feedback

> ⚠️ **ADVANCED TOPIC:** Attaching feedback to specific lines of a diff, not just the PR overall.
> **Skip on first read** — this repo's gates publish a PR-level verdict, not per-line feedback.

The Checks API supports `output.annotations` — up to 50 per API call, each naming a file path,
line range, severity (`notice`/`warning`/`failure`), and message, rendered inline in the PR's
"Files changed" view exactly like a human reviewer's line comment. A linter or static-analysis gate
would use this; this curriculum's three gates operate on whole-PR properties (size, CI conclusion,
critical-path hits) rather than specific lines, so none of them need it.

## 11. Case Study: A Renamed Job, A PR Stuck Forever

A team renames a workflow's job from `risk-score` to `gate3-risk-score` for clarity, without
updating branch protection's required-check list (still expecting `risk-score`). The new check
publishes successfully, under its new name — but branch protection is still waiting for a check
named `risk-score` that will never arrive again. Every subsequent PR sits with a permanently
pending required check, no error message anywhere, until someone notices the mismatch and either
renames the job back or updates the required-check list to match. This is exactly the failure mode
Chapter 05 §2 warned about, now with a concrete trigger (a rename) attached.

## 12. Case Study: This Repo's Three Published Check Names

This repo's own branch protection requires exactly three check names: `test` (published by
`ci.yml`'s job, via the older mechanism GitHub uses for workflow job results directly),
`gate2-pr-health`, and `gate3-risk-score` (both published explicitly via the Checks API, matching
this chapter's Section 5 pattern). Renaming any of `gate2-pr-health.yml`'s or `gate3-score.yml`'s
published check name without updating branch protection would reproduce Section 11's exact failure
— a fact worth remembering before ever touching those workflow files.

## 13. Practical Tips: Diagnosing a Perpetually-Pending Check

```
A required check has been "pending" for a long time -- why?
──────────────────────────────────────────────────────────────
[ ] Did the workflow that's SUPPOSED to publish it actually run at all? (Chapter 13)
[ ] Compare the EXACT string in branch protection's required list against the
    EXACT name/context the workflow publishes -- case-sensitive, no trailing spaces
[ ] Was the publishing job/workflow recently renamed? (Section 11 -- the most common cause)
[ ] Check the workflow's own run log -- did the publish step itself error?
```

## 14. Your First Project: Publish One Yourself

Against a real commit on a repo you control:

```bash
gh api repos/<owner>/<repo>/check-runs \
  -f name=my-first-check \
  -f head_sha=$(git rev-parse HEAD) \
  -f status=completed \
  -f conclusion=success
```

Then look at the commit in GitHub's UI and confirm your check appears, exactly as this chapter's
lab script does in fixture mode.

## 15. Your Second Project: Break the Name Match Deliberately

On a disposable branch protection setup: register `my-check` as a required check, publish a check
run named `my-check-v2` instead, and watch the PR sit blocked with no error anywhere except "1
required check has not completed." This is Section 11's failure mode, deliberately reproduced —
the fastest way to internalize why the exact-string-match rule matters.

## 16. Common Pitfalls & Misconceptions

1. **"The Commit Status API and Checks API are the same thing under different names."** No — they're
   two separate APIs with different field shapes; only the Checks API supports Markdown summaries
   and line annotations.

2. **"`status` and `conclusion` are the same field."** No — `status` tracks progress
   (queued/in_progress/completed); `conclusion` is the outcome, meaningful only once `status` is
   `completed`.

3. **"A check run is tied to the job that created it."** No — matching is purely by the `name`
   string (Chapter 05 §2 again), with no structural link back to any specific job or workflow.

4. **"If a required check never reports, GitHub will tell me why."** No — the PR just shows the
   check as permanently pending. There's no automatic detection of "this required check name will
   never be published by anything."

5. **"Any token can publish a check run."** Mostly yes with `checks: write`, but Section 9 covers a
   real permission nuance around PATs specifically — verify with the identity you're actually
   using.

## 17. Key Takeaways

- **"Status check" is the umbrella term** — two distinct APIs (Commit Status, Checks) both produce
  one.
- **The Checks API is strictly richer** — Markdown summaries and line annotations the older API
  can't express — and it's what every gate in this repo uses.
- **`status` and `conclusion` are separate fields** — progress vs outcome, not interchangeable.
- **Name matching is purely string-based**, identical to required-check matching from Chapter 05 —
  a rename silently orphans the required-check requirement, with no error anywhere.
- **Always publish against the real head SHA**, never the synthetic merge commit (Chapter 10 §12).

## 18. What's Next: Chapter 13 — Debugging Workflows That Didn't Fire

Chapter 13 covers the other half of "why is this check pending forever" — cases where the
publishing workflow never ran *at all*, and how to diagnose that from the Actions UI and logs.

[→ Chapter 13: Debugging Workflows That Didn't Fire](chapter_13_debugging_workflows.md)

## 19. Additional Resources

- **GitHub Docs, "About status checks"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks (fetched 2026-08)
- **GitHub REST API, "Checks"** — https://docs.github.com/en/rest/checks/runs (fetched 2026-08)
- **GitHub REST API, "Commit statuses"** — https://docs.github.com/en/rest/commits/statuses (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Publishing a Check Run (from Section 14)

**What the code does:** Publishes a completed check run with a `success` conclusion, and returns
the two-API comparison table as structured data.

**ASCII flowchart:**

```
publish_check_run(repo, head_sha, name, conclusion, title, summary)
        │
        ▼
POST /repos/{o}/{r}/check-runs → {"id": ..., "name": ..., "status": "completed", "conclusion": ...}
```

See `labs/lab_12_check_runs.py` for the full runnable version.
