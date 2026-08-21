# Improvements Summary — Intro to PR Auto-Merge

Backward-looking, dated completion ledger. See `THINGS_TASK_TRACKER.md` for the
forward backlog.

## Chapter Completion Tracker

| # | Chapter | Status | Date | Notes |
| - | ------- | ------ | ---- | ----- |
| 01 | Auto-Merge & The Airlock Principle | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 02 | Refs, Branches & What a PR Really Is | 📋 Planned | — | Stub only |
| 03 | Merge Commit vs Squash vs Rebase | 📋 Planned | — | Stub only |
| 04 | Reading PR Data | 📋 Planned | — | Stub only |
| 05 | Branch Protection & Rulesets | 📋 Planned | — | Stub only |
| 06 | Native Auto-Merge vs Your Own Merge Call | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; verified live GraphQL restriction |
| 07 | The GitHub API In Depth & GitHub Apps | ✅ Complete | 2026-08-21 | Added mid-build per explicit request; full 20-section content, lab, notebook pair |
| 08 | Actions Anatomy | 📋 Planned | — | Stub only |
| 09 | The Event Model | 📋 Planned | — | Stub only |
| 10 | Contexts, Expressions, Outputs & `needs` | 📋 Planned | — | Stub only |
| 11 | Tokens & Permissions | 📋 Planned | — | Stub only |
| 12 | Status Checks, Check Runs & Commit Statuses | 📋 Planned | — | Stub only |
| 13 | Debugging Workflows That Didn't Fire | 📋 Planned | — | Stub only |
| 14 | Gate 1 — Repo Readiness | 📋 Planned | — | Stub, but live workflow built + verified |
| 15 | Gate 2 — PR Health | 📋 Planned | — | Stub, but live workflow built + verified |
| 16 | Gate 3 — Risk Scoring | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; live workflow verified |
| 17 | Wiring the Airlock | 📋 Planned | — | Stub, but `automerge.yml` built + redesigned once + verified |
| 18 | Security | 📋 Planned | — | Stub only |
| 19 | Calibrating the Threshold | 📋 Planned | — | Stub only |
| 20 | Merge Queues (⭐) | 📋 Planned | — | Stub only |
| 21 | Reusable Workflows & Composite Actions (⭐) | 📋 Planned | — | Stub only |
| 22 | Buy vs Build (⭐) | 📋 Planned | — | Stub only |
| 23 | Capstone | 📋 Planned | — | Stub only |

## Batch Update Log

**2026-08-21 — Initial build.** Scaffolded the repo per `proj_ml_intro_to_ml`'s own
`learning-repo-setup` skill blueprint: directory skeleton, four
`.github/instructions/*.instructions.md` format contracts, `CLAUDE.md`, `README.md`,
the shared `pr_automerge` package, five live gate workflows, and the test suite.
Chapters 01, 06, 07, and 16 written to full depth with matching lab scripts and
notebook pairs; the remaining 19 chapters are header-block stubs with correct,
final metadata (so `CLAUDE.md`'s mapping table and `README.md`'s curriculum tables
are already accurate for the whole 23-chapter arc).

**2026-08-21 — Chapter 07 inserted mid-build.** User requested a dedicated chapter
on `gh api` depth and GitHub Apps partway through the build, correctly identifying
it as a real gap (Chapter 04 only covered reading; the original Chapter 10 only
covered token *choice*, never what an App structurally is). Inserted as the new
Chapter 07 — a bridge from PR fundamentals (Phase 1) into Actions mechanics
(Phase 2) — and every chapter 07+ was renumbered. Cheap to do at that point since no
chapter content files existed yet; only code comments/docstrings referenced numbers.

## Live-Repo Verification Log

Everything below was verified against a real, public GitHub repository
(`Friend09/practice_git_intro_to_pr_automerge`), not simulated. Three genuine
infrastructure discoveries came out of this, each folded directly into the
curriculum as load-bearing content rather than quietly worked around:

1. **`GITHUB_TOKEN` cannot read branch protection settings.**
   `repos/{repo}/branches/main/protection` returns 403 even with
   `permissions: contents: write` declared — that endpoint requires
   Administration permission, a scope `GITHUB_TOKEN` can never hold. Fixed by
   reading the lighter-weight `protected: true/false` boolean from the basic
   `branches/{branch}` endpoint instead, which `GITHUB_TOKEN` *can* read. Feeds
   directly into Chapter 07 (token identities) and Chapter 14 (Gate 1).

2. **A bot pushing to a protected `main` gets rejected — with no bypass.**
   `gate1-repo-health.yml`'s first version tried to commit `readiness.json`
   straight to `main`; branch protection rejected it (`GH006: Required status
   check "test" is expected"`), because — unlike a human repo admin, who bypasses
   protection by default when `enforce_admins: false` — the Actions bot identity
   gets no such exemption. Fixed by publishing the badge to a dedicated,
   unprotected `gate-status` branch instead.

3. **`GITHUB_TOKEN` cannot enable auto-merge, full stop.** Calling
   `gh pr merge --auto` with the default token returns `GraphQL: Resource not
   accessible by integration (enablePullRequestAutoMerge)` — even with
   `pull-requests: write` granted and the repo's `allow_auto_merge` setting on.
   This is a deliberate GitHub restriction, not a config mistake. Fixed by adding
   a `PRA_BOT_TOKEN` fallback path with an honest failure message when neither
   token can enable it. This single discovery is *why* Chapter 07 exists at all.

A fourth, smaller bug was found and fixed in the workflow-chaining design itself:
`automerge.yml`'s original approach tried to recompute "did every gate pass" by
listening to `workflow_run` events from Gate 2 and Gate 3, then reading
`github.event.workflow_run.head_sha` to find the right PR. That field is only
reliable on the *first* hop of a chained `workflow_run` trigger — Gate 3 is
directly `pull_request`-triggered so its `head_sha` is always correct, but Gate 2
is itself `workflow_run`-triggered (off CI), so *its* `head_sha`/`head_branch`
metadata collapses to the default branch's context by the second hop. Verified
live: the PR-discovery logic silently queried the wrong commit and the merge
never queued. The fix was architectural, not a patch: stop recomputing the
verdict at all. Required status checks plus native auto-merge already do that
correctly, for free — `automerge.yml` now triggers directly on `pull_request` and
makes exactly one call, `gh pr merge --auto --squash`.

**End-to-end confirmed working:** CI fires and passes on a real PR; Gate 1 reads
real repo state and actively enforces `allow_auto_merge`; Gate 2 correctly reads
CI's conclusion via `workflow_run` chaining and publishes a fail-closed check run;
Gate 3 fetches real PR diff metadata, computes the exact risk scores from the
Chapter 16 worked example, and publishes both a check run and a PR comment;
`automerge.yml` correctly attempts to queue the PR and correctly reports why it
can't complete the enrollment without a `PRA_BOT_TOKEN` (discovery #3 above).

## How to Log Updates

When you complete a chapter (write its full 20-section content and matching
notebook/lab pair):

1. Change `📋 Planned` → `✅ Complete` in the Chapter Completion Tracker above
2. Add the date
3. Add a brief note about what was covered
4. If the chapter's live workflow required a fix to make the chapter's claims
   true, log it in the Live-Repo Verification Log — a discovery made building this
   curriculum is exactly the kind of content the curriculum itself should contain
