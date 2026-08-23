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

**2026-08-23 — Depth retrofit Batch 4 + 3,000-file-cap correction (Chapters 00–08; initiative
complete).** Backfill of the chapters behind the reader's position, all in the Worked Trace
pattern, with git output captured from throwaway scratchpad repos (never authored): Ch 00 walks
one file untracked→staged→committed→modified with real `git status`/`git diff` at each stop
(vA/vB labels embedded in the file content so they appear in actual diffs) plus the
add-copies-not-moves proof and an Actions run view for §11. Ch 01 finally shows the fail-open
bug numerically: two tables where a failing blocker's missing signal inflates the prior-art
score 0.50 → 1.00, plus Ch 16 forward refs (5.9, 510.0). Ch 02: real `ls-remote` output from
`fixtures/git_refs_sample.json`, HEAD→branch-file pointer trace, detached-HEAD subsection.
Ch 03: full merge-conflict anatomy with the captured "still merging" intermediate state,
rebase replay decomposition + Golden Rule, and the doc-verified non-fast-forward PR-merge
default. Ch 04: the marquee fixture→`PRMetadata` worked trace, camelCase-vs-snake_case shown
side by side, real `Link` header + page math. Ch 05: light-vs-full protection reads side by
side from fixtures. Ch 06: auto-merge lifecycle in fixture data, real `gh pr merge --auto`
output verified against the gh CLI source (success line is stderr and TTY-only — in Actions
the exit code is the only signal), and the `autoMergeRequest` artifact. Ch 07: `--jq` output
trace, 3-row rate-limit table (App-token scaling verified), check-run response excerpt
cross-linked to Ch 12, `actions/github-script@v9` subsection. Ch 08: the real `ci.yml` quoted
line-numbered with per-block commentary (full listing in new Appendix A.2), runners deepened
(images, labels, JIT), matrix worked 3×2→6-job expansion.

**Major factual correction found by the fact-check protocol:** the repo-wide claim of a
"300-file cap" on `GET /pulls/{n}/files` is wrong — current GitHub docs give that endpoint a
**3,000-file** maximum; the 300-file limit belongs to the *compare-two-commits* endpoint.
Corrected across 7 files: Ch 04 (incl. the §8 heading rename with ToC anchor synced, and the
§12 case study rescaled to a 3,340-file PR with the critical hit at #3,012), Ch 07 §4/A.1
pseudocode, `labs/lab_04_pr_data.py` (`MAX_FILES_LISTED = 3000`), `labs/lab_07_api_and_apps.py`
(`FILE_COUNT_TRUNCATION_LIMIT = 3000`), the instructions file's concrete-numbers rule, and the
Ch 04 notebook pair (markdown synced byte-identically; reference notebook re-executed so its
output prints 3000). The compare-endpoint 300 is kept as an explicit contrast with dated
citations. Tests after everything: 158 passed, 2 skipped; both labs run clean in fixture mode.

**2026-08-23 — Depth retrofit Batch 3 (Chapters 19–23, +330 lines).** Ch 19 (verification
pass): zero numeric drift in the 5×5 sweep table; fixed two stale "Ch 16 §7" ceiling
citations to §5; What-to-notice bullets added (the 172.0 refactor is threshold-bound, flipping
at 200.0). Ch 20: the semantic conflict is now a concrete spot-the-diff (PR #201 adds a flag,
PR #202 removes its fallback, both green alone, combined file broken), and §4 shows literal
`gh-readonly-queue/main/...` speculative refs — the documented prefix cited, the `pr-N-<sha>`
suffix honestly labeled observed convention; `merge_group`/`checks_requested` trigger cited.
Ch 21: custom-action flavors table (5-axis vocabulary; node20/node24, not Node 16), an 18-line
`action.yml` traced end-to-end (noting action inputs are untyped strings — only `workflow_call`
has types), the gate2/gate3 duplicated steps quoted verbatim, and required workflows described
via the CURRENT mechanism (repository rulesets, with the 2023 migration history and honest
plan-availability caveats); 8 dated citations. Ch 22 (verification pass): §3's drifted table
replaced with a compliant 5-axis table + feature-facts matrix; §6's build=0/buy=4 made
derivable (Team B's budget input was unstated — the one inconsistency found); noted no single
input flips either verdict. Ch 23: §7 now shows the verbatim `explain_decision()` output
captured from a real fixture-mode lab run (PR #301 MERGED, risk 5.9; PR #302 HELD on the
hard ceiling), §6 shows a real `audit_log.jsonl` line, §15 gained expected output. Note: a
mid-batch session interruption left some edits staged by a hook; all resumed cleanly (use
`git diff HEAD` to see the full delta). Tests: 158 passed, 2 skipped.

**2026-08-23 — Depth retrofit Batch 2 (Chapters 14–18, +333 lines).** Ch 14: the four Gate 1
conditions became an input→result table reading exact fixture fields, and `readiness.json` is
now shown byte-for-byte as `gate1-repo-health.yml` writes it. Ch 15: the fail-closed contract
became a 7-row conclusion→GateResult table with character-exact rationale strings from
`evaluate_gate2`, plus a fixture→gate→`gate_table` end-to-end trace captured from a real
fixture-mode lab run. Ch 16 (verification pass): zero numeric drift vs `test_scoring.py`;
gained the pre-formula plain-English line + 66.0 worked arithmetic, and a ceiling bracket —
notable discovery: at threshold 70 no PR over 234 lines can score under threshold, so the
under-threshold/over-ceiling demo correctly uses the test-pinned recalibrated threshold 200.0.
Ch 17: new concurrency-race subsection (push A cancelled by push B via
`concurrency: gates-<PR#>`, honestly noting none of the five live workflows uses
`concurrency:` today) and environments-as-human-approval-gate subsection; PR #101 spine SHAs
threaded through the §4 fan-out. Ch 18: §15.1 spot-the-diff exercise (3-token malicious
delta), §6 expanded into the canonical trusted/untrusted taxonomy (where Ch 09 §4 now
points), CODEOWNERS-owns-workflows checklist item with the requests-vs-requires caveat.
All new claims carry `(fetched 2026-08)` doc URLs. Tests: 158 passed, 2 skipped.

**2026-08-23 — Depth retrofit Batch 0 + Batch 1 (Worked Trace pattern; Chapters 09–13).**
Gap analysis against two O'Reilly books (*Learning Git*, Skoulikari; *Learning GitHub
Actions*, Laster) found chapters used structural diagrams but rarely transformational
worked examples (input → command → exact output), with concrete data systematically
deferred to labs. Batch 0: codified the six-device **Worked Trace pattern** as a new
"Depth Standard" section in `.github/instructions/chapter-content.instructions.md`, and
fixed a factual error — `GITHUB_TOKEN` in Actions gets 1,000 req/hr per repository, not
5,000 (corrected in Ch 04 §11 and the instructions file; dated docs URL added to Ch 04
§19; Ch 07 §5 was already right). Batch 1 (Ch 09–13, +~490 lines): Ch 09 gained its
first-ever event payload JSON (spine-consistent `pull_request` and `workflow_run`
excerpts) and literal SHAs in the two-hop collapse diagram; Ch 10 gained the 66.0
output-plumbing trace in three increments, an `always()`-on-cancel subsection, a verbatim
`##[debug]` engine trace, and the new artifacts-vs-caches-vs-outputs home (current majors
verified: `cache@v6`, `upload-artifact@v7`, `download-artifact@v8`); Ch 11 gained
token-lifetime facts (6 h hosted / 24 h self-hosted-refresh, doc-verified), a worked 403
scope-missing trace, and the fork-PR approval-settings subsection ("external
contributors" is the current name); Ch 12 inlined both check-run fixtures with the
Ch 05 name-match link made explicit; Ch 13 gained one shown symptom per diagnostic check
(§4–§8), debug-logging + log-archive subsection (archive tree taken from a real
downloaded Gate 1 run — the 2026 layout differs from the 2023 book), and status-badge /
version-to-run mapping. All new behavioral claims carry `(fetched 2026-08)` doc URLs.
Tests: 158 passed, 2 skipped; no section renumbering; no notebook/lab changes needed.
Batches 2–4 (Ch 14–18, 19–23, backfill 00–08) remain — see the tracker's IN PROGRESS entry.

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
