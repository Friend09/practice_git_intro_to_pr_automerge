# Chapter 02: Refs, Branches & What a PR Really Is

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 01 (the Airlock Principle)
**Practice Notebook:** `notebooks/practice_02.ipynb`
**Reference Notebook:** `notebooks/lab_02_pr_refs.ipynb`
**Script:** `labs/lab_02_pr_refs.py`
**Doc Reference:** Pro Git Ch 3 (Branching), Ch 10.3 (Git Internals -- refs) · GitHub Docs "About pull requests"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8. That's the whole chapter's payload: a PR is not a Git
object, it's GitHub's bookkeeping *on top of* two refs it creates for you.

**What to SKIP on first read:** Section 11 (the `merge` ref's staleness behavior). Return once
you've watched `mergeable_state` actually change on a real PR in the hands-on section.

**Key concepts in plain English:**

- **Ref:** A named pointer to a commit. `refs/heads/main` is a ref; so is a tag. Refs are how Git
  gives human-readable names to specific points in history.
- **`refs/pull/N/head`:** A ref GitHub creates automatically for every open PR, pointing at the
  latest commit on the PR's source branch — even if that branch lives in a fork you don't have
  push access to.
- **`refs/pull/N/merge`:** A second, GitHub-managed ref pointing at a synthetic commit: what the
  repo would look like if PR #N were merged into its base branch *right now*. GitHub recomputes
  this constantly; it is not a ref you ever create or update yourself.
- **`mergeable_state`:** A field on the PR API object, computed from the `merge` ref, describing
  whether that synthetic merge succeeded, conflicted, or is still being calculated.
- **PR object:** The REST/GraphQL API's higher-level view of a PR — title, reviewers, checks,
  `mergeable_state` — built on top of the two refs above, but not reducible to them.

**Your prior knowledge connection:** If you've ever run `git fetch origin` and watched refs like
`refs/remotes/origin/main` update locally, you already understand what a ref is. This chapter's
only new idea is that GitHub publishes *two extra refs per PR*, automatically, that you never
explicitly pushed.

---

> **🔬 Automation Engineer's Lens:** Automation built against "the PR" as an opaque object breaks
> in exactly the moments that matter: when `mergeable_state` is `null` mid-computation, or when a
> script assumes `refs/pull/N/merge` reflects the current head when it's actually one push stale.
> Knowing that these are two separate, independently-updating refs — not one atomic fact — is what
> lets you write a gate that asks the right question at the right layer, instead of trusting a
> field that hasn't finished being computed yet.

---

> **🚦 Native vs Custom:** GitHub creates and maintains both PR refs entirely natively — you never
> push to `refs/pull/N/head` or `refs/pull/N/merge` yourself, and attempting to would be rejected.
> What you build, if anything, is code that *reads* these refs and the PR object built on them
> (Chapter 04 goes deep on reading; this chapter only establishes what exists to be read).

---

## What You'll Learn

- What a Git ref actually is, underneath the branch/tag vocabulary
- The two refs GitHub silently maintains for every open PR, and what each one means
- Why `refs/pull/N/merge` is a *computed*, sometimes-stale synthetic commit, not a copy of `head`
- How `mergeable_state` is derived from that computed ref, and why it can be `null`
- The full list of `mergeable_state` values and what each one tells an automation script
- How this maps onto what `gh pr view` and the REST API actually return
- Why a PR is "GitHub bookkeeping on top of Git," not a Git-native concept at all

---

## Table of Contents

- [Chapter 02: Refs, Branches \& What a PR Really Is](#chapter-02-refs-branches--what-a-pr-really-is)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Why This Chapter Exists](#1-why-this-chapter-exists)
  - [2. A Ref Is Just a Named Pointer](#2-a-ref-is-just-a-named-pointer)
  - [3. Two Refs Per Open PR](#3-two-refs-per-open-pr)
  - [4. `refs/pull/N/head`: The Easy One](#4-refspullnhead-the-easy-one)
  - [5. `refs/pull/N/merge`: A Synthetic, Computed Commit](#5-refspullnmerge-a-synthetic-computed-commit)
  - [6. Seeing Both Refs Yourself](#6-seeing-both-refs-yourself)
  - [7. From Refs to "The PR Object"](#7-from-refs-to-the-pr-object)
  - [8. `mergeable_state`: The Full Vocabulary](#8-mergeable_state-the-full-vocabulary)
  - [9. ⚠️ ADVANCED: Why `mergeable` Is Sometimes `null`](#9-️-advanced-why-mergeable-is-sometimes-null)
  - [10. ⚠️ ADVANCED: Forked PRs and `refs/pull/N/head`](#10-️-advanced-forked-prs-and-refspullnhead)
  - [11. ⚠️ ADVANCED: `refs/pull/N/merge` Staleness](#11-️-advanced-refspullnmerge-staleness)
  - [12. Case Study: A Gate That Trusted a Stale `merge` Ref](#12-case-study-a-gate-that-trusted-a-stale-merge-ref)
  - [13. Case Study: Debugging "Which Commit Is This, Really?"](#13-case-study-debugging-which-commit-is-this-really)
  - [14. Practical Tips: Reading Refs Without `gh`](#14-practical-tips-reading-refs-without-gh)
  - [15. Your First Project: List the Refs, Then Fetch the Object](#15-your-first-project-list-the-refs-then-fetch-the-object)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 03 — Merge Commit vs Squash vs Rebase](#18-whats-next-chapter-03--merge-commit-vs-squash-vs-rebase)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Listing PR Refs With Plain Git (from Section 6)](#a1--listing-pr-refs-with-plain-git-from-section-6)

---

## 1. Why This Chapter Exists

Chapter 01 said, loosely, that a PR is "a request to merge one branch into another, plus a pile
of metadata." That's true but it skips the layer that explains almost every confusing PR-API
behavior you'll hit later: a pull request is not a first-class Git object at all. Git itself has
no concept of a "pull request" — commits, trees, blobs, and refs, full stop. Everything you think
of as "the PR" is GitHub's own bookkeeping, built by creating two ordinary refs and computing a
higher-level object on top of them. Once that's visible, `mergeable_state` being `null`,
`refs/pull/N/merge` lagging a push, and "which SHA is this check actually running against?" all
stop being mysteries.

## 2. A Ref Is Just a Named Pointer

A Git ref is nothing more than a file (or a packed-refs entry) mapping a name to a commit SHA.
`refs/heads/main` maps the name `main` to whatever commit is currently main's tip. `refs/tags/v1.0`
does the same for a tag. That's the entire mechanism:

```
refs/heads/main   ──points to──▶  a1b2c3d (a commit)
refs/tags/v1.0    ──points to──▶  9f8e7d6 (a commit)
```

Nothing about this is GitHub-specific — it's how local Git has always worked. GitHub's PR feature
is built entirely out of more refs, following the exact same mechanism, just under a different
top-level path (`refs/pull/` instead of `refs/heads/`).

## 3. Two Refs Per Open PR

The moment a PR is opened, GitHub creates — and continuously maintains — exactly two refs on the
*base* repository, regardless of whether the PR's source branch lives in that repo or a fork:

```
PR #101 opened
        │
        ▼
refs/pull/101/head   ──points to──▶  the PR branch's latest commit
refs/pull/101/merge  ──points to──▶  a synthetic "what if we merged this now" commit
```

Both refs exist under `refs/pull/`, which is why a plain `git fetch` doesn't show them by
default — most Git clients only fetch `refs/heads/*` and `refs/tags/*` unless told otherwise
(Section 6 shows how to see them anyway).

## 4. `refs/pull/N/head`: The Easy One

`refs/pull/N/head` is exactly what it sounds like: a pointer to the current tip of the PR's source
branch, updated every time the PR author pushes a new commit. It behaves like any other branch
ref — it's just namespaced under `pull/N/` instead of `heads/`, and (crucially) it exists on the
*base* repo even when the PR comes from someone else's fork, which is otherwise not something you
could `git fetch` directly by branch name.

```
Author pushes commit X to their fork's `feature` branch
        │
        ▼
GitHub updates refs/pull/101/head on the BASE repo to point at X
```

This is why `git fetch origin refs/pull/101/head` works even for a PR opened from a fork you have
no access to — GitHub already copied the pointer (and the underlying objects) into the base repo
for you.

## 5. `refs/pull/N/merge`: A Synthetic, Computed Commit

`refs/pull/N/merge` is a different kind of thing entirely. It points at a commit GitHub generates
by attempting to merge the PR branch into its base branch, right now, using a regular three-way
merge. Nobody authored this commit; you'll never see it in `git log` on any branch you actually
work on. It exists purely as a probe: "if this were merged this instant, what would the result
look like, and did it conflict?"

```
refs/heads/main ─┐
                  ├──▶ GitHub attempts a merge ──▶ refs/pull/101/merge (synthetic commit)
refs/pull/101/head ─┘         │
                                ▼
                        conflicts? ──yes──▶ ref is absent / mergeable=false
                                │no
                                ▼
                        ref points at the synthetic merge commit
```

GitHub recomputes this ref **every time either input changes** — a new commit on the PR branch, or
a new commit on `main`. That recomputation is asynchronous, which is exactly why `mergeable_state`
can be `null`: the computation hasn't finished yet (Section 9).

## 6. Seeing Both Refs Yourself

A normal `git clone` or `git fetch` doesn't pull `refs/pull/*` by default, but nothing stops you
from asking for them explicitly — no GitHub-specific tool required:

```bash
git ls-remote https://github.com/<owner>/<repo>.git 'refs/pull/*'
```

This lists every open PR's `head` and `merge` refs and their current SHAs, using plain Git —
`ls-remote` just asks the remote to list its refs, and PR refs are refs like any other. You could
even `git fetch origin refs/pull/101/head:pr-101-local` to pull a specific PR's commits into a
local branch, entirely without `gh` or the API.

## 7. From Refs to "The PR Object"

Everything so far is Git-level and GitHub-agnostic-in-mechanism (even though GitHub is the one
creating these particular refs). The PR *object* you get back from `gh pr view` or
`GET /repos/{owner}/{repo}/pulls/{number}` is a different layer on top: GitHub's own database
record, which happens to *reference* `head.sha` and `base.sha` — the same SHAs `refs/pull/N/head`
and `refs/heads/main` point to — plus fields Git has no concept of at all: `mergeable_state`,
review status, requested reviewers, labels, linked issues.

```
Git layer:           refs/pull/101/head ──▶ a1b2c3d
                      refs/pull/101/merge ──▶ 9182736 (synthetic)
                      refs/heads/main ──▶ 0f1e2d3

PR-object layer:      { "head": {"sha": "a1b2c3d", "ref": "fix/typo"},
                         "base": {"sha": "0f1e2d3", "ref": "main"},
                         "mergeable_state": "clean",   ← no Git equivalent
                         "requested_reviewers": [...]  ← no Git equivalent
                       }
```

The PR object is not a Git object dressed up — it's a GitHub record that *points at* Git objects.
That's the whole chapter's thesis in one diagram.

## 8. `mergeable_state`: The Full Vocabulary

`mergeable_state` is GitHub's computed summary of what `refs/pull/N/merge` found. Every value your
automation might see:

| Value | Meaning | Setup Effort to Handle |
| --- | --- | --- |
| `clean` | Merges without conflicts; all required checks (if any) currently pass | Minimal — the happy path |
| `dirty` | Merges would conflict; the author needs to resolve them | Low — surface it, don't retry |
| `blocked` | No conflicts, but a required status check or review hasn't passed | Low — this is the *expected* state while gates are pending |
| `unstable` | No conflicts, but a check is failing (non-required) or some other soft blocker exists | Moderate — distinguish "failing" from "still running" |
| `behind` | Base branch has moved and the PR must be updated before it can merge (usually a required "up to date" ruleset) | Moderate — needs a rebase/update-branch step |
| `unknown` / `null` | GitHub hasn't finished computing it yet | Moderate — treat as "not ready," never as a pass (Chapter 01's fail-closed rule) |

Note the direct link to Chapter 01: `unknown`/`null` is precisely the "sensor hasn't reported yet"
case. A gate that treats it as anything other than "not ready" reintroduces the exact fail-open
bug this curriculum exists to avoid.

## 9. ⚠️ ADVANCED: Why `mergeable` Is Sometimes `null`

> ⚠️ **ADVANCED TOPIC:** The asynchronous computation behind `mergeable`/`mergeable_state`.
> **Skip on first read** — return once you've queried a freshly-opened PR yourself and seen `null`.

The boolean `mergeable` field and the `mergeable_state` string are both derived from the same
background job: GitHub attempting the synthetic merge described in Section 5. That job does not
run synchronously inside your `GET` request — it's queued and computed out of band, typically
finishing within a few seconds of a PR being opened or updated, but with no documented upper
bound. If you query the PR object before that job finishes, both fields come back `null`. GitHub's
own docs recommend polling (with backoff) rather than treating a single `null` response as
authoritative. A gate that reads `mergeable_state` exactly once, immediately after a webhook
fires, is reading it at the moment it's least likely to be populated.

## 10. ⚠️ ADVANCED: Forked PRs and `refs/pull/N/head`

> ⚠️ **ADVANCED TOPIC:** Why fork-based PRs still give you a fetchable ref on the base repo.
> **Skip on first read.**

When a contributor opens a PR from their own fork, their branch physically lives in their fork's
repository, not yours. You'd normally have no reason to have push or even read access to it. But
because `refs/pull/N/head` is created on the **base** repository and GitHub replicates the
necessary Git objects there as part of accepting the PR, you can fetch a fork's PR commits without
ever adding the fork as a remote. This is also precisely why `pull_request_target` (Chapter 09,
Chapter 18) is a security-sensitive trigger: it runs workflow code from your own repo's default
branch, but can be told to check out `refs/pull/N/head` from an *untrusted* fork — mixing a
trusted execution context with untrusted checked-out code.

## 11. ⚠️ ADVANCED: `refs/pull/N/merge` Staleness

> ⚠️ **ADVANCED TOPIC:** The narrow window where `refs/pull/N/merge` doesn't yet reflect the
> latest push.
> **Skip on first read** — return after you've watched this happen live in the hands-on section.

Because `refs/pull/N/merge` is recomputed asynchronously (Section 9), there's a real window —
usually seconds, occasionally longer under load — where `head` has already moved to a new commit
but `merge` still reflects the *previous* one. Any workflow step that checks out
`refs/pull/N/merge` (some do, to test "would this merge cleanly" without touching the real base
branch) can, in that window, be testing a commit combination that no longer matches what's about
to actually merge. This is one of two real "workflow_run second-hop" surprises this curriculum's
own build process hit — see Chapter 06 §12 and Chapter 17 for the other one.

## 12. Case Study: A Gate That Trusted a Stale `merge` Ref

Imagine a Gate 2 implementation that, instead of reading the CI conclusion for `head.sha`
(Chapter 15's actual design), checked out `refs/pull/N/merge` and ran tests against *that*. Two
pushes land on the PR branch within a few seconds of each other. The gate's checkout races the
second push's `merge`-ref recomputation and gets the *first* push's synthetic merge commit — a
combination of code that no longer exists on the branch. The gate reports "tests pass" against a
commit combination nobody will actually merge. This is a real category of bug, not a hypothetical:
it's why this curriculum's Gate 2 (Chapter 15) is built to key strictly off `head.sha` and the
Checks API for that exact SHA, never off `refs/pull/N/merge`.

## 13. Case Study: Debugging "Which Commit Is This, Really?"

A common Actions confusion: a `pull_request` workflow's `github.sha` context variable is *not*
the PR branch's head commit — it's the SHA of the synthetic merge commit
(`refs/pull/N/merge`), by default, for that trigger. If your workflow logs "testing commit
`github.sha`" and a teammate can't find that SHA anywhere in the PR's own commit history, this is
why: they're looking for `head.sha`, and what got logged was the ephemeral merge commit's SHA
instead. `github.event.pull_request.head.sha` is the one that matches what the PR author actually
pushed — Chapter 10 covers this context distinction in full.

## 14. Practical Tips: Reading Refs Without `gh`

```
Reading PR refs at the Git level -- no GitHub token required
──────────────────────────────────────────────────────────────
[ ] git ls-remote <url> 'refs/pull/*'          -- list every open PR's refs
[ ] git ls-remote <url> 'refs/pull/101/head'    -- just one PR's head SHA
[ ] git fetch origin refs/pull/101/head:local   -- pull one PR's commits locally
[ ] Compare that SHA against `gh pr view 101 --json headRefOid` to confirm they match
```

Every one of these works against a **public** repo with zero authentication — a useful fact when
you only need a SHA and don't want to spend an API rate-limit call on it.

## 15. Your First Project: List the Refs, Then Fetch the Object

Run this against this curriculum's own sandbox repo (or any public repo with open PRs):

```bash
git ls-remote https://github.com/<owner>/<repo>.git 'refs/pull/*'
gh pr view <N> --repo <owner>/<repo> --json headRefOid,baseRefOid,mergeable,mergeStateStatus
```

Confirm the `headRefOid` from the second command matches the `refs/pull/<N>/head` SHA from the
first. That equality — computed two completely different ways — is the concrete proof that the PR
object and the raw ref are two views of the same underlying fact, not two unrelated systems.

## 16. Common Pitfalls & Misconceptions

1. **"A PR is a Git object."** No — Git has no PR concept. A PR is GitHub bookkeeping referencing
   two refs it maintains for you.

2. **"`refs/pull/N/merge` is just a copy of `head`."** No — it's a synthetic three-way merge
   result against the base branch, recomputed on every relevant change, and it can be absent
   entirely if the merge conflicts.

3. **"`mergeable_state: null` means the PR has a problem."** No — it usually just means GitHub
   hasn't finished computing it yet. Treat it as "not ready," not as "broken."

4. **"`github.sha` in a `pull_request` workflow is the commit the author pushed."** By default,
   no — it's the synthetic merge commit's SHA. Use `github.event.pull_request.head.sha` for the
   author's actual commit (Chapter 10).

5. **"I need a token to see any of this."** Reading refs via `git ls-remote` and reading public PR
   objects both work unauthenticated against public repos — no `gh auth login` required for the
   read-only exploration in this chapter.

## 17. Key Takeaways

- **A ref is just a name-to-SHA pointer** — nothing GitHub-specific about the mechanism itself.
- **GitHub creates two refs per open PR:** `head` (the real branch tip) and `merge` (a synthetic,
  recomputed "what if" commit) — both live under `refs/pull/`, invisible to a default fetch.
- **The PR object is a separate layer** — a GitHub record that references these refs' SHAs plus
  fields (`mergeable_state`, reviews, labels) that have no Git equivalent at all.
- **`mergeable_state` can be `null`** while GitHub is still computing it — that's the fail-closed
  case from Chapter 01, not a broken PR.
- **`github.sha` in a `pull_request` trigger is the merge ref's SHA, not the author's commit** —
  a frequent source of "I can't find this commit anywhere" confusion.

## 18. What's Next: Chapter 03 — Merge Commit vs Squash vs Rebase

Chapter 03 picks up exactly where `refs/pull/N/merge` left off: the three different ways GitHub
can actually combine a PR's commits into the base branch once auto-merge decides to fire, and why
that choice changes what `main`'s history looks like afterward.

[→ Chapter 03: Merge Commit vs Squash vs Rebase](chapter_03_merge_strategies.md)

## 19. Additional Resources

- **Pro Git, Chapter 3 — "Git Branching"** — https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell (foundational; not date-sensitive)
- **Pro Git, Chapter 10.3 — "Git Internals: Git References"** — https://git-scm.com/book/en/v2/Git-Internals-Git-References (foundational; not date-sensitive)
- **GitHub Docs, "About pull requests"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests (fetched 2026-08)
- **GitHub REST API, "Get a pull request"** — https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request (fetched 2026-08) — see the `mergeable`/`mergeable_state` field descriptions

## 20. Appendix A — Code Index

### A.1 — Listing PR Refs With Plain Git (from Section 6)

**What the code does:** In fixture mode, loads a canned ref listing so the notebook runs offline
and deterministically; in live mode, shells out to `git ls-remote` against a real repo URL and
parses the tab-separated `sha\tref` output into structured records.

**ASCII flowchart:**

```
PRA_MODE == "fixture"?
    │yes                              │no
    ▼                                  ▼
load fixtures/git_refs_sample.json   git ls-remote <url> 'refs/pull/*' 'refs/heads/main'
    │                                  │
    ▼                                  ▼
return [{"ref": ..., "sha": ...}]    parse "sha\tref" lines → same shape
```

See `labs/lab_02_pr_refs.py`'s `list_pr_refs` and `fetch_pr_object` for the full runnable version,
including the PR-object fetch that Section 7's comparison needs.
