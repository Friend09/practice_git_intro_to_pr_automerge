# Chapter 03: Merge Commit vs Squash vs Rebase

**Reading Time:** ~40 minutes
**Prerequisites:** Chapter 02 (Refs & PRs)
**Practice Notebook:** `notebooks/practice_03.ipynb`
**Reference Notebook:** `notebooks/lab_03_merge_strategies.ipynb`
**Script:** `labs/lab_03_merge_strategies.py`
**Doc Reference:** Pro Git Ch 3.2 (Basic Merging), Ch 7.6 (Rewriting History) · GitHub Docs "About merge methods"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–6 — the three strategies and their side-by-side history
diagrams. That's the entire practical payload of this chapter.

**What to SKIP on first read:** Section 10 (rebase's rewritten-SHA implications for signed
commits). Return once you've hit a signature-verification failure after a rebase.

**Key concepts in plain English:**

- **Merge commit:** A new commit with *two* parents — the tip of `main` and the tip of the PR
  branch — that GitHub creates to record "these two histories are now joined."
- **Squash:** All of a PR's commits are collapsed into exactly one new commit applied on top of
  `main`; the PR branch's individual commits never appear in `main`'s history.
- **Rebase (as a merge method):** Every commit on the PR branch is individually replayed on top of
  `main`'s current tip, each getting a *new* SHA, with no merge commit at all.
- **Fast-forward:** A merge that doesn't need a new commit because `main` hasn't moved since the
  branch diverged — it can just move the `main` pointer forward. GitHub's "rebase and merge" method
  produces this after the replay.
- **Linear vs non-linear history:** Whether `main`'s commit graph ever branches (merge commits) or
  reads as one straight line (squash and rebase both produce this on `main`).

**Your prior knowledge connection:** If you've ever run `git merge --no-ff` versus `git rebase`
locally, you've already performed the exact two operations GitHub's "Create a merge commit" and
"Rebase and merge" buttons perform for you. Squash is the one operation without a familiar local
analog most people reach for by hand — `git merge --squash` exists but is used far less often than
its GitHub-button popularity would suggest.

---

> **🔬 Automation Engineer's Lens:** The merge strategy isn't cosmetic — it's a policy decision
> baked into `gh pr merge --auto --squash` (or `--merge`, or `--rebase`) at enrollment time, and it
> determines what a future `git bisect`, `git blame`, or revert actually operates on. An automated
> pipeline that lets every PR author pick their own strategy produces a `main` history that's
> useless for automated tooling built on commit-per-change assumptions (like a changelog generator
> keyed off commit messages). Pick one strategy repo-wide and enforce it in the merge button
> configuration, not by convention.

---

> **🚦 Native vs Custom:** All three strategies are 100% native GitHub features — you select which
> ones are *allowed* in repo settings, and `gh pr merge` takes a flag (`--merge`/`--squash`/
> `--rebase`) naming which one to use for a specific PR. There is nothing to build here. The only
> thing you own is the *policy choice* (Section 7) and making sure `automerge.yml` passes the flag
> matching that policy.

---

## What You'll Learn

- What a merge commit actually is: a commit with two parents, not a metaphor
- Exactly what "squash" collapses, and what information about individual commits is lost
- Why rebase-and-merge gives every replayed commit a brand new SHA
- How to read the resulting `main` history for each strategy, using real `git log --graph` output
- The repo-wide settings that restrict which strategies are even selectable
- Why this repo picked squash, and the trade-off table behind that choice

---

## Table of Contents

- [Chapter 03: Merge Commit vs Squash vs Rebase](#chapter-03-merge-commit-vs-squash-vs-rebase)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Three Buttons, Three Different Git Operations](#1-three-buttons-three-different-git-operations)
  - [2. The Starting Point: A Diverged Branch](#2-the-starting-point-a-diverged-branch)
  - [3. Merge Commit](#3-merge-commit)
  - [4. Squash](#4-squash)
  - [5. Rebase (and Merge)](#5-rebase-and-merge)
  - [6. Side-by-Side Comparison](#6-side-by-side-comparison)
  - [7. This Repo's Design Decision](#7-this-repos-design-decision)
  - [8. Configuring Which Strategies Are Allowed](#8-configuring-which-strategies-are-allowed)
  - [9. ⚠️ ADVANCED: Squash and the PR's Individual Commit Messages](#9-️-advanced-squash-and-the-prs-individual-commit-messages)
  - [10. ⚠️ ADVANCED: Rebase, New SHAs, and Signed Commits](#10-️-advanced-rebase-new-shas-and-signed-commits)
  - [11. ⚠️ ADVANCED: Reverting Each Strategy's Output](#11-️-advanced-reverting-each-strategys-output)
  - [12. Case Study: A Changelog Bot Broken by Mixed Strategies](#12-case-study-a-changelog-bot-broken-by-mixed-strategies)
  - [13. Case Study: Bisecting a Squashed History](#13-case-study-bisecting-a-squashed-history)
  - [14. Practical Tips: Reading `git log --graph`](#14-practical-tips-reading-git-log---graph)
  - [15. Your First Project: Run All Three, Diff the Results](#15-your-first-project-run-all-three-diff-the-results)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 04 — Reading PR Data](#18-whats-next-chapter-04--reading-pr-data)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Building and Comparing All Three Strategies (from Section 15)](#a1--building-and-comparing-all-three-strategies-from-section-15)

---

## 1. Three Buttons, Three Different Git Operations

GitHub's PR page shows one green button with a dropdown: "Create a merge commit," "Squash and
merge," "Rebase and merge." They look like three cosmetic variations on the same action. They are
not — each performs a genuinely different Git operation, producing a differently-shaped `main`
history, and — this is the part that surprises people — differently-shaped even in how many
commits end up on `main` at all.

## 2. The Starting Point: A Diverged Branch

Every example in this chapter starts from the same shape: `main` has moved on since a `feature`
branch was created, and `feature` has two commits of its own.

```
main:     A---B
               \
feature:        C---D
```

`A` is the common ancestor, `B` is a commit that landed on `main` after `feature` diverged, `C` and
`D` are `feature`'s own commits. What each merge strategy does with this shape is the entire
chapter.

## 3. Merge Commit

"Create a merge commit" performs the Git operation `git merge --no-ff feature` on `main`. This
creates a brand-new commit whose *parents* are both `B` (main's tip) and `D` (feature's tip) — it
introduces no new file changes of its own, it just records that these two lines of history joined.

```
main:     A---B-------M
               \      /
feature:        C-----D
```

`main` now contains `B`, `C`, `D`, and the new merge commit `M` — four commits added to its
history for what may have been a two-commit PR (three, counting `B` which was already there).

### Even With No Divergence: PRs Merge Non-Fast-Forward by Default

That `--no-ff` flag is not decoration. GitHub's docs state a PR "is merged using the `--no-ff`
option" — so even when `main` has *not* moved (no `B`; a plain `git merge` would fast-forward),
the Merge button still creates a merge commit `M` (sometimes called an **explicit merge**, since
`M` permanently marks where the join happened). For Chapter 06's auto-merge this has a concrete
consequence: the SHA that lands on `main` is `M` — a commit that did not exist until the moment
of merging — **not** the PR's head SHA (`D`; fixture spine: PR #101 head `a1b2c3d4e5f6…`).
Automation that waits for "the PR's head commit to appear on `main`" waits forever; read the
merge result's own SHA from the API instead.

## 4. Squash

"Squash and merge" performs `git merge --squash feature`, which stages the *combined diff* of `C`
and `D` without creating a merge commit, then a plain `git commit` on top of `main` records that
combined diff as one new commit.

```
main:     A---B---S
               \
feature:        C---D    (feature's own history is untouched, and never appears in main)
```

`S` is a single new commit whose diff equals `C` + `D` combined. `main`'s history gained exactly
one commit, no matter how many commits the PR had. `C` and `D` themselves never appear in `main`'s
history — the *branch* still has them, but nothing on `main` points at them.

## 5. Rebase (and Merge)

"Rebase and merge" performs `git rebase main` on the `feature` branch itself (replaying `C` and
`D` on top of `B`, producing new commits `C'` and `D'` with new SHAs), then fast-forwards `main` to
the rebased tip — no merge commit needed, because after the rebase `main` and the rebased branch
tip are directly connected.

```
main:     A---B---C'---D'
```

`main` gained two commits — same count as the original PR — but they are **not** `C` and `D`;
they're new commits (`C'`, `D'`) with the same diffs and messages but different parent commits and
therefore different SHAs.

### What "Replay" Actually Means, Step by Step

Rebase is four mechanical steps, and the last one is why the primes appear:

1. **Find the common ancestor** of `feature` and `main` — here, `A`.
2. **Set aside the branch's own changes** — the diffs introduced by `C` and `D` are saved to a
   temporary area.
3. **Reset to the new base** — the branch is pointed at `main`'s tip, `B`.
4. **Re-apply each saved set of changes in order, committing each as a *new* commit** — same
   diff, same message, but a different parent (`C'` sits on `B`, where `C` sat on `A`), and a
   commit's SHA hashes its parent — so `C'` and `D'` are genuinely new commits carrying old
   changes, not moved copies of `C` and `D`.

## 6. Side-by-Side Comparison

| Property | Merge Commit | Squash | Rebase | Interpretability | Setup Effort |
| --- | --- | --- | --- | --- | --- |
| Commits added to `main` | N (branch) + 1 (merge commit) | Exactly 1, regardless of N | N (branch), each with a new SHA | Strong — merge commit history shows exact PR boundaries | Minimal — all three are one button/flag |
| Original commit SHAs preserved | Yes | No — collapsed away | No — every commit gets a new SHA | Weak (squash/rebase) — original SHAs are gone from `main` | Minimal |
| `main` history shape | Non-linear (has merges) | Linear | Linear | Fair — linear is easier to read but loses branch boundaries | Minimal |
| `git bisect` granularity on `main` | Per original commit | Per PR (one commit) | Per original commit | Strong (merge/rebase) — squash means bisect can't isolate a mid-PR commit | Low — no setup, just a property of the result |
| Best fit | Teams that want explicit PR boundaries preserved | Teams that want one commit per PR/feature, don't care about internal commit granularity | Teams that want linear history *and* per-commit granularity, accept SHA rewriting | Fair overall — depends entirely on team convention | Minimal — this is a policy pick, not an implementation cost |

## 7. This Repo's Design Decision

This curriculum's own `automerge.yml` calls `gh pr merge --auto --squash`. The reasoning: this
repo's sandbox PRs are deliberately small (generated by `sandbox/generate_pr.py` for exactly this
kind of practice), so per-commit granularity inside a single PR has little value, and a clean
one-commit-per-PR history on `main` makes the curriculum's own commit log easy to skim
chronologically by feature. A team merging large, multi-day feature branches with meaningful
internal commit boundaries might reasonably choose merge-commit instead — the point of this
section is that the choice should be made deliberately and once, not left to whichever button an
individual contributor happens to click.

## 8. Configuring Which Strategies Are Allowed

Repo settings — not branch protection — control which of the three buttons even appear:

```bash
gh api -X PATCH repos/{owner}/{repo} \
  -F allow_merge_commit=false \
  -F allow_squash_merge=true \
  -F allow_rebase_merge=false
```

Restricting to exactly one (as above) removes the ambiguity at the source: a contributor can't
accidentally pick the "wrong" strategy because only one is offered. `gh pr merge --auto` will fail
loudly if you pass a flag for a disabled strategy, rather than silently falling back to another
one.

## 9. ⚠️ ADVANCED: Squash and the PR's Individual Commit Messages

> ⚠️ **ADVANCED TOPIC:** What happens to a PR's individual commit messages under squash.
> **Skip on first read** — return once you've squash-merged a multi-commit PR yourself.

By default, GitHub's squash-merge commit message is the PR's title as the summary line, followed
by a body listing every individual commit message from the branch. This means the information
isn't strictly *lost* — it survives inside the merge commit's message body — but it's no longer
independently `git log`-addressable per original commit. A commit message convention that assumes
`git log --oneline` shows one line per logical change breaks under squash unless your team also
adopts a PR-title convention that carries the same weight a commit message used to.

## 10. ⚠️ ADVANCED: Rebase, New SHAs, and Signed Commits

> ⚠️ **ADVANCED TOPIC:** Why a rebased commit's original GPG/SSH signature doesn't survive.
> **Skip on first read** — return if your org requires signed commits.

Because rebase produces new commits with new parents (and therefore new SHAs), any GPG or SSH
signature on the *original* commit does not carry over — the signature was made over the original
commit's exact content including its old parent SHA, which no longer matches. GitHub's own
"Rebase and merge" re-signs the new commits as the GitHub web-flow identity (if commit signing is
enabled repo-wide), but a contributor's personal signature on their original commits is gone from
`main`'s copy. Teams that require signed commits from specific authors as an audit requirement
should treat this as a hard reason to prefer merge-commit or squash instead. The same SHA
rewriting is behind the **Golden Rule of Rebasing**: never rebase commits that other people may
have based work on — their work would then hang off commits that no longer exist in the rewritten
history. (GitHub's server-side rebase-and-merge skirts the rule only because it rewrites the
branch at merge time, when the PR is finished.)

## 11. ⚠️ ADVANCED: Reverting Each Strategy's Output

> ⚠️ **ADVANCED TOPIC:** `git revert` behaves differently against each strategy's result.
> **Skip on first read.**

Reverting a squash commit is simple — `git revert <squash-sha>` undoes the whole PR in one step,
since it was one commit. Reverting a merge commit requires `git revert -m 1 <merge-sha>`, telling
Git which parent (`main`'s side) to revert *to* — a detail that trips people up the first time they
try it, because a plain `git revert` on a merge commit errors out asking for `-m`. Reverting a
rebased PR means reverting each of its individual commits (or a range), since there's no single
commit representing the whole PR.

## 12. Case Study: A Changelog Bot Broken by Mixed Strategies

A team allows all three merge strategies with no policy. A changelog generator that parses
`main`'s commit log expecting "one commit == one changelog entry" works fine for squash-merged
PRs, silently produces multiple (sometimes internal, WIP-labeled) entries for merge-commit PRs, and
occasionally misses entries entirely for rebase-merged PRs where an author's commit message didn't
follow the expected format (since rebase preserves whatever the author originally wrote, with no
PR-title override the way squash gets one). The fix wasn't in the changelog bot — it was Section 7:
pick one strategy repo-wide, matching what any downstream tooling assumes.

## 13. Case Study: Bisecting a Squashed History

A regression is found in `main`. `git bisect` walks the commit history in `main`, testing each
commit. Under squash, the smallest unit `bisect` can isolate is "the whole PR" — if the actual
regression was introduced by the *second* of five commits inside one squashed PR, `bisect` can only
tell you "somewhere in this PR," not which internal change. Under merge-commit or rebase, the
original five commits are individually addressable and `bisect` can pinpoint the exact one. This is
the concrete cost behind the "bisect granularity" row in Section 6's table.

## 14. Practical Tips: Reading `git log --graph`

```
git log --oneline --graph --all
──────────────────────────────────
*   commit with two parents above it (| \)   → a merge commit
|\
| * commit only reachable via one branch      → still on that branch, not on main
* | commit that continues the OTHER line       → main's own commit at time of merge
|/
* commit both lines share                      → the common ancestor
```

A straight line of `*` with no `|\` or `|/` anywhere means the history is fully linear — the
signature of squash or rebase, never merge-commit.

### Anatomy of a Merge Conflict

All three strategies can hit a conflict when both sides changed the same lines. Here is one for
real, from a throwaway repo where `main` set `threshold: 80` and `feature` set `threshold: 60`
on the same line of a `gates.yml` (outputs captured verbatim from git 2.x):

```
$ git merge feature
Auto-merging gates.yml
CONFLICT (content): Merge conflict in gates.yml
Automatic merge failed; fix conflicts and then commit the result.
```

Git pauses the merge and writes **conflict markers** into the file — seven left angle brackets,
seven equals signs, seven right angle brackets, each row naming its branch:

```
<<<<<<< HEAD
threshold: 80
=======
threshold: 60
>>>>>>> feature
ceiling: 400
```

**What to notice:**

- Above `=======` is the **target** branch's version (`HEAD`, i.e. `main`); below it, the
  **source** branch's (`feature`).
- `ceiling: 400` sits *outside* the markers — unconflicted lines were already merged; only the
  disputed region is fenced.

`git status` at this point names the escape hatch itself:

```
$ git status
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   gates.yml
```

**What to notice:** `both modified` is the conflict signature, and `git merge --abort` — printed
by Git itself — walks everything back to the pre-merge state at any point before the final commit.

Resolving is two steps: edit the file to what you want to keep (here, back to `threshold: 70`)
and delete the marker lines, then `git add` it. After the `add` comes the intermediate state most
tutorials skip:

```
$ git add gates.yml
$ git status
On branch main
All conflicts fixed but you are still merging.
  (use "git commit" to conclude merge)

Changes to be committed:
	modified:   gates.yml
```

**What to notice:**

- "still merging" — resolution is not completion: the resolved content is only *staged*. A plain
  `git commit` now concludes the merge as merge commit `M`; until then the merge is still open
  and `git merge --abort` still works.

**Rebase contrast:** a three-way merge presents *all* conflicts at once — one resolve/`add`/
`commit` cycle total. Rebase (Section 5) replays commits one at a time, so it pauses at each
conflicting commit: resolve, `git add`, then `git rebase --continue` (or `git rebase --abort`),
possibly once per commit that conflicts.

## 15. Your First Project: Run All Three, Diff the Results

Against a real disposable repo (never `main` of anything you care about): create a `feature`
branch with two commits diverged from `main`, then apply all three strategies to independent
copies and diff their `git log --oneline --graph --all` output side by side. This lab's script does
exactly this — run it in live mode to build the actual repo rather than reading the fixture's
canned diagrams.

## 16. Common Pitfalls & Misconceptions

1. **"They're just three UI options for the same operation."** No — they are three distinct Git
   operations (`merge --no-ff`, `merge --squash` + `commit`, `rebase` + fast-forward) with
   different SHA and commit-count outcomes.

2. **"Squash loses information."** Not entirely — individual commit messages survive in the merge
   commit's body by default, just not as independently addressable commits.

3. **"Rebase preserves the original commits."** No — every replayed commit gets a new SHA. The
   diffs and messages match, but `git log` sees them as entirely different commits.

4. **"I can pick whichever strategy I want per PR and it won't matter."** It matters the moment
   any tooling (changelog generators, bisect workflows, blame-based ownership tools) assumes one
   consistent shape.

5. **"A signed commit stays signed after rebase."** No — see Section 10. The signature doesn't
   transfer to the new SHA.

## 17. Key Takeaways

- **Three buttons, three Git operations:** merge commit (`--no-ff`), squash (`--squash` + one new
  commit), rebase (replay + fast-forward) — not cosmetic variants of one thing.
- **Only squash guarantees exactly one commit added to `main`ˊ per PR**, regardless of how many
  commits the PR branch had.
- **Rebase gives every commit a new SHA** — this breaks signatures and matters for any tooling that
  keys off SHA identity.
- **This is a policy decision, not an implementation cost** — restrict the repo to one strategy
  (Section 8) so the choice can't drift PR-to-PR.
- **This repo picked squash** for its own reasons (small, generated sandbox PRs); your repo's
  right answer depends on how much you value per-commit `bisect`/`blame` granularity.

## 18. What's Next: Chapter 04 — Reading PR Data

Chapter 04 moves from "what does GitHub do to history when it merges" to "how do I read what's
happening to a PR *before* it merges" — `gh pr view`, `gh api`, and pagination, which is what
every gate in Phase 3 is actually built on.

[→ Chapter 04: Reading PR Data](chapter_04_reading_pr_data.md)

## 19. Additional Resources

- **Pro Git, "Basic Branching and Merging"** — https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging (foundational; not date-sensitive)
- **Pro Git, "Rewriting History"** — https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History (foundational; not date-sensitive)
- **GitHub Docs, "About merge methods on GitHub"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-merge-methods-on-github (fetched 2026-08)
- **GitHub Docs, "Configuring commit squashing for pull requests"** — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests (fetched 2026-08)
- **GitHub Docs, "About pull request merges"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges (fetched 2026-08) — source for §3's `--no-ff` default and §10's note that server-side rebase always creates new commit SHAs

## 20. Appendix A — Code Index

### A.1 — Building and Comparing All Three Strategies (from Section 15)

**What the code does:** Builds a disposable local repo with a diverged `feature` branch, copies it
three times, and applies a different merge strategy to each copy, printing the resulting
`git log --graph` output for direct comparison.

**ASCII flowchart:**

```
build_demo_repo() → base repo (main has 1 extra commit, feature has 2)
        │
        ├── copy 1 → apply_merge_commit() → git log --graph
        ├── copy 2 → apply_squash()       → git log --graph
        └── copy 3 → apply_rebase()       → git log --graph
```

See `labs/lab_03_merge_strategies.py` for the full runnable version. Fixture mode prints canned
diagrams verified once against a real live-mode run; live mode builds and diffs a real disposable
repo under a temp directory, touching no network at all.
