# Chapter 13: Debugging Workflows That Didn't Fire

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 09 (The Event Model), Chapter 11 (Tokens & Permissions)
**Practice Notebook:** `notebooks/practice_13.ipynb`
**Reference Notebook:** `notebooks/lab_13_why_no_trigger.ipynb`
**Script:** `labs/lab_13_why_no_trigger.py`
**Doc Reference:** GitHub Docs "Using workflow run logs"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Section 3, the ordered checklist — work it top to bottom against a real
silent workflow, and most of the rest of this chapter becomes reference material you consult in
passing.

**What to SKIP on first read:** Section 10 (fork PR restrictions in depth). Return only if you're
specifically debugging a fork-originated PR.

**Key concepts in plain English:**

- **"Didn't fire" vs "failed":** A workflow that *ran and failed* leaves a red X and logs to read. A
  workflow that *never ran at all* leaves nothing — no run, no log, no error — which is why this is
  a harder debugging category than an ordinary test failure.
- **Registration:** GitHub's process of reading a workflow file and making it eligible to respond to
  events — a file with a YAML/schema error can fail to register at all, silently.
  it's on.
- **Default-branch requirement:** `schedule` and some other triggers only ever read the workflow
  file as it exists on the repo's *default* branch — a schedule added only on a feature branch will
  never fire, ever.
- **Silent no-fire vs silent skip:** A trigger that doesn't match (wrong event, wrong path) produces
  *zero* trace anywhere in the Actions UI — distinct from a job that ran but was skipped by an
  `if:` condition, which at least shows up as "skipped" in the run log.

**Your prior knowledge connection:** If you've ever debugged a cron job that "just didn't run" with
no log file to check, this chapter's core frustration will be familiar — the absence of any error
is itself the whole problem.

---

> **🔬 Automation Engineer's Lens:** The most expensive class of Actions bug is the one that
> produces zero evidence. A failed job at least tells you it failed. A workflow that never fired
> tells you nothing — no run appears in the Actions tab, there's no log to open, and the PR just
> sits there. Every gate in this curriculum's own build process hit at least one silent no-fire
> during development; this chapter's checklist is built directly from diagnosing those.

---

> **🚦 Native vs Custom:** Diagnosis tooling here is a mix — the Actions UI (native) shows what
> *did* run; there's no native tool that shows what *should have* run but didn't. What you build is
> the checklist discipline (Section 3) and, for the trickiest cases, small scripts that replay a
> trigger's matching logic locally (this chapter's lab) before touching the real repo.

---

## What You'll Learn

- Why "didn't fire" produces zero trace, unlike a failed run
- The ordered checklist for diagnosing a silent workflow, from cheapest check to most expensive
- Why a YAML/schema error can fail an entire workflow's registration, not just one step
- The default-branch requirement for `schedule` and how it silently defeats feature-branch testing
- How to replay `paths:`/`branches:` filter matching against a real PR's changed files locally
- What's actually different about fork PRs that makes them a distinct diagnostic category

---

## Table of Contents

- [Chapter 13: Debugging Workflows That Didn't Fire](#chapter-13-debugging-workflows-that-didnt-fire)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Two Different Failure Categories](#1-two-different-failure-categories)
  - [2. Where "Didn't Fire" Leaves No Trace](#2-where-didnt-fire-leaves-no-trace)
  - [3. The Ordered Diagnostic Checklist](#3-the-ordered-diagnostic-checklist)
  - [4. Check 1: Does It Even Parse?](#4-check-1-does-it-even-parse)
  - [5. Check 2: Is It On the Default Branch?](#5-check-2-is-it-on-the-default-branch)
  - [6. Check 3: Does the Event Type Match?](#6-check-3-does-the-event-type-match)
  - [7. Check 4: Do `paths:`/`branches:` Filters Match?](#7-check-4-do-pathsbranches-filters-match)
  - [8. Check 5: Is the Workflow Disabled?](#8-check-5-is-the-workflow-disabled)
  - [9. ⚠️ ADVANCED: Replaying Filter Logic Locally](#9-️-advanced-replaying-filter-logic-locally)
    - [Debug Logging: When a Run Exists but Won't Explain Itself](#debug-logging-when-a-run-exists-but-wont-explain-itself)
  - [10. ⚠️ ADVANCED: Fork PR Restrictions](#10-️-advanced-fork-pr-restrictions)
  - [11. ⚠️ ADVANCED: Workflow Disabled Due to Inactivity](#11-️-advanced-workflow-disabled-due-to-inactivity)
  - [12. Case Study: A Schedule That Never Fired](#12-case-study-a-schedule-that-never-fired)
  - [13. Case Study: This Curriculum's Own Path-Filter Design](#13-case-study-this-curriculums-own-path-filter-design)
  - [14. Practical Tips: The Checklist, In Order](#14-practical-tips-the-checklist-in-order)
    - [Two Observability Shortcuts: Status Badges and Version-to-Run Mapping](#two-observability-shortcuts-status-badges-and-version-to-run-mapping)
  - [15. Your First Project: Deliberately Break Each Check](#15-your-first-project-deliberately-break-each-check)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 14 — Gate 1: Repo Readiness](#18-whats-next-chapter-14--gate-1-repo-readiness)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Three Diagnostics: Syntax, Path Filter, Event Match (from Section 15)](#a1--three-diagnostics-syntax-path-filter-event-match-from-section-15)

---

## 1. Two Different Failure Categories

```
"Ran and failed"                          "Never fired"
──────────────────                        ──────────────
A run appears in the Actions tab           NO run appears anywhere
Logs exist for every step                  No logs, because no run happened
Red X, clear error message                 Nothing -- just silence
Chapter 08/10's debugging tools apply       Requires checking the TRIGGER, not the run
```

This chapter is entirely about the second category — by far the more frustrating one, because
there's no artifact to start investigating from.

## 2. Where "Didn't Fire" Leaves No Trace

Unlike a job skipped by an `if:` condition (which still shows up in the run log as "skipped"), a
workflow whose *trigger* never matched produces no run at all. The Actions tab shows nothing for
this workflow at this point in time — not a skipped run, not a greyed-out entry, nothing. This is
the mechanical reason this category needs its own systematic checklist rather than "read the logs":
there are no logs.

## 3. The Ordered Diagnostic Checklist

```
[1] Does the workflow file parse as valid YAML at all?           (cheapest, check first)
[2] Is the workflow file on the DEFAULT branch?                   (schedule/workflow_dispatch need this)
[3] Does the fired event type match anything under on:?
[4] If on: has a paths: filter, does the changed-file set match a glob?
[5] If on: has a branches: filter, does the target branch match?
[6] Is the workflow disabled in the repo's Actions settings?
[7] Is this a fork PR hitting a restriction on secrets/workflow runs?   (most involved, check last)
```

Ordered cheapest-to-check first — Sections 4–8 walk through each in the same order.

## 4. Check 1: Does It Even Parse?

A YAML syntax error, or a value that's syntactically valid YAML but violates the workflow schema
(an unrecognized top-level key, a malformed `on:` block), typically means GitHub fails to register
the **entire workflow file** — not just the malformed section. `gh workflow list` and the Actions
tab's "..." menu on the workflow will show a parse-error indicator if this is the cause; `yamllint`
or a local `yaml.safe_load()` catches most syntax errors before you even push.

**Shown symptom.** Before: `gate2-pr-health.yml` is pushed to `main` with `jbos:` where `jobs:`
should be. The event fires → no run appears; the Actions tab instead shows this annotation on
the workflow:

```
Invalid workflow file: .github/workflows/gate2-pr-health.yml#L14
The workflow is not valid. .github/workflows/gate2-pr-health.yml
(Line: 14, Col: 1): Unexpected value 'jbos'
```

**What to notice:**

- The annotation names the exact file, line, and column — but it lives on the *workflow*, not on
  any run, because registration failed before any run could exist.
- One bad key failed the **whole file**: every trigger in it is dead until the parse error is fixed.

## 5. Check 2: Is It On the Default Branch?

`schedule` triggers (Chapter 09 §5) are read **only** from the default branch's copy of the
workflow file — adding or editing a cron schedule on a feature branch has zero effect until that
branch is merged. This single fact explains an entire category of "I added a schedule and it never
fires" reports: the schedule genuinely works, it's just reading a version of the file that doesn't
have your change yet.

**Shown symptom.** Before: the cron edit to `gate1-repo-health.yml` sits on a feature branch,
not yet merged to `main` (Section 12's case study). Days later:

```
$ gh run list --workflow=gate1-repo-health.yml --event=schedule
(no output — exit status 0)
```

**What to notice:**

- The command *succeeds* and prints nothing — zero scheduled runs is an empty list, not an
  error. Silence is the entire symptom.
- `--event=schedule` matters: manual `workflow_dispatch` test runs *can* run from any branch,
  and without the filter they mask the dead cron.

## 6. Check 3: Does the Event Type Match?

The most basic check, and the most commonly overlooked once you're deep into filter debugging:
confirm the event GitHub actually fired (visible in the repo's Events feed, or inferred from what
action was taken) is even listed under `on:` at all. A `push`-only workflow will never fire for a
PR event, however correctly everything else is configured.

**Shown symptom.** Before: a gate workflow declares `on: push` only. Opening PR #101
(`fix/readme-typo` → `main`) fires a `pull_request` event:

```
Event fired:            pull_request (action: opened)
Workflow's on: block:   on:
                          push:
                            paths: ['sandbox/**']
Result:                 no run created — event type not declared
```

**What to notice:**

- The `paths:` filter never even got consulted — event-type matching happens first, and
  `pull_request` is simply absent from `on:`.
- Opening a PR does not fire `push`; the push happened earlier, to the *head branch*.

## 7. Check 4: Do `paths:`/`branches:` Filters Match?

Every gate workflow in this repo carries `paths: ['sandbox/**']` (Chapter 09 §10) — deliberately,
so curriculum-only PRs never wake the airlock. This is also the single most common *intentional*
"why didn't this fire" answer in this specific repo: if you're wondering why editing
`learning_modules/` didn't trigger a gate, that's Section 7's filter working exactly as designed,
not a bug. `branches:` filters work identically — check the PR's actual base branch against
whatever the filter specifies.

**Shown symptom — spot the diff.** Two PRs against the same filter, `paths: ['sandbox/**']`:

```
PR #101  changed files: sandbox/README.md          → matches sandbox/**  → gates RUN
PR #102  changed files: learning_modules/          → no glob matches     → NO run,
                          chapter_13_debugging_workflows.md                 no trace
```

**What to notice:**

- Same workflow, same event type, same base branch — the *only* delta is the changed-file list.
- The no-match case leaves nothing in the Actions tab. Compare the file list against the glob
  yourself (Section 9's lab replays this with `fnmatch`); GitHub won't show you the non-match.

## 8. Check 5: Is the Workflow Disabled?

A workflow can be manually disabled from the Actions tab's "..." menu — a real, if easy-to-forget,
possibility. GitHub also auto-disables a scheduled workflow after 60 days of repository
inactivity (Section 11) — a fact worth checking before assuming a misconfiguration is the cause.

**Shown symptom.** Before: someone disabled Gate 2 from the "..." menu during an incident and
forgot. `gh workflow list --all` (without `--all`, disabled workflows are hidden entirely):

```
$ gh workflow list --all
Automerge — Queue on Open/Update  active             339521379
CI                                active             339521380
Gate 1 — Repo Readiness           active             339521382
Gate 2 — PR Health                disabled_manually  339521383
Gate 3 — Risk Score               active             339521384
```

**What to notice:**

- The state column distinguishes `disabled_manually` from `disabled_inactivity` (Section 11's
  60-day case) — the two have different fixes and different people to ask.
- Re-enable with `gh workflow enable 339521383` (the third column is the workflow ID).

## 9. ⚠️ ADVANCED: Replaying Filter Logic Locally

> ⚠️ **ADVANCED TOPIC:** Testing `paths:`/event-matching logic without pushing anything.
> **Skip on first read** — return once you're debugging a filter mismatch you can't reproduce by
> inspection alone.

Before pushing a change to test whether a `paths:` filter would match, you can replay the same
glob-matching logic locally against a known changed-file list — exactly what this chapter's lab
script does with `fnmatch`. This turns "push, wait, check the Actions tab, repeat" into an instant
local loop, useful for anything beyond the most obvious filter mismatches.

### Debug Logging: When a Run Exists but Won't Explain Itself

Checks 1–5 get a run to *exist*; sometimes the run then behaves strangely and the default log is
too terse. Setting a repository secret **or** variable `ACTIONS_STEP_DEBUG=true` (the secret wins
if both exist) makes the engine narrate every step, including its expression evaluation — the
exact trace for "why did this step run/skip?":

```
##[debug]Evaluating condition for step: 'Evaluate Gate 2 and publish a check run'
##[debug]Evaluating: success()
##[debug]Evaluating success:
##[debug]=> true
##[debug]Result: true
##[debug]Starting: Evaluate Gate 2 and publish a check run
```

`ACTIONS_RUNNER_DEBUG=true` (same secret-or-variable mechanism) additionally uploads runner
diagnostic logs — visible only via "Download log archive", never in the browser. The real
archive layout from this repo's Gate 1 run `32503470962`:

```
gate1_logs.zip
├── 0_check-readiness.txt        ← full job log; one ##[group]…##[endgroup] per step
├── check-readiness/
│   └── system.txt               ← runner assignment ("Job defined at: …@refs/heads/main")
└── runner-diagnostic-logs/      ← present only with ACTIONS_RUNNER_DEBUG=true
    └── (runner + worker process logs per job)
```

**What to notice:** the `##[debug]Evaluating:` lines are the engine's own reasoning, verbatim —
when an `if:` skips a step you expected to run, this trace shows the exact expression and result.

## 10. ⚠️ ADVANCED: Fork PR Restrictions

> ⚠️ **ADVANCED TOPIC:** Why a fork PR's workflow behavior differs from a same-repo PR's.
> **Skip on first read** — return only if debugging a fork-originated PR specifically.

By default, workflows triggered by a fork PR run with a **read-only** `GITHUB_TOKEN` regardless of
the workflow's own `permissions:` block, and secrets are withheld entirely for `pull_request`
(never `pull_request_target`, Chapter 09 §4). A workflow that *does* fire for a fork PR but then
fails at a write step (posting a comment, publishing a check run) is very often hitting this
restriction, not a bug in the workflow's own logic — this looks like "ran and failed" (Section 1's
first category) but the root cause is fork-related, so it belongs in this chapter's checklist too.
Repository settings also let an admin require approval before any workflow runs at all for
first-time contributors — a run that never starts for a fork PR from a new contributor may simply
be waiting on that approval.

## 11. ⚠️ ADVANCED: Workflow Disabled Due to Inactivity

> ⚠️ **ADVANCED TOPIC:** GitHub's automatic scheduled-workflow disabling.
> **Skip on first read.**

GitHub automatically disables a `schedule`-triggered workflow if the repository has had no activity
for 60 days — a real, documented behavior, not a bug report waiting to happen. A schedule that
worked for months and then silently stopped is a strong signal to check the workflow's enabled/
disabled state in the Actions tab before suspecting a cron-expression or YAML change.

## 12. Case Study: A Schedule That Never Fired

A contributor adds `gate1-repo-health.yml`'s weekly cron on a feature branch, tests locally with
`workflow_dispatch` (which *does* work from any branch when manually triggered against that ref),
merges the PR, and later reports "the schedule never fires." The manual test passing masked
Section 5's requirement — `workflow_dispatch` genuinely can run against any ref, but `schedule`
specifically only reads the default branch's copy. Once merged, the schedule started working
immediately; the earlier "it's broken" reports were accurate observations of a real (if temporary
and expected) limitation, not a bug in the workflow file itself.

## 13. Case Study: This Curriculum's Own Path-Filter Design

Every one of this repo's five gate workflows filters on `paths: ['sandbox/**']` specifically
because this repo plays two roles (Chapter 01 §10) — curriculum and live lab in one repository. A
new contributor's first PR, editing only `learning_modules/`, correctly triggers *zero* gate
workflows — not a bug, Section 7's filter working exactly as designed. Understanding this checklist
is what turns that observation from "why isn't CI running on my PR" (a support question) into "of
course, that's the path filter" (an understood design decision).

## 14. Practical Tips: The Checklist, In Order

```
Workflow X should have run but didn't -- work through in order, stop at the first match:
[1] yaml.safe_load() the file locally -- does it even parse?
[2] Is this a schedule/workflow_dispatch-pairing trigger, and is the file merged to default?
[3] Is the fired event type literally listed under on: at all?
[4] Replay paths:/branches: filters against the actual changed files (Section 9)
[5] Check the Actions tab's "..." menu -- is the workflow disabled?
[6] Is the triggering PR from a fork? (Section 10)
```

### Two Observability Shortcuts: Status Badges and Version-to-Run Mapping

**A stale badge is a visible "didn't fire".** Every workflow exposes a live status badge at:

```
https://github.com/OWNER/REPO/actions/workflows/gate2-pr-health.yml/badge.svg
```

Append `?branch=main` or `?event=push` to pin it to one branch or trigger. Put the gate badges
in the README and a silently-dead workflow stops being invisible — a badge frozen on an old
result (or showing "no status") is this whole chapter's failure category, surfaced passively.

**Which YAML produced this run?** Every run records the commit it ran for (`head_sha`) and the
workflow file's repo path — so a run always maps back to the exact version of the YAML that
produced it. Real output for Section 9's Gate 1 run, via `GET /repos/{owner}/{repo}/actions/runs/{run_id}`:

```
$ gh api repos/OWNER/REPO/actions/runs/32503470962 --jq '{head_sha: .head_sha, path: .path}'
{"head_sha":"61391762a36663fc898854202f1202b57ee3f7b7",
 "path":".github/workflows/gate1-repo-health.yml"}
$ git show 61391762:.github/workflows/gate1-repo-health.yml   # the YAML that ran
```

The archive's `system.txt` (Section 9) records the same fact as a ref (`Job defined at:
…/gate1-repo-health.yml@refs/heads/main`); reusable workflows get pinned SHAs in
`referencedWorkflows`. Debugging "this used to fire"? Diff the YAML between two runs' `headSha`s
first.

## 15. Your First Project: Deliberately Break Each Check

On a disposable test repo, break each of Section 3's five checks one at a time (bad YAML, a
schedule on a feature branch, a mismatched event, a `paths:` filter that excludes your test file, a
manually disabled workflow) and confirm each produces exactly the symptom this chapter predicts —
building the pattern-recognition that makes the checklist fast to apply for real later.

## 16. Common Pitfalls & Misconceptions

1. **"If the workflow file is valid YAML, it'll register."** Not necessarily — a schema violation
   (unrecognized key, malformed `on:` shape) can still fail registration even with valid YAML
   syntax.

2. **"I tested it with `workflow_dispatch` on my branch, so the real trigger will work too."** Not
   for `schedule` — `workflow_dispatch` can run against any ref; `schedule` only reads the default
   branch, always (Section 5, Section 12).

3. **"A workflow that doesn't fire always means something's broken."** Not in this repo — the
   `paths: ['sandbox/**']` filter deliberately, correctly excludes curriculum-only PRs (Section
   13).

4. **"Fork PR workflow issues are the same bug category as a normal failure."** They often look
   identical (a failed write step) but the root cause — restricted token permissions for fork PRs —
   is structurally different and belongs on this chapter's checklist, not Chapter 08/10's.

5. **"A workflow that worked for months and stopped must have a new bug."** Check Section 11 first
   — 60 days of repo inactivity auto-disables a scheduled workflow, with no code change required to
   trigger it.

## 17. Key Takeaways

- **"Didn't fire" and "failed" are different debugging categories** — the first produces zero
  trace anywhere in the Actions UI.
- **The checklist is ordered cheapest-first**: YAML validity, default-branch placement, event-type
  match, path/branch filters, disabled state, fork restrictions.
- **`schedule` only ever reads the default branch's copy of the file** — a feature-branch schedule
  change has zero effect until merged.
- **This repo's own `paths: ['sandbox/**']` filters are usually the correct, intentional "why
  didn't this fire" answer**, not a bug.
- **Fork PRs are a distinct diagnostic category** — restricted tokens and withheld secrets, not a
  logic bug in the workflow itself.

## 18. What's Next: Chapter 14 — Gate 1: Repo Readiness

Chapter 14 starts Phase 3 — building the first real gate for real, against this repo's own live
sandbox: is the repository even eligible for auto-merge at all?

[→ Chapter 14: Gate 1 — Repo Readiness](chapter_14_gate1_repo_readiness.md)

## 19. Additional Resources

- **GitHub Docs, "Using workflow run logs"** — https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs (fetched 2026-08)
- **GitHub Docs, "Disabling and enabling a workflow"** — https://docs.github.com/en/actions/using-workflows/disabling-and-enabling-a-workflow (fetched 2026-08) — see the 60-day auto-disable note
- **GitHub Docs, "Approving workflow runs from public forks"** — https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/approving-workflow-runs-from-public-forks (fetched 2026-08)
- **GitHub Docs, "Enabling debug logging"** — https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/troubleshooting-workflows/enabling-debug-logging (fetched 2026-08) — `ACTIONS_STEP_DEBUG` / `ACTIONS_RUNNER_DEBUG`, secret or variable, secret takes precedence; runner logs land in the archive's `runner-diagnostic-logs` folder
- **GitHub Docs, "Adding a workflow status badge"** — https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/monitoring-workflows/adding-a-workflow-status-badge (fetched 2026-08) — `badge.svg` URL pattern with `?branch=` / `?event=` parameters
- **GitHub REST API, "Workflow runs"** — https://docs.github.com/en/rest/actions/workflow-runs (fetched 2026-08) — run object's `head_sha`, `path`, and `referenced_workflows[].sha` fields (the version-to-run mapping in Section 14)

## 20. Appendix A — Code Index

### A.1 — Three Diagnostics: Syntax, Path Filter, Event Match (from Section 15)

**What the code does:** Validates YAML syntax (reporting the failing line), replays `paths:` glob
matching against a changed-file list, and checks whether a fired event type is declared under
`on:`.

**ASCII flowchart:**

```
diagnose_yaml_syntax(text)         → {"valid": bool, "error": ..., "line": ...}
check_path_filter_match(files, globs) → bool  (would sandbox/** match this PR's files?)
check_event_type_match(event, on_block) → bool
```

See `labs/lab_13_why_no_trigger.py` for the full runnable version.
