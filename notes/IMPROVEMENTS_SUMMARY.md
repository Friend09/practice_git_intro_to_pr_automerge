# Improvements Summary — Intro to PR Auto-Merge

Backward-looking, dated completion ledger. See `THINGS_TASK_TRACKER.md` for the
forward backlog.

## Chapter Completion Tracker

| # | Chapter | Status | Date | Notes |
| - | ------- | ------ | ---- | ----- |
| 00 | Fundamentals — Git, PRs & GitHub Actions | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; added per explicit user request AFTER the 23-chapter curriculum was otherwise complete |
| 01 | Auto-Merge & The Airlock Principle | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 02 | Refs, Branches & What a PR Really Is | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 03 | Merge Commit vs Squash vs Rebase | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 04 | Reading PR Data | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 05 | Branch Protection & Rulesets | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 06 | Native Auto-Merge vs Your Own Merge Call | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; verified live GraphQL restriction |
| 07 | The GitHub API In Depth & GitHub Apps | ✅ Complete | 2026-08-21 | Added mid-build per explicit request; full 20-section content, lab, notebook pair |
| 08 | Actions Anatomy | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 09 | The Event Model | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 10 | Contexts, Expressions, Outputs & `needs` | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 11 | Tokens & Permissions | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 12 | Status Checks, Check Runs & Commit Statuses | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 13 | Debugging Workflows That Didn't Fire | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 14 | Gate 1 — Repo Readiness | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; live workflow built + verified |
| 15 | Gate 2 — PR Health | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; live workflow built + verified |
| 16 | Gate 3 — Risk Scoring | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; live workflow verified |
| 17 | Wiring the Airlock | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; `automerge.yml` built + redesigned once + verified |
| 18 | Security | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair |
| 19 | Calibrating the Threshold | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; added `gates.yml` + `load_config` |
| 20 | Merge Queues (⭐) | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 21 | Reusable Workflows & Composite Actions (⭐) | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 22 | Buy vs Build (⭐) | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; promoted from notebook-only |
| 23 | Capstone | ✅ Complete | 2026-08-21 | Full 20-section content, lab, notebook pair; fulfills Ch 01 §9's audit-trail promise |

## Batch Update Log

**2026-08-21 — Initial build.** Scaffolded the repo per `proj_ml_intro_to_ml`'s own
`learning-repo-setup` skill blueprint: directory skeleton, four
`.github/instructions/*.instructions.md` format contracts, `CLAUDE.md`, `README.md`,
the shared `pr_automerge` package, five live gate workflows, and the test suite.
Chapters 01, 06, 07, and 16 written to full depth with matching lab scripts and
notebook pairs; the remaining 19 chapters are header-block stubs with correct,
final metadata (so `CLAUDE.md`'s mapping table and `README.md`'s curriculum tables
were already accurate for the 23-chapter arc as it stood then; Chapter 00 was
added later, on 2026-08-21, after the user asked for a Git/PR/Actions fundamentals
refresher, bringing the curriculum to 24 chapters — see the batch entry below).

**2026-08-21 — Curriculum backfill Batch 1 (Phase 1, Chapters 02–05).** Wrote full
20-section content, a lab script, and a reference + practice notebook pair for
Chapters 02, 03, 04, and 05, closing Phase 1 entirely (Chapters 01–06 are now all
complete). Chapters 03 and 05 were originally scoped as "notebook-only" (practice
notebook with no reference/lab); per the user's explicit decision they were promoted
to full lab + reference-notebook chapters like every other chapter, so no practice
notebook in the curriculum lacks an answer key. Chapter 05's lab
(`lab_05_branch_protection.py`) directly demonstrates the real `GITHUB_TOKEN` 403
discovery already logged below (Live-Repo Verification Log #1) rather than
re-describing it in the abstract. Five new fixtures added to support these labs.

**2026-08-21 — Curriculum backfill Batch 2 (Phase 2, Chapters 08–13).** Wrote full
20-section content, a lab script, and a reference + practice notebook pair for
Chapters 08 through 13, closing Phase 2 entirely (Chapters 01–13 are now all
complete). Chapters 08 and 11 were promoted from "notebook-only" for the same
reason as Batch 1's 03/05. Chapter 09's lab reproduces the real `workflow_run`
two-hop `head_sha` collapse (the fourth discovery in the Live-Repo Verification Log
below) as a runnable simulation rather than only describing it in prose; Chapter
11's lab reproduces the real `-f`/`-F` encoding bug the same way.

**2026-08-21 — Curriculum backfill Batch 3 (Phase 3, Chapters 14, 15, 17).** Wrote
full 20-section content, a lab script, and a reference + practice notebook pair for
Chapters 14, 15, and 17, closing Phase 3 entirely (Chapters 01–17 are now all
complete). All five live workflow files were read in full before writing, since
these three chapters describe those exact files and the real bugs found building
them. `lab_14_repo_health.py` and `lab_15_pr_health.py` are thin wrappers around
`pr_automerge.gates.evaluate_gate1`/`evaluate_gate2`, matching the design the
tracker specified when those functions were first built. `lab_17_airlock.py`
composes all three gates into one `decide() -> Decision` call, made explicit in
Python for teaching purposes even though none of the five real workflows need this
composition — they achieve it entirely through required status checks and native
auto-merge, with zero direct coordination between the three gate workflows.

**2026-08-21 — Curriculum backfill Batch 4 (Phase 4, Chapters 18–23) — CURRICULUM
COMPLETE.** Wrote full 20-section content, a lab script, and a reference + practice
notebook pair for Chapters 18 through 23, completing every one of the 23 planned
chapters. Chapters 20–22 (the three ⭐ optional deep-dives) were promoted from
"notebook-only" for the same reason as every earlier promoted chapter. Added
`gates.yml` and `pr_automerge.scoring.load_config` — the config file Chapter 16 §9
promised would exist, finally built to support Chapter 19's calibration lab.
Chapter 23's capstone reuses Chapter 17's `decide()` unchanged and adds the durable,
queryable audit trail Chapter 01 §9 promised on day one — "why did PR #N merge?" now
has a genuine one-command answer (`explain_decision`), tested against two
contrasting sample PRs. All 23 chapters, all 23 lab scripts, and all 23 notebook
pairs are now complete; this file's Chapter Completion Tracker above reflects the
finished state.

**2026-08-21 — Chapter 00 added: Fundamentals — Git, Pull Requests & GitHub
Actions.** After the 23-chapter curriculum was otherwise complete, the user asked
for a Git fundamentals refresher — their own working vocabulary stopped at
`git add . && git commit -m "..." && git push origin main`, with `git merge`
itself still a gap — and, mid-request, also asked for the end-to-end pull-request
lifecycle (what a successful merge looks like) and a basic primer on what a
GitHub Actions workflow file even is, correctly noting that Chapter 08's full
Actions Anatomy treatment is too many chapters deep to serve as the on-ramp.
Added as Chapter 00 (not a renumbering — every existing chapter keeps its number)
with full 20-section content, a lab script, and a reference + practice notebook
pair, covering: the three areas (working directory/staging/history) and the
add→commit cycle, branches as pointers, a fast-forward merge (deliberately the
simplest case, deferring the three real merge strategies to Chapter 03), the
nine-stage PR lifecycle, the exact fields (`merged: true` + `merge_commit_sha`,
not `state` alone) that mark a successful merge, and a minimal real workflow
YAML parsed into its four pieces (name/trigger/jobs/steps). One new fixture
(`pr_merged_example.json`). Chapter 01's Prerequisites field updated to point to
Chapter 00. `FULL_CHAPTERS` and `PAIRED_NOTEBOOKS` extended to include `"00"`;
`CLAUDE.md` and `README.md` updated throughout (23→24 chapters, Phase 1 now reads
Chapters 0–6, new mapping-table row, updated reading-time totals and schedules).

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
