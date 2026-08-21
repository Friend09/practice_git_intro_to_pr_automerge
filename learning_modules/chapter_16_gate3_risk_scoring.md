# Chapter 16: Gate 3 — Risk Scoring

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 04 (Reading PR Data), Chapter 15 (Gate 2 — PR Health)
**Practice Notebook:** `notebooks/practice_16.ipynb`
**Reference Notebook:** `notebooks/lab_16_risk_scoring.ipynb`
**Script:** `labs/lab_16_risk_scoring.py`
**Doc Reference:** This repo's own design — no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 (the scoring model itself) and Section 8 (the worked
example table — memorize its shape, not its numbers). This is the chapter that decides whether
your auto-merge system is trustworthy or dangerous.

**What to SKIP on first read:** Section 10 (calibration theory). Return after Chapter 19, once
you have real merged-PR history to calibrate against.

**Key concepts in plain English:**

- **Risk score:** A number computed from a PR's diff — more lines, more files, more
  security-sensitive paths touched, all push it *up*.
- **Threshold:** The line a risk score must stay *under* to auto-merge. Above it, a human looks.
- **Hard ceiling:** A size limit that blocks auto-merge outright, regardless of score — a safety
  net for the case where the linear scoring formula alone would let something huge slip through.
- **Blocker:** A rule that isn't part of the weighted score at all — it's a separate pass/fail gate
  that overrides everything (Gates 1 and 2 are, structurally, blockers relative to Gate 3).

**Your prior knowledge connection:** If you've ever eyeballed a PR and thought "this is way too
big to review carefully in five minutes," you already have the intuition this chapter formalizes.

---

> **🔬 Automation Engineer's Lens:** A scoring model that "usually seems right" is worse than no
> scoring model at all, because it earns trust it hasn't verified. The only thing that makes a
> risk score defensible is that its *direction* is stated explicitly and never silently flips —
> Section 7 exists because this exact curriculum's own prior art disagreed with itself about which
> way the number should run.

---

> **🚦 Native vs Custom:** GitHub has no native "is this diff too risky" feature — there is no
> platform setting for this. Everything in this chapter is fully custom, which is exactly why it
> gets the most scrutiny of any chapter in the curriculum: nothing here is GitHub second-guessing
> your logic for you.

---

## What You'll Learn

- Why this repo scores **risk** (higher = more dangerous), not readiness (higher = more ready)
- The exact formula this repo uses, and how to read/modify its weights
- Why a hard line-count ceiling exists on top of the weighted formula, not instead of it
- The fail-closed contrast with this curriculum's prior-art POC, in code, not just theory
- How to carry a worked example from formula to code to a real PR's verdict
- Where scoring config should live (never as bare constants) and why

---

## Table of Contents

- [Chapter 16: Gate 3 — Risk Scoring](#chapter-16-gate-3--risk-scoring)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What Gate 3 Answers](#1-what-gate-3-answers)
  - [2. Inputs: The PR Fact Sheet](#2-inputs-the-pr-fact-sheet)
  - [3. The Formula](#3-the-formula)
  - [4. Reading the Formula, Piece by Piece](#4-reading-the-formula-piece-by-piece)
  - [5. The Hard Ceiling](#5-the-hard-ceiling)
  - [6. The Merge Decision](#6-the-merge-decision)
  - [7. Which Way Does Your Score Run?](#7-which-way-does-your-score-run)
  - [8. Worked Example: Five PRs](#8-worked-example-five-prs)
  - [9. ⚠️ ADVANCED: Config, Not Constants](#9-️-advanced-config-not-constants)
  - [10. ⚠️ ADVANCED: Calibration, Previewed](#10-️-advanced-calibration-previewed)
  - [11. ⚠️ ADVANCED: What Critical Paths Should Include](#11-️-advanced-what-critical-paths-should-include)
  - [12. Case Study: The Prior-Art Fail-Open Bug](#12-case-study-the-prior-art-fail-open-bug)
  - [13. Case Study: A Borderline PR](#13-case-study-a-borderline-pr)
  - [14. Practical Tips: Testing a Scoring Engine](#14-practical-tips-testing-a-scoring-engine)
  - [15. Your First Project: Score Real PRs](#15-your-first-project-score-real-prs)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 17 — Wiring the Airlock](#18-whats-next-chapter-17--wiring-the-airlock)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Risk-Scoring Engine (from Sections 3–6)](#a1--the-risk-scoring-engine-from-sections-36)

---

## 1. What Gate 3 Answers

Gates 1 and 2 answer yes/no questions: is the repo ready, did CI pass. Gate 3 answers a judgment
question — given a *healthy* PR, is its size and shape safe to merge without a human looking? A
PR can pass every other gate and still be the kind of change a team wants eyes on before it lands.

## 2. Inputs: The PR Fact Sheet

Gate 3 consumes exactly the normalized PR data Chapter 07's pagination-aware fetch produces:

```python
PRMetadata(
    number=42, title="...", base="main", head="feat/x",
    additions=100, deletions=20, changed_files=6,
    critical_path_hits=0,   # files matching a configured "sensitive path" glob
)
```

`lines_changed` is `additions + deletions` — a rename-heavy PR with balanced adds/deletes scores
the same as one with the same total churn concentrated as pure additions, which is a deliberate
simplification, not an oversight (Section 11 revisits it).

## 3. The Formula

```python
RISK_WEIGHTS = {"lines": 30.0, "files": 25.0, "critical_paths": 45.0}
DEFAULT_THRESHOLD = 70.0
HARD_CEILING_LINES = 500

risk = (lines_changed / 100.0) * W["lines"] \
     + (files_changed / 5.0)   * W["files"] \
     + critical_path_hits      * W["critical_paths"]
```

In plain English: every 100 lines changed contributes 30 points; every 5 files touched contributes
25 points; every critical-path file touched contributes 45 points, flat, per file. There is no
upper bound on the formula itself — that's what Section 5's ceiling is for.

## 4. Reading the Formula, Piece by Piece

| Term | What it represents | Why this weight |
| --- | --- | --- |
| `lines_changed / 100 * 30` | Raw diff size | The single biggest, most reliable proxy for "how much a reviewer would need to read" |
| `changed_files / 5 * 25` | Diff spread | A PR touching many small files is harder to reason about as a unit than one touching few |
| `critical_path_hits * 45` | Sensitive-area touches | Flat per-file, not normalized — touching *any* critical path is disproportionately risky, on purpose |

## 5. The Hard Ceiling

The linear formula alone has a blind spot: a single enormous file with zero critical-path hits and
few total files could, in principle, score deceptively low on the `files` and `critical_paths`
terms while still being 900 lines a human should see. The hard ceiling closes that gap:

```python
if lines_changed > HARD_CEILING_LINES:
    return FAIL, "exceeds hard ceiling, regardless of score"
```

No score, however low, overrides this. It is deliberately the one rule in this chapter that is not
a weighted contribution to a formula — it's a blocker, structurally identical in kind to "did CI
pass" from Gate 2.

## 6. The Merge Decision

```python
merge = (risk <= threshold) and (lines_changed <= HARD_CEILING_LINES) and gate1_ready and gate2_pass
```

Gate 3 in isolation only computes its own `risk <= threshold and not ceiling_hit` — Chapter 17
composes it with Gates 1 and 2 into the full decision above.

## 7. Which Way Does Your Score Run?

This is the section that exists because this exact curriculum's own design brief and its own
prior-art code disagreed with each other.

| Model | What a high number means | Merge condition | Where it's used |
| --- | --- | --- | --- |
| **Pure risk (this repo)** | Dangerous | `risk <= threshold` | `pr_automerge/scoring.py` — everything built in this curriculum |
| **Readiness ratio** | Ready to merge | `score >= threshold` | `pr-auto-approve-poc/src/pr_gate/engine.py` — the earlier prototype this curriculum references throughout |
| **Confidence with penalties** | Confident it's safe | `score >= threshold`, but size *subtracts* rather than adds | A hybrid some teams use — not implemented here, mentioned for completeness |

The prototype's model (`score = earned_weight / total_weight`, merge at `>= 0.9`) is not wrong —
it answers a different, equally valid question ("how many of my quality signals passed?") rather
than this chapter's question ("how much unreviewed risk is in this diff?"). What's *not* valid is
mixing the two conventions in one pipeline, which is exactly the trap a copy-pasted rule from one
model into the other would fall into: a `>=` comparison pasted into a risk-scored system inverts
its entire meaning silently, with no error, no warning — just PRs merging exactly backwards from
intent. State your direction once, in one place (`RiskConfig` and this section), and never let a
new rule get added without checking which convention it assumes.

## 8. Worked Example: Five PRs

The same five PRs, threaded through this chapter, the reference notebook, and
`tests/test_scoring.py` — change one, and all three must agree.

| PR | Lines | Files | Critical | Risk | vs 70 | Verdict |
| -- | ----: | ----: | -------: | ---: | ----- | ------- |
| Typo fix | 3 | 1 | 0 | 5.9 | ≤ 70 | ✅ auto-merge |
| Small feature | 120 | 6 | 0 | 66.0 | ≤ 70 | ✅ auto-merge |
| Touches `.github/workflows/` | 40 | 2 | 1 | 67.0 | ≤ 70 | ⚠️ 3 points from blocking |
| Refactor | 340 | 14 | 0 | 172.0 | > 70 | ❌ hold for human |
| Large migration | 900 | 30 | 2 | 510.0 | ceiling | ❌ hold — hard ceiling |

In plain English: the "small feature" row shows the formula working as intended — comfortably
under threshold. The "touches workflows" row shows why the flat critical-path weight matters: a
much smaller diff (40 lines, 2 files) sits closer to the threshold than the small feature purely
because of *where* it touches. The "large migration" row never reaches the threshold comparison at
all — it's caught by the ceiling first.

## 9. ⚠️ ADVANCED: Config, Not Constants

> ⚠️ **ADVANCED TOPIC:** Why weights and thresholds live in `gates.yml`, not bare Python
> constants.
> **Skip on first read** — return once you're ready to tune this for a real repo.

The prototype hard-codes `DEFAULT_THRESHOLD = 0.9` and a coverage minimum with no override
mechanism at all. This repo's `RiskConfig` dataclass is deliberately constructed so every value —
weights, threshold, ceiling — can be overridden without touching source: from `gates.yml`, or at
the command line via `PRA_THRESHOLD`. Chapter 19's calibration work is only possible because this
chapter refused to hard-code the numbers it's tuning.

## 10. ⚠️ ADVANCED: Calibration, Previewed

> ⚠️ **ADVANCED TOPIC:** How you'd know if 70 is the right threshold.
> **Skip on first read** — Chapter 19 is the full treatment.

70 is a starting point, not a proven-correct value. The only way to know if it's right is to run
it, retroactively, against PRs your team already merged and ask: would this threshold have flagged
anything that turned out fine, or waved through anything that later caused a problem? Chapter 19
builds `lab_19_calibrate.py` to do exactly that.

## 11. ⚠️ ADVANCED: What Critical Paths Should Include

> ⚠️ **ADVANCED TOPIC:** Choosing your own critical-path globs.
> **Skip on first read.**

This repo's own gate3 workflow treats `.github/workflows/**` and `pr_automerge/**` as critical —
the automation's own control surface. A real team's list is specific to what would be expensive to
get wrong: auth code, payment logic, database migrations, infrastructure-as-code. There's no
universal list; Chapter 19's calibration work is the mechanism for discovering yours empirically
rather than guessing.

## 12. Case Study: The Prior-Art Fail-Open Bug

Revisit Chapter 01 §3's example with the actual code now in view. The prototype's rule:

```python
if not payload:
    return "skip", "no signal"     # removed from BOTH numerator and denominator
```

applied to a *blocker* rule means a security scanner that never ran contributes nothing to either
side of the ratio — a PR with a crashed scanner can outscore one where the scanner ran clean. This
repo's Gate 2 (Chapter 15) is the direct, deliberate rebuttal: a missing CI conclusion is coded as
an explicit `FAIL`, never a `SKIP`. Gate 3 itself never returns `SKIP` at all — PR metadata is
always available the moment a PR exists, so there's no missing-data case to get wrong here in the
first place; the lesson is inherited from how it composes with Gate 2 in Chapter 17.

## 13. Case Study: A Borderline PR

The "touches workflows" row from Section 8 is the interesting case, not the extremes. 67 against a
threshold of 70 is close enough that a small change to the weights — or a slightly larger diff on
the same PR — flips the verdict. This is precisely the kind of PR Chapter 19's calibration exists
to examine: is 70 actually the right line, or did it happen to land just above this one PR by
coincidence?

## 14. Practical Tips: Testing a Scoring Engine

```
Testing a risk-scoring formula
─────────────────────────────────
[ ] Pin exact expected scores for known inputs (not just pass/fail)
[ ] Test the hard ceiling independently of the weighted formula
[ ] Test that lowering the threshold can flip a borderline PR's verdict
[ ] Test the direction explicitly: a bigger PR must never score LOWER
[ ] Never let "config" and "code" disagree -- one source of truth for weights
```

## 15. Your First Project: Score Real PRs

Use `sandbox/generate_pr.py` to produce the five sizes from Section 8's table against the real
sandbox repo, then run `python labs/lab_16_risk_scoring.py --pr <N>` (live mode) against each and
confirm your local run matches what Gate 3's workflow published as a check run on GitHub.

## 16. Common Pitfalls & Misconceptions

1. **"A higher score is always worse, in every scoring system."** Only in *this* repo's
   convention. The prototype's readiness score is the opposite — Section 7 exists because this
   confusion is exactly what motivated the whole curriculum.

2. **"The hard ceiling is redundant with the weighted formula."** It isn't — it exists precisely
   for the diff shape (huge, but few files, no critical paths) the formula alone underweights.

3. **"70 is a scientifically derived number."** It's a reasonable starting point. Chapter 19 is
   the process for finding out if it's actually right for your team's PRs.

4. **"Gate 3 needs Gates 1 and 2 to compute its own score."** No — Gate 3's risk computation only
   needs PR metadata. Composing it with the other two gates' verdicts happens in Chapter 17.

5. **"Weights should be hard-coded for reproducibility."** The opposite — hard-coded weights are
   what made the prototype's threshold impossible to tune without a code change. Config makes
   reproducibility *and* tunability both possible, via a committed `gates.yml`.

## 17. Key Takeaways

- **Gate 3 answers a judgment question**, not a yes/no one: is this diff small/safe enough to
  merge unattended.
- **The formula is linear and explicit** — lines, files, and critical-path touches each contribute
  a weighted amount, with no hidden terms.
- **A hard ceiling exists on top of the formula**, catching the shape of PR the linear model alone
  would underweight.
- **State your score's direction once, explicitly, and never let it silently flip** — this
  chapter's entire Section 7 exists because it once nearly did, inside this very curriculum's
  design process.
- **Config, not constants** — every tunable number lives somewhere other than bare Python, so
  Chapter 19's calibration work is possible at all.

## 18. What's Next: Chapter 17 — Wiring the Airlock

Chapter 17 composes all three gates into one decision, chains the workflows that implement them,
and walks through the two real bugs this curriculum's own build hit doing exactly that — including
the `workflow_run` SHA-chaining trap and the `GITHUB_TOKEN` auto-merge restriction from Chapter 06.

[→ Chapter 17: Wiring the Airlock](chapter_17_wiring_the_airlock.md)

## 19. Additional Resources

- **`pr_automerge/scoring.py`** — this chapter's full, tested implementation, in this repo
- **`proj_AI/dev/pr-auto-approve-poc/src/pr_gate/engine.py`** — the readiness-scoring prior art referenced in Section 7 and Section 12
- **`proj_AI/research/research_pr_auto_review_scoring_system.md`** — the unbuilt design roadmap that first proposed a nine-dimension weighted score and tiered thresholds; a preview of how far Section 11's "choose your own critical paths" idea can be extended

## 20. Appendix A — Code Index

### A.1 — The Risk-Scoring Engine (from Sections 3–6)

**What the code does:** Computes the weighted risk score from Section 3, applies the hard ceiling
from Section 5, and returns a typed `GateResult` with a rationale string — never a bare boolean.

**ASCII flowchart:**

```
Inputs: PRMetadata, RiskConfig
    ↓
risk = weighted sum of lines/files/critical_paths (Section 3)
    ↓
lines_changed > ceiling?  ──yes──▶  FAIL "exceeds hard ceiling"
    │no
    ▼
risk <= threshold?  ──no──▶  FAIL "risk={risk} > threshold={threshold}"
    │yes
    ▼
PASS "risk={risk} <= threshold={threshold}"
```

See `pr_automerge/scoring.py` → `compute_risk()` and `evaluate_gate3()` for the full
implementation, and `tests/test_scoring.py` for the pinned five-row worked example from Section 8.
