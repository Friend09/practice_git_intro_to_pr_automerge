# Things Task Tracker — Intro to PR Auto-Merge

Forward-looking backlog. See `IMPROVEMENTS_SUMMARY.md` for the dated completion ledger.

## 🔴 IN PROGRESS

None currently.

---

## 📋 CHAPTER TODO LIST

### Phase 1 — What a Pull Request Actually Is (Ch 01–06)

- [x] Chapter 01: Auto-Merge & The Airlock Principle
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 02: Refs, Branches & What a PR Really Is
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 03: Merge Commit vs Squash vs Rebase
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Promoted from notebook-only to a full lab per explicit user request (batch backfill).
- [x] Chapter 04: Reading PR Data
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 05: Branch Protection & Rulesets
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Promoted from notebook-only to a full lab per explicit user request (batch backfill).
- [x] Chapter 06: Native Auto-Merge vs Your Own Merge Call
  - Full 20-section content, lab, reference + practice notebook pair — all complete

### Phase 2 — The GitHub API & Actions Mechanics (Ch 07–13)

- [x] Chapter 07: The GitHub API In Depth & GitHub Apps
  - Added per explicit user request mid-build (pulling/pushing data via the API,
    what a GitHub App is, multi-repo automation). Full 20-section content, lab,
    reference + practice notebook pair — all complete. Every chapter number from
    07 onward was shifted +1 to make room for it.
- [x] Chapter 08: Actions Anatomy
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Promoted from notebook-only to a full lab per explicit user request (batch backfill).
- [x] Chapter 09: The Event Model
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 10: Contexts, Expressions, Outputs & `needs`
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 11: Tokens & Permissions
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Promoted from notebook-only to a full lab per explicit user request (batch backfill).
- [x] Chapter 12: Status Checks, Check Runs & Commit Statuses
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [x] Chapter 13: Debugging Workflows That Didn't Fire
  - Full 20-section content, lab, reference + practice notebook pair — all complete

### Phase 3 — Building the Three Gates (Ch 14–17)

- [x] Chapter 14: Gate 1 — Repo Readiness
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Live workflow `gate1-repo-health.yml` built, tested live, and enforces readiness.
- [x] Chapter 15: Gate 2 — PR Health
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Live workflow `gate2-pr-health.yml` built and verified against a real PR.
- [x] Chapter 16: Gate 3 — Risk Scoring
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Live workflow `gate3-score.yml` verified against a real PR.
- [x] Chapter 17: Wiring the Airlock
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    `automerge.yml` built, redesigned once after a live bug, and verified live.

### Phase 4 — Hardening, Scale & Operations (Ch 18–23)

- [ ] Chapter 18: Security (stub only)
- [ ] Chapter 19: Calibrating the Threshold (stub only)
- [ ] Chapter 20: Merge Queues — ⭐ Optional (stub only)
- [ ] Chapter 21: Reusable Workflows & Composite Actions — ⭐ Optional (stub only)
- [ ] Chapter 22: Buy vs Build — ⭐ Optional (stub only)
- [ ] Chapter 23: Capstone (stub only)

---

## 📋 NOTEBOOK TODO LIST

Reference + practice pairs complete for Ch 01–17 (Phase 1, Phase 2, and Phase 3 all
fully done). Per the 2026-08-21 scope decision, every chapter (including the
⭐-optional ones and the originally "notebook-only" 03/05/08/11/18/20/21/22) gets a
full reference + practice pair — remaining chapters pending in curriculum order
(Batch 4: 18–23).

---

## 📋 LAB SCRIPT TODO LIST

Complete: `lab_01_airlock_principle.py`, `lab_02_pr_refs.py`,
`lab_03_merge_strategies.py`, `lab_04_pr_data.py`, `lab_05_branch_protection.py`,
`lab_06_merge_modes.py`, `lab_07_api_and_apps.py`, `lab_08_actions_anatomy.py`,
`lab_09_event_matrix.py`, `lab_10_job_outputs.py`, `lab_11_tokens_and_permissions.py`,
`lab_12_check_runs.py`, `lab_13_why_no_trigger.py`, `lab_14_repo_health.py`,
`lab_15_pr_health.py`, `lab_16_risk_scoring.py`, `lab_17_airlock.py`.

Pending, per the `CLAUDE.md` Chapter-Notebook-Lab Mapping table plus the promoted
chapters from the 2026-08-21 scope decision: `lab_18_security.py`,
`lab_19_calibrate.py`, `lab_20_merge_queues.py`, `lab_21_reusable_workflows.py`,
`lab_22_buy_vs_build.py`, `lab_23_capstone.py`.

Note: `lab_14_repo_health.py` and `lab_15_pr_health.py` should be thin wrappers
around the logic already implemented and live-verified in `pr_automerge/gates.py`
(`evaluate_gate1`, `evaluate_gate2`) — the engine exists; only the CLI-facing lab
script (per `python-labs.instructions.md`'s required structure) is missing.
Likewise `lab_17_airlock.py` should compose `pr_automerge.gates` +
`pr_automerge.scoring` into a single `decide(pr) -> Decision` entry point, mirroring
what `automerge.yml`'s live workflow logic does today only inside YAML.

---

## 📋 INFRASTRUCTURE TODO LIST

- [x] Directory skeleton, `.gitignore`, `Makefile`, `.code-workspace`
- [x] `.github/instructions/*.instructions.md` — all four (chapter, labs, notebooks, workflows)
- [x] `.github/copilot-instructions.md`
- [x] `CLAUDE.md` with full 23-chapter mapping table
- [x] `README.md` with full 4-phase curriculum, gate mapping, doc alignment, schedules
- [x] `pr_automerge/` shared package: `models.py`, `gh_client.py`, `gates.py`, `scoring.py`, `render.py`
- [x] `fixtures/` — five worked-example PR payloads
- [x] `sandbox/app/` — trivial greeting package CI actually builds/tests
- [x] `sandbox/generate_pr.py` — generates a diff of a known size for gate practice
- [x] `tests/` — scoring, gates, workflow YAML safety, chapter structure, notebook pairing
- [x] Live GitHub repo created (`Friend09/practice_git_intro_to_pr_automerge`, public)
- [x] Branch protection configured, required checks registered (`test`, `gate2-pr-health`, `gate3-risk-score`)
- [x] `allow_auto_merge` enabled and actively enforced by Gate 1
- [x] All five live workflows built, pushed, and fired against real PRs — see the three
      real bugs found and fixed, logged in `IMPROVEMENTS_SUMMARY.md`
- [ ] `PRA_BOT_TOKEN` PAT — not yet minted (this is inherently a browser action; see
      Chapter 07 §14). Until it exists, `automerge.yml` will fail loudly with a clear
      job-summary message rather than silently no-op, by design.
- [ ] `gates.yml` config file for weights/threshold/ceiling — `RiskConfig` already
      supports overriding these; the committed config file itself doesn't exist yet

---

## 📋 DATA TODO LIST

- [x] `fixtures/pr_typo_fix.json`, `pr_small_feature.json`, `pr_workflow_touch.json`,
      `pr_refactor.json`, `pr_large_migration.json` — the Chapter 16 worked example
- [x] `fixtures/pr_raw_pull.json`, `git_refs_sample.json` — Chapter 02 (raw PR object with
      `mergeable_state`, and a plain git refs listing)
- [x] `fixtures/pr_list_sample.json` — Chapter 04 (a 12-PR list for pagination demos)
- [x] `fixtures/branch_light_status.json`, `branch_protection_full.json` — Chapter 05
      (the two branch-protection read shapes)
- [x] `fixtures/check_run_response.json` — Chapter 12 (a published check-run response)
- [x] `fixtures/repo_settings.json` — Chapter 14 (repo-level `allow_auto_merge` read)
- [x] `fixtures/check_runs_for_sha.json` — Chapter 15 (per-SHA check-run listing)
- [x] `resources/gha_event_reference.md`, `resources/token_permission_matrix.md` —
      cheatsheets referenced in `CLAUDE.md`'s repo structure (already written; this line
      was stale — corrected 2026-08-21 batch 1)

---

## ✅ COMPLETED

- **2026-08-21** — Repo scaffolded; format contracts adapted from `proj_ml_intro_to_ml`;
  `pr_automerge` package built and unit-tested; five live gate workflows built,
  pushed to a real public GitHub repo, and verified end-to-end against real PRs.
  Three real infrastructure bugs found and fixed during that verification (see
  `IMPROVEMENTS_SUMMARY.md`). Chapter 07 (GitHub API & Apps) added mid-build per
  explicit request; all chapters 07+ renumbered. Four chapters written to full
  20-section depth (01, 06, 07, 16) with matching labs and notebook pairs; the
  remaining 19 are header-block stubs with correct metadata.

- **2026-08-21 — Curriculum backfill Batch 1 (Phase 1, Ch 02-05).** Full 20-section
  content, lab script, and reference + practice notebook pair written for Chapters 02
  (Refs, Branches & What a PR Really Is), 03 (Merge Commit vs Squash vs Rebase), 04
  (Reading PR Data), and 05 (Branch Protection & Rulesets). Chapters 03 and 05 were
  promoted from "notebook-only" to full lab + reference-notebook chapters per the
  user's explicit scope decision, so every practice notebook in the curriculum has an
  answer key. Four new fixture files added (`pr_raw_pull`, `git_refs_sample`,
  `pr_list_sample`, `branch_light_status`, `branch_protection_full`). `FULL_CHAPTERS`
  and `PAIRED_NOTEBOOKS` extended in the test suite; `CLAUDE.md` and `README.md`
  mapping tables updated. All 93 tests pass (2 skipped, pre-existing and unrelated);
  all four new labs run cleanly offline in fixture mode; all four reference notebooks
  executed via `nbconvert` and stripped for commit.

- **2026-08-21 — Curriculum backfill Batch 2 (Phase 2, Ch 08-13).** Full 20-section
  content, lab script, and reference + practice notebook pair written for Chapters 08
  (Actions Anatomy), 09 (The Event Model), 10 (Contexts, Expressions, Outputs &
  `needs`), 11 (Tokens & Permissions), 12 (Status Checks, Check Runs & Commit
  Statuses), and 13 (Debugging Workflows That Didn't Fire) — closing Phase 2
  entirely. Chapters 08 and 11 were promoted from "notebook-only" per the same
  2026-08-21 scope decision as Batch 1. Chapter 09's lab and Chapter 11's lab encode
  the `resources/gha_event_reference.md` and `resources/token_permission_matrix.md`
  cheatsheets as structured, testable data rather than duplicating their prose.
  Chapter 09's lab also reproduces the real `workflow_run` two-hop `head_sha`
  collapse bug from the Live-Repo Verification Log as a runnable simulation. One new
  fixture (`check_run_response.json`) added. `FULL_CHAPTERS` and `PAIRED_NOTEBOOKS`
  extended; `CLAUDE.md` and `README.md` updated. All 117 tests pass (2 skipped,
  pre-existing and unrelated); all six new labs run cleanly offline; all six
  reference notebooks executed via `nbconvert` and stripped for commit.

- **2026-08-21 — Curriculum backfill Batch 3 (Phase 3, Ch 14/15/17).** Full
  20-section content, lab script, and reference + practice notebook pair written for
  Chapters 14 (Gate 1 — Repo Readiness), 15 (Gate 2 — PR Health), and 17 (Wiring the
  Airlock) — closing Phase 3 entirely (Ch 01–17 all complete; only 18–23 remain).
  Chapter 16 was already complete from the initial build. Read all five live
  workflow files and `workflows.instructions.md` before writing, per the plan;
  chapters 14/15/17 describe those exact files, including the four real discoveries
  in the Live-Repo Verification Log. `lab_14_repo_health.py` and
  `lab_15_pr_health.py` are thin CLI wrappers over `pr_automerge.gates`, as the
  tracker anticipated; `lab_17_airlock.py` composes `pr_automerge.gates` +
  `pr_automerge.scoring` into a single `decide(pr) -> Decision`, demonstrating in
  Python what the five real workflows achieve without any direct coordination, via
  required status checks and native auto-merge alone. Two new fixtures added
  (`repo_settings.json`, `check_runs_for_sha.json`). `FULL_CHAPTERS` and
  `PAIRED_NOTEBOOKS` extended. All 129 tests pass (2 skipped, pre-existing and
  unrelated); all three new labs run cleanly offline; all three reference notebooks
  executed via `nbconvert` and stripped for commit. No `.github/workflows/*.yml`
  files were edited — read-only per the plan's scope.
