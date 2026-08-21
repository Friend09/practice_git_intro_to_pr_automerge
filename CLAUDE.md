# CLAUDE.md — Intro to PR Auto-Merge Project Conventions

## Project Overview

A 23-chapter learning curriculum on GitHub pull-request auto-merge, from Git-level fundamentals
through a working 3-gate auto-merge "airlock" built and fired for real against this repo's own
sandbox. Every chapter includes an **Automation Engineer's Lens** and a **Native vs Custom**
callout. This repo is unusual among learning repos: it is simultaneously the curriculum *and*
the live lab — its own `sandbox/` directory and `.github/workflows/` gates are real, executing
GitHub Actions, guarded by a `paths: ['sandbox/**']` filter so they never touch curriculum PRs.

**Philosophy:** `main` is a sealed chamber. Nothing enters except through a sequence of doors,
each of which opens only when the one before it is verified shut — airlocks fail **closed**, not
open. See Chapter 01 for the full Airlock Principle.

## Essential Commands

```bash
# Install dependencies
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt

# Run a lab script (offline, fixture mode — the default)
python labs/lab_XX_<topic>.py

# Run a lab against the real sandbox repo
PRA_MODE=live PRA_REPO=<you>/practice_git_intro_to_pr_automerge python labs/lab_XX_<topic>.py

# Run all notebooks (execute + strip outputs for clean commits)
make run-notebooks

# Run a specific lab via make
make lab-01

# Generate a throwaway sandbox PR of a known size
make pr LINES=120 FILES=6

# Run tests (must pass with zero network access)
pytest tests/ -v --tb=short
```

## Architecture

```
practice_git_intro_to_pr_automerge/
├── learning_modules/     # Reading content (chapter_XX_<topic>.md)
├── notebooks/            # Jupyter labs (practice_XX.ipynb) — PRIMARY format
├── labs/                 # Python scripts (lab_XX_<topic>.py) — importable gate logic
├── sandbox/              # Files edited to generate throwaway PRs of known size — GATED PRs only
├── notes/                # THINGS_TASK_TRACKER.md (forward backlog), IMPROVEMENTS_SUMMARY.md (ledger)
├── research/              # Deep-dive research reports (report_<topic>.md)
├── resources/             # gha_event_reference.md, token_permission_matrix.md
├── output/                # Generated artifacts (gitignored)
├── tests/                 # pytest — scoring, notebook pairing, workflow YAML, chapter structure
└── .github/
    ├── copilot-instructions.md              # Agent workflow guidance
    ├── instructions/                        # Auto-applying conventions
    │   ├── chapter-content.instructions.md  # → learning_modules/**/*.md
    │   ├── python-labs.instructions.md      # → labs/**/*.py
    │   ├── notebooks.instructions.md        # → notebooks/**/*.ipynb
    │   └── workflows.instructions.md        # → .github/workflows/*.yml  (LIVE gates — read first)
    └── workflows/                           # THE LIVE GATES — real, firing workflows
        ├── ci.yml                           # Gate 2 reads this build's conclusion
        ├── gate1-repo-health.yml            # weekly cron + workflow_dispatch
        ├── gate2-pr-health.yml
        ├── gate3-score.yml
        └── automerge.yml                    # gh pr merge --auto only — never a direct merge call
```

## Conventions

### Naming

| Item                | Pattern                                  | Example                              |
| ------------------- | ----------------------------------------- | ------------------------------------- |
| Chapters            | `learning_modules/chapter_XX_<topic>.md` | `chapter_16_gate3_risk_scoring.md`    |
| Practice Notebooks  | `notebooks/practice_XX.ipynb`            | `practice_15.ipynb`                   |
| Reference Notebooks | `notebooks/lab_XX_<topic>.ipynb`         | `lab_15_risk_scoring.ipynb`           |
| Lab scripts         | `labs/lab_XX_<topic>.py`                 | `lab_15_risk_scoring.py`              |
| Research            | `research/report_<topic>.md`             | `report_merge_queue_landscape.md`     |
| Gate workflows      | `.github/workflows/gateN-<topic>.yml`    | `gate3-score.yml`                     |

### Python Code

- **Namespace:** `pr_automerge` for any shared utilities/modules
- **Env var prefix:** `PRA_` (e.g., `PRA_OUTPUT_DIR`, `PRA_REPO`, `PRA_MODE`, `PRA_THRESHOLD`)
- **Imports:** stdlib → third-party → `pr_automerge`
- **Docstrings:** Required on all functions and classes (also required repo-wide by user's global
  CLAUDE.md instruction)
- **Type hints:** Required on function signatures
- **File paths:** `pathlib.Path` — never f-string or os.path concatenation
- **Fixture/live duality:** every lab that talks to GitHub must run offline via
  `PRA_MODE=fixture` (default) and support `PRA_MODE=live` against `PRA_REPO`

### Chapter Header Block

```markdown
# Chapter XX: Title

**Reading Time:** ~NN minutes
**Prerequisites:** Chapter N (topic) — or "None"
**Practice Notebook:** `notebooks/practice_XX.ipynb` — or "— (reading-only)"
**Reference Notebook:** `notebooks/lab_XX_<topic>.ipynb` — or "— (pair pending generation)"
**Script:** `labs/lab_XX_topic.py` — or "— (notebook-only)"
**Doc Reference:** GitHub Docs § ... · Pro Git Ch N
**Depth:** Core | ⭐ Optional Deep-Dive
```

## Chapter-Notebook-Lab Mapping

This table is the **single source of truth** for chapter status — do not duplicate it into a
second file. `—` means the pair has not been backfilled yet.

| Ch  | Title                                     | Practice Notebook | Reference Notebook | Script                          | Depth       |
| --- | ------------------------------------------ | ------------------ | -------------------- | -------------------------------- | ----------- |
| 01  | Auto-Merge & The Airlock Principle         | practice_01.ipynb  | lab_01_airlock_principle.ipynb | lab_01_airlock_principle.py | Core |
| 02  | Refs, Branches & What a PR Really Is       | practice_02.ipynb  | lab_02_pr_refs.ipynb | lab_02_pr_refs.py | Core |
| 03  | Merge Commit vs Squash vs Rebase           | practice_03.ipynb  | —                     | —                                 | Core        |
| 04  | Reading PR Data                            | practice_04.ipynb  | lab_04_pr_data.ipynb | lab_04_pr_data.py | Core |
| 05  | Branch Protection & Rulesets               | practice_05.ipynb  | —                     | —                                 | Core        |
| 06  | Native Auto-Merge vs Your Own Merge Call   | practice_06.ipynb  | lab_06_merge_modes.ipynb | lab_06_merge_modes.py | Core |
| 07  | The GitHub API In Depth & GitHub Apps      | practice_07.ipynb  | lab_07_api_and_apps.ipynb | lab_07_api_and_apps.py | Core |
| 08  | Actions Anatomy                            | practice_08.ipynb  | —                     | —                                 | Core        |
| 09  | The Event Model                            | practice_09.ipynb  | lab_09_event_matrix.ipynb | lab_09_event_matrix.py | Core |
| 10  | Contexts, Expressions, Outputs & `needs`   | practice_10.ipynb  | lab_10_job_outputs.ipynb | lab_10_job_outputs.py | Core |
| 11  | Tokens & Permissions                       | practice_11.ipynb  | —                     | —                                 | Core        |
| 12  | Status Checks, Check Runs & Commit Statuses | practice_12.ipynb | lab_12_check_runs.ipynb | lab_12_check_runs.py | Core |
| 13  | Debugging Workflows That Didn't Fire       | practice_13.ipynb  | lab_13_why_no_trigger.ipynb | lab_13_why_no_trigger.py | Core |
| 14  | Gate 1 — Repo Readiness                    | practice_14.ipynb  | lab_14_repo_health.ipynb | lab_14_repo_health.py | Core |
| 15  | Gate 2 — PR Health                         | practice_15.ipynb  | lab_15_pr_health.ipynb | lab_15_pr_health.py | Core |
| 16  | Gate 3 — Risk Scoring                      | practice_16.ipynb  | lab_16_risk_scoring.ipynb | lab_16_risk_scoring.py | Core |
| 17  | Wiring the Airlock                         | practice_17.ipynb  | lab_17_airlock.ipynb | lab_17_airlock.py | Core |
| 18  | Security                                   | practice_18.ipynb  | —                     | —                                 | Core        |
| 19  | Calibrating the Threshold                  | practice_19.ipynb  | lab_19_calibrate.ipynb | lab_19_calibrate.py | Core |
| 20  | Merge Queues                               | practice_20.ipynb  | —                     | —                                 | ⭐ Optional |
| 21  | Reusable Workflows & Composite Actions     | practice_21.ipynb  | —                     | —                                 | ⭐ Optional |
| 22  | Buy vs Build                               | practice_22.ipynb  | —                     | —                                 | ⭐ Optional |
| 23  | Capstone                                   | practice_23.ipynb  | lab_23_capstone.ipynb | lab_23_capstone.py | Core |

## Gate 3 Scoring Model (locked design decision — do not silently flip)

**Pure risk score.** Size and complexity ADD points; a HIGH score means dangerous; merge only
when `risk <= threshold`.

```python
RISK_WEIGHTS = {"lines": 30.0, "files": 25.0, "critical_paths": 45.0}
DEFAULT_THRESHOLD = 70.0
HARD_CEILING_LINES = 500   # never auto-merge above this, regardless of score

risk = (lines_changed / 100.0) * W["lines"] \
     + (files_changed / 5.0)   * W["files"] \
     + critical_path_hits      * W["critical_paths"]

merge = (risk <= threshold) and (lines_changed <= HARD_CEILING_LINES) and gate1 and gate2
```

This is the opposite convention from the prior-art POC at
`proj_AI/dev/pr-auto-approve-poc/src/pr_gate/engine.py` (a readiness score, `score >= 0.9` to
merge). Chapter 16 §7 explains both directions side by side. Config lives in `gates.yml`
(weights, threshold, ceiling, critical-path globs) — never hard-code these as bare constants;
`pr-auto-approve-poc` did that and it made recalibration (Ch 19) impossible without a code edit.

## Fail-Closed, Not Fail-Open

Gate 2 must treat a **missing** CI result as a failure, not a pass. This is a deliberate
inversion of the POC's `engine.py`, which treats a missing signal as `skip` — removed from both
numerator and denominator, so a missing blocker does not block
(`test_missing_signal_skips_rule_without_failing` asserts `auto_approve is True` there). That is
fail-open. This repo is fail-**closed** by design — see the Airlock Principle in Ch 01 and the
worked contrast in Ch 15.

## Research & Verification

Every factual claim about GitHub Actions behavior needs a dated docs URL in the chapter's §19 —
this surface changes fast. Record "verified against gh CLI 2.x / GitHub Docs as of 2026-08" at
the top of any chapter that makes a specific behavioral claim.

## Content Editing / Validation

After chapter edits, run `pytest tests/test_chapter_structure.py` to confirm no required section
was dropped, and `pytest tests/test_notebook_pairs.py` if the paired notebooks changed.

## Standard Workflow

For each chapter: draft against the instruction files → write the paired lab script and notebook
pair → `make test` (offline) → if the chapter claims live behavior, verify against the real
sandbox repo with `PRA_MODE=live` → log to `notes/THINGS_TASK_TRACKER.md` and
`notes/IMPROVEMENTS_SUMMARY.md`. Do not make unrequested extra edits.

## Notebook/Code Generation

When generating notebooks or scripts, write real newlines, not literal `\n`, and verify the
generated file renders/runs before finishing. Never write a real token or credential into a
notebook output cell — notebooks are committed with cleared outputs, but the source must never
contain one either.
