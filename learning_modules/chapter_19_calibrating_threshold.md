# Chapter 19: Calibrating the Threshold

**Reading Time:** ~50 minutes
**Prerequisites:** Chapter 16 (Gate 3 -- Risk Scoring)
**Practice Notebook:** `notebooks/practice_19.ipynb`
**Reference Notebook:** `notebooks/lab_19_calibrate.ipynb`
**Script:** `labs/lab_19_calibrate.py`
**Doc Reference:** This repo's own design -- no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 — the threshold sweep itself, and reading `gates.yml` as
the single source of truth for the current value.

**What to SKIP on first read:** Section 11 (statistical calibration against historical PR data).
Return once you have enough real merged-PR history to calibrate against — a single-repo curriculum
sandbox doesn't have that yet.

**Key concepts in plain English:**

- **Threshold drift:** A threshold that was right when a team's typical PR size was small becomes
  wrong (too strict or too lax) as PR patterns change — it's not a "set once" number.
- **Threshold sweep:** Running the same PR set through Gate 3's scoring formula at several
  candidate thresholds, to see concretely how many PRs would auto-merge at each — replacing
  intuition with a table.
- **False negative (too high):** A threshold set too loosely lets a genuinely risky PR through
  unattended — the cost of getting this wrong is a bad merge.
- **False positive (too low):** A threshold set too strictly blocks a genuinely safe PR from
  auto-merging — the cost of getting this wrong is unnecessary human review burden, not safety.
- **`gates.yml`:** The single committed file recalibration actually edits — never a source-code
  constant (Chapter 16 §9).

**Your prior knowledge connection:** If you've ever tuned an alert threshold on a monitoring system
— too sensitive means alert fatigue, too loose means you miss real incidents — Gate 3's threshold
calibration is the exact same trade-off, just applied to merge risk instead of infrastructure
alerts.

---

> **🔬 Automation Engineer's Lens:** A threshold set once at launch and never revisited is a
> silent, slowly-growing risk. Teams' typical PR size changes — a growing codebase means routine
> refactors touch more files; a maturing test suite means CI catches more, shifting what "safe"
> looks like. A threshold that was calibrated correctly on day one, left untouched for a year, is
> answering a question about a team that no longer exists.

---

> **🚦 Native vs Custom:** There's no GitHub feature for "is my auto-merge threshold well-
> calibrated" — this is entirely a property of your own scoring model, and entirely your
> responsibility to periodically re-examine. What GitHub gives you natively is the audit trail
> (every gate's rationale, Chapter 01 §9) that makes calibration *possible* — without those
> recorded verdicts, you'd have nothing to calibrate against.

---

## What You'll Learn

- Why a fixed threshold drifts out of correctness as PR patterns change over time
- How to run a threshold sweep against a known PR set and read the resulting table
- The false-negative vs false-positive trade-off, in this domain's specific terms
- How `gates.yml` and `pr_automerge.scoring.load_config` make recalibration a config edit
- What data you'd want to calibrate against with real historical PR history
- Why this repo's own worked example (Chapter 16 §8) is a fixed reference point, not a moving target

---

## Table of Contents

- [Chapter 19: Calibrating the Threshold](#chapter-19-calibrating-the-threshold)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Why a Threshold Needs Calibration At All](#1-why-a-threshold-needs-calibration-at-all)
  - [2. The Two Ways to Get It Wrong](#2-the-two-ways-to-get-it-wrong)
  - [3. The Sweep: Replacing Intuition With a Table](#3-the-sweep-replacing-intuition-with-a-table)
  - [4. Reading the Worked Example's Sweep](#4-reading-the-worked-examples-sweep)
  - [5. `gates.yml`: Where the Number Actually Lives](#5-gatesyml-where-the-number-actually-lives)
  - [6. `load_config`: From File to `RiskConfig`](#6-load_config-from-file-to-riskconfig)
  - [7. Recalibrating: The Actual Workflow](#7-recalibrating-the-actual-workflow)
  - [8. ⚠️ ADVANCED: The Hard Ceiling Doesn't Move With the Threshold](#8-️-advanced-the-hard-ceiling-doesnt-move-with-the-threshold)
  - [9. ⚠️ ADVANCED: Weight Calibration vs Threshold Calibration](#9-️-advanced-weight-calibration-vs-threshold-calibration)
  - [10. ⚠️ ADVANCED: A/B-Style Calibration in Practice](#10-️-advanced-ab-style-calibration-in-practice)
  - [11. ⚠️ ADVANCED: Calibrating Against Real Historical Data](#11-️-advanced-calibrating-against-real-historical-data)
  - [12. Case Study: A Threshold That Drifted Too Loose](#12-case-study-a-threshold-that-drifted-too-loose)
  - [13. Case Study: A Threshold That Drifted Too Strict](#13-case-study-a-threshold-that-drifted-too-strict)
  - [14. Practical Tips: A Recalibration Checklist](#14-practical-tips-a-recalibration-checklist)
  - [15. Your First Project: Sweep Your Own Repo's Real PRs](#15-your-first-project-sweep-your-own-repos-real-prs)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 20 — Merge Queues](#18-whats-next-chapter-20--merge-queues)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Loading Config and Sweeping Thresholds (from Section 15)](#a1--loading-config-and-sweeping-thresholds-from-section-15)

---

## 1. Why a Threshold Needs Calibration At All

Chapter 16 picked `DEFAULT_THRESHOLD = 70.0` so that "a ~100-line, ~5-file PR with no critical-path
touches sits comfortably under" it — a design choice tuned to a specific, assumed PR shape. If a
team's actual PRs grow larger over time (a maturing codebase, more files touched per routine
change), that same threshold silently stops matching the team it was calibrated for. Nothing alerts
you to this — the formula keeps computing correctly; it's the *target* that's drifted.

## 2. The Two Ways to Get It Wrong

```
Threshold too HIGH (too loose)              Threshold too LOW (too strict)
────────────────────────────────            ─────────────────────────────
Genuinely risky PRs auto-merge               Genuinely safe PRs get held
unattended                                    for human review unnecessarily
        │                                              │
        ▼                                              ▼
COST: a bad merge slips through              COST: review burden, slower
     -- a safety failure                          throughput -- an efficiency cost
```

These costs are not symmetric — a safety failure is typically far more expensive than an
unnecessary review — which is a real reason to err toward "too strict" over "too loose" when in
doubt, though the right balance point depends entirely on your own team's risk tolerance.

## 3. The Sweep: Replacing Intuition With a Table

Rather than guessing at a "right-feeling" number, sweep several candidate thresholds against a
known PR set and read off exactly which PRs would pass at each:

```python
def sweep_thresholds(prs, thresholds, config):
    for threshold in thresholds:
        # recompute risk at this threshold, count passes
        ...
```

This turns "does 70 feel right" into "at 70, exactly these 3 of 5 PRs would auto-merge — is that
the set I'd want to?" — a concrete, checkable question instead of a vibe.

## 4. Reading the Worked Example's Sweep

Running this chapter's lab against Chapter 16's five worked-example PRs, across candidate
thresholds 40/55/70/85/100:

| Threshold | Typo fix (5.9) | Small feature (66.0) | Workflow touch (67.0) | Refactor (172.0) | Large migration (hard ceiling) |
| --- | --- | --- | --- | --- | --- |
| 40 | MERGE | HOLD | HOLD | HOLD | HOLD |
| 55 | MERGE | HOLD | HOLD | HOLD | HOLD |
| 70 (default) | MERGE | MERGE | MERGE | HOLD | HOLD |
| 85 | MERGE | MERGE | MERGE | HOLD | HOLD |
| 100 | MERGE | MERGE | MERGE | HOLD | HOLD |

**What to notice:**

- The typo fix (5.9) merges at every swept threshold — no candidate in a realistic range holds it.
- The default of 70 is the exact crossing point for the small feature (66.0) and the workflow
  touch (67.0): a threshold of 65 would hold both; 70 admits both. The whole calibration debate
  for this PR set lives in that 55→70 gap.
- The refactor (172.0) holds across this entire sweep, but it's threshold-bound, not
  ceiling-bound: `test_lowering_threshold_can_flip_a_borderline_pr` in `tests/test_scoring.py`
  pins that at threshold 200.0 it merges (340 lines is still under the 500-line ceiling).
- The large migration **never** merges at ANY threshold — 900 lines exceeds the hard ceiling of
  500, so it's blocked before the weighted score is even compared (Section 8).

## 5. `gates.yml`: Where the Number Actually Lives

```yaml
weights:
  lines: 30.0
  files: 25.0
  critical_paths: 45.0

threshold: 70.0
hard_ceiling_lines: 500

critical_path_globs:
  - ".github/workflows/"
  - "pr_automerge/"
```

This file — not a Python constant — is what `gate3-score.yml`'s scoring step would read from in a
deployment that's recalibrated at least once (Chapter 16 §9 promised this design; this chapter is
where the file actually exists). Editing `threshold: 70.0` to a new value and committing is the
entire recalibration action.

## 6. `load_config`: From File to `RiskConfig`

```python
from pr_automerge.scoring import load_config

config = load_config("gates.yml")   # -> RiskConfig(weights=..., threshold=70.0, hard_ceiling_lines=500)
```

`load_config` reads the YAML, falling back to this module's own defaults for any key the file
omits — so a `gates.yml` that only overrides `threshold` still gets sensible weights and ceiling
without needing to restate them.

## 7. Recalibrating: The Actual Workflow

```
Recalibrating Gate 3's threshold
──────────────────────────────────────
[ ] Gather a representative PR set (this chapter's worked example, or real history -- Section 11)
[ ] Run sweep_thresholds() across a range of candidates
[ ] For each candidate, ask: "would I want exactly this set of PRs auto-merging unattended?"
[ ] Pick the threshold where the answer first becomes yes
[ ] Edit gates.yml's threshold value, commit, open a PR (this repo's own dogfooding loop)
[ ] Watch the next few real PRs and confirm the new threshold behaves as swept
```

## 8. ⚠️ ADVANCED: The Hard Ceiling Doesn't Move With the Threshold

> ⚠️ **ADVANCED TOPIC:** Why `hard_ceiling_lines` is a separate calibration axis from `threshold`.
> **Skip on first read** — Chapter 16 §5 already introduced the ceiling; this section is the
> calibration-specific implication.

Section 4's table showed the large migration PR held at every threshold from 40 to 100 — because
`compute_risk`'s linear formula alone can't express "this is simply too big, full stop," the hard
ceiling exists as an independent check (Chapter 16 §5). Recalibrating `threshold` alone never
changes this PR's outcome; recalibrating `hard_ceiling_lines` is a separate decision with its own
sweep, answering a different question ("what's the absolute largest diff I'd EVER auto-merge") from
what `threshold` answers ("within that limit, how risky is too risky"). Chapter 16 §5 works the
exact bracket: at the recalibrated threshold of 200.0, a 600-line PR scores 185.0 — passing on
score — and still holds on the ceiling.

## 9. ⚠️ ADVANCED: Weight Calibration vs Threshold Calibration

> ⚠️ **ADVANCED TOPIC:** Adjusting the weights themselves, not just the threshold.
> **Skip on first read.**

This chapter's sweep only varies `threshold`, holding `weights` fixed — the simpler, more common
calibration. A deeper recalibration adjusts the weights themselves (e.g., raising `critical_paths`
from 45.0 if critical-path touches are proving riskier in practice than the current weight
reflects) — a higher-dimensional sweep, since now every combination of weight values needs its own
evaluation against the PR set. Start with threshold-only calibration; only reach for weight
calibration once you have evidence a *specific dimension* (lines, files, or critical paths) is
mis-weighted relative to the others, not just that the overall bar is in the wrong place.

## 10. ⚠️ ADVANCED: A/B-Style Calibration in Practice

> ⚠️ **ADVANCED TOPIC:** Running two thresholds side by side before committing to one.
> **Skip on first read.**

A lower-risk way to validate a new threshold before fully committing: run Gate 3 at the *new*
threshold in "shadow mode" — compute and log the verdict it would have produced, without actually
gating the merge on it — alongside the current, live threshold for some window of real PRs. Compare
the two logs' verdicts before switching over. This repo's own single-maintainer sandbox doesn't
need this level of caution (Section 7's simpler sweep-then-commit loop is proportionate to its
risk), but a production system merging dozens of PRs daily would.

## 11. ⚠️ ADVANCED: Calibrating Against Real Historical Data

> ⚠️ **ADVANCED TOPIC:** Using real merged-PR history instead of a fixed worked example.
> **Skip on first read** — return once you have enough real PR history in your own repo to make
> this worthwhile.

The strongest calibration input isn't a curated worked example — it's your own repo's real merged
PRs, each labeled after the fact with whether it turned out to need extra scrutiny (a revert, a
hotfix, a "this should have gotten more review" retrospective note). Sweeping thresholds against
that labeled history directly answers "what threshold would have correctly separated the PRs that
needed review from the ones that didn't," which is the actual question calibration is trying to
answer — Chapter 16's worked example is a fixed, illustrative stand-in for this real process.

## 12. Case Study: A Threshold That Drifted Too Loose

A team's typical PR grows from ~100 lines to ~250 lines over a year as the codebase matures and
routine changes touch more generated/config files. A threshold set for the smaller era now lets
250-line PRs through that would have been held a year earlier — not because the formula changed,
but because the *population* of PRs shifted underneath a static number. Section 4's sweep table,
re-run periodically against recent real PRs, is exactly what would surface this drift before it
becomes a genuine incident.

## 13. Case Study: A Threshold That Drifted Too Strict

The opposite case: a team invests in better test coverage and stricter linting over time, making
CI (Gate 2) a much stronger safety net than it was when the threshold was first set. A threshold
calibrated for a weaker CI setup is now unnecessarily conservative — safe PRs that CI would have
caught any real problem in are still being held for human review that adds no safety value, just
latency. This is the "too strict" cost from Section 2, and it's just as real a calibration failure
as the "too loose" case, even though it never shows up as an incident.

## 14. Practical Tips: A Recalibration Checklist

```
Before changing threshold: 70.0 in gates.yml
──────────────────────────────────────────────
[ ] Run the sweep against your best available PR set (worked example, or real history)
[ ] Confirm the new value doesn't change the hard-ceiling PRs' outcome (Section 8 -- it can't)
[ ] Write down WHY, in the PR description that changes gates.yml -- this is itself an audit trail
[ ] Watch the next handful of real PRs against the new threshold before considering it settled
```

## 15. Your First Project: Sweep Your Own Repo's Real PRs

Against any repo with real merged-PR history: pull the last 20 merged PRs' additions/deletions/
changed_files (Chapter 04's `gh pr list` + normalization pattern), build `PRMetadata` objects for
each, and run this chapter's `sweep_thresholds` against them at several candidate values. Compare
the result against your own memory of which of those PRs, in hindsight, actually needed a human
look — that comparison is the real calibration signal Section 11 describes.

## 16. Common Pitfalls & Misconceptions

1. **"A threshold, once set correctly, stays correct."** No — it drifts as the population of PRs it
   scores changes over time (Sections 12–13).

2. **"Raising the threshold is always the 'safer' direction."** No — raising it lets MORE PRs
   through unattended (Section 2); lowering it is the direction that reduces safety risk, at the
   cost of more human review burden.

3. **"Recalibrating the threshold also changes the hard ceiling."** No — they're independent
   dimensions; the ceiling requires its own separate calibration (Section 8).

4. **"I should adjust the weights whenever the threshold feels wrong."** Start with threshold-only
   calibration (Section 3's simpler sweep) — only adjust weights once you have specific evidence one
   dimension is mis-weighted (Section 9).

5. **"Without real historical data, calibration is impossible."** Not entirely — a curated worked
   example (Chapter 16's five PRs) is a reasonable starting reference point; it's just weaker
   evidence than real, labeled history (Section 11).

## 17. Key Takeaways

- **A fixed threshold silently drifts** as a team's real PR patterns change — recalibration is an
  ongoing practice, not a one-time setup step.
- **The sweep replaces intuition with a table**: run several candidate thresholds against a known
  PR set and read off exactly what changes.
- **The costs of "too loose" and "too strict" are asymmetric** — a bad merge is typically far more
  expensive than an unnecessary review, a real reason to err toward strict when uncertain.
- **`gates.yml` is where the number actually lives** — recalibration is a config-file edit, never a
  source-code change, exactly per Chapter 16 §9's design promise.
- **The hard ceiling and the threshold are independent calibration axes** — moving one never moves
  the other.

## 18. What's Next: Chapter 20 — Merge Queues

Chapter 20 (an optional deep-dive) covers what changes once a single repo has *many* simultaneously
-ready PRs: auto-merge alone answers "should this PR merge," but not "in what order, re-tested
against a constantly-moving `main`" — the question a merge queue exists to answer.

[→ Chapter 20: Merge Queues](chapter_20_merge_queues.md)

## 19. Additional Resources

- **This repo's own** `gates.yml` — the live config file this chapter's recalibration workflow edits
- **This repo's own** `pr_automerge/scoring.py` — `load_config`'s full implementation
- **This repo's own** `fixtures/pr_*.json` — the five worked-example PRs this chapter sweeps
- **Google SRE Workbook, "Alerting on SLOs"** — background on the same false-positive/false-negative trade-off applied to monitoring thresholds — https://sre.google/workbook/alerting-on-slos/ (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Loading Config and Sweeping Thresholds (from Section 15)

**What the code does:** Loads `gates.yml` into a `RiskConfig`, loads the five worked-example PR
fixtures, and sweeps several candidate thresholds against them, printing a pass/hold table for
each.

**ASCII flowchart:**

```
load_config("gates.yml") → RiskConfig(weights, threshold=70.0, hard_ceiling_lines=500)
load_worked_example() → [PRMetadata, PRMetadata, ...]  (5 PRs)
        │
        ▼
sweep_thresholds(prs, [40, 55, 70, 85, 100], config)
    → {threshold: [(title, risk, passes), ...]}
```

See `labs/lab_19_calibrate.py` for the full runnable version.
