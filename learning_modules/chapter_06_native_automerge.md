# Chapter 06: Native Auto-Merge vs Your Own Merge Call

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 05 (Branch Protection & Rulesets)
**Practice Notebook:** `notebooks/practice_06.ipynb`
**Reference Notebook:** `notebooks/lab_06_merge_modes.ipynb`
**Script:** `labs/lab_06_merge_modes.py`
**Doc Reference:** GitHub Docs "Automatically merging a pull request" · GitHub REST API "Merge a pull request"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7. That's the whole chapter, condensed to one distinction:
enqueue vs execute.

**What to SKIP on first read:** Section 10 (rebasing the merge queue against this). Return after
Chapter 20.

**Key concepts in plain English:**

- **Native auto-merge:** A per-PR GitHub setting. You flip it on; GitHub itself performs the merge
  later, once every required check passes. You never call an API to make the merge *happen* — you
  called one to make it *eligible*.
- **Direct merge call:** Your own code calling the merge endpoint right now, this instant,
  regardless of what checks exist or whether they've finished.
- **`mergeable_state`:** A GitHub-computed field describing whether a PR *could* be merged cleanly
  right now — separate from whether it *should* be, per your policies.
- **Squash / merge / rebase:** The three ways GitHub can combine a PR's commits into the base
  branch (Chapter 03 covers the mechanics; this chapter cares only that auto-merge requires you to
  pick one up front).

**Your prior knowledge connection:** If you've ever clicked the green "Merge pull request" button
on GitHub's UI, you've made a direct merge call by hand. Native auto-merge is that same action,
just deferred and made conditional.

---

> **🔬 Automation Engineer's Lens:** Every incident report involving a bad auto-merge starts the
> same way: someone built a direct-merge call because it felt more "in control," then discovered
> it bypassed a check they assumed was blocking. Native auto-merge is *slower to feel done* — you
> flip a switch and nothing visibly happens — which is exactly why teams reach for a direct call
> instead. That impulse is the bug.

---

> **🚦 Native vs Custom:** This callout usually asks "does GitHub already do this, or must I build
> it?" For this chapter, the entire chapter *is* the answer: **the merge itself is 100% native.**
> You never write code that merges a PR. You write code that (a) publishes check results GitHub's
> native auto-merge waits on, and (b) makes one API call to enroll the PR in that native queue.
> Nothing else.

---

## What You'll Learn

- The precise difference between "queue this for auto-merge" and "merge this right now"
- Why native auto-merge is a *conditional intent*, not an imperative action
- What `gh pr merge --auto` actually does under the hood (the `enablePullRequestAutoMerge` mutation)
- Why a direct merge call bypasses branch protection in ways that surprise people
- How this repo's own `automerge.yml` is built, and the two real bugs discovered building it
- When (rarely) a direct merge call is still the right tool

---

## Table of Contents

- [Chapter 06: Native Auto-Merge vs Your Own Merge Call](#chapter-06-native-auto-merge-vs-your-own-merge-call)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Two Ways to "Merge a PR from Code"](#1-two-ways-to-merge-a-pr-from-code)
  - [2. Why This Distinction Gets Lost](#2-why-this-distinction-gets-lost)
  - [3. Native Auto-Merge: What It Actually Does](#3-native-auto-merge-what-it-actually-does)
  - [4. Direct Merge: What It Actually Does](#4-direct-merge-what-it-actually-does)
  - [5. Side-by-Side Comparison](#5-side-by-side-comparison)
  - [6. What Happens If You Enable Auto-Merge With No Required Checks](#6-what-happens-if-you-enable-auto-merge-with-no-required-checks)
  - [7. This Repo's Design Decision](#7-this-repos-design-decision)
  - [8. The `gh pr merge --auto` Command, Piece by Piece](#8-the-gh-pr-merge---auto-command-piece-by-piece)
  - [9. ⚠️ ADVANCED: The GraphQL Mutation Underneath](#9-️-advanced-the-graphql-mutation-underneath)
  - [10. ⚠️ ADVANCED: Where Merge Queues Fit](#10-️-advanced-where-merge-queues-fit)
  - [11. ⚠️ ADVANCED: Revoking a Queued Auto-Merge](#11-️-advanced-revoking-a-queued-auto-merge)
  - [12. Case Study: automerge.yml, Built Wrong Then Right](#12-case-study-automergeyml-built-wrong-then-right)
  - [13. Case Study: When a Direct Merge Call *Is* Correct](#13-case-study-when-a-direct-merge-call-is-correct)
  - [14. Practical Tips: Enabling Auto-Merge on a Repo](#14-practical-tips-enabling-auto-merge-on-a-repo)
  - [15. Your First Project: Enable It, Watch It Wait](#15-your-first-project-enable-it-watch-it-wait)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 07 — The GitHub API In Depth \& GitHub Apps](#18-whats-next-chapter-07--the-github-api-in-depth--github-apps)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Enabling and Attempting a Direct Merge (from Section 8)](#a1--enabling-and-attempting-a-direct-merge-from-section-8)

---

## 1. Two Ways to "Merge a PR from Code"

There are exactly two API-level actions that end with a PR merged, and they behave nothing alike:

```
gh pr merge <N> --auto --squash        gh api -X PUT /repos/{o}/{r}/pulls/{n}/merge
        │                                       │
        ▼                                       ▼
  "enroll this PR in the             "merge this PR RIGHT NOW,
   native auto-merge queue"           if it's currently mergeable"
        │                                       │
        ▼                                       ▼
  GitHub polls required checks        Executes immediately, synchronously,
  and merges LATER, only if           whether or not any check has even
  every one reports success           started running
```

The `--auto` flag is not a performance detail — it changes which of two entirely different
operations you're invoking.

## 2. Why This Distinction Gets Lost

Both operations are called "merging a PR" in casual conversation, both live under `gh pr merge`,
and both eventually produce the same visible outcome (a merged PR). The difference only becomes
visible the moment something *isn't ready yet* — and that's precisely the moment most people are
writing this code under time pressure, copying a snippet without reading the flag.

## 3. Native Auto-Merge: What It Actually Does

Enabling auto-merge on a PR does not check anything at the moment you call it. It sets a flag:
*"when every required status check on this PR reports success, and branch protection is otherwise
satisfied, merge it."* GitHub's own systems then watch the PR asynchronously. If a required check
is still running, auto-merge simply waits. If a required check fails, auto-merge waits forever (or
until you disable it) — it never falls back to merging anyway.

```
enable auto-merge  →  PR sits in "auto-merge enabled" state
                            │
                            ▼
            (time passes; checks report in)
                            │
                            ▼
        ALL required checks == success?  ──no──▶ keeps waiting
                            │
                           yes
                            ▼
                  GitHub performs the merge
```

### The Lifecycle in Fixture Data: PR #101, Enrolled Then Merged

**State at enrollment** (authored on the fixture spine — the fixture captures only the final
state). Checks are still running, so GitHub reports the PR blocked:

```json
{
  "number": 101,
  "state": "open",
  "merged": false,
  "mergeable_state": "blocked",
  "head": { "ref": "fix/readme-typo", "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678" }
}
```

**Event:** the required gate checks report success. Nobody issues another command.

**State after GitHub merges** — trimmed verbatim from `fixtures/pr_merged_example.json`:

```json
{
  "number": 101,
  "state": "closed",
  "merged": true,
  "merged_at": "2026-08-15T14:32:07Z",
  "merge_commit_sha": "7c4a9e8d13ad1e0c9a18bd5e2f4b6789012cdef3",
  "mergeable_state": "clean",
  "head": { "ref": "fix/readme-typo", "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678" }
}
```

**What to notice:**

- Enrollment changed *nothing* above: `state` still `open`, `merged` still `false` —
  enrollment is not merging. `"blocked"` mirrors GraphQL's `MergeStateStatus: BLOCKED`
  ("the merge is blocked"), here by unmet required checks.
- `merge_commit_sha` `7c4a9e8d…` is a **new SHA**, not head `a1b2c3d4…` — GitHub manufactured
  the squash commit at merge time (Chapter 03: a merge produces a commit the source branch
  never contained).
- `head.sha` is byte-identical in both states — neither enrollment nor the merge touches the
  PR branch.

## 4. Direct Merge: What It Actually Does

A direct call to the merge endpoint evaluates the PR's mergeability **at that instant** and, if
mergeable, executes the merge synchronously. "Mergeable" here means "no conflicts with the base
branch" — it does **not** by default mean "every check has passed," unless branch protection is
configured to block the merge endpoint itself for non-passing checks (which it is, for *human*
merges through the UI and for merges attempted by non-privileged callers — but a sufficiently
privileged token calling the API directly can still hit surprising edge cases depending on
`enforce_admins` and bypass settings, which Chapter 18 covers).

## 5. Side-by-Side Comparison

| Property | Native Auto-Merge | Direct Merge Call | Interpretability | Setup Effort |
| --- | --- | --- | --- | --- |
| Waits for checks | Strong — literally its purpose | Weak — evaluates mergeability now, not check completion | Excellent — the PR UI shows "auto-merge enabled" | Minimal — one flag |
| Timing | Asynchronous — merges whenever conditions are met | Synchronous — merges now or errors now | Strong — a clear before/after state | Minimal |
| Failure mode | Waits indefinitely; never merges a failing PR | Errors immediately if not mergeable *right now* | Strong — an explicit error you can catch | Low — one API call, but you own the retry logic |
| Who decides *when* | GitHub's own systems | Your workflow's own scheduling | Fair — depends on your trigger design | Moderate — you must decide when to call it |

## 6. What Happens If You Enable Auto-Merge With No Required Checks

Nothing protects you. If a repo has branch protection with zero required status checks
configured, enabling auto-merge on a PR merges it **immediately** — there is nothing for it to
wait on. This is the single most common way a team "discovers" auto-merge is dangerous: they
enable the feature before configuring the checks it's supposed to wait for. Chapter 05's branch
protection setup and this chapter are a matched pair for exactly this reason.

## 7. This Repo's Design Decision

This repo's `automerge.yml` calls `gh pr merge --auto --squash` and nothing else. It never calls
the direct merge endpoint in production. The three gate workflows (Chapters 14–16) publish check
runs; branch protection lists those check runs as required; `automerge.yml`'s only job is to
enroll a qualifying PR in the queue GitHub already maintains.

```
gate1 / gate2 / gate3 workflows  →  publish check runs
                                            │
branch protection required checks ◀────────┘
                                            │
automerge.yml  →  gh pr merge --auto --squash   (enrolls; does not merge)
                                            │
                                            ▼
                          GitHub merges once all required checks pass
```

`lab_06_merge_modes.py`'s reference notebook builds a direct merge call exactly once, purely so you
can feel the difference — then the design is retired for the rest of the curriculum.

## 8. The `gh pr merge --auto` Command, Piece by Piece

```bash
gh pr merge 42 --repo owner/name --auto --squash
```

- `42` — the PR number.
- `--auto` — the flag that changes this from an immediate merge attempt into an enrollment.
- `--squash` — which merge strategy to use *once* GitHub actually performs the merge (Chapter 03).
- Exit code and stdout tell you whether the *enrollment* succeeded — not whether the PR has
  merged. A successful `gh pr merge --auto` can leave a PR open for hours if checks are slow.

### What Success and Failure Actually Look Like

**Before:** PR #101 open, `mergeable_state: "blocked"` (Section 3), repo `allow_auto_merge` on.

```console
$ gh pr merge 101 --auto --squash
✓ Pull request <you>/practice_git_intro_to_pr_automerge#101 will be automatically merged via squash when all requirements are met
$ echo $?
0
```

**Contrast — same command, but the repo's `allow_auto_merge` setting is off:**

```console
$ gh pr merge 101 --auto --squash
GraphQL: Auto merge is not allowed for this repository (enablePullRequestAutoMerge)
$ echo $?
1
```

**What to notice:**

- Exit `0` proves **enrollment**, nothing more — "will be automatically merged" is future
  tense. PR #101 is still open after this command returns.
- The ✓ line goes to **stderr**, and only when attached to a terminal (per gh 2.98.0's
  source). Inside an Actions job — no TTY — success prints nothing at all: the exit code is
  the only signal, which is why `automerge.yml` branches on `if gh pr merge …; then` instead
  of parsing output text.
- Failure is loud and non-zero (`gh help exit-codes`: `0` = success, `1` = any failure). The
  wording varies by cause; the stable contract is a `GraphQL: … (enablePullRequestAutoMerge)`
  line — same shape as Section 9's token-refusal error — plus exit `1`. A refused enrollment
  never falls back to merging.

## 9. ⚠️ ADVANCED: The GraphQL Mutation Underneath

> ⚠️ **ADVANCED TOPIC:** What `gh pr merge --auto` calls under the hood, and why it can fail in a
> way a direct merge call never does.
> **Skip on first read** — return once you've seen `gh pr merge --auto` fail for yourself.

`gh pr merge --auto` is a thin wrapper around GitHub's GraphQL `enablePullRequestAutoMerge`
mutation. This matters because that specific mutation is one of a small set of operations GitHub
withholds from the default Actions token: calling it with `GITHUB_TOKEN` — even with
`pull-requests: write` declared and the repo's `allow_auto_merge` setting on — returns:

```
GraphQL: Resource not accessible by integration (enablePullRequestAutoMerge)
```

This was verified against this repo's own `automerge.yml` while it was being built. A direct merge
call, by contrast, uses a plain REST endpoint that `GITHUB_TOKEN` *can* call. The fix for enabling
auto-merge is a personal access token or GitHub App installation token with `pull_requests: write`
— Chapter 07 and Chapter 11 cover minting one, and this repo's `automerge.yml` falls back to a
`PRA_BOT_TOKEN` secret when `GITHUB_TOKEN` is refused.

## 10. ⚠️ ADVANCED: Where Merge Queues Fit

> ⚠️ **ADVANCED TOPIC:** Auto-merge vs merge queue.
> **Skip on first read** — return at Chapter 20, which is dedicated to this.

Auto-merge answers "should *this* PR merge once its checks pass?" A merge queue answers a
different question: "in what *order* should several simultaneously-ready PRs merge, re-testing
each against the latest `main` as it goes?" You can have one without the other. This curriculum
builds auto-merge only; Chapter 20 explains when that stops being enough.

## 11. ⚠️ ADVANCED: Revoking a Queued Auto-Merge

> ⚠️ **ADVANCED TOPIC:** Disabling auto-merge once it's enabled.
> **Skip on first read.**

`gh pr merge <N> --disable-auto` removes a PR from the queue without touching its mergeability.
Useful when Gate 3 (Chapter 16) later revises a risk score upward — Chapter 17's wiring chapter
covers when you'd want to actively *dequeue* a PR rather than just letting a later check fail.

## 12. Case Study: automerge.yml, Built Wrong Then Right

This repo's own build process hit this chapter's lesson directly. An early version of
`automerge.yml` tried to *recompute* "did every gate pass" by chaining off `workflow_run` events
and manually reading each gate's published check-run conclusion — essentially reimplementing what
native auto-merge already does. Two real bugs came from that: the PR-discovery logic depended on
`github.event.workflow_run.head_sha`, which is only reliable on the first hop of a chained
`workflow_run` trigger (verified live — see Chapter 17). The fix was to delete the recomputation
entirely: register every gate as a required status check, and let one trivial `automerge.yml` just
call `gh pr merge --auto` on every PR open/update event. Less code, and correct by construction.

## 13. Case Study: When a Direct Merge Call *Is* Correct

A release-automation bot that merges a pre-approved, pre-validated release-notes PR the instant a
human clicks "approve" in a separate system — where "wait for checks" isn't the semantics you
want, because the checks already ran as part of the approval step. This is rare. If you find
yourself reaching for a direct merge call, the default assumption should be that you actually
want auto-merge plus a required check, not a direct call — Section 9's GraphQL restriction is
also a strong practical nudge in that direction.

## 14. Practical Tips: Enabling Auto-Merge on a Repo

```
Enabling native auto-merge — order matters
────────────────────────────────────────────
[ ] Branch protection configured on main (Chapter 05)
[ ] At least one required status check registered
[ ] Repo setting allow_auto_merge = true
    (gh api -X PATCH repos/{o}/{r} -F allow_auto_merge=true)
[ ] A token that can call enablePullRequestAutoMerge
    (a PAT/App token -- GITHUB_TOKEN cannot, see Section 9)
[ ] THEN, and only then: gh pr merge <N> --auto --squash
```

## 15. Your First Project: Enable It, Watch It Wait

Against the sandbox repo: open a PR with a failing check, then run `gh pr merge <N> --auto
--squash`. Watch it queue rather than merge (`gh pr view <N> --json autoMergeRequest`). Then fix
the check and watch the PR merge itself with no further action from you. This one experiment is
worth more than the rest of the chapter combined.

While it waits, `gh pr view 101 --json autoMergeRequest` is your proof of enrollment (trimmed;
field names per gh 2.98.0):

```json
{
  "autoMergeRequest": {
    "enabledAt": "2026-08-15T14:05:11Z",
    "enabledBy": { "login": "<you>" },
    "mergeMethod": "SQUASH",
    "commitHeadline": null,
    "commitBody": null
  }
}
```

After the merge completes — or if enrollment never happened — the same query returns:

```json
{ "autoMergeRequest": null }
```

**What to notice:**

- A non-null `autoMergeRequest` is the queued-state artifact: `mergeMethod: "SQUASH"` was
  locked in at enrollment (`enabledAt` 14:05:11Z — about 27 minutes before the fixture's
  `merged_at` of 14:32:07Z in Section 3).
- `null` is ambiguous on its own — already merged, or never enrolled? Pair it with Section 3's
  `merged` / `merge_commit_sha` fields to tell which story you're in.

## 16. Common Pitfalls & Misconceptions

1. **"`--auto` just makes the merge happen faster."** No — it changes *when* and *whether* it
   happens at all, from "now, unconditionally" to "later, conditionally."

2. **"If `gh pr merge --auto` returns success, the PR is merged."** No — it returns success when
   the *enrollment* succeeds. The merge itself may happen minutes later, or never.

3. **"`GITHUB_TOKEN` can do anything `permissions:` grants it."** Section 9 is a direct
   counterexample: `pull-requests: write` is not sufficient for `enablePullRequestAutoMerge`.

4. **"Auto-merge is safe by default."** Only if required checks are already configured. Enabling
   it before Chapter 05's branch protection work is done merges everything, immediately.

5. **"A direct merge call is more reliable because it's synchronous."** It's more reliable at
   telling you the outcome *immediately* — it is not more reliable at respecting your checks.

## 17. Key Takeaways

- **Two different operations share the name "merge a PR":** enroll-and-wait (`--auto`) vs
  execute-now (direct call). They are not interchangeable.
- **Native auto-merge does the merging; you never write merge code.** Your code publishes check
  results and makes one enrollment call.
- **`GITHUB_TOKEN` cannot enable auto-merge**, verified empirically — this needs a PAT or App
  token, covered in Chapter 07/11.
- **Auto-merge with no required checks merges immediately** — order your setup: protection, then
  checks, then the `allow_auto_merge` setting, then the enrollment call.
- **This repo's `automerge.yml` is intentionally trivial** — one `gh pr merge --auto` call,
  because required checks plus native auto-merge already do the hard part.

## 18. What's Next: Chapter 07 — The GitHub API In Depth & GitHub Apps

Chapter 07 goes deep on the GitHub REST/GraphQL API generally — reading data at scale, pushing
data back (comments, labels, check runs), and what a GitHub App actually is and why it's the right
tool once you're automating across more than one repository, including a hands-on walkthrough of
minting the PAT this chapter's Section 9 needed.

[→ Chapter 07: The GitHub API In Depth & GitHub Apps](chapter_07_github_api_and_apps.md)

## 19. Additional Resources

- **GitHub Docs, "Automatically merging a pull request"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request (fetched 2026-08)
- **GitHub REST API, "Merge a pull request"** — https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request (fetched 2026-08)
- **GitHub Changelog, "Enabling and disabling auto-merge for pull requests"** — background on the feature's rollout
- **gh CLI source: `pr merge` output strings & `AutoMergeRequest` JSON fields** — https://github.com/cli/cli/blob/trunk/pkg/cmd/pr/merge/merge.go and https://github.com/cli/cli/blob/trunk/api/queries_pr.go (fetched 2026-08; cross-checked locally against gh 2.98.0 `gh pr merge --help`, `gh pr view --json`, and `gh help exit-codes`)
- **GitHub GraphQL API, `MergeStateStatus` enum** — https://docs.github.com/en/graphql/reference/enums#mergestatestatus (fetched 2026-08; REST's `mergeable_state` is its lowercase mirror)

## 20. Appendix A — Code Index

### A.1 — Enabling and Attempting a Direct Merge (from Section 8)

Both code paths, side by side, for the notebook to run once each and compare their responses.

**What the code does:** Calls `gh pr merge --auto` on one PR and the direct REST merge endpoint on
another, printing both responses so the asynchronous-vs-synchronous difference is visible in
output, not just in prose.

**ASCII flowchart:**

```
PR A: gh pr merge --auto --squash
    ↓
prints: "Auto-merge enabled for #A" (regardless of check state)

PR B: gh api -X PUT pulls/{B}/merge
    ↓
prints: merged=true (if mergeable now)  OR  405 (if blocked by protection)
```

See `labs/lab_06_merge_modes.py` for the full runnable comparison.
