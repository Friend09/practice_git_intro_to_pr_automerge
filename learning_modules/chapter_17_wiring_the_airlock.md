# Chapter 17: Wiring the Airlock

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 06, Chapter 14, Chapter 15, Chapter 16
**Practice Notebook:** `notebooks/practice_17.ipynb`
**Reference Notebook:** `notebooks/lab_17_airlock.ipynb`
**Script:** `labs/lab_17_airlock.py`
**Doc Reference:** This repo's own design -- no canonical doc
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 — how three independent workflows compose into one
airlock without any of them calling each other directly.

**What to SKIP on first read:** Section 10 (the abandoned `workflow_run`-chaining design, in full
detail). Chapter 06 §12 and Chapter 09 §12 already gave you the concept; this section is the
complete incident writeup.

**Key concepts in plain English:**

- **Composition without coordination:** This repo's three gates never call each other or share
  state directly — they compose entirely through branch protection's required-check list and
  native auto-merge, both native GitHub mechanisms.
- **`decide()`:** This chapter's own composing function — not something the real workflows use
  (they don't need to, per the point above), but a way to *see* the composition explicitly in one
  place.
- **Enrollment, not merging:** `automerge.yml`'s only job is `gh pr merge --auto --squash` — an
  enrollment call (Chapter 06 §3), never a direct merge.
- **The abandoned design:** An earlier version of `automerge.yml` tried to manually recompute "did
  every gate pass" — this chapter tells that story in full, as the case study for why the current
  design is simpler *and* more correct.

**Your prior knowledge connection:** If you've ever configured a deploy pipeline where several
independent CI checks all have to pass before a merge button unlocks — without writing any code
that explicitly asks "did check A and check B and check C all pass" — you've already used this
exact composition pattern; GitHub just formalizes it as required status checks.

---

> **🔬 Automation Engineer's Lens:** The single biggest lesson this repo's own build process
> produced is in this chapter: the "obviously correct" design (write code that explicitly checks
> all three gates' results and then decides) was built, shipped, found broken via a real bug, and
> replaced with a design that does *less* — required checks plus native auto-merge, and nothing
> else. Less code was more correct. Every automation engineer eventually reaches for the
> recompute-the-verdict pattern instinctively; this chapter is the concrete story of why that
> instinct was wrong here.

---

> **🚦 Native vs Custom:** This chapter is the purest instance of "native does more than you'd
> expect" in the whole curriculum. Required status checks and native auto-merge together implement
> the *entire* composition logic — waiting for all three gates, holding the PR if any fails,
> merging once all pass. `automerge.yml` contributes exactly one line of actual logic: the
> enrollment call. Everything else is GitHub's own machinery.

---

## What You'll Learn

- How three independent gate workflows compose into one airlock with zero direct coordination
- Why `automerge.yml`'s only real job is a single enrollment call
- The full story of the abandoned `workflow_run`-chaining design and the real bug that killed it
- How to compose `pr_automerge.gates` and `pr_automerge.scoring` into one `decide()` call, as a
  teaching tool distinct from what the real workflows do
- What "wiring the airlock" actually means once you've built all three gate workflows separately
- Why this design needs no additional code to add a fourth gate later

---

## Table of Contents

- [Chapter 17: Wiring the Airlock](#chapter-17-wiring-the-airlock)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Three Gates, Zero Direct Coordination](#1-three-gates-zero-direct-coordination)
  - [2. What Actually Composes Them](#2-what-actually-composes-them)
  - [3. `automerge.yml`'s One Job](#3-automergeymls-one-job)
  - [4. The Full Picture, End to End](#4-the-full-picture-end-to-end)
  - [5. Gate 1's Independent Backstop](#5-gate-1s-independent-backstop)
  - [6. `decide()`: Composing the Gates in Python](#6-decide-composing-the-gates-in-python)
  - [7. Enrollment: `enqueue_for_automerge()`](#7-enqueue_for_automerge)
  - [8. ⚠️ ADVANCED: The `PRA_BOT_TOKEN` Fallback, In Full](#8-️-advanced-the-pra_bot_token-fallback-in-full)
  - [9. ⚠️ ADVANCED: Adding a Fourth Gate Later](#9-️-advanced-adding-a-fourth-gate-later)
  - [10. ⚠️ ADVANCED: The Abandoned `workflow_run`-Chaining Design](#10-️-advanced-the-abandoned-workflow_run-chaining-design)
  - [11. Case Study: The Fix, Verified Live](#11-case-study-the-fix-verified-live)
  - [12. Case Study: A PR That Sails Through All Three Gates](#12-case-study-a-pr-that-sails-through-all-three-gates)
  - [13. Practical Tips: Verifying the Wiring Yourself](#13-practical-tips-verifying-the-wiring-yourself)
  - [14. Your First Project: Trace One PR Through All Five Workflows](#14-your-first-project-trace-one-pr-through-all-five-workflows)
  - [15. Your Second Project: Break One Gate, Watch the Others Not Notice](#15-your-second-project-break-one-gate-watch-the-others-not-notice)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 18 — Security](#18-whats-next-chapter-18--security)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Composing Three Gates Into One Decision (from Section 6)](#a1--composing-three-gates-into-one-decision-from-section-6)

---

## 1. Three Gates, Zero Direct Coordination

Gate 1 (`gate1-repo-health.yml`), Gate 2 (`gate2-pr-health.yml`), and Gate 3 (`gate3-score.yml`)
never call each other, never read each other's output files, and don't even know the others exist
at the YAML level. Gate 1 runs on a weekly cron. Gate 2 runs on CI's completion. Gate 3 runs
directly on `pull_request`. Nothing in any of the three files references either of the other two.

## 2. What Actually Composes Them

The composition happens entirely outside any of the three gate workflows, in two native GitHub
mechanisms working together:

```
Branch protection's required_status_checks.contexts:
    ["test", "gate2-pr-health", "gate3-risk-score"]
        │
        ▼
GitHub itself refuses to merge until ALL THREE report success
        │
        ▼
Native auto-merge (Chapter 06): once that condition holds, GitHub performs the merge
```

Gate 1 sits slightly apart — it doesn't publish a required check at all; it enforces at the
platform level instead (Section 5).

## 3. `automerge.yml`'s One Job

```bash
gh pr merge <N> --repo <owner>/<repo> --auto --squash
```

That's the entire logic. It runs on every PR open/update event, enrolls the PR in native
auto-merge, and then does nothing else — GitHub's own required-check enforcement (Section 2)
handles literally everything about *when* the actual merge is allowed to happen.

### Concurrency: When Push B Lands While Push A's Gates Are Still Running

"On every PR open/update event" hides a race. **State before:** PR #101's head is
`a1b2c3d4e5f6…` (push A, version vA); Gate 3's run for vA is `in_progress`. **Event:** 20
seconds later, push B moves the head to `b2c3d4e5f6a7…` (vB) — a `pull_request` `synchronize`
event starts a second Gate 3 run. **State after, WITHOUT `concurrency:`** (this repo today):
both runs execute to completion, and run A publishes its check on the now-outdated SHA
`a1b2c3d4e5f6…`. Here that's merely wasteful — these gates capture the head SHA from their own
triggering event, and branch protection only evaluates checks on the *current* head (Section 4)
— but a gate that instead queried "the PR's current head" at completion time could stamp vB's
fresh SHA with a verdict computed against vA's diff. One `concurrency` block per gate workflow
closes the race:

```yaml
concurrency:
  group: gates-${{ github.event.pull_request.number }}   # "gates-101"
  cancel-in-progress: true
```

**State after, WITH `concurrency:`** — push B's run cancels push A's mid-flight:

```
$ gh run list --workflow=gate3-score.yml --limit 2
in_progress  -          Gate 3 — Risk Score  fix/readme-typo   (run B — head b2c3d4e5f6a7…)
completed    cancelled  Gate 3 — Risk Score  fix/readme-typo   (run A — head a1b2c3d4e5f6…)
```

**What to notice:**

- **The group key ties to the PR number**, so the group is `gates-101`: pushes to PR #101 cancel
  only each other, never another PR's runs. The `github` context is one of the contexts allowed
  in a `concurrency` group expression, and GitHub keeps at most one run *pending* per group.
- **`cancelled` is not a passing conclusion.** Branch protection counts only `success`,
  `skipped`, and `neutral` as passing — so run A's cancelled required check can never
  accidentally satisfy the check list. The airlock fails closed; only run B's fresh verdict on
  `b2c3d4e5f6a7…` can open the door.
- **Honestly: none of this repo's five live workflows uses `concurrency:` today.** The sandbox
  generates single-push throwaway PRs, so the race window is rarely hit — but it's the first
  hardening you'd add before pointing this airlock at real multi-push traffic.

## 4. The Full Picture, End to End

```
PR #101 opens/updates against sandbox/**
(head SHA a1b2c3d4e5f6… — every check below attaches to THIS commit)
        │
        ├──▶ ci.yml runs (test job)                          on a1b2c3d4e5f6…
        │         │
        │         └──▶ gate2-pr-health.yml (workflow_run off CI)
        │              publishes "gate2-pr-health"           on a1b2c3d4e5f6…
        │              (reads github.event.workflow_run.head_sha)
        │
        ├──▶ gate3-score.yml (pull_request)
        │    publishes "gate3-risk-score" + PR comment       on a1b2c3d4e5f6…
        │    (reads github.event.pull_request.head.sha)
        │
        └──▶ automerge.yml (pull_request) calls gh pr merge 101 --auto --squash
                    │
                    ▼
        branch protection watches: test, gate2-pr-health, gate3-risk-score
        — all evaluated against the CURRENT head, a1b2c3d4e5f6…
                    │
              all three == success?
                    │yes
                    ▼
        GitHub merges a1b2c3d4e5f6… into main (base 0f1e2d3c4b5a…)
```

**What to notice:**

- **The same head SHA appears at every stage.** Three independently-triggered workflows converge
  on one commit — not by coordinating, but because each extracts the SHA from its own event
  payload. Two different context paths (`workflow_run.head_sha` vs `pull_request.head.sha`), one
  value: `a1b2c3d4e5f6…`.
- **Gate 2 gets the SHA second-hand** — via `workflow_run.head_sha`, reliable exactly one hop off
  the original `pull_request` event. Section 10 is the story of what happens at hop two.
- **Branch protection's question is per-commit,** not per-PR: "do all three required checks report
  success *on the current head* `a1b2c3d4e5f6…`?" Checks stamped on an older head don't count.

Gate 1 runs independently on its own weekly schedule, enforcing `allow_auto_merge` at the repo
level the whole time this is happening (Section 5).

## 5. Gate 1's Independent Backstop

Gate 1 doesn't publish a required check the other two gates' verdicts flow through — it operates
one level up, on the platform switch itself (`allow_auto_merge`, Chapter 14 §4). If Gate 1's last
run found the repo unready and flipped that switch off, `automerge.yml`'s `gh pr merge --auto` call
fails outright, regardless of what Gate 2 and Gate 3 say. This is deliberate redundancy: even a
bug in `automerge.yml` that ignored the other two gates' checks entirely couldn't merge an unsafe
PR while `allow_auto_merge` is off.

## 6. `decide()`: Composing the Gates in Python

None of the five real workflows need this function — Section 2's native composition already does
the job. But seeing the composition made *explicit*, in one place, is valuable for understanding
what's implicitly happening across three separate YAML files:

```python
def decide(pr, *, main_exists, protection_configured, required_checks_registered,
           auto_merge_enabled, ci_conclusion, risk_config=None) -> Decision:
    gate1 = evaluate_gate1(...)
    gate2 = evaluate_gate2(ci_conclusion)
    gate3 = evaluate_gate3(pr, risk_config or RiskConfig())
    return Decision(pr_number=pr.number, merge=all(g.passed for [gate1, gate2, gate3]), gates=[...])
```

This mirrors `pr_automerge.models.Decision`'s own definition of `merge` exactly:
`all(g.passed for g in gates)` — the same rule GitHub's required-check enforcement applies, just
made visible as one Python call instead of three independently-triggered workflows.

## 7. `enqueue_for_automerge()`

This chapter's lab also demonstrates the enrollment step conditioned on a composed `Decision` —
refusing to even attempt `gh pr merge --auto` if `decision.merge` is `False`, and naming exactly
which gate(s) blocked it. The real `automerge.yml` doesn't need this pre-check (native auto-merge
handles "not ready yet" by simply waiting, per Chapter 06 §3) — but for a `decide()`-based tool run
outside a workflow context, refusing to even try is the more honest behavior.

## 8. ⚠️ ADVANCED: The `PRA_BOT_TOKEN` Fallback, In Full

> ⚠️ **ADVANCED TOPIC:** The real `automerge.yml`'s complete token-fallback logic.
> **Skip on first read** — Chapter 07 §9 and Chapter 11 §4 already covered the underlying
> restriction; this section is the full shell logic.

```bash
if gh pr merge "$PR" --auto --squash; then
  echo "Queued via GITHUB_TOKEN."
elif [ -n "$PRA_BOT_TOKEN" ]; then
  if GH_TOKEN="$PRA_BOT_TOKEN" gh pr merge "$PR" --auto --squash; then
    echo "Queued via PRA_BOT_TOKEN (PAT)."
  else
    echo "PRA_BOT_TOKEN is set but also failed -- check its pull_requests:write scope."
    exit 1
  fi
else
  echo "GITHUB_TOKEN cannot enable auto-merge. No PRA_BOT_TOKEN configured."
  exit 1
fi
```

Every branch writes an explicit message to `$GITHUB_STEP_SUMMARY` — this workflow is designed to
fail loudly and specifically (Chapter 11 §12), never silently, whichever branch it takes.

## 9. ⚠️ ADVANCED: Adding a Fourth Gate Later

> ⚠️ **ADVANCED TOPIC:** What changes if this curriculum's design grows a fourth gate.
> **Skip on first read.**

Because composition happens through branch protection's required-check list (Section 2), adding a
fourth gate needs exactly two changes: a new workflow publishing a new named check run, and adding
that name to `required_status_checks.contexts`. `automerge.yml` needs **zero** changes — it still
just calls `gh pr merge --auto --squash`, and GitHub's own enforcement now waits on four checks
instead of three. This is the concrete payoff of composing through native mechanisms instead of a
custom recomputation (Section 10): the design scales without touching the composing code at all.

### The Native Fourth Gate That Already Exists: An Environment as a Manually Operated Door

Every door in this airlock so far opens on a verified *sensor* — a check turning green. GitHub
ships one more native door type: a **deployment environment with required reviewers**, which
opens only when a *human turns the wheel*. Configure an environment (say, `production-merge`)
with up to 6 required reviewers, then point a gate job at it:

```yaml
jobs:
  final-door:
    runs-on: ubuntu-latest
    environment: production-merge   # environment has required reviewers configured
```

**State before:** PR #101's three automated checks are green. **Event:** the `final-door` job
reaches the runner queue and hits its `environment:` reference. **State after:** the run pauses
— the job shows **"Waiting for review"**, the designated reviewers get an email, and nothing
proceeds until one of them (only one approval is needed) approves in the run's UI. On approval
the job resumes, finishes, and its check goes green like any other required check.

**What to notice:** this is the entire "human in the loop" feature — pause, notify, approve,
audit trail in the deployment history — with zero custom code. Building the same thing yourself
(a `/approve`-comment-parsing bot, a label check) means re-implementing all four of those pieces.
One caveat: on private repos, environment protection rules require a paid plan (they're free on
public repos), which is exactly the kind of platform precondition Gate 1 exists to verify.

## 10. ⚠️ ADVANCED: The Abandoned `workflow_run`-Chaining Design

> ⚠️ **ADVANCED TOPIC:** The full incident writeup — what was tried, what broke, why it broke.
> **Skip on first read** — return once you're tempted to build a custom verdict-recomputation gate
> yourself.

An earlier version of `automerge.yml` tried to be "smarter": listen via `workflow_run` to Gate 2
and Gate 3's completions, read `github.event.workflow_run.head_sha` from whichever one fired, look
up that PR, and manually check whether all three gates had passed before calling the merge
endpoint. Two real problems surfaced:

```
Gate 3 is directly pull_request-triggered  → its own workflow_run listener sees the CORRECT head_sha (hop 1)
Gate 2 is itself workflow_run-triggered (off CI) → a workflow_run LISTENING TO GATE 2 sees head_sha
                                                     COLLAPSED to the default branch (hop 2!)
```

The PR-discovery logic, built on this second hop's SHA, silently queried the wrong commit — the
merge never queued for any PR whose enrollment attempt was triggered off Gate 2's completion. This
is the Chapter 09 §8 collapse, hit for real, not simulated.

## 11. Case Study: The Fix, Verified Live

The fix wasn't a smarter SHA lookup — it was recognizing that the entire recomputation was
unnecessary. Required status checks (Section 2) already correctly track "has every gate passed,"
for free, using GitHub's own reliable internal bookkeeping — no `workflow_run` chain, no SHA to get
right, nothing to collapse. `automerge.yml` was rewritten to trigger directly on `pull_request` and
do exactly one thing (Section 3). This was verified end-to-end against this repo's real sandbox:
CI passes, Gate 1 enforces readiness, Gate 2 and Gate 3 publish their checks correctly, and
`automerge.yml` correctly attempts enrollment and reports the token restriction from Section 8
honestly when `PRA_BOT_TOKEN` isn't yet configured.

## 12. Case Study: A PR That Sails Through All Three Gates

A three-line typo fix (Chapter 01 §13's running example): Gate 1 passes because the repo is ready
(unrelated to this specific PR). CI passes because the change is trivially correct. Gate 2 passes
because CI's conclusion is `success`. Gate 3 passes because the risk score is near zero. Branch
protection sees all three required checks green. Native auto-merge performs the merge. No human
looked at this PR at any point, and — per this whole curriculum's design — that's the intended
outcome, not a gap.

## 13. Practical Tips: Verifying the Wiring Yourself

```
Confirming the airlock is actually wired correctly
──────────────────────────────────────────────────────
[ ] Branch protection's required_status_checks.contexts matches all published check names exactly
[ ] automerge.yml triggers on pull_request, paths: ['sandbox/**'] -- not workflow_run chaining
[ ] Gate 1's schedule is running (check gate-status branch's readiness.json freshness)
[ ] Open a real sandbox PR and watch all three checks report, then watch it auto-merge
[ ] Deliberately fail one check and confirm the merge stays blocked
```

## 14. Your First Project: Trace One PR Through All Five Workflows

Open a real PR against `sandbox/**` on this repo's own sandbox, then watch the Actions tab: note
the order each of the five workflows starts and finishes, and confirm the merge only happens after
all three required checks report success — regardless of the order they finished in (Chapter 15
§12: Gate 2 and Gate 3 run in parallel, with no fixed ordering).

## 15. Your Second Project: Break One Gate, Watch the Others Not Notice

On a disposable test setup: make Gate 3 fail deliberately (a PR that trips the hard line-count
ceiling) while Gate 1 and Gate 2 both pass. Confirm the PR stays blocked, and confirm Gate 1's next
scheduled run and Gate 2's next CI-triggered run both behave completely normally — neither one
"notices" or reacts to Gate 3's failure in any way, because none of the three gates has any
awareness of the others at all (Section 1).

## 16. Common Pitfalls & Misconceptions

1. **"The three gates must coordinate somehow to know about each other."** No — they compose
   entirely through branch protection's required-check list, a native mechanism none of the three
   workflows references directly.

2. **"`automerge.yml` decides whether the PR is safe to merge."** No — it only enrolls. The
   decision is entirely GitHub's, based on required-check state (Chapter 06 §3).

3. **"A smarter, custom recomputation of the verdict would be more reliable."** This repo tried
   exactly that and it was less reliable — Section 10's real incident is the concrete evidence.

4. **"Gate 1 works the same way as Gate 2 and Gate 3."** No — Gate 1 enforces at the platform
   level (`allow_auto_merge`), not via a required check (Section 5).

5. **"Adding a new gate requires touching `automerge.yml`."** No — it requires a new required-check
   name; `automerge.yml` itself needs zero changes (Section 9).

## 17. Key Takeaways

- **Zero direct coordination between the three gates** — composition happens entirely through
  branch protection's required-check list and native auto-merge.
- **`automerge.yml`'s only real logic is one enrollment call** — everything else is GitHub's own
  machinery.
- **The abandoned `workflow_run`-chaining design is a real, live-verified cautionary tale** — less
  code, not more, was the fix.
- **Gate 1 is an independent, platform-level backstop** — not part of the required-check chain the
  other two gates use.
- **Adding a fourth gate later needs zero changes to `automerge.yml`** — the concrete payoff of
  composing through native mechanisms.

## 18. What's Next: Chapter 18 — Security

Chapter 18 starts Phase 4 — hardening this airlock against the failure modes that matter once it's
handling real traffic: the `pull_request_target` footgun in full, secret exposure, and what changes
once contributors you don't fully trust start opening PRs.

[→ Chapter 18: Security](chapter_18_security.md)

## 19. Additional Resources

- **This repo's own** `.github/workflows/automerge.yml` — the live, executing implementation, including its full design-note comments
- **This repo's own** `notes/IMPROVEMENTS_SUMMARY.md` — the Live-Repo Verification Log, discovery #4 (the `workflow_run` chaining bug)
- **GitHub Docs, "About protected branches"** — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches (fetched 2026-08)
- **GitHub Docs, "Automatically merging a pull request"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request (fetched 2026-08)
- **GitHub Docs, "Control workflow concurrency"** — https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (fetched 2026-08) — `concurrency` group semantics, `cancel-in-progress`, allowed contexts, one-pending-run-per-group rule (Section 3)
- **GitHub Docs, "Troubleshooting required status checks"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks (fetched 2026-08) — passing conclusions are `success`, `skipped`, `neutral`; a cancelled check does not satisfy a required check (Section 3)
- **GitHub Docs, "Manage environments for deployment"** — https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (fetched 2026-08) — required reviewers (up to 6, one approval unblocks), wait timers, plan availability (Section 9)

## 20. Appendix A — Code Index

### A.1 — Composing Three Gates Into One Decision (from Section 6)

**What the code does:** Evaluates Gate 1, Gate 2, and Gate 3 against a single PR and composes the
results into one `Decision`, then conditionally attempts native auto-merge enrollment.

**ASCII flowchart:**

```
decide(pr, gate1_inputs, ci_conclusion, risk_config)
    → evaluate_gate1(...) + evaluate_gate2(...) + evaluate_gate3(...)
    → Decision(merge = all three passed)
        │
        ▼
enqueue_for_automerge(repo, pr_number, decision)
    → decision.merge? → gh pr merge --auto --squash : refuse, name the blocking gate(s)
```

See `labs/lab_17_airlock.py` for the full runnable version.
