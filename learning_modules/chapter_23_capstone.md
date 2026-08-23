# Chapter 23: Capstone

**Reading Time:** ~65 minutes
**Prerequisites:** Chapter 17, Chapter 18, Chapter 19
**Practice Notebook:** `notebooks/practice_23.ipynb`
**Reference Notebook:** `notebooks/lab_23_capstone.ipynb`
**Script:** `labs/lab_23_capstone.py`
**Doc Reference:** This repo's own design -- no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Section 3 (the full-curriculum map) and Section 6 (the audit trail this
chapter finally builds) — everything else is detail supporting those two.

**What to SKIP on first read:** Nothing — this is the capstone; if you've read the prerequisite
chapters, every section here should land on already-familiar ground.

**Key concepts in plain English:**

- **Audit trail:** A durable, queryable record of every merge decision this system ever made,
  including every gate's rationale — not just a bare pass/fail, and not just for the moment the
  decision was made.
- **The one-command answer:** Chapter 01 §9 promised that "why did this merge?" would eventually
  have a single, fast answer. This chapter is where that promise is kept.
- **End-to-end:** Every piece from Chapters 01–22 — refs, events, tokens, three gates, composition,
  security, calibration — used together in one run, not studied in isolation.
- **Cold start:** Running this system against a repo state that assumes nothing has been set up yet
  — the practical test of whether the curriculum actually taught a *buildable* system, not just a
  readable one.

**Your prior knowledge connection:** If you've ever finished a long technical course with a final
project that makes you actually *use* everything instead of just having read about it, this chapter
plays that role — there's no new GitHub mechanism introduced here, only composition of what you
already have.

---

> **🔬 Automation Engineer's Lens:** A system is only as trustworthy as its explainability after
> the fact. Every gate in this curriculum returns a `GateResult` with a rationale, not a bare
> boolean — this was a design decision made in Chapter 01, restated in every chapter since, and
> only now, in this capstone, actually assembled into something a human can query six months later
> without re-deriving the logic from scratch. That gap between "the pieces exist" and "the system
> answers your question" is exactly what this chapter closes.

---

> **🚦 Native vs Custom:** Every native mechanism this curriculum relied on — required checks,
> native auto-merge, the Checks API, `workflow_run`, `permissions:` scoping — did the actual
> enforcement work throughout. What's fully custom, and what this capstone finally makes concrete,
> is the audit layer sitting on top: nothing about GitHub natively gives you a queryable "why did
> PR #301 merge" answer across your own three gates' combined verdict. That's the one piece this
> entire curriculum was building toward that had no native equivalent to lean on.

---

## What You'll Learn

- How every chapter's piece fits into one coherent system, reviewed end to end
- How to run this repo's complete airlock against a cold-start repo state
- How to build and query a durable audit trail, fulfilling Chapter 01 §9's promise
- What "done" looks like for a system like this — and what would still need attention beyond it
- How to extend this system with a fourth gate, using Chapter 17 §9's design property directly
- Where to go next, having completed the full 23-chapter arc

---

## Table of Contents

- [Chapter 23: Capstone](#chapter-23-capstone)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What This Chapter Is](#1-what-this-chapter-is)
  - [2. What You've Actually Built](#2-what-youve-actually-built)
  - [3. The Full Curriculum Map, Reviewed](#3-the-full-curriculum-map-reviewed)
  - [4. The One Piece Never Fully Assembled Until Now](#4-the-one-piece-never-fully-assembled-until-now)
  - [5. Composing the Full Airlock, Once More](#5-composing-the-full-airlock-once-more)
  - [6. Building the Audit Trail](#6-building-the-audit-trail)
  - [7. The One-Command Answer](#7-the-one-command-answer)
  - [8. Running This Against a Cold-Start Repo](#8-running-this-against-a-cold-start-repo)
  - [9. ⚠️ ADVANCED: What "Done" Doesn't Mean](#9-️-advanced-what-done-doesnt-mean)
  - [10. ⚠️ ADVANCED: Adding a Fourth Gate, For Real](#10-️-advanced-adding-a-fourth-gate-for-real)
  - [11. ⚠️ ADVANCED: Operating This in Production](#11-️-advanced-operating-this-in-production)
  - [12. Case Study: Two PRs, One Audit Log](#12-case-study-two-prs-one-audit-log)
  - [13. Case Study: What This Repo's Own Verification Log Already Demonstrated](#13-case-study-what-this-repos-own-verification-log-already-demonstrated)
  - [14. Practical Tips: Extending This System Responsibly](#14-practical-tips-extending-this-system-responsibly)
  - [15. Your Final Project: Fire the Airlock End to End](#15-your-final-project-fire-the-airlock-end-to-end)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Beyond This Curriculum](#18-whats-next-beyond-this-curriculum)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Audit Trail: Building and Querying It (from Section 15)](#a1--the-audit-trail-building-and-querying-it-from-section-15)

---

## 1. What This Chapter Is

Every prior chapter introduced something new — a Git concept, an Actions mechanic, one gate, one
hardening concern. This chapter introduces nothing new mechanically. It composes everything into
one final piece — a durable audit trail — and walks the complete system end to end, exactly the way
Chapter 01 §14 told you to read the whole curriculum in the first place: skim the callouts, read
the core sections in order, treat advanced topics as optional, do the hands-on step.

## 2. What You've Actually Built

By this point, you have: a working understanding of what a PR is at the Git level (Ch 02-03), how
to read and write PR data (Ch 04, 07), how Actions triggers/contexts/tokens/checks compose (Ch
08-13), three real, live-verified gates (Ch 14-16), their composition into one airlock with zero
direct coordination (Ch 17), a hardened understanding of the injection and `pull_request_target`
risks (Ch 18), a calibration practice for the one genuinely custom piece (Ch 19), and — from the
optional chapters — an understanding of merge queues, workflow reuse, and the buy-vs-build decision
(Ch 20-22). This isn't a toy. It's a real system, verified against a real repository throughout.

## 3. The Full Curriculum Map, Reviewed

```
Phase 1 (Ch 01-06)   What a PR IS at the Git level, and how merging actually works
Phase 2 (Ch 07-13)   The GitHub API and Actions mechanics: events, tokens, contexts, debugging
Phase 3 (Ch 14-17)   The three gates, built for real, composed with zero direct coordination
Phase 4 (Ch 18-23)   Harden it: security, calibration, merge queues, buy-vs-build, THIS capstone
```

Every phase built directly on the one before it — Phase 3's gates would have been unwritable
without Phase 2's token/event/context vocabulary; Phase 2's mechanics would have been confusing
without Phase 1's Git-level foundation.

## 4. The One Piece Never Fully Assembled Until Now

Chapter 01 §9 promised: "every gate in this curriculum returns a typed result... carrying a
rationale string... Chapter 23's capstone assembles these into a durable log so 'why did this
merge?' has a one-command answer." Every gate has, in fact, returned exactly that typed
`GateResult` since Chapter 01's own lab. What's been missing is the durable, queryable *log* —
this chapter builds it.

## 5. Composing the Full Airlock, Once More

This chapter's lab reuses `labs.lab_17_airlock.decide()` directly — no gate logic is reimplemented
here. This is deliberate: the capstone's job is to add the missing audit layer on top of an
already-correct composition, not to re-derive Chapter 17's work a second time.

```python
from labs.lab_17_airlock import decide

decision = decide(pr, main_exists=True, protection_configured=True,
                   required_checks_registered=True, auto_merge_enabled=True,
                   ci_conclusion="success")
```

## 6. Building the Audit Trail

```python
def build_audit_entry(decision: Decision) -> dict:
    return {
        "pr_number": decision.pr_number,
        "merge": decision.merge,
        "gates": [{"gate": g.gate, "status": g.status.value, "rationale": g.rationale}
                  for g in decision.gates],
    }
```

Each entry is appended, one JSON object per line, to a durable log file — a format chosen
specifically because it's append-only, human-readable, and trivially greppable without any special
tooling, matching the same "no unnecessary complexity" philosophy this repo's `automerge.yml`
(Chapter 17 §3) has followed throughout.

### What one audit line actually looks like

Here is the exact line the lab appends to `output/audit_log.jsonl` for PR #301 (the trivial typo
fix this chapter's lab decides in §12) — captured verbatim from a fixture-mode run of
`python labs/lab_23_capstone.py`:

```json
{"pr_number": 301, "merge": true, "gates": [{"gate": "gate1_repo_readiness", "status": "pass", "rationale": "main exists, protection configured, checks registered, auto-merge enabled"}, {"gate": "gate2_pr_health", "status": "pass", "rationale": "CI conclusion is 'success'"}, {"gate": "gate3_risk_scoring", "status": "pass", "rationale": "risk=5.9 <= threshold=70"}]}
```

**What to notice:**

- The three `gates` objects map one-to-one onto Chapters 14, 15, and 16 — each gate's name,
  `GateStatus` value, and rationale string serialized straight from the `GateResult` dataclass
  (`pr_automerge/models.py`), with nothing summarized away.
- `"risk=5.9 <= threshold=70"` is Gate 3's own rationale — the same 5.9 that Chapter 16's worked
  example computes for a 3-line, 1-file, zero-critical-path change, and that
  `tests/test_scoring.py` pins.
- The top-level `"merge": true` is the composed verdict — but it's the *rationales* that make this
  line auditable months later, which is why `build_audit_entry` keeps all of them.

## 7. The One-Command Answer

```python
def explain_decision(pr_number: int, log_path: Path) -> str:
    entries = [json.loads(line) for line in log_path.read_text().splitlines()]
    entry = [e for e in entries if e["pr_number"] == pr_number][-1]
    lines = [f"PR #{pr_number}: {'MERGED' if entry['merge'] else 'HELD'}"]
    for gate in entry["gates"]:
        lines.append(f"  {gate['gate']}: {gate['status'].upper()} — {gate['rationale']}")
    return "\n".join(lines)
```

Call this with any PR number ever decided, and get back every gate's exact rationale — this is
Chapter 01 §9's promise, kept: not a vague "it merged," but the full, gate-by-gate reasoning,
readable long after the original decision was made.

### The promise, kept — verbatim

State before: `output/audit_log.jsonl` holds the two entries §12's lab run appended. The one
command:

```python
print(explain_decision(301, log_path))
```

And its exact printed output, captured from a fixture-mode run of `python labs/lab_23_capstone.py`:

```
PR #301: MERGED
  gate1_repo_readiness: PASS — main exists, protection configured, checks registered, auto-merge enabled
  gate2_pr_health: PASS — CI conclusion is 'success'
  gate3_risk_scoring: PASS — risk=5.9 <= threshold=70
```

**What to notice:**

- Every gate's line is a sentence a human can audit — not a bare boolean. Twenty-two chapters of
  insisting on `GateResult.rationale` existed so these four lines could be printed.
- This is the same `Decision` object Chapter 17 §6 composes — `explain_decision` adds zero gate
  logic; it only renders what `decide()` already recorded.
- `risk=5.9` matches Chapter 16's worked example and `tests/test_scoring.py` exactly — the audit
  trail reports the engine's real number, not a re-derivation.
- The verdict says `MERGED`/`HELD` (past tense) where the live run's decision line says
  `MERGE`/`HOLD` — this is a *record* being read back, not a decision being made.

## 8. Running This Against a Cold-Start Repo

The truest test of whether this curriculum taught a *buildable* system: clone this repo fresh, run
`make install`, and — without any prior local state — run this chapter's lab (fixture mode needs
nothing further) or the full live pipeline against a freshly-forked sandbox repo (following Chapter
07's PAT-minting steps, Chapter 05's branch-protection setup, and Chapter 14's Gate 1 run to
initialize readiness). Every piece needed to do this cold-start has been covered — this chapter's
job is only to confirm you can actually assemble it.

## 9. ⚠️ ADVANCED: What "Done" Doesn't Mean

> ⚠️ **ADVANCED TOPIC:** Honest scope boundaries on what this curriculum built.
> **Skip on first read** — return once you're considering operating a system like this for real.

This system is complete for its own stated scope: three gates, composed through native mechanisms,
audited. It is **not**: a merge queue (Chapter 20 — add one only if your traffic pattern needs it),
a multi-repo rollout mechanism (Chapter 21's reusable workflows would need building out further),
a monitoring/alerting layer beyond the job summaries and audit log this curriculum built, or a
replacement for human judgment on PRs that don't fit its risk model's assumptions. Treating a
finished curriculum as a finished production system without addressing these gaps would be a
mistake this curriculum itself, via Chapter 22, explicitly warns against making uncritically.

## 10. ⚠️ ADVANCED: Adding a Fourth Gate, For Real

> ⚠️ **ADVANCED TOPIC:** Applying Chapter 17 §9's promise concretely.
> **Skip on first read** — return once you actually have a fourth condition to gate on.

Chapter 17 §9 promised that adding a fourth gate needs zero changes to `automerge.yml` — only a new
workflow publishing a new required check name, added to branch protection's list. This capstone's
audit trail needs exactly one addition to keep working: extend `decide()` to also evaluate the new
gate and include it in the composed `Decision`'s `gates` list — everything downstream (the audit
entry structure, `explain_decision`'s output) already generalizes to any number of gates without
modification, because `Decision.gates` was always typed as a list, never fixed at three.

## 11. ⚠️ ADVANCED: Operating This in Production

> ⚠️ **ADVANCED TOPIC:** What changes moving from a curriculum sandbox to a real, high-stakes repo.
> **Skip on first read.**

A production deployment of this system would want: the audit log persisted somewhere more durable
than a single runner's ephemeral filesystem (a committed file, per-PR comments, or an external
store), Chapter 19's calibration practice actually exercised on a recurring schedule against real
merged-PR history, Chapter 18's security checklist run against every workflow change before merge,
and — per Chapter 22 — a periodic re-examination of whether a third-party tool would now serve
better than continued custom maintenance. None of this changes the core mechanics this curriculum
taught; all of it is operational discipline layered on top.

## 12. Case Study: Two PRs, One Audit Log

This chapter's lab runs exactly this: a trivial, safe fix (PR #301) and a large migration (PR
#302) both decided and logged in the same run. Querying the log afterward for each PR
independently returns each one's full, correct rationale — #301's `MERGE` verdict with all three
gates' `PASS` reasons, #302's `HOLD` verdict naming Gate 3's hard-ceiling rationale specifically.
Neither entry interferes with the other; this is the durable, per-PR queryability the audit trail
exists to provide.

PR #301's explanation is shown in §7. Here is `explain_decision(302, log_path)`'s exact output
from the same fixture-mode run:

```
PR #302: HELD
  gate1_repo_readiness: PASS — main exists, protection configured, checks registered, auto-merge enabled
  gate2_pr_health: PASS — CI conclusion is 'success'
  gate3_risk_scoring: FAIL — 900 lines exceeds the hard ceiling of 500 — never auto-merged regardless of score
```

**What to notice:**

- Two gates passed, yet the PR held — the airlock fails closed on any single `FAIL`, and the log
  preserves *which* door stayed shut and why (700 additions + 200 deletions = 900 lines > the
  `hard_ceiling_lines: 500` from `gates.yml`, per Chapter 16 §5).
- The rationale cites the hard ceiling, not a risk score — the ceiling short-circuits regardless
  of score, exactly the behavior Chapter 16's `evaluate_gate3` implements.

## 13. Case Study: What This Repo's Own Verification Log Already Demonstrated

`notes/IMPROVEMENTS_SUMMARY.md`'s Live-Repo Verification Log — four real discoveries, each dated,
each with a concrete "verified live" claim — is itself an audit trail, just for this curriculum's
*build process* rather than for individual PR decisions. The same instinct (record what happened
and why, durably, so it's answerable later without re-deriving it) that motivated keeping that log
is exactly what motivates this chapter's `audit_log.jsonl`. You've been living inside this
philosophy since Chapter 01; this chapter just gives it its final, PR-decision-specific form.

## 14. Practical Tips: Extending This System Responsibly

```
Before adding to this system
──────────────────────────────────────
[ ] Does the new piece return a typed result with a rationale, like every existing gate?
[ ] Does it compose through a native mechanism (required checks) rather than custom coordination?
[ ] Is it captured in the audit trail, not just evaluated and discarded?
[ ] Has it been checked against Chapter 18's security checklist?
[ ] Is its threshold/config committed to a file (like gates.yml), never a bare constant?
```

## 15. Your Final Project: Fire the Airlock End to End

Against this repo's own sandbox: generate a real PR with `make pr LINES=50 FILES=3`, watch all
five real workflows fire, confirm the airlock's actual verdict, and then — separately — run this
chapter's lab to build a parallel audit-trail entry for a couple of representative PRs and query
`explain_decision` for each. Compare the *reasoning* your local audit trail produces against what
the real gates' published check runs and PR comment show for the real PR — they should describe
the same underlying logic, even though this lab's entries are separate, local records rather than
the live gates' own output.

Expected result for the local half: your `explain_decision(301, ...)` and `explain_decision(302,
...)` calls should print exactly the §7 and §12 blocks above — `PR #301: MERGED` with three `PASS`
lines, `PR #302: HELD` on the hard-ceiling `FAIL` — and `output/audit_log.jsonl` should hold two
lines shaped like §6's.

## 16. Common Pitfalls & Misconceptions

1. **"This capstone introduces new gate logic."** No — it reuses Chapter 17's `decide()` exactly;
   the only new piece is the audit layer on top.

2. **"An audit trail is optional polish, not core to the system."** Chapter 01 §9 treated it as a
   load-bearing design requirement from the very first chapter — it's not an afterthought.

3. **"Completing this curriculum means the system is production-ready."** Section 9 is explicit:
   completeness for the curriculum's stated scope isn't the same as production-readiness.

4. **"Adding a fourth gate requires rewriting the audit trail."** No — `Decision.gates` was always a
   list; the audit code generalizes to any number of gates with zero structural changes (Section
   10).

5. **"The audit log and this repo's own IMPROVEMENTS_SUMMARY.md ledger are unrelated."** They're
   the same underlying instinct — durable, dated, explainable records — applied at two different
   scopes (Section 13).

## 17. Key Takeaways

- **This chapter introduces no new mechanics** — it composes everything from Chapters 01–22 into
  one final piece: a durable audit trail.
- **Chapter 01 §9's promise is now kept** — every gate's typed rationale, assembled into a
  queryable log, answering "why did this merge?" with one function call.
- **The system is complete for its stated scope, not production-complete** — Section 9's honest
  boundary matters as much as anything built.
- **Adding a fourth gate needs no structural changes** to either `automerge.yml` (Chapter 17 §9) or
  this chapter's audit code (`Decision.gates` was always a list).
- **You've built a real, live-verified system**, not a toy — every claim in this curriculum was
  checked against this repo's actual sandbox, not asserted from theory alone.

## 18. What's Next: Beyond This Curriculum

There is no Chapter 24. From here: operate this system for real on a repo that matters to you,
watch Chapter 19's calibration practice earn its keep as your own PR patterns evolve, revisit
Chapter 22's buy-vs-build decision as your situation changes, and — if a real incident or near-miss
ever happens — add it to your own audit trail's story the same way this repo's own
`IMPROVEMENTS_SUMMARY.md` did for every real bug found building it.

## 19. Additional Resources

- **This repo's own** `notes/IMPROVEMENTS_SUMMARY.md` — the build-process audit trail this chapter's PR-level audit trail mirrors
- **This repo's own** `pr_automerge/models.py` — `Decision` and `GateResult`, the typed foundation every audit entry is built from
- **GitHub Docs, "About pull requests"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests (fetched 2026-08) — worth re-reading once, now that every mechanic behind it is familiar
- **GitHub Docs, "Automatically merging a pull request"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — The Audit Trail: Building and Querying It (from Section 15)

**What the code does:** Composes the full airlock for two sample PRs (reusing Chapter 17's
`decide()`), appends each verdict to a JSON-lines audit log, and answers "why did PR #N merge?"
for each with one function call.

**ASCII flowchart:**

```
decide(pr, ...) → Decision  (Chapter 17, reused unchanged)
        │
        ▼
build_audit_entry(decision) → {"pr_number", "merge", "gates": [...]}
        │
        ▼
append_audit_log(entry, log_path) → one JSON line per decision, durable

explain_decision(pr_number, log_path) → the most recent matching entry,
                                          rendered as a human-readable, gate-by-gate explanation
```

See `labs/lab_23_capstone.py` for the full runnable version.
