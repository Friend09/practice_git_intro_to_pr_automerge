# Things Task Tracker — Intro to PR Auto-Merge

Forward-looking backlog. See `IMPROVEMENTS_SUMMARY.md` for the dated completion ledger.

## 🔴 IN PROGRESS

None currently.

---

## 📋 CHAPTER TODO LIST

### Phase 1 — What a Pull Request Actually Is (Ch 01–06)

- [x] Chapter 01: Auto-Merge & The Airlock Principle
  - Full 20-section content, lab, reference + practice notebook pair — all complete
- [ ] Chapter 02: Refs, Branches & What a PR Really Is (stub only)
- [ ] Chapter 03: Merge Commit vs Squash vs Rebase (stub only)
- [ ] Chapter 04: Reading PR Data (stub only)
- [ ] Chapter 05: Branch Protection & Rulesets (stub only)
- [x] Chapter 06: Native Auto-Merge vs Your Own Merge Call
  - Full 20-section content, lab, reference + practice notebook pair — all complete

### Phase 2 — The GitHub API & Actions Mechanics (Ch 07–13)

- [x] Chapter 07: The GitHub API In Depth & GitHub Apps
  - Added per explicit user request mid-build (pulling/pushing data via the API,
    what a GitHub App is, multi-repo automation). Full 20-section content, lab,
    reference + practice notebook pair — all complete. Every chapter number from
    07 onward was shifted +1 to make room for it.
- [ ] Chapter 08: Actions Anatomy (stub only)
- [ ] Chapter 09: The Event Model (stub only)
- [ ] Chapter 10: Contexts, Expressions, Outputs & `needs` (stub only)
- [ ] Chapter 11: Tokens & Permissions (stub only)
- [ ] Chapter 12: Status Checks, Check Runs & Commit Statuses (stub only)
- [ ] Chapter 13: Debugging Workflows That Didn't Fire (stub only)

### Phase 3 — Building the Three Gates (Ch 14–17)

- [ ] Chapter 14: Gate 1 — Repo Readiness (stub only — but the live workflow
      `gate1-repo-health.yml` is built, tested live, and enforces readiness)
- [ ] Chapter 15: Gate 2 — PR Health (stub only — live workflow
      `gate2-pr-health.yml` built and verified against a real PR)
- [x] Chapter 16: Gate 3 — Risk Scoring
  - Full 20-section content, lab, reference + practice notebook pair — all complete.
    Live workflow `gate3-score.yml` verified against a real PR.
- [ ] Chapter 17: Wiring the Airlock (stub only — but `automerge.yml` is built,
      redesigned once after a live bug, and verified live)

### Phase 4 — Hardening, Scale & Operations (Ch 18–23)

- [ ] Chapter 18: Security (stub only)
- [ ] Chapter 19: Calibrating the Threshold (stub only)
- [ ] Chapter 20: Merge Queues — ⭐ Optional (stub only)
- [ ] Chapter 21: Reusable Workflows & Composite Actions — ⭐ Optional (stub only)
- [ ] Chapter 22: Buy vs Build — ⭐ Optional (stub only)
- [ ] Chapter 23: Capstone (stub only)

---

## 📋 NOTEBOOK TODO LIST

Reference + practice pairs complete for Ch 01, 06, 07, 16. All others pending, in the
same order as the chapter backlog above — a chapter's prose should exist before its
notebook pair, since the notebook narrates against the chapter's own vocabulary.

---

## 📋 LAB SCRIPT TODO LIST

Complete: `lab_01_airlock_principle.py`, `lab_06_merge_modes.py`,
`lab_07_api_and_apps.py`, `lab_16_risk_scoring.py`.

Pending, per the `CLAUDE.md` Chapter-Notebook-Lab Mapping table: `lab_02_pr_refs.py`,
`lab_04_pr_data.py`, `lab_09_event_matrix.py`, `lab_10_job_outputs.py`,
`lab_12_check_runs.py`, `lab_13_why_no_trigger.py`, `lab_14_repo_health.py`,
`lab_15_pr_health.py`, `lab_17_airlock.py`, `lab_19_calibrate.py`,
`lab_23_capstone.py`.

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
- [ ] `resources/gha_event_reference.md`, `resources/token_permission_matrix.md` —
      cheatsheets referenced in `CLAUDE.md`'s repo structure but not yet written

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
