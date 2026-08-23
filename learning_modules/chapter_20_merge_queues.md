# Chapter 20: Merge Queues

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 17 (Wiring the Airlock)
**Practice Notebook:** `notebooks/practice_20.ipynb`
**Reference Notebook:** `notebooks/lab_20_merge_queues.ipynb`
**Script:** `labs/lab_20_merge_queues.py`
**Doc Reference:** GitHub Docs "Merging a pull request with a merge queue"
**Depth:** ⭐ Optional Deep-Dive

---

## Beginner's Guide

**What to focus on first:** Sections 3–6 — the exact gap auto-merge leaves open, and how a queue
closes it.

**What to SKIP on first read:** Section 10 (merge queue's own required-check semantics, which
differ subtly from ordinary branch protection). Return once you're actually configuring one.

**Key concepts in plain English:**

- **Merge queue:** A GitHub feature that serializes several simultaneously-ready PRs, testing each
  one (or a batch) against a speculative, updated base branch that already includes the PRs ahead
  of it in the queue.
- **Semantic conflict:** Two PRs that each individually apply cleanly and pass CI, but whose
  *combined* effect breaks something neither PR's own test run could have caught alone.
- **Speculative base:** The queue's internal, temporary combination of `main` plus every PR ahead
  in line — what each queued PR is actually tested against, not the real `main` as it existed when
  the PR was opened.
- **Batching:** A queue can test several PRs together as one speculative combination, not just one
  at a time — trading some latency for throughput.
- **"Should this PR merge" vs "in what order":** Auto-merge (Chapters 06, 17) only ever answers the
  first question, one PR at a time. A queue exists specifically to answer the second.

**Your prior knowledge connection:** If you've ever had two PRs each pass CI independently, merge
one after another, and then watched the *second* merge silently break something the first
introduced — even though neither PR's own tests ever failed — you've already experienced exactly
the gap this chapter is about.

---

> **🔬 Automation Engineer's Lens:** This repo's own design — required checks plus native
> auto-merge, described across Chapters 06/14/17 as complete — is complete for its actual traffic
> pattern: a handful of PRs, opened and merged one at a time, in this curriculum's own sandbox.
> That completeness is conditional. The moment PR volume rises enough that two PRs are routinely
> "ready" at the same moment, the composition this curriculum spent three chapters building stops
> being sufficient, silently, with no error anywhere — it just starts occasionally producing
> semantic conflicts nobody's tests caught.

---

> **🚦 Native vs Custom:** GitHub's merge queue is a native, first-class feature — you enable it in
> branch protection settings; you don't build the serialization or speculative-testing logic
> yourself. What you decide, entirely on your own judgment, is *whether* your traffic pattern has
> crossed the threshold where you need it — nothing in GitHub tells you this; Section 12's
> heuristic is the closest thing to native guidance available.

---

## What You'll Learn

- The exact gap between "does this PR merge" and "in what order do several ready PRs merge"
- What a semantic conflict is, and why passing CI independently doesn't rule one out
- How a merge queue's speculative base branch closes this gap
- The trade-off between per-PR queuing and batched queuing
- How merge queue's required-check semantics differ subtly from ordinary branch protection
- A concrete heuristic for when this repo's own simpler design would need to add a queue

---

## Table of Contents

- [Chapter 20: Merge Queues](#chapter-20-merge-queues)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. The Question Auto-Merge Never Answers](#1-the-question-auto-merge-never-answers)
  - [2. A Semantic Conflict, Concretely](#2-a-semantic-conflict-concretely)
  - [3. Why Each PR's Own CI Run Can't Catch This](#3-why-each-prs-own-ci-run-cant-catch-this)
  - [4. The Speculative Base Branch](#4-the-speculative-base-branch)
  - [5. Serializing the Queue](#5-serializing-the-queue)
  - [6. Comparing the Two Strategies Side by Side](#6-comparing-the-two-strategies-side-by-side)
  - [7. Enabling a Merge Queue](#7-enabling-a-merge-queue)
  - [8. ⚠️ ADVANCED: Batching Multiple PRs](#8-️-advanced-batching-multiple-prs)
  - [9. ⚠️ ADVANCED: Queue Latency vs Throughput](#9-️-advanced-queue-latency-vs-throughput)
  - [10. ⚠️ ADVANCED: Required Checks Under a Merge Queue](#10-️-advanced-required-checks-under-a-merge-queue)
  - [11. Case Study: The Feature-Flag Collision](#11-case-study-the-feature-flag-collision)
  - [12. Case Study: When This Repo Would Actually Need One](#12-case-study-when-this-repo-would-actually-need-one)
  - [13. Practical Tips: Deciding Whether You Need a Queue](#13-practical-tips-deciding-whether-you-need-a-queue)
  - [14. Your First Project: Reproduce the Conflict Yourself](#14-your-first-project-reproduce-the-conflict-yourself)
  - [15. Your Second Project: Simulate a Larger Queue](#15-your-second-project-simulate-a-larger-queue)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 21 — Reusable Workflows \& Composite Actions](#18-whats-next-chapter-21--reusable-workflows--composite-actions)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Parallel Auto-Merge vs a Queue Simulation (from Section 14)](#a1--parallel-auto-merge-vs-a-queue-simulation-from-section-14)

---

## 1. The Question Auto-Merge Never Answers

Chapter 01 §4 phrased Gate 2/Gate 3 as answering "did *this* PR's build succeed" and "is *this*
diff safe" — always singular, always about one PR in isolation. Native auto-merge (Chapter 06)
enrolls PRs the same way: one at a time, each evaluated independently against whatever `main`
looked like when its own checks ran. Nothing in this design ever asks: "if PR A and PR B *both*
merge around the same time, does the combination still work?"

## 2. A Semantic Conflict, Concretely

Two PRs both edit `config/feature_flags.yml` — PR A adds a new flag at line 12, PR B removes an
unrelated flag at line 40. Neither PR's diff touches the same *lines* as the other, so Git itself
sees no textual conflict — both apply cleanly. But if the two flags interact (B's removed flag was
a dependency A's new flag assumed still existed), the combined file is broken in a way neither PR's
own isolated CI run — tested against `main` *before* the other PR merged — could ever have caught.

### Spot the Diff: Two Green PRs, One Broken File

**State before** — `config/feature_flags.yml` at `main` (`0f1e2d3c4b5a…`), the commit both PRs
branched from (trimmed excerpt):

```yaml
flags:
  search_v2: true             # line 11
# … lines 13–38 unchanged …
  legacy_payment_path: true   # line 40 — fallback route, currently unreferenced
```

**PR #201 (A)** adds one flag at line 12 — CI against `main + A`: **green**:

```diff
   search_v2: true
+  new_checkout: true          # falls back to legacy_payment_path on payment error
```

**PR #202 (B)** removes one "unused" flag at line 40 — CI against `main + B`: **green**:

```diff
-  legacy_payment_path: true   # line 40 — fallback route, currently unreferenced
```

**State after both merge** — what `main` actually contains:

```yaml
flags:
  search_v2: true
  new_checkout: true          # falls back to legacy_payment_path on payment error
# … lines 13–38 unchanged …
                              # legacy_payment_path is gone — the fallback points at nothing
```

A's run was green because `legacy_payment_path` still existed in `main + A`; B's run was green
because in `main + B` no flag referenced the one being removed. Only the combination breaks.

**What to notice:**

- Line 12 and line 40 never overlap — Git merges both diffs cleanly, with **zero** textual conflict.
- Each PR's CI verdict was honest *for the tree it tested* — the other PR's edit simply wasn't in it.
- The bug exists in no diff and no tested tree; it exists only in the pair — which is why no
  single-PR gate (Gate 2, Gate 3, required checks) can ever be positioned to catch it.

## 3. Why Each PR's Own CI Run Can't Catch This

CI for PR A runs against `main` + PR A's changes. CI for PR B runs against `main` + PR B's changes.
Neither run ever sees `main` + PR A + PR B combined — that combination doesn't exist as a real,
testable branch until *after* both merges have already happened. By the time the semantic conflict
is visible, it's already on `main`.

## 4. The Speculative Base Branch

A merge queue closes this gap by constructing a **speculative** branch — `main` plus every PR
already ahead of this one in the queue — and running CI against *that*, not against plain `main`.
If PR B is queued behind PR A, B's CI run tests `main + A + B`, not just `main + B`. The semantic
conflict from Section 2 now shows up as a real CI failure, before either commit lands.

```
main ─┐
       ├─▶ speculative: main + A          → A's queue CI runs here
       └─▶ speculative: main + A + B      → B's queue CI runs here (sees A's changes too)
```

### The Speculative Refs, Literally

These speculative bases are not an abstraction — they are real, temporary, read-only branches
GitHub pushes to your repo. The documented contract is the prefix: every queue branch begins with
`gh-readonly-queue/{base_branch}` (this is what third-party CI is told to match on). In practice
the full branch name also embeds the PR number and a SHA — observed convention, not a documented
API surface. For Section 2's two PRs (#201 and #202, base `main` at `0f1e2d3c4b5a…`), the queue
creates:

```
refs/heads/gh-readonly-queue/main/pr-201-0f1e2d3c4b5a…   ← contains: main + A
refs/heads/gh-readonly-queue/main/pr-202-<sha-of-A's-speculative-merge>… ← contains: main + A + B
```

`config/feature_flags.yml` on each ref:

```
pr-201 ref: search_v2 ✓  new_checkout ✓  legacy_payment_path ✓   → queue CI: green, A merges
pr-202 ref: search_v2 ✓  new_checkout ✓  legacy_payment_path ✗   → queue CI: RED, B is held
```

The `pr-202` ref's content is byte-for-byte the broken combined file from Section 2 — but now it
exists *before* the merge, as a testable tree. Workflows run against these refs via the
`merge_group` event (`types: [checks_requested]`), which must be added as a trigger alongside
`pull_request`, or the queue's required checks never fire (Chapter 13's silent-no-trigger failure
mode, in queue form).

**What to notice:**

- B is tested against a base that already contains A — *before* A has actually merged. The queue
  manufactures the future `main` and tests it early.
- Section 2's "invisible" pairwise bug has become an ordinary red check on an ordinary ref —
  nothing clever detects the semantic conflict; plain CI does, pointed at the right tree.
- The gating check runs on the speculative merge commit, not the PR's own head SHA — the same
  shift Section 10 returns to.

## 5. Serializing the Queue

The other half of the mechanism: PRs are processed **in order**, not simultaneously. PR A merges
(or is rejected) first; only then does PR B's speculative test — now against the *actual*,
updated `main` — proceed. This ordering is what makes the speculative base in Section 4 meaningful
rather than just another guess.

## 6. Comparing the Two Strategies Side by Side

| Property | Naive Parallel Auto-Merge (this repo) | Merge Queue | Setup Effort |
| --- | --- | --- | --- |
| Tests each PR against | `main` as of when ITS OWN checks ran | `main` + every PR ahead in the queue | Minimal (auto-merge) / Low (queue, one setting) |
| Catches semantic conflicts before merge | Weak — only textual conflicts, never semantic ones | Strong — speculative testing catches both | — |
| Throughput at low PR volume | Excellent — no serialization overhead | Fair — some queue wait even with nothing to conflict with | — |
| Throughput at high, frequently-conflicting PR volume | Weak — conflicts land on `main`, need after-the-fact fixes | Strong — caught before landing, at the cost of queue latency | — |
| Right fit | A handful of PRs, rarely simultaneous (this repo) | Many simultaneously-ready PRs on a shared codebase | — |

## 7. Enabling a Merge Queue

A merge queue is a branch-protection-level setting (`gh api` or the repo settings UI) — you don't
write workflow YAML to implement queuing logic; you enable the native feature and specify which
required checks the queue itself should wait on for each speculative combination, same vocabulary
as ordinary required checks (Chapter 05).

## 8. ⚠️ ADVANCED: Batching Multiple PRs

> ⚠️ **ADVANCED TOPIC:** Testing several PRs together as one speculative combination.
> **Skip on first read** — return once single-PR queue latency becomes the bottleneck.

Rather than testing PR A alone, then A+B, then A+B+C, a queue can be configured to batch several
PRs into one speculative combination and test them together — if the batch's CI passes, all of
them merge at once; if it fails, the queue typically bisects to find which PR(s) caused the
failure. This trades some diagnostic precision (a failing batch doesn't immediately name the
culprit) for significantly higher throughput at high PR volume.

## 9. ⚠️ ADVANCED: Queue Latency vs Throughput

> ⚠️ **ADVANCED TOPIC:** Why a queue can make an individual PR's time-to-merge *worse*.
> **Skip on first read.**

A PR that would have merged immediately under naive parallel auto-merge might now wait behind
several others in the queue, even if it has zero actual conflict with any of them — the
serialization (Section 5) is unconditional, not conditional on an actual conflict existing. This is
the real cost of Section 6's safety improvement: individual PR latency can increase, in exchange
for the semantic-conflict guarantee. Batching (Section 8) partially offsets this at the cost of
diagnostic precision.

## 10. ⚠️ ADVANCED: Required Checks Under a Merge Queue

> ⚠️ **ADVANCED TOPIC:** How "required check" semantics shift once a queue is involved.
> **Skip on first read** — return once you're actually configuring queue-specific required checks.

Under ordinary branch protection (Chapter 05), a required check runs against the PR's own head
commit. Under a merge queue, the check that actually gates merging runs against the **speculative,
combined** commit (Section 4) — a different commit than the PR's own head. Some CI configurations
need adjustment to correctly trigger against this speculative ref rather than assuming they're
always testing the PR's own branch in isolation; workflows written assuming the simpler Chapter 05
model may need real changes to work correctly under a queue.

## 11. Case Study: The Feature-Flag Collision

This chapter's lab reproduces Section 2's exact scenario: PR #201 and #202 both touch
`config/feature_flags.yml`, each individually passing CI. Naive parallel auto-merge (this repo's
actual design) lets both through — the conflict is only detected *after* the fact, by inspecting
the merged set. The queue simulation catches it immediately: #202 is held the moment its
speculative test would include #201's already-claimed resource, exactly matching Section 4's
mechanism.

## 12. Case Study: When This Repo Would Actually Need One

This repo's own sandbox generates one throwaway PR at a time (`sandbox/generate_pr.py`), evaluated
and merged individually with no realistic chance of two PRs racing each other. A merge queue would
add pure overhead here — queue latency with nothing to protect against. The crossover point isn't
about codebase size or PR *count* per se — it's about how often two or more PRs are genuinely
*simultaneously ready* to merge, touching adjacent or shared resources. A repo with a handful of
contributors merging a few PRs a day rarely crosses it; a repo with dozens of contributors landing
PRs continuously against shared config or infra code crosses it quickly.

## 13. Practical Tips: Deciding Whether You Need a Queue

```
Signals you've crossed the threshold
──────────────────────────────────────
[ ] You've had a real incident traceable to two independently-passing PRs conflicting
[ ] Multiple PRs are routinely "ready" (all checks green) at the same moment
[ ] Contributors frequently touch the same shared files/config in different PRs
[ ] Auto-merge throughput is limited more by conflicts-after-the-fact than by CI time itself
```

If none of these are true yet, naive parallel auto-merge (this repo's own design) remains the
right, simpler choice — a queue is a real cost (latency, setup, required-check semantics shifting
per Section 10) that should be paid for a real, observed problem, not preemptively.

## 14. Your First Project: Reproduce the Conflict Yourself

Run this chapter's lab and confirm: `simulate_parallel_automerge` merges all three sample PRs and
*then* reports a conflict; `simulate_merge_queue` catches the same conflict *before* merging #202.
Change the `resources_touched` sets to make PR #202 conflict-free and confirm both strategies now
agree — the queue only diverges from naive auto-merge when a real conflict exists.

## 15. Your Second Project: Simulate a Larger Queue

Extend the lab's PR list to five or six PRs, several sharing resources in different combinations,
and trace through `simulate_merge_queue` by hand before running it — predict which PRs will be held
and why, then confirm against the actual output. This is the fastest way to internalize how queue
ordering (Section 5) determines *which* PR in a conflicting pair gets held, not just *that* one
does.

## 16. Common Pitfalls & Misconceptions

1. **"A merge queue is just auto-merge with extra steps."** No — it answers a structurally
   different question (ordering across multiple PRs, not just one PR's own readiness).

2. **"If each PR's CI passes, the merged result is safe."** Not necessarily — a semantic conflict
   between two independently-passing PRs is exactly what a queue exists to catch (Section 2).

3. **"Enabling a queue requires building the serialization logic myself."** No — it's a native,
   enable-in-settings feature (Section 7); no custom workflow logic implements the queuing itself.

4. **"A merge queue always makes things faster."** Not for an individual PR — queue latency is
   unconditional, even for PRs with zero actual conflicts (Section 9).

5. **"Every repo eventually needs a merge queue."** Not necessarily — it's proportionate to
   simultaneous-readiness frequency and shared-resource contention (Section 12), not to codebase
   size alone.

## 17. Key Takeaways

- **Auto-merge answers "should THIS PR merge"; a queue answers "in what order, against what every
  other ready PR is also doing."**
- **A semantic conflict passes both PRs' independent CI runs** — the danger is entirely in the
  combination, invisible to either PR's own test run.
- **A merge queue's speculative base branch** — `main` plus every PR ahead in line — is the
  mechanism that makes the combination testable before it lands.
- **Serialization plus speculative testing together close the gap** — neither alone is sufficient.
- **This repo doesn't need one, deliberately** — its own traffic pattern (single PRs, low
  simultaneous-readiness) doesn't cross the threshold where a queue's cost is worth paying.

## 18. What's Next: Chapter 21 — Reusable Workflows & Composite Actions

Chapter 21 (also optional) covers a different scaling axis — not PR volume, but *workflow*
duplication: how to share logic across multiple workflows or repositories without copy-pasting
YAML.

[→ Chapter 21: Reusable Workflows & Composite Actions](chapter_21_reusable_workflows.md)

## 19. Additional Resources

- **GitHub Docs, "Merging a pull request with a merge queue"** — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue (fetched 2026-08)
- **GitHub Docs, "Events that trigger workflows" § `merge_group`** — the `checks_requested` activity type and the requirement to add `merge_group:` as a trigger for queue-gating checks — https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (fetched 2026-08)
- **GitHub Changelog, "Merge queue is generally available"** — background on the feature's rollout and required-check interaction (fetched 2026-08)
- **This repo's own** `.github/workflows/automerge.yml` — the design this chapter contrasts against

## 20. Appendix A — Code Index

### A.1 — Parallel Auto-Merge vs a Queue Simulation (from Section 14)

**What the code does:** Simulates a batch of PRs under naive parallel auto-merge (all independently
-passing PRs merge, conflicts detected only after the fact) and under a serialized, speculatively
-retested merge queue.

**ASCII flowchart:**

```
simulate_parallel_automerge(prs) → merges everyone whose own CI passed
        │
        ▼
    checks the MERGED SET for resource overlaps → conflict found, too late

simulate_merge_queue(prs) → processes one at a time, tracking claimed resources
        │
        ▼
    each PR checked against resources claimed by EARLIER queue members → held BEFORE merging
```

See `labs/lab_20_merge_queues.py` for the full runnable version.
