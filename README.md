# Intro to PR Auto-Merge

## A 24-Chapter Curriculum — 4 Phases, Built on a Live Sandbox Repo

> **Philosophy:** `main` is a sealed chamber. Nothing enters except through a sequence of doors,
> each of which opens only when the one before it is verified shut.
> Airlocks fail **closed** — when a sensor breaks, the door stays locked.
> An auto-merge bot that merges when a check is *missing* is an airlock that opens when the
> sensor dies.

---

## Who This Is For

You've run `git merge` a thousand times and written a CI pipeline or two, but the exact mechanics
of **automated** PR merging keep slipping — what a pull request actually *is* at the Git level,
what a GitHub Actions trigger really fires on, which token does what, and where "auto-merge" is a
GitHub *feature* you flip on versus code you write yourself. You've prototyped a scoring engine
before (mocked data, no live Actions) and want to close the gap between that prototype and a
system that actually runs.

**Prerequisites:** Comfortable with `git` day to day, has written at least one `.github/workflows/*.yml`
file before (even a trivial one), has a GitHub account with a repo you can experiment on freely.
New to `git`, PRs, or GitHub Actions entirely? Start with Chapter 00 — it's a from-scratch refresher
built specifically for exactly that gap.

---

## Curriculum Overview — 24 Chapters, 4 Phases

⭐ = Optional Deep-Dive (can skip on first pass, return when ready)

### Phase 1 — What a Pull Request Actually Is _(Chapters 0–6)_

| Ch  | Title                                                                   | Lab                        | Depth | Reading |
| --- | ------------------------------------------------------------------------ | --------------------------- | ----- | ------- |
| 00  | Fundamentals: Git, Pull Requests \& GitHub Actions                      | 📓 practice_00 · 🐍 lab_00 | Core  | ~50 min |
| 01  | Auto-Merge & The Airlock Principle                                       | 📓 practice_01 · 🐍 lab_01 | Core  | ~40 min |
| 02  | Refs, Branches & What a PR Really Is                                     | 📓 practice_02 · 🐍 lab_02 | Core  | ~45 min |
| 03  | Merge Commit vs Squash vs Rebase                                         | 📓 practice_03 · 🐍 lab_03 | Core  | ~35 min |
| 04  | Reading PR Data: `gh pr view`, `gh api`, Pagination                      | 📓 practice_04 · 🐍 lab_04 | Core  | ~45 min |
| 05  | Branch Protection & Rulesets                                             | 📓 practice_05 · 🐍 lab_05 | Core  | ~45 min |
| 06  | **Native Auto-Merge vs Your Own Merge Call**                             | 📓 practice_06 · 🐍 lab_06 | Core  | ~50 min |

### Phase 2 — The GitHub API & Actions Mechanics _(Chapters 7–13)_

| Ch  | Title                                                                   | Lab                        | Depth | Reading |
| --- | ------------------------------------------------------------------------ | --------------------------- | ----- | ------- |
| 07  | **The GitHub API In Depth: Pulling & Pushing Data, and GitHub Apps**    | 📓 practice_07 · 🐍 lab_07 | Core  | ~55 min |
| 08  | Actions Anatomy: Workflows, Jobs, Steps, Runners                        | 📓 practice_08 · 🐍 lab_08 | Core  | ~40 min |
| 09  | The Event Model: `pull_request`, `pull_request_target`, `schedule`, …   | 📓 practice_09 · 🐍 lab_09 | Core  | ~50 min |
| 10  | Contexts, Expressions, Outputs & `needs`                                | 📓 practice_10 · 🐍 lab_10 | Core  | ~45 min |
| 11  | **Tokens & Permissions** — the no-downstream-trigger rule                | 📓 practice_11 · 🐍 lab_11 | Core  | ~50 min |
| 12  | Status Checks, Check Runs & Commit Statuses                             | 📓 practice_12 · 🐍 lab_12 | Core  | ~40 min |
| 13  | Debugging Workflows That Didn't Fire                                    | 📓 practice_13 · 🐍 lab_13 | Core  | ~40 min |

### Phase 3 — Building the Three Gates _(Chapters 14–17)_

| Ch  | Title                                                                   | Lab                        | Depth | Reading |
| --- | ------------------------------------------------------------------------ | --------------------------- | ----- | ------- |
| 14  | Gate 1 — Repo Readiness + the Weekly Health Cron                        | 📓 practice_14 · 🐍 lab_14 | Core  | ~45 min |
| 15  | Gate 2 — PR Health: Fail-Closed vs Fail-Open                            | 📓 practice_15 · 🐍 lab_15 | Core  | ~45 min |
| 16  | **Gate 3 — Risk Scoring**                                                | 📓 practice_16 · 🐍 lab_16 | Core  | ~55 min |
| 17  | Wiring the Airlock: Chaining 1→2→3→Merge                                | 📓 practice_17 · 🐍 lab_17 | Core  | ~50 min |

### Phase 4 — Hardening, Scale & Operations _(Chapters 18–23)_

| Ch  | Title                                                                   | Lab                        | Depth       | Reading |
| --- | ------------------------------------------------------------------------ | --------------------------- | ----------- | ------- |
| 18  | Security: `pull_request_target` & Fork PRs                              | 📓 practice_18 · 🐍 lab_18 | Core        | ~50 min |
| 19  | Calibrating the Threshold                                                | 📓 practice_19 · 🐍 lab_19 | Core        | ~50 min |
| 20  | Merge Queues                                                             | 📓 practice_20 · 🐍 lab_20 | ⭐ Optional | ~40 min |
| 21  | Reusable Workflows & Composite Actions                                  | 📓 practice_21 · 🐍 lab_21 | ⭐ Optional | ~40 min |
| 22  | Buy vs Build: Mergify, Kodiak, Renovate                                 | 📓 practice_22 · 🐍 lab_22 | ⭐ Optional | ~35 min |
| 23  | **Capstone**: The Complete Airlock, Audit Trail & Rollback              | 📓 practice_23 · 🐍 lab_23 | Core        | ~60 min |

**Total reading (Core only, ~21 chapters):** ~15–16 hours
**Total reading (all 24 chapters):** ~18–20 hours

---

## Gate Mapping

| Gate | Question it answers | Primary chapters | Supporting chapters |
| ---- | -------------------- | ------------------ | --------------------- |
| **1 — Repo Readiness** | Is this repo even eligible for auto-merge? | 05, 14 | 07 |
| **2 — PR Health** | Did CI succeed on this PR? | 12, 15 | 04 |
| **3 — Risk Scoring** | Given the diff, is this PR safe to merge unattended? | 04, 16, 19 | 07 |
| **Wiring** | How do the three gates connect to an actual merge? | 06, 07, 11, 17 | — |

---

## Doc Alignment

Unlike a book-anchored curriculum, this one is anchored to living documentation. Every chapter
cites GitHub Docs (with a fetch date, since this surface moves fast) and, for Phase 1's Git-level
material, *Pro Git* (Chacon & Straub, free at git-scm.com/book).

| Repo Chapter(s) | GitHub Docs | Pro Git |
| ---------------- | ------------ | -------- |
| Ch 00 | "About pull requests", "Understanding GitHub Actions" | Ch 1 (Getting Started), Ch 2 (Git Basics) |
| Ch 01–02 | "About pull requests" | Ch 3 (Branching), Ch 10.3 (Git Internals — refs) |
| Ch 03 | "About merge methods" | Ch 3.2 (Basic Merging), Ch 7.6 (Rewriting History) |
| Ch 04 | REST API — Pulls | — |
| Ch 05 | "About protected branches", "Rulesets" | — |
| Ch 06 | "Automatically merging a pull request" | — |
| Ch 07 | REST API overview, "About creating GitHub Apps", "Differences between GitHub Apps and OAuth apps" | — |
| Ch 08–10 | "Understanding GitHub Actions" | — |
| Ch 09 | "Events that trigger workflows" | — |
| Ch 11 | "Automatic token authentication" | — |
| Ch 12 | "About status checks" | — |
| Ch 13 | "Using workflow run logs" | — |
| Ch 14–17 | (this repo's own design — no canonical doc) | — |
| Ch 18 | "Security hardening for GitHub Actions" | — |
| Ch 20 | "Merging a pull request with a merge queue" | — |
| Ch 22 | Mergify / Kodiak / Renovate docs | — |

---

## Learning Schedules

| Pace         | Hours/Week | Chapters                     | Duration  |
| ------------ | ---------- | ----------------------------- | --------- |
| 🐢 Relaxed   | 3–4 hrs    | Core only (~21 chapters)     | ~15 weeks |
| 🚶 Moderate  | 5–6 hrs    | Core + selected ⭐ chapters   | ~11 weeks |
| 🏃 Intensive | 8–10 hrs   | All 24 chapters               | ~8 weeks  |

---

## Repo Structure

```
practice_git_intro_to_pr_automerge/
├── learning_modules/     # 24 chapters (chapter_XX_<topic>.md)
├── notebooks/            # practice notebooks (practice_XX.ipynb) + reference notebooks (lab_XX_<topic>.ipynb)
├── labs/                 # importable gate logic (lab_XX_<topic>.py)
├── sandbox/              # generate throwaway PRs of known size — the only paths the gates watch
├── notes/                # Task tracker + improvements ledger
├── research/             # Research reports (report_<topic>.md)
├── resources/             # Event/token reference cheatsheets
├── tests/                 # pytest suite
├── CLAUDE.md              # Project conventions & commands
├── requirements.in/.txt   # Dependencies
├── Makefile                # Common commands
└── .github/
    ├── instructions/       # Auto-applying format rules
    └── workflows/          # THE LIVE GATES — real, firing Actions
```

---

## How to Use This Repo

This repo provides three complementary artifacts per chapter, plus a fourth that is unique to
this curriculum: real, executing GitHub Actions.

### The Four Artifacts

| Artifact               | File                                     | Purpose                                                                                     |
| ----------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Chapter**             | `learning_modules/chapter_XX_<topic>.md` | Core reading — mechanics, trade-offs, the Airlock lens                                       |
| **Reference notebook**  | `notebooks/lab_XX_<topic>.ipynb`         | Annotated Jupyter companion, `PRA_MODE=fixture` by default so it runs identically for everyone |
| **Practice notebook**   | `notebooks/practice_XX.ipynb`            | Your coding sandbox — same structure, blank code cells                                       |
| **Live gate**           | `.github/workflows/gateN-*.yml`          | The real workflow this chapter builds toward — you push it and watch it fire on a real PR    |

### Recommended Learning Flow

```
1. Read  →  learning_modules/chapter_XX_<topic>.md        (mechanics + trade-offs)
2. Skim  →  labs/lab_XX_<topic>.py                         (importable, testable gate logic)
3. Read  →  notebooks/lab_XX_<topic>.ipynb                 (annotated reference, fixture mode)
4. Code  →  notebooks/practice_XX.ipynb                    (write it yourself)
5. Do    →  open a real PR against sandbox/ and watch the gate fire (see "Hands-On" table below)
```

---

## Getting Started

```bash
# 1. Navigate to this repo
cd practice_git_intro_to_pr_automerge

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
make install

# 4. Open in VS Code via workspace file
code _practice_git_intro_to_pr_automerge.code-workspace

# 5. Push this repo to GitHub as a PUBLIC repo (see "Why public" below)
gh repo create <you>/practice_git_intro_to_pr_automerge --public --source=. --push

# 6. Enable native auto-merge on the repo (off by default)
gh api -X PATCH /repos/<you>/practice_git_intro_to_pr_automerge -F allow_auto_merge=true

# 7. Start with Chapter 1
# Open: learning_modules/chapter_01_airlock_principle.md
# Then: notebooks/practice_01.ipynb
```

**Why public:** branch protection *and* rulesets — the mechanism every gate in this curriculum
depends on — are both gated behind GitHub Pro/Team on private repos under the Free plan. The
sandbox repo holds nothing sensitive (sample files and throwaway PRs only), so it defaults to
public rather than hitting that wall at Chapter 5.

**Why one repo does two jobs:** the curriculum and the live lab share a repo for simplicity. Every
gate workflow is scoped with `paths: ['sandbox/**']`, so opening a PR that edits
`learning_modules/`, `labs/`, or `notebooks/` never triggers auto-merge — only PRs touching
`sandbox/` do. See Chapter 17 §3.
