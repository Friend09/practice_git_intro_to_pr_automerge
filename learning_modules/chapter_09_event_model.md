# Chapter 09: The Event Model

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 08 (Actions Anatomy)
**Practice Notebook:** `notebooks/practice_09.ipynb`
**Reference Notebook:** `notebooks/lab_09_event_matrix.ipynb`
**Script:** `labs/lab_09_event_matrix.py`
**Doc Reference:** GitHub Docs "Events that trigger workflows"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7, plus the [event reference cheatsheet](../resources/gha_event_reference.md) — keep it open in a second tab, this chapter narrates it rather than
re-deriving it.

**What to SKIP on first read:** Section 11 (`check_suite`/`repository_dispatch`, rarely-used
events). Return only if a specific project needs them.

**Key concepts in plain English:**

- **Event:** Something that happened on GitHub (a PR opened, a schedule tick, another workflow
  finishing) that can start a workflow run.
- **Trigger (`on:`):** The workflow-level declaration of which event(s) it reacts to, optionally
  filtered further (branches, paths, types).
- **`pull_request` vs `pull_request_target`:** Two triggers that sound alike and behave almost
  oppositely on the one axis that matters most: which code gets checked out and whether secrets
  are exposed to it.
- **`workflow_run`:** A trigger that fires when a *different* workflow finishes — the sanctioned way
  to react to another workflow's completion, and the only trigger this curriculum uses that a
  bot-authored event can still fire.
- **Fork PR:** A PR opened from a contributor's own fork rather than a branch on the base repo —
  the case that makes `pull_request` vs `pull_request_target` a security question, not just a
  vocabulary one.

**Your prior knowledge connection:** If you've ever configured a CI system to "run on push to
main, but skip on forks," you've already reasoned about exactly the trust boundary this chapter
formalizes — GitHub's event model just gives it specific, named triggers instead of a config flag.

---

> **🔬 Automation Engineer's Lens:** `pull_request_target` combined with an explicit checkout of
> the PR's own head commit is the single most dangerous pattern in this entire curriculum's domain
> — it runs attacker-controlled code with your repo's secrets attached. Nothing else covered here
> has that severity. If you remember exactly one fact from this chapter, make it Section 4's
> footgun diagram.

---

> **🚦 Native vs Custom:** Every event and trigger is 100% native — GitHub fires them, you only
> declare which ones you care about in `on:`. What you build is judgment: choosing `pull_request`
> over `pull_request_target` by default, and only reaching for the latter with the specific
> safeguards Chapter 18 covers. This chapter is entirely about knowing the menu well enough to
> order safely.

---

## What You'll Learn

- The full menu of events this curriculum uses, and what each one checks out and exposes
- Precisely how `pull_request` and `pull_request_target` differ, and why that difference is a
  security boundary, not a style choice
- Why fork PRs can't see secrets under `pull_request` but always can under `pull_request_target`
- What `workflow_run` is for, and the two-hop `head_sha` collapse this repo's own build hit live
- Why every gate workflow in this repo carries a `paths: ['sandbox/**']` filter
- How to choose the right trigger for a new automation task without re-deriving this chapter

---

## Table of Contents

- [Chapter 09: The Event Model](#chapter-09-the-event-model)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What "Event" Means Here](#1-what-event-means-here)
  - [2. The Trigger Menu This Curriculum Uses](#2-the-trigger-menu-this-curriculum-uses)
  - [3. `pull_request`: The Safe Default](#3-pull_request-the-safe-default)
  - [4. `pull_request_target`: The Footgun](#4-pull_request_target-the-footgun)
  - [5. `schedule`: Cron on the Default Branch Only](#5-schedule-cron-on-the-default-branch-only)
  - [6. `workflow_dispatch`: The Manual Escape Hatch](#6-workflow_dispatch-the-manual-escape-hatch)
  - [7. `workflow_run`: Reacting to Another Workflow](#7-workflow_run-reacting-to-another-workflow)
  - [8. The Two-Hop `head_sha` Collapse](#8-the-two-hop-head_sha-collapse)
  - [9. ⚠️ ADVANCED: Why Automation-Authored Events Don't Trigger Normal Events](#9-️-advanced-why-automation-authored-events-dont-trigger-normal-events)
  - [10. ⚠️ ADVANCED: Path Filters as a Trust Boundary](#10-️-advanced-path-filters-as-a-trust-boundary)
  - [11. ⚠️ ADVANCED: `check_suite` and `repository_dispatch`](#11-️-advanced-check_suite-and-repository_dispatch)
  - [12. Case Study: The `workflow_run` Second Hop, Live](#12-case-study-the-workflow_run-second-hop-live)
  - [13. Case Study: A `pull_request_target` Near-Miss](#13-case-study-a-pull_request_target-near-miss)
  - [14. Practical Tips: Choosing a Trigger](#14-practical-tips-choosing-a-trigger)
  - [15. Your First Project: Trace This Repo's Five Triggers](#15-your-first-project-trace-this-repos-five-triggers)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 10 — Contexts, Expressions, Outputs \& `needs`](#18-whats-next-chapter-10--contexts-expressions-outputs--needs)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Event Matrix and the Chaining Simulation (from Section 15)](#a1--the-event-matrix-and-the-chaining-simulation-from-section-15)

---

## 1. What "Event" Means Here

An event is anything GitHub recognizes as having happened that *can* start a workflow: a PR
opened or synchronized, a scheduled tick, another workflow finishing, a human clicking "Run
workflow." A trigger (the `on:` block) is your workflow's declared subscription to one or more of
these — Chapter 08 treated `on:` as a black box; this chapter opens it.

## 2. The Trigger Menu This Curriculum Uses

The full comparison — checked-out ref, secret availability, fork-PR reach, whether an
automation-authored event can fire it — lives in
[`resources/gha_event_reference.md`](../resources/gha_event_reference.md), verified live building
this repo's own five workflows. This chapter narrates the reasoning behind that table rather than
repeating it wholesale; keep it open alongside this chapter.

## 3. `pull_request`: The Safe Default

`pull_request` checks out the PR's synthetic merge commit (Chapter 02 §13) and, critically,
**withholds secrets from fork PRs** — a workflow triggered this way by a stranger's fork PR simply
doesn't have your repo's secrets available to leak, even if the workflow's own code tried to print
them. This is why `pull_request` is the correct default for "run CI against this PR's code": the
blast radius of a malicious PR is capped at "wasted compute," not "stolen secrets."

### What the Event Actually Delivers

When PR #101's author pushes a new commit to `fix/readme-typo`, GitHub fires a `pull_request`
event with `"action": "synchronize"`. Trimmed to the fields this curriculum's gates actually
read (fixture spine, PR #101):

```json
{
  "action": "synchronize",
  "number": 101,
  "pull_request": {
    "head": {
      "ref": "fix/readme-typo",
      "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
    },
    "base": {
      "ref": "main",
      "sha": "0f1e2d3c4b5a69788796a5b4c3d2e1f009182736"
    }
  }
}
```

**What to notice:**

- `pull_request.head.sha` (`a1b2c3d4e5f6…`) is the PR's own tip — the exact SHA Gate 2 later
  queries check runs for (`fixtures/check_runs_for_sha.json` carries the same value).
- `github.sha` in a `pull_request`-triggered run is **not** this value — it's the last merge
  commit on `refs/pull/101/merge`, the synthetic merge ref from Chapter 02 §13. When you mean
  the PR's own tip, say `github.event.pull_request.head.sha` explicitly.
- `"action": "synchronize"` is the push-to-an-open-PR case: a workflow declaring
  `types: [opened, synchronize, reopened]` (this repo's `automerge.yml`) re-fires on every push.

## 4. `pull_request_target`: The Footgun

`pull_request_target` looks almost identical in YAML but differs on the two axes that matter most:
it checks out the **base branch's** code by default (not the PR's), and it makes secrets available
**always**, even for fork PRs.

```
pull_request:                          pull_request_target:
  checks out THE PR'S CODE               checks out THE BASE BRANCH'S CODE
  no secrets (fork PRs)                  secrets ALWAYS available
      │                                       │
      ▼                                       ▼
  safe to run untrusted code             DANGEROUS if you then explicitly
  with no secret exposure                checkout the PR's head AND have secrets
```

The danger isn't the trigger alone — it's `pull_request_target` **plus** a step that explicitly
checks out `github.event.pull_request.head.sha` while secrets are present. That combination runs
untrusted, attacker-controlled code with your secrets attached. `pull_request_target` exists for a
real purpose (labeling fork PRs, posting a comment as a privileged bot) — it's dangerous only when
combined with checking out the PR's own code. Chapter 18 covers the safe patterns in full, and its
§6 gives the field-by-field taxonomy of which event-payload values (titles, bodies, branch names)
are attacker-controlled and which are trustworthy.

## 5. `schedule`: Cron on the Default Branch Only

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'   # every Monday at 06:00 UTC
```

`schedule` always runs against the **default branch's** copy of the workflow file — you cannot
schedule a run against a PR branch or any other ref. This repo's `gate1-repo-health.yml` uses this
trigger for its weekly readiness check. `schedule` triggers are also the one type you genuinely
cannot test on demand without waiting for the cron to fire — which is exactly why Section 6 exists.

## 6. `workflow_dispatch`: The Manual Escape Hatch

`workflow_dispatch` lets a human with write access trigger a workflow on demand, against whatever
ref they choose, from the Actions UI or `gh workflow run`. Every `schedule`-triggered workflow in
this repo also declares `workflow_dispatch: {}` alongside it — without it, testing a scheduled
workflow means either waiting for the real cron tick or temporarily editing the cron expression,
both slow. Pairing them costs one line and removes an entire class of "I can't test this" friction.

## 7. `workflow_run`: Reacting to Another Workflow

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

`workflow_run` fires when a *named* workflow finishes, regardless of what triggered that upstream
workflow or which token it ran under. This is the mechanism Gate 2 (Chapter 15) uses to react to
CI's conclusion — and it's the one trigger in this table that **can** be fired by an
automation-authored event (Section 9), making it the standard way to chain automation beyond what
GitHub's anti-recursion protection otherwise allows.

## 8. The Two-Hop `head_sha` Collapse

`workflow_run`'s event payload includes `github.event.workflow_run.head_sha` — the commit SHA of
whatever triggered the *upstream* workflow. This field is reliable on the **first hop**: a
`workflow_run` listening directly to a `pull_request`-triggered workflow sees the correct PR SHA.
On a **second hop** — a `workflow_run` listening to another `workflow_run`-triggered workflow —
that field collapses to the default branch's SHA, because the second listener's own trigger
context no longer traces cleanly back to the original PR.

Traced with PR #101's spine values (head `a1b2c3d4e5f6…`, `main` at `0f1e2d3c4b5a…`):

```
Workflow A: CI (pull_request, PR #101)     head_sha = a1b2c3d4e5f6…  (the PR's tip)
        │ completes
        ▼
Workflow B (workflow_run off A)            reads event.workflow_run.head_sha
                                             = a1b2c3d4e5f6…   ← hop 1: still the PR's tip
        │ completes
        ▼
Workflow C (workflow_run off B)            reads event.workflow_run.head_sha
                                             = 0f1e2d3c4b5a…   ← hop 2: main's tip. COLLAPSED
```

**What to notice:**

- Hop 1's `head_sha` (`a1b2c3d4e5f6…`) equals `pull_request.head.sha` from Section 3's payload —
  the chain of custody from the original event is still intact.
- Hop 2's value (`0f1e2d3c4b5a…`) is a perfectly valid SHA — it's just the **wrong commit**
  (`main`'s tip). Nothing errors; a check-run lookup against it silently returns the wrong runs.
- In a real log, the collapse looks exactly like this: a SHA that matches no PR head. Recognizing
  the default-branch SHA on sight is how Section 12's live bug was finally diagnosed.

### The Hop-1 Payload, Trimmed

What Gate 2 actually receives when CI finishes for PR #101 — the reliable, single-hop case:

```json
{
  "action": "completed",
  "workflow_run": {
    "name": "CI",
    "event": "pull_request",
    "status": "completed",
    "conclusion": "success",
    "head_branch": "fix/readme-typo",
    "head_sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
  }
}
```

**What to notice:**

- `conclusion` is the field Gate 2 reads for pass/fail; `head_sha` is how it finds *which* PR the
  upstream run belonged to.
- The listener itself runs in **default-branch context** — its own `github.sha` is `main`'s latest
  commit, not the PR's. The PR's identity survives only inside `event.workflow_run.*`.

This is Section 12's real-world case, not a hypothetical.

## 9. ⚠️ ADVANCED: Why Automation-Authored Events Don't Trigger Normal Events

> ⚠️ **ADVANCED TOPIC:** GitHub's deliberate anti-recursion protection.
> **Skip on first read** — return once you've hit "why didn't my second workflow fire" yourself.

GitHub deliberately suppresses normal event triggering (push, PR events) for actions taken *by* the
default `GITHUB_TOKEN` within a workflow run — a `GITHUB_TOKEN`-authored push doesn't itself
trigger another `push`-triggered workflow. This prevents infinite automation loops by design, not
by accident. `workflow_run` is exempt from this suppression (Section 7), which is precisely why
it's the sanctioned mechanism for chaining automation-authored events — full detail in Chapter 07
§10 and the [token permission matrix](../resources/token_permission_matrix.md).

## 10. ⚠️ ADVANCED: Path Filters as a Trust Boundary

> ⚠️ **ADVANCED TOPIC:** How `paths:` filtering keeps this repo's dual role safe.
> **Skip on first read** — return once you're editing this repo's own workflow files.

This repo is both curriculum and live lab (Chapter 01 §8, §10). Every gate workflow here carries a
`paths: ['sandbox/**']` filter on its `pull_request` trigger, so a PR that only edits
`learning_modules/` never wakes the airlock at all — the event fires, GitHub evaluates the path
filter, and the workflow simply doesn't run. This is a *trigger-level* boundary, evaluated before
any job starts, distinct from an `if:` condition (Chapter 08 §9) evaluated once a job is already
running.

## 11. ⚠️ ADVANCED: `check_suite` and `repository_dispatch`

> ⚠️ **ADVANCED TOPIC:** Two less-common triggers, for completeness.
> **Skip on first read** — this repo doesn't use either.

`check_suite` fires when a check suite completes — useful for reacting to third-party CI systems
that report via the Checks API rather than running as GitHub Actions workflows themselves.
`repository_dispatch` fires on a custom, externally-sent HTTP event, requiring a token to send —
useful for triggering a workflow from a system entirely outside GitHub (a deploy pipeline, an
external monitoring tool). Neither appears in this repo's five real workflows; both exist in the
[event reference](../resources/gha_event_reference.md) for completeness.

## 12. Case Study: The `workflow_run` Second Hop, Live

This isn't hypothetical — it's exactly what broke this repo's own `automerge.yml` during
development. An early design had `automerge.yml` itself listen via `workflow_run` to Gate 3, which
itself listened via `workflow_run` to Gate 2, which listened via `workflow_run` to CI — three hops
deep. By the time `automerge.yml` read `event.workflow_run.head_sha`, it had already collapsed to
the default branch's SHA, and the PR-discovery logic silently queried the wrong commit; the merge
never queued. The fix was architectural: stop chaining past one hop. `automerge.yml` now triggers
directly on `pull_request` (Chapter 06 §12, Chapter 17), and only Gate 2 uses `workflow_run` at all
— a single hop, exactly where the field is still reliable.

## 13. Case Study: A `pull_request_target` Near-Miss

A common real-world pattern: a workflow uses `pull_request_target` to let a bot label incoming fork
PRs (a legitimate use — labeling only needs the base repo's own code and a privileged token, never
the PR's own code). A later contributor, wanting to also run the PR's tests in the *same* workflow
for convenience, adds `actions/checkout@v4` with `ref:
${{ github.event.pull_request.head.sha }}` to the same job — now the fork's untrusted code runs
with the bot's secrets attached. The fix isn't "don't use `pull_request_target`" — it's "never
combine it with checking out the PR's own head in a job that has secrets," full stop (Chapter 18).

## 14. Practical Tips: Choosing a Trigger

```
Which trigger do I want?
──────────────────────────────────────────────────────────
[ ] React to a PR's own code, safely?           → pull_request
[ ] React to a PR but need secrets/base-repo
    privileges (labeling, commenting)?           → pull_request_target (NEVER checkout PR head)
[ ] Run on a schedule?                           → schedule + workflow_dispatch (pair them)
[ ] React to another workflow finishing?         → workflow_run (ONE hop only)
[ ] Let a human trigger it manually?             → workflow_dispatch
```

## 15. Your First Project: Trace This Repo's Five Triggers

Open all five workflow files under `.github/workflows/` and, for each, write down: which event
triggers it, and — using this chapter's vocabulary — whether it's the first or a later hop in any
`workflow_run` chain. Confirm your trace matches Chapter 08 §13's table and this chapter's
description of Gate 2 as the only single-hop `workflow_run` listener in the whole repo.

**Expected output** — your trace should match this exactly:

```
workflow                 trigger(s)                         workflow_run hop?
───────────────────────  ─────────────────────────────────  ──────────────────────────────
ci.yml                   pull_request (sandbox/**),         no — the hop-0 source Gate 2
                         workflow_dispatch                    listens to
gate1-repo-health.yml    schedule (0 6 * * 1),              no — not in any chain
                         workflow_dispatch
gate2-pr-health.yml      workflow_run (off "CI")            YES — hop 1, the only one
gate3-score.yml          pull_request (sandbox/**)          no
automerge.yml            pull_request (sandbox/**)          no — direct by design (§12)
```

## 16. Common Pitfalls & Misconceptions

1. **"`pull_request` and `pull_request_target` are basically the same trigger with different
   names."** No — they differ on checked-out code and secret exposure, the two axes that make one
   safe by default and the other dangerous when misused.

2. **"`workflow_run`'s `head_sha` is always reliable."** No — only on the first hop. A second hop
   collapses to the default branch's SHA (Section 8, Section 12).

3. **"My bot's commit should trigger the next workflow automatically."** By design, it usually
   won't — GitHub suppresses `GITHUB_TOKEN`-authored events from re-triggering normal event types
   (Section 9). Use `workflow_run` instead.

4. **"A `paths:` filter is the same as an `if:` condition."** No — `paths:` is evaluated at the
   trigger level, before any job starts; `if:` is evaluated once a job is already running.

5. **"`pull_request_target` is always dangerous, avoid it entirely."** It's dangerous specifically
   when combined with checking out the PR's own head while secrets are present — used correctly
   (labeling, commenting, never touching the PR's code), it's the right tool for its job.

## 17. Key Takeaways

- **`pull_request` is the safe default** — no secrets for fork PRs, runs the PR's own code.
- **`pull_request_target` + checking out the PR's head + secrets is the single most dangerous
  pattern in this curriculum** — never combine all three.
- **`workflow_run` is the sanctioned way to chain automation-authored events**, but `head_sha`
  reliability holds only for the first hop.
- **Path filters are trigger-level trust boundaries**, evaluated before a job even starts —
  distinct from an `if:` condition evaluated mid-run.
- **This repo's own `automerge.yml` bug was a real, live instance of the two-hop collapse** — fixed
  by refusing to chain past one hop, not by patching the SHA lookup.

## 18. What's Next: Chapter 10 — Contexts, Expressions, Outputs & `needs`

Chapter 10 goes deep on the `github.*` context objects this chapter has been referencing
(`github.event.pull_request.head.sha`, `github.event.workflow_run.head_sha`) — what contexts exist,
how expressions evaluate, and how `needs` passes data between jobs.

[→ Chapter 10: Contexts, Expressions, Outputs & `needs`](chapter_10_contexts_expressions.md)

## 19. Additional Resources

- **GitHub Docs, "Events that trigger workflows"** — https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows (fetched 2026-08)
- **GitHub Docs, "Webhook events and payloads"** — https://docs.github.com/en/webhooks/webhook-events-and-payloads (fetched 2026-08) — field-level reference for the `pull_request` and `workflow_run` payload excerpts in §3 and §8
- **GitHub Security Lab, "Keeping your GitHub Actions and workflows secure: Preventing pwn requests"** — https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/ (fetched 2026-08) — the canonical `pull_request_target` writeup
- **This repo's own** [`resources/gha_event_reference.md`](../resources/gha_event_reference.md) — the full comparison matrix, verified against this repo's five real workflows

## 20. Appendix A — Code Index

### A.1 — The Event Matrix and the Chaining Simulation (from Section 15)

**What the code does:** Encodes the event comparison matrix as structured data and simulates
`head_sha` fidelity across a multi-hop `workflow_run` chain, printing where it collapses.

**ASCII flowchart:**

```
EVENT_MATRIX → print_event_matrix() → table: event, secrets, fork reach, automation-fires

simulate_workflow_run_chain(hops=3)
    hop 1 → real SHA
    hop 2 → COLLAPSED
    hop 3 → COLLAPSED
```

See `labs/lab_09_event_matrix.py` for the full runnable version.
