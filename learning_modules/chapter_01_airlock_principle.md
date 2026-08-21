# Chapter 01: Auto-Merge & The Airlock Principle

**Reading Time:** ~40 minutes
**Prerequisites:** Chapter 00 (Git, PR & Actions Fundamentals) — or skip it if you're already
comfortable with `git`, the PR lifecycle, and what a workflow YAML file is
**Practice Notebook:** `notebooks/practice_01.ipynb`
**Reference Notebook:** `notebooks/lab_01_airlock_principle.ipynb`
**Script:** `labs/lab_01_airlock_principle.py`
**Doc Reference:** GitHub Docs "About pull requests" · GitHub Docs "Automatically merging a pull request"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 1–4 (what auto-merge actually is, and the airlock mental
model) and Section 11 (the three-gate map). These carry almost all of this chapter's value.

**What to SKIP on first read:** Section 9 (the audit-trail design). Return after Chapter 17
(Wiring the Airlock), when you have something real to audit.

**Key concepts in plain English:**

- **Pull request (PR):** A proposal to merge one branch into another, plus everything GitHub
  attaches to that proposal — comments, checks, reviews, a computed mergeability state.
- **GitHub Actions:** GitHub's built-in automation runner. You write a YAML file describing
  "when X happens, run Y"; GitHub executes Y on a fresh virtual machine.
- **Native auto-merge:** A GitHub *feature* you switch on per-PR. It does not merge anything
  itself — it tells GitHub "merge this the moment every required check passes," then waits.
- **Gate:** A yes/no checkpoint a PR must clear before the next stage of automation proceeds.
- **Required status check:** A named check (e.g. `test`) that branch protection refuses to let a
  PR merge without, whether the merge is manual or automatic.

**Your prior knowledge connection:** If you've ever set up a CI pipeline that has to go green
before a teammate can click "Merge," you already understand three-quarters of this system. Auto-
merge automates only the last step — the click.

---

> **🔬 Automation Engineer's Lens:** The single most expensive mistake in PR automation is an
> airlock that opens when its sensor goes quiet. A gate that treats "I don't know" the same as
> "yes" doesn't reduce review burden — it just moves the burden from before the merge to after the
> incident. Every gate in this curriculum is built to fail *closed*: no data means no merge, full
> stop.

---

> **🚦 Native vs Custom:** GitHub already ships an auto-merge feature — you don't write a single
> line of code to enable it. What you build is everything *upstream* of it: the checks it waits
> on. This distinction is the one that gets lost most often, and it gets a full chapter to itself
> (Chapter 06). For now, hold onto this: **"auto-merge" is a queue-and-wait flag; your gates are
> what feed it a verdict.**

---

## What You'll Learn

- What "PR auto-merge" actually consists of: a native GitHub feature plus your own upstream checks
- The Airlock Principle — this curriculum's governing mental model, and why it fails *closed*
- The three-gate map this whole curriculum builds toward, and what question each gate answers
- Why "the repo isn't ready" is a distinct failure mode from "the PR isn't ready"
- How to read the rest of this curriculum's structure so each chapter's purpose is obvious
- The one design flaw, found in real prior-art code, that motivates the fail-closed rule

---

## Table of Contents

- [Chapter 01: Auto-Merge \& The Airlock Principle](#chapter-01-auto-merge--the-airlock-principle)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What "Auto-Merge" Actually Means](#1-what-auto-merge-actually-means)
  - [2. The Airlock Principle](#2-the-airlock-principle)
  - [3. Why Airlocks Fail Closed](#3-why-airlocks-fail-closed)
    - [A real example: the prior-art bug](#a-real-example-the-prior-art-bug)
  - [4. The Three Gates, At a Glance](#4-the-three-gates-at-a-glance)
  - [5. What a Pull Request Is, Loosely](#5-what-a-pull-request-is-loosely)
  - [6. What GitHub Actions Is, Loosely](#6-what-github-actions-is-loosely)
  - [7. Where This Curriculum Is Going](#7-where-this-curriculum-is-going)
  - [8. The Sandbox Repo You'll Build In](#8-the-sandbox-repo-youll-build-in)
  - [9. ⚠️ ADVANCED: Designing for an Audit Trail](#9-️-advanced-designing-for-an-audit-trail)
  - [10. ⚠️ ADVANCED: Why One Repo Plays Two Roles Here](#10-️-advanced-why-one-repo-plays-two-roles-here)
  - [11. The Three-Gate Map](#11-the-three-gate-map)
  - [12. Case Study: A PR That Should Never Auto-Merge](#12-case-study-a-pr-that-should-never-auto-merge)
  - [13. Case Study: A PR That Should Always Auto-Merge](#13-case-study-a-pr-that-should-always-auto-merge)
  - [14. Practical Tips: Reading This Curriculum](#14-practical-tips-reading-this-curriculum)
  - [15. Your First Project: The Tiny PR](#15-your-first-project-the-tiny-pr)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 02 — Refs, Branches \& What a PR Really Is](#18-whats-next-chapter-02--refs-branches--what-a-pr-really-is)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Gate/GateResult Model (from Section 11)](#a1--the-gategateresult-model-from-section-11)

---

## 1. What "Auto-Merge" Actually Means

Say it out loud and it sounds like one thing: "the PR merges itself." In practice it's two
completely different systems wearing the same name:

```
"Auto-merge" =  A native GitHub feature          +  Everything YOU build
                (enable once per PR,                 (the checks that feature
                 GitHub waits and merges)             is waiting on)
```

The feature half is a checkbox. The half you build is a pipeline: something has to decide the repo
is safe to automate on, something has to confirm the PR's own build is green, and something has to
decide whether *this specific diff* is a reasonable thing to merge without a human looking at it.
That pipeline is what this curriculum is actually about. Chapter 06 draws the line between the two
halves precisely; for now, just notice that the line exists.

## 2. The Airlock Principle

Picture a spacecraft airlock: an outer door, an inner door, and a chamber between them that only
one door can open into at a time. You don't get from outside to inside in one step — you pass
through a sequence of checks, and *each check has to independently agree* before the next one even
gets asked.

```
   OUTSIDE                  AIRLOCK CHAMBER                  INSIDE (main)
  (open PR)   ──door 1──▶  ┌─────────────────┐  ──door 2──▶  (merged)
                            │  pressure OK?    │
                            │  seal intact?    │
                            └─────────────────┘
```

That's the mental model for this whole system:

- **Door 1 (Gate 1):** Is the *station* — the repository — even pressurized? Does it have a `main`
  branch, protection configured, a place for checks to report to?
- **Door 2 (Gate 2):** Did *this specific PR's* build pass?
- **Door 3 (Gate 3):** Even with a green build, is the size and shape of this change something
  that's safe to let through without a person looking?

Every door has to say yes. None of them gets to abstain.

## 3. Why Airlocks Fail Closed

A real airlock that opens when a pressure sensor breaks is not a safety system — it's a hole with
extra steps. The property that makes it a safety system is that **the failure mode of "I don't
know" is treated identically to "no."**

### A real example: the prior-art bug

This isn't hypothetical. An earlier prototype scoring engine (referenced throughout this
curriculum) computes a readiness score like this:

```
score = (sum of weights for rules that PASSED) / (sum of weights for rules that were APPLICABLE)
```

A rule that has **no data** — say, a security scan that never ran — is marked `skip`, and a
`skip`ped rule is removed from *both* the numerator and the denominator. That sounds harmless until
you notice: if that missing rule was a **blocker** (a hard "must pass" rule, like "no critical
vulnerabilities"), a `skip` doesn't just fail to lower the score — it silently removes the blocker
from the equation. A PR with a security scanner that crashed can score *higher* than one where the
scanner ran and found nothing. The prototype's own test suite documents this as intended behavior:
a missing blocker signal does not block approval.

That's a door that opens when the sensor dies. Chapter 14 rebuilds the same kind of check the
opposite way: no data on a required signal is an automatic **fail**, not a shrug.

## 4. The Three Gates, At a Glance

| Gate | Question it answers | Fails when |
| ---- | -------------------- | ---------- |
| 1 — Repo Readiness | Is this repository even eligible for auto-merge? | No `main`, no branch protection, no required checks registered, auto-merge disabled at the repo level |
| 2 — PR Health | Did this specific PR's build succeed? | Build failed, or — critically — no build result exists yet |
| 3 — Risk Scoring | Is this diff small/safe enough to merge unattended? | The computed risk score exceeds a threshold, or the diff exceeds a hard size ceiling regardless of score |

You'll build all three, for real, against a live sandbox repository. Chapters 14–17 are where that
happens; everything before them is the vocabulary and mechanics you need to build them correctly.

## 5. What a Pull Request Is, Loosely

For now: a PR is a request to merge one branch into another, plus a pile of metadata GitHub
tracks on your behalf — who opened it, what checks have run against it, whether GitHub currently
believes it can be merged cleanly. Chapter 02 goes underneath this to the actual Git refs GitHub
creates for every open PR, which is where most "wait, how does GitHub even know that?" confusion
gets resolved.

## 6. What GitHub Actions Is, Loosely

For now: GitHub Actions is GitHub's automation runner. You commit a YAML file under
`.github/workflows/`; it describes a trigger ("when a PR opens against `main`...") and a sequence
of commands to run on a fresh virtual machine when that trigger fires. Chapters 08–13 go deep on
the mechanics — which events exist, what identity your automation runs as, how to debug a workflow
that silently never fired.

## 7. Where This Curriculum Is Going

```
Phase 1 (Ch 01-06)   What a PR actually IS, at the Git level, and how merging works
Phase 2 (Ch 07-13)   The GitHub API and Actions mechanics: events, tokens, contexts, debugging
Phase 3 (Ch 14-17)   Build the three gates for real, against a live sandbox repo
Phase 4 (Ch 18-23)   Harden it: security, calibration, merge queues, and the capstone
```

Phase 1 and 2 exist because the confusion this curriculum is written to fix — what a PR is, what
Actions is, which token does what — has to be solid *before* the three gates make sense. Building
Gate 1 without understanding branch protection, or Gate 3 without understanding how to read a PR's
diff via the API, just relocates the confusion instead of resolving it.

## 8. The Sandbox Repo You'll Build In

This curriculum is unusual in one respect: it is **both** the material you're reading and a live
lab. The repository you're reading this chapter in also contains real, executing GitHub Actions
workflows under `.github/workflows/` — the same three gates described above, wired up and firing
against real pull requests. A `sandbox/` directory holds throwaway content specifically so you can
open PRs of a known size and watch the gates react in real time, without risking anything that
matters. Every gate workflow is scoped with a `paths: ['sandbox/**']` filter, so a PR that only
edits chapter content never triggers the airlock — only a PR touching `sandbox/` does.

## 9. ⚠️ ADVANCED: Designing for an Audit Trail

> ⚠️ **ADVANCED TOPIC:** How to make an automated merge decision explainable after the fact.
> **Skip on first read** — return after Chapter 17, once you have a working pipeline to add an
> audit trail to.

An auto-merge system that can't explain *why* it merged something is a liability the moment
something goes wrong. Every gate in this curriculum returns a typed result — not a bare `True`/
`False` — carrying a rationale string: `"risk=66.0 <= threshold=70"`, `"CI conclusion is
'success'"`. Chapter 23's capstone assembles these into a durable log so "why did this merge?" has
a one-command answer.

## 10. ⚠️ ADVANCED: Why One Repo Plays Two Roles Here

> ⚠️ **ADVANCED TOPIC:** The trade-off in using one repo as both curriculum and live lab.
> **Skip on first read** — this only matters once you're editing the curriculum itself.

Keeping the reading material and the live lab in one repository is simpler to navigate, but it
creates one real hazard: the gates would, by default, be able to act on a PR that edits the
curriculum itself. The `sandbox/**` path filter (Section 8) is what prevents that — every gate
workflow ignores any PR that doesn't touch `sandbox/`. Chapter 16 §3 covers path-scoped triggers as
a general technique, of which this is one instance.

## 11. The Three-Gate Map

This is the map you'll be building toward for the rest of the curriculum:

```
PR opens against main
        │
        ▼
┌───────────────────┐   fail   ┌──────────────┐
│  Gate 1: Ready?     │────────▶│  HOLD         │
│  (repo-level,       │         │  (repo not    │
│   runs on a cron)    │         │   ready)      │
└───────────────────┘          └──────────────┘
        │ pass
        ▼
┌───────────────────┐   fail   ┌──────────────┐
│  Gate 2: Healthy?   │────────▶│  HOLD         │
│  (did CI pass?)      │         │  (build red   │
│                       │         │   or unknown) │
└───────────────────┘          └──────────────┘
        │ pass
        ▼
┌───────────────────┐   fail   ┌──────────────┐
│  Gate 3: Safe size?  │────────▶│  HOLD         │
│  (risk score)         │         │  (too risky)  │
└───────────────────┘          └──────────────┘
        │ pass
        ▼
  gh pr merge --auto --squash   (queues it; GitHub performs the merge)
```

The shared vocabulary from `pr_automerge/models.py` names this: every gate returns a `GateResult`
(status: pass/fail/skip, plus a rationale), and the three combine into a `Decision`.

## 12. Case Study: A PR That Should Never Auto-Merge

A 900-line PR that touches `.github/workflows/` and rewrites the data layer. Even with green CI,
this is exactly the shape of change a risk-based Gate 3 exists to catch: large, and touching a
critical path. In this curriculum's scoring model (Chapter 16), it hits a hard-coded line-count
ceiling and is blocked regardless of its computed score — no amount of green CI overrides "too
big to auto-merge."

## 13. Case Study: A PR That Should Always Auto-Merge

A three-line typo fix in a single file. Green CI, no critical paths touched, a risk score near
zero. This is the case the whole system exists to *not* burden a human with — every chapter's
"hands-on" section produces PRs exactly like this one to prove the pipeline works before testing
its edges.

## 14. Practical Tips: Reading This Curriculum

```
How to read a chapter
──────────────────────
[ ] Read "Beginner's Guide" first -- it tells you what to skip
[ ] Skim the 🔬 and 🚦 callouts -- they're the chapter's opinion, stated plainly
[ ] Read sections 1-8 in order -- they build on each other
[ ] Treat "⚠️ ADVANCED" sections as optional on a first pass
[ ] Do the hands-on step for this chapter before moving to the next
[ ] Check "Key Takeaways" against your own understanding before continuing
```

## 15. Your First Project: The Tiny PR

Before Chapter 02, do this once, so the rest of the curriculum has something concrete to point at:

```bash
git ls-remote origin 'refs/pull/*'
```

Run this against any public GitHub repo with open PRs (or this curriculum's own sandbox repo, once
you've forked/cloned it in Chapter 02's hands-on section). You'll see refs like `refs/pull/1/head`
and `refs/pull/1/merge` — Git objects GitHub created for a PR you never explicitly asked it to
create. That's the first thread Chapter 02 pulls on.

## 16. Common Pitfalls & Misconceptions

1. **"Auto-merge means GitHub decides whether to merge."** No — GitHub only checks whether the
   conditions you configured are met. All the judgment lives in the checks you build; GitHub is
   just the queue.

2. **"If I write good YAML, it'll work."** Most of what breaks this system isn't bad YAML — it's a
   misunderstanding of *when* an event fires, *which* token is running, or *what* a status check
   actually requires. Phase 2 is dedicated to exactly these mechanics.

3. **"A missing check is the same as a passing one, roughly."** This is the fail-open trap from
   Section 3. It is never true in this curriculum's gates — missing data is always a fail.

4. **"I can test this locally with `act`."** You can, for some things, but this curriculum
   deliberately runs everything against a real sandbox repo instead, because several of the most
   important lessons (token scoping, event chaining, branch protection) only show up against real
   GitHub infrastructure.

5. **"Once it's built, it doesn't need recalibrating."** A risk threshold that was right on day
   one drifts as your team's PR patterns change. Chapter 19 is dedicated to catching this.

## 17. Key Takeaways

- **"Auto-merge" is two systems, not one:** a native GitHub feature (a queue-and-wait flag) plus
  your own upstream gates that feed it a verdict.
- **The Airlock Principle:** a sequence of independent gates, each of which must actively pass —
  never merely fail to object.
- **Fail closed, always:** missing data on a required signal is a fail, never a skip that quietly
  drops out of the decision.
- **Three gates, three questions:** is the repo ready, is this PR's build healthy, is this diff
  small/safe enough.
- **This repo is both the book and the lab:** its own `sandbox/` directory and live workflows are
  what you'll build and break throughout.

## 18. What's Next: Chapter 02 — Refs, Branches & What a PR Really Is

Chapter 02 goes underneath the PR abstraction to the actual Git refs GitHub maintains for every
open pull request — `refs/pull/N/head` and `refs/pull/N/merge` — and why `mergeable_state` is a
computed, sometimes-`null` value rather than a fixed property of the PR.

[→ Chapter 02: Refs, Branches & What a PR Really Is](chapter_02_refs_and_prs.md)

## 19. Additional Resources

- **GitHub Docs, "About pull requests"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests (fetched 2026-08)
- **GitHub Docs, "Automatically merging a pull request"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request (fetched 2026-08)
- **GitHub Blog, "About merge queue"** — background on why auto-merge alone doesn't scale to high PR volume (previewed in Chapter 20)

## 20. Appendix A — Code Index

### A.1 — The Gate/GateResult Model (from Section 11)

The typed result every gate in this curriculum returns, instead of a bare boolean. Used throughout
Sections 3 and 11.

**What the code does:** Defines a three-valued status (`pass`/`fail`/`skip`), a `GateResult`
dataclass carrying that status plus a human-readable rationale, and a `Decision` that composes all
three gates' results into one final verdict.

**ASCII flowchart:**

```
GateStatus: PASS | FAIL | SKIP
    ↓
GateResult(gate, status, rationale, details)
    ↓  (one per gate, three total)
Decision(pr_number, merge: bool, gates: list[GateResult])
    ↓
decision.merge == all(g.passed for g in decision.gates)
```

See `pr_automerge/models.py` for the full implementation, and `labs/lab_01_airlock_principle.py`
for a runnable demo that constructs three stub gates and prints the airlock table.
