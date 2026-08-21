# Chapter 14: Gate 1 — Repo Readiness

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 05 (Branch Protection), Chapter 07 (The GitHub API & Apps)
**Practice Notebook:** `notebooks/practice_14.ipynb`
**Reference Notebook:** `notebooks/lab_14_repo_health.ipynb`
**Script:** `labs/lab_14_repo_health.py`
**Doc Reference:** This repo's own design -- no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8 — what Gate 1 checks, and the crucial detail that it
*enforces*, not just observes.

**What to SKIP on first read:** Section 10 (the weekly-cron vs live-verify timing trade-off).
Return once you're tuning how often Gate 1 actually runs.

**Key concepts in plain English:**

- **Gate 1:** The first airlock door (Chapter 01 §4) — is the *repository itself* even eligible
  for auto-merge, independent of any individual PR?
- **Enforcement vs observation:** Gate 1 doesn't just report "ready" or "not ready" — it actively
  flips the repo's `allow_auto_merge` setting to match what it finds, every time it runs.
- **`readiness.json`:** A committed badge file recording Gate 1's last verdict, published to a
  dedicated branch (Section 7 explains why not `main`).
- **Weekly cron + `workflow_dispatch`:** Gate 1 runs on a schedule (repo state changes slowly) but
  is also manually triggerable, so it's testable without waiting a week.
- **Fail-closed by construction:** Because Gate 1 actively disables `allow_auto_merge` the moment
  any readiness condition regresses, a broken repo is *structurally* incapable of auto-merging —
  no other workflow needs to coordinate or double-check this.

**Your prior knowledge connection:** If you've ever built a health-check that also *acts* on what
it finds (a Kubernetes liveness probe that restarts a pod, not just an alert that pages a human),
Gate 1's enforce-not-just-observe design will feel familiar — it's the same philosophy applied to
a repo setting instead of a container.

---

> **🔬 Automation Engineer's Lens:** A gate that only *reports* readiness leaves a race condition:
> the repo could regress to "not ready" between the last report and the next PR's merge attempt,
> and nothing would stop that merge. Gate 1 closes that gap by acting directly on the platform-level
> switch (`allow_auto_merge`) rather than trusting every downstream workflow to re-check readiness
> itself — even if `automerge.yml` had a bug that skipped its own checks, GitHub itself would
> refuse to merge with `allow_auto_merge` off.

---

> **🚦 Native vs Custom:** The `allow_auto_merge` repo setting and its enforcement (GitHub refusing
> `gh pr merge --auto` when it's off) are entirely native. What you build is the *policy loop*:
> reading readiness signals, deciding whether they hold, and writing the enforcement decision back
> — this repo's `gate1-repo-health.yml` is exactly that loop, running on a schedule against real
> repo state.

---

## What You'll Learn

- What Gate 1 actually checks, and why it's phrased as repo-level, not PR-level
- Why Gate 1 both reads AND writes the `allow_auto_merge` setting — enforcement, not observation
- How Gate 1 reads branch protection status using only what `GITHUB_TOKEN` can access (Chapter 05)
- Why the readiness badge is published to a dedicated `gate-status` branch, not `main`
- How `pr_automerge.gates.evaluate_gate1` composes with the real workflow's shell-out logic
- What happens, concretely, when Gate 1 detects a regression (the issue it opens)

---

## Table of Contents

- [Chapter 14: Gate 1 — Repo Readiness](#chapter-14-gate-1--repo-readiness)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What Question Gate 1 Answers](#1-what-question-gate-1-answers)
  - [2. The Four Conditions](#2-the-four-conditions)
  - [3. Reading Protection Status, the Chapter 05 Way](#3-reading-protection-status-the-chapter-05-way)
  - [4. Enforcement: Writing `allow_auto_merge`, Not Just Reading It](#4-enforcement-writing-allow_auto_merge-not-just-reading-it)
  - [5. `pr_automerge.gates.evaluate_gate1`, the Engine](#5-pr_automergegatesevaluate_gate1-the-engine)
  - [6. `readiness.json`: The Committed Badge](#6-readinessjson-the-committed-badge)
  - [7. Why the Badge Goes to `gate-status`, Not `main`](#7-why-the-badge-goes-to-gate-status-not-main)
  - [8. The Weekly Cron + `workflow_dispatch` Pairing](#8-the-weekly-cron--workflow_dispatch-pairing)
  - [9. ⚠️ ADVANCED: What Gate 1 Cannot Verify](#9-️-advanced-what-gate-1-cannot-verify)
  - [10. ⚠️ ADVANCED: Cron Cadence Trade-offs](#10-️-advanced-cron-cadence-trade-offs)
  - [11. ⚠️ ADVANCED: The Regression Issue](#11-️-advanced-the-regression-issue)
  - [12. Case Study: The Protected-Branch Push Rejection](#12-case-study-the-protected-branch-push-rejection)
  - [13. Case Study: Gate 1 as the Platform-Level Backstop](#13-case-study-gate-1-as-the-platform-level-backstop)
  - [14. Practical Tips: Reading `gate1-repo-health.yml` End to End](#14-practical-tips-reading-gate1-repo-healthyml-end-to-end)
  - [15. Your First Project: Run Gate 1 Against a Real Repo](#15-your-first-project-run-gate-1-against-a-real-repo)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 15 — Gate 2: PR Health](#18-whats-next-chapter-15--gate-2-pr-health)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Fetching Inputs and Evaluating Gate 1 (from Section 15)](#a1--fetching-inputs-and-evaluating-gate-1-from-section-15)

---

## 1. What Question Gate 1 Answers

Chapter 01 §4 named it: "Is this repository even eligible for auto-merge?" — a question entirely
independent of any specific PR. A repo with no `main` branch, no protection, no required checks, or
`allow_auto_merge` disabled at the platform level fails Gate 1 regardless of how good any individual
PR looks. Gate 2 and Gate 3 never even get a chance to matter if Gate 1 says no.

## 2. The Four Conditions

`pr_automerge.gates.evaluate_gate1` (already implemented and live-verified) checks exactly four
booleans:

```
main_exists                    -- does a branch named "main" exist at all?
protection_configured          -- is SOME protection turned on for it? (Chapter 05)
required_checks_registered     -- are required status checks registered?
auto_merge_enabled             -- is the repo-level allow_auto_merge setting on?
```

All four must hold for `PASS`; the rationale names every missing condition, not just the first one
— useful for a human reading the job summary to see the whole picture at once, not one failure at a
time across several runs.

## 3. Reading Protection Status, the Chapter 05 Way

Gate 1's real implementation reads `repos/{repo}/branches/main` — the **light** endpoint from
Chapter 05 §6, not the full protection endpoint that 403s for `GITHUB_TOKEN` (Chapter 05 §8). This
means `required_checks_registered` can't actually be verified as "these SPECIFIC checks are
required" without a PAT/App token — the real workflow's own code comment is explicit about this,
treating it as mirroring `protection_configured` (an honest, token-limited signal) rather than
pretending to a precision it doesn't have.

## 4. Enforcement: Writing `allow_auto_merge`, Not Just Reading It

This is Gate 1's defining property, and what separates it from a passive health check: after
computing whether the repo *should* be ready, it **writes** that decision back:

```bash
gh api -X PATCH repos/{o}/{r} -F allow_auto_merge=<computed true/false>
```

using `main_exists and protection_configured` as the write condition (Chapter 11 §9's `-F`, not
`-f` — a boolean field). If the repo regresses (someone disables protection, say), the very next
Gate 1 run flips `allow_auto_merge` off *itself* — no PR needs to be open, no other workflow needs
to notice. The platform-level switch is now off, and `gh pr merge --auto` will fail for every PR
until readiness is restored.

## 5. `pr_automerge.gates.evaluate_gate1`, the Engine

```python
def evaluate_gate1(*, main_exists, protection_configured,
                    required_checks_registered, auto_merge_enabled) -> GateResult:
    ...
```

This function is pure — it takes four booleans and returns a `GateResult`, with no knowledge of
*how* those booleans were determined. The real workflow's shell-out Python computes them by calling
`gh api` directly (not importing this function — the workflow predates a clean Python import path
being wired in); this chapter's lab (`lab_14_repo_health.py`) is the missing piece: a proper
CLI-facing wrapper that fetches inputs and calls this exact engine function, matching the
`python-labs.instructions.md` structure the workflow's inline script never needed to follow.

## 6. `readiness.json`: The Committed Badge

Every Gate 1 run writes a small JSON file recording all four conditions plus the overall verdict:

```json
{
  "main_exists": true, "protection_configured": true,
  "required_checks_registered": true, "auto_merge_enabled": true, "ready": true
}
```

This is a durable, git-committed record of the *last* readiness check — useful as a quick status
reference independent of digging through Actions run history.

## 7. Why the Badge Goes to `gate-status`, Not `main`

`main` is protected and requires the `test` status check on every push, including this bot's own —
attempting to commit `readiness.json` straight to `main` gets flatly rejected (`GH006: Required
status check "test" is expected"`), because the Actions bot identity gets no admin-style exemption
(Chapter 05 §13). The fix, verified live during this repo's own build, is a dedicated, unprotected
`gate-status` branch that exists solely to carry this one file — `automerge.yml` (Chapter 17) would
read from there rather than `main` if it needed to.

## 8. The Weekly Cron + `workflow_dispatch` Pairing

Repo-level readiness changes slowly — there's no need to re-check it on every PR. A weekly cron
(`0 6 * * 1`) is enough to catch a regression within a reasonable window, and `workflow_dispatch`
(Chapter 09 §6) is paired alongside it so the gate is testable in seconds during development rather
than waiting up to a week for the next scheduled tick — exactly the pairing
`.github/instructions/workflows.instructions.md` requires of every scheduled workflow in this repo.

## 9. ⚠️ ADVANCED: What Gate 1 Cannot Verify

> ⚠️ **ADVANCED TOPIC:** The honest gap in what `GITHUB_TOKEN`-only readiness checking can confirm.
> **Skip on first read** — return once you're deciding whether to add a `PRA_BOT_TOKEN` path to
> Gate 1 itself.

Because Gate 1 can only read the light `protected` boolean (Section 3), it cannot distinguish
"protection is configured with the right required checks" from "protection is configured with the
*wrong* checks, or none at all beyond the base setting." A PAT/App token would let Gate 1 read the
full protection object and verify the *exact* required-check list matches expectations — a
meaningfully stronger guarantee this repo's current design deliberately doesn't pay the setup cost
for, given a single-repo, single-maintainer context where that gap is low-risk.

## 10. ⚠️ ADVANCED: Cron Cadence Trade-offs

> ⚠️ **ADVANCED TOPIC:** Why weekly, not hourly or daily.
> **Skip on first read.**

A tighter cadence catches a regression faster but burns more Actions minutes for a condition that,
in practice, almost never changes between runs. A looser cadence (weekly, as chosen here) accepts a
longer detection window in exchange for near-zero overhead — reasonable for repo-level settings
that change rarely and deliberately, in contrast to Gate 2/Gate 3, which must run on every single PR
because *those* conditions genuinely do change per-PR.

## 11. ⚠️ ADVANCED: The Regression Issue

> ⚠️ **ADVANCED TOPIC:** What happens when Gate 1 actually fails.
> **Skip on first read** — return once you've seen this fire for real.

On failure, Gate 1's last step (`if: failure()`, Chapter 08 §9 / Chapter 10 §4) opens a GitHub
issue naming the run, so a human gets a durable, trackable notification rather than needing to
proactively check the Actions tab. The issue-creation call itself is defensive
(`|| echo "issue create failed..."`) so a missing `automated` label doesn't cause a confusing
secondary failure on top of the real one being reported.

## 12. Case Study: The Protected-Branch Push Rejection

This is Section 7's bug, told as it actually happened: the first version of this workflow tried
`git push origin main` with the readiness badge. Branch protection rejected it —
`GH006: Required status check "test" is expected"` — because the bot identity, unlike a human admin
under `enforce_admins: false`, gets no bypass. The fix was architectural, not a permissions
workaround: publish to an unprotected branch built specifically for this purpose. This is discovery
#2 in this repo's own Live-Repo Verification Log.

## 13. Case Study: Gate 1 as the Platform-Level Backstop

Imagine `automerge.yml` (Chapter 17) had a latent bug that skipped checking Gate 2/Gate 3's
verdicts entirely. Without Gate 1's enforcement design, that bug could merge an unsafe PR. *With*
it, `allow_auto_merge` being off (because Gate 1 detected a readiness regression, say) means
`gh pr merge --auto` fails at the platform level regardless of what `automerge.yml`'s own logic
does — a second, independent line of defense that doesn't rely on every other workflow being bug-
free. This is the concrete payoff of "enforce, don't just observe" (Section 4).

## 14. Practical Tips: Reading `gate1-repo-health.yml` End to End

```
Reading this repo's real Gate 1 workflow
──────────────────────────────────────────
[ ] on: -- schedule + workflow_dispatch (Section 8)
[ ] permissions: contents: write (badge commit), issues: write (regression issue)
[ ] Step 1: compute the four booleans via light-endpoint reads (Section 3)
[ ] Step 1 (same step): PATCH allow_auto_merge to match (Section 4) -- enforcement
[ ] Step 2: commit readiness.json to gate-status, not main (Section 7)
[ ] Step 3: if: failure() -- open a regression issue (Section 11)
```

## 15. Your First Project: Run Gate 1 Against a Real Repo

```bash
PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge python labs/lab_14_repo_health.py
```

Compare the printed verdict against the real `readiness.json` on this repo's `gate-status` branch
— they should agree, since both are computed by the same underlying logic (Section 5), just via two
different code paths (this lab's Python function calls vs the real workflow's inline shell-out
script).

## 16. Common Pitfalls & Misconceptions

1. **"Gate 1 just checks whether things look okay."** No — it actively enforces, flipping
   `allow_auto_merge` to match what it finds, in either direction (Section 4).

2. **"Gate 1 verifies exactly which checks are required."** No — it can only confirm SOME
   protection exists (the light endpoint), not the exact required-check list, without a PAT/App
   token (Section 9).

3. **"The readiness badge lives on `main` like everything else."** No — `main`'s own protection
   would reject the bot's push; it lives on a dedicated `gate-status` branch (Section 7).

4. **"Gate 1 needs to run on every PR, like Gate 2/3."** No — repo-level readiness changes rarely;
   a weekly cron is enough, paired with `workflow_dispatch` for on-demand testing (Section 8).

5. **"If Gate 1 fails silently, nobody would notice."** It doesn't fail silently — a regression
   opens a tracked GitHub issue (Section 11), not just a red X buried in the Actions tab.

## 17. Key Takeaways

- **Gate 1 answers a repo-level question**, independent of any specific PR: is the repository even
  eligible for auto-merge at all?
- **It enforces, not just observes** — writing `allow_auto_merge` to match computed readiness is
  what makes it a platform-level backstop, not just a report.
- **It reads protection status via the light endpoint only** (Chapter 05 §6), an honest,
  token-limited signal, not a claim of full verification.
- **The badge publishes to `gate-status`, not `main`**, because the bot identity gets no
  admin-style bypass on protected branches.
- **Weekly cron + `workflow_dispatch`** balances low overhead against real testability — a pairing
  every scheduled workflow in this repo follows.

## 18. What's Next: Chapter 15 — Gate 2: PR Health

Chapter 15 covers the second door: given a healthy, ready repo, did *this specific PR's* CI build
actually succeed — and why a missing CI result must be treated as a fail, never a skip.

[→ Chapter 15: Gate 2 — PR Health](chapter_15_gate2_pr_health.md)

## 19. Additional Resources

- **This repo's own** `.github/workflows/gate1-repo-health.yml` — the live, executing implementation this chapter describes
- **This repo's own** `notes/IMPROVEMENTS_SUMMARY.md` — the Live-Repo Verification Log, discoveries #1 and #2
- **GitHub REST API, "Update a repository"** — https://docs.github.com/en/rest/repos/repos#update-a-repository (fetched 2026-08) — see `allow_auto_merge`
- **GitHub Docs, "Events that trigger workflows"** — https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule (fetched 2026-08) — see the 60-day auto-disable note

## 20. Appendix A — Code Index

### A.1 — Fetching Inputs and Evaluating Gate 1 (from Section 15)

**What the code does:** Fetches the four readiness inputs the same way the real workflow does
(light endpoint only) and hands them to `pr_automerge.gates.evaluate_gate1`.

**ASCII flowchart:**

```
fetch_readiness_inputs(repo) → {main_exists, protection_configured,
                                  required_checks_registered, auto_merge_enabled}
        │
        ▼
evaluate_gate1(**inputs) → GateResult(status, rationale)
```

See `labs/lab_14_repo_health.py` for the full runnable version.
