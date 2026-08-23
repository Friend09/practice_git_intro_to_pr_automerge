# Chapter 00: Fundamentals — Git, Pull Requests & GitHub Actions

**Reading Time:** ~55 minutes
**Prerequisites:** None
**Practice Notebook:** `notebooks/practice_00.ipynb`
**Reference Notebook:** `notebooks/lab_00_fundamentals.ipynb`
**Script:** `labs/lab_00_fundamentals.py`
**Doc Reference:** Pro Git Ch 1 (Getting Started), Ch 2 (Git Basics) · GitHub Docs "About pull requests", "Understanding GitHub Actions"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 2–7 (the three areas, add/commit), Section 10 (the PR
lifecycle end to end), and Sections 11–12 (what a workflow file even is). If `git add . && git
commit -m "..." && git push origin main` is currently your entire mental model of Git, and "GitHub
Actions" is a phrase you've heard but never opened a `.yml` file for, those are the sections that
fill in what's actually happening underneath.

**What to SKIP on first read:** Section 8 (the deep mechanics of what a merge commit actually is).
Chapter 03 owns that; this chapter only needs you to know that branches can be combined.

**Key concepts in plain English:**

- **Working directory:** The actual files on your disk, exactly as you're editing them right now.
- **Staging area (the "index"):** A holding area where you tell Git "include this specific change
  in the *next* commit" — separate from the working directory, and separate from history.
- **Repository (history):** The permanent, committed record — every commit you've ever made, each
  one a snapshot, chained to the one before it.
- **Branch:** A movable, named pointer to one specific commit — not a copy of any files.
- **Merge:** Combining two branches' histories into one — the simplest form just moves a pointer
  forward; the general form (Chapter 03) creates a new commit joining both histories.
- **Pull request (PR):** A GitHub-hosted proposal to merge one branch into another, plus everything
  GitHub attaches to that proposal along the way — checks, reviews, comments, a final merge.
- **GitHub Actions workflow:** A YAML file, committed to your repo under `.github/workflows/`, that
  tells GitHub "when X happens, automatically run Y" — the mechanism behind every automated check a
  PR waits on.

**Your prior knowledge connection:** `git add .` stages every changed file at once; `git commit -m
"message"` snapshots whatever's staged; `git push origin main` uploads your local commits to
GitHub. You already know the three verbs — this chapter's job is to make the three *nouns* they
operate on (working directory, staging area, repository) visible, walk what happens to those
commits once they become a pull request, and show you the one file type (a workflow YAML) that
makes any of this automatic.

---

> **🔬 Automation Engineer's Lens:** Every automated PR pipeline this curriculum builds is, at its
> core, a program that watches for state transitions in the exact lifecycle Section 10 describes —
> branch pushed, checks run, merge becomes available, merged — and Section 11's workflow file is
> the concrete mechanism that makes "checks run" happen at all. If either of those isn't solid
> intuition yet, every later chapter's automation will read as magic instead of mechanism. This
> chapter's only job is to make sure it isn't magic.

---

> **🚦 Native vs Custom:** Everything in this chapter — staging, committing, branching, merging,
> pushing, the PR lifecycle, and the existence of workflow files — is 100% native Git and native
> GitHub behavior. Nothing here is custom to this curriculum. This chapter is pure foundation;
> Chapter 01 is where this repo's own design decisions (the Airlock Principle) begin.

---

## What You'll Learn

- The three areas every Git operation moves a change through: working directory, staging, history
- What `git add` and `git commit` actually do to those areas, not just what they output
- How to read `git status` and `git diff` at each stage
- What a branch really is (a pointer, not a copy) and what the simplest possible merge looks like
- The full, plain-language, end-to-end lifecycle of a pull request — branch to merge
- What a *successful* merge concretely looks like in GitHub's own data
- What a GitHub Actions workflow file actually is, where it lives, and its four basic pieces
- Enough vocabulary to make every later chapter's terms (ref, PR object, merge strategy, workflow) land on solid ground

---

## Table of Contents

- [Chapter 00: Fundamentals — Git, Pull Requests \& GitHub Actions](#chapter-00-fundamentals--git-pull-requests--github-actions)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Why This Chapter Exists, and What a Commit Actually Is](#1-why-this-chapter-exists-and-what-a-commit-actually-is)
  - [2. The Three Areas](#2-the-three-areas)
  - [3. `git add` and `git commit`: Working Directory → Staging → History](#3-git-add-and-git-commit-working-directory--staging--history)
  - [4. Reading `git status` and `git diff`](#4-reading-git-status-and-git-diff)
  - [5. Branches Are Just Pointers](#5-branches-are-just-pointers)
  - [6. The Simplest Merge: A Fast-Forward](#6-the-simplest-merge-a-fast-forward)
  - [7. Remotes: `push` and `pull`, Precisely](#7-remotes-push-and-pull-precisely)
  - [8. The Pull Request Lifecycle, End to End](#8-the-pull-request-lifecycle-end-to-end)
  - [9. What a Successful Merge Actually Looks Like](#9-what-a-successful-merge-actually-looks-like)
  - [10. What a GitHub Actions Workflow File Actually Is](#10-what-a-github-actions-workflow-file-actually-is)
  - [11. Anatomy of a Minimal Workflow: `on:`, `jobs:`, `steps:`](#11-anatomy-of-a-minimal-workflow-on-jobs-steps)
  - [12. How a Workflow Connects Back to the PR Lifecycle](#12-how-a-workflow-connects-back-to-the-pr-lifecycle)
  - [13. ⚠️ ADVANCED: Amending vs a New Commit](#13-️-advanced-amending-vs-a-new-commit)
  - [14. Practical Tips: A Command-to-Area Cheat Sheet](#14-practical-tips-a-command-to-area-cheat-sheet)
  - [15. Your First Project: Walk the Whole Lifecycle Yourself](#15-your-first-project-walk-the-whole-lifecycle-yourself)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 01 — Auto-Merge \& The Airlock Principle](#18-whats-next-chapter-01--auto-merge--the-airlock-principle)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Three Areas, a Merge, the PR Lifecycle, and a Workflow File (from Section 15)](#a1--the-three-areas-a-merge-the-pr-lifecycle-and-a-workflow-file-from-section-15)

---

## 1. Why This Chapter Exists, and What a Commit Actually Is

This curriculum's other 23 chapters assume you're comfortable with Git day to day (the README says
so explicitly) and go straight into PR-level and Actions-level mechanics. If your actual working
vocabulary stops at `git add . && git commit -m "..." && git push origin main` — a sequence that
works perfectly well without you needing to know *why* — and "GitHub Actions" is a name you've seen
without ever opening the file behind it, this chapter is the missing layer underneath, before
Chapter 01 starts using all of this vocabulary at speed.

One concept underlies everything below: Git doesn't store a list of *changes* the way some older
version-control systems do — it stores a full snapshot of every tracked file at each commit. Two
commits in a row that only changed one line still each represent Git's *complete* picture of every
file at that point; Git is simply efficient enough internally that this doesn't cost what it sounds
like it should.

## 2. The Three Areas

Every file you touch in a Git repo is, at any moment, in one of three areas:

```
Working Directory  ──(git add)──▶  Staging Area  ──(git commit)──▶  Repository (history)
   (your files,                    ("what will be                   (permanent,
    as you're                       in the NEXT                      committed
    editing them)                   commit")                         snapshots)
```

This is the single mental model the rest of the chapter builds on. `git add . && git commit -m
"..."` is just this diagram, compressed into two commands run back to back. The working directory
is exactly what it sounds like — the actual files sitting on your disk right now. Git watches this
directory for changes but doesn't act on any of them until you tell it to.

## 3. `git add` and `git commit`: Working Directory → Staging → History

```bash
git add README.md      # stage one specific file
git add .               # stage every changed file in the current directory and below
```

`git add` copies the *current* state of a file from the working directory into the staging area.
This is why editing a file *after* running `git add` on it means the staged copy and the working
copy diverge — `git add` snapshots the file at the moment you run it, not "this file, forever."

```bash
git commit -m "fix: correct typo in README"
```

`git commit` takes everything currently in the staging area and seals it into a new, permanent
commit — a snapshot with a message, an author, a timestamp, and a pointer back to the commit that
came before it. Anything in the working directory that was never staged is **not** included, even
if it's sitting right next to files that were.

### `git add` copies — it does not move

Staging a file does not take it *out* of the working directory. `git add` **copies** its current
content into the staging area. Real proof, from a throwaway repo (hint lines trimmed) — stage a
brand-new file (call its content **vA**), then edit the working copy again (**vB**) *before*
committing:

```
$ git add quicknote.txt          # working copy is vA; a COPY of vA is now staged
$ git status
On branch main
Changes to be committed:
        new file:   quicknote.txt

$ echo "edited after staging" >> quicknote.txt    # working copy is now vB
$ git status
On branch main
Changes to be committed:
        new file:   quicknote.txt

Changes not staged for commit:
        modified:   quicknote.txt
```

**What to notice:**

- The **same file appears under both headings at once** — the staged copy (vA) and the working
  copy (vB) are two different versions living in two different areas. If `git add` *moved* the
  file, this state couldn't exist.
- Committing right now would commit **vA**, not the vB you see in your editor — `git add`
  snapshots the moment you run it, not "this file, forever."
- The staging area is a real file on disk: the first time you ever stage anything in a fresh
  repo, watch `.git/index` appear in your file browser — that file *is* the staging area.

## 4. Reading `git status` and `git diff`

`git status` is the one command that tells you, at any moment, exactly what's in each of the three
areas:

```
Untracked files:                    ← in the working directory, Git doesn't know about it yet
Changes not staged for commit:      ← Git knows the file, but working copy differs from staged/last commit
Changes to be committed:            ← in the staging area, will be in the NEXT commit
nothing to commit, working tree clean   ← all three areas agree
```

`git diff` (no arguments) compares the working directory against the staging area — "what have I
changed that I haven't staged yet." `git diff --staged` (or `--cached`) compares the staging area
against the last commit — "what will actually go into the next commit." These are genuinely
different comparisons, and conflating them is a common source of "I thought I already staged that"
confusion. This chapter's lab walks a single file through all of these states, printing the real
`git status`/`git diff` output at each one.

### Worked trace: one file through every state

The legend above becomes concrete by walking one file through it. Real output from a throwaway
repo (repeated `On branch main` and hint lines trimmed). Create `notes.md` containing one line —
call that content **vA** — then stage and commit it:

```
$ git status                        # notes.md just created (vA)
On branch main
Untracked files:
        notes.md

$ git add notes.md
$ git status
Changes to be committed:
        new file:   notes.md

$ git commit -m "docs: add notes.md"
[main 76e060d] docs: add notes.md
 1 file changed, 1 insertion(+)
$ git status
nothing to commit, working tree clean
```

**What to notice:**

- The file moves through the legend's headings in order: `Untracked files:` (working directory
  only) → `Changes to be committed:` (a vA copy in the staging area) → gone once committed.
- `nothing to commit, working tree clean` is the all-areas-agree state: working directory,
  staging area, and history all hold vA of `notes.md`.

Now append a second line to `notes.md` — the working copy becomes **vB** — and run both commands
from the legend:

```
$ git status                        # after the edit (working copy is vB)
Changes not staged for commit:
        modified:   notes.md

$ git diff
--- a/notes.md
+++ b/notes.md
@@ -1 +1,2 @@
 Airlock demo notes (vA).
+Second line: gates fail closed (vB).
```

**What to notice:**

- `modified:` under `Changes not staged for commit:` — the staging area and history still hold
  vA; only the working directory has vB.
- `git diff` (no arguments) shows exactly that gap: the working directory's new vB line against
  the staged vA. `git diff --staged` right now would print *nothing* — staging and the last
  commit still agree. One more `git add` + `git commit` repeats the first block's middle and the
  file is back to clean — the cycle every change in this curriculum travels.

## 5. Branches Are Just Pointers

A branch is a name pointing at one specific commit — nothing more. `main` isn't a folder or a copy
of your project; it's a label that currently points at whatever commit is main's latest. Creating a
new branch (`git checkout -b feature`) doesn't copy any files — it just creates a second pointer,
initially pointing at the exact same commit `main` does. As you commit on `feature`, only
`feature`'s pointer moves forward; `main`'s stays put until something merges back into it.

```
main    ──▶ A ──▶ B                    (main points at B)
                    \
feature              ──▶ C ──▶ D       (feature points at D, diverged after B)
```

## 6. The Simplest Merge: A Fast-Forward

When `main` hasn't moved at all since a branch diverged from it, merging that branch back is the
simplest possible case: Git just moves `main`'s pointer forward to match the branch's tip — no new
commit needed, because there's nothing to *combine*, only a pointer to advance.

```
Before:  main ──▶ A ──▶ B
                          \
                feature    ──▶ C        (feature is one commit ahead)

After merge (fast-forward):
         main ────────────────▶ C      (main's pointer just moved)
```

This is deliberately the *only* merge case this chapter covers. The moment `main` has ALSO moved
since the branch diverged, Git needs to make a real decision about how to combine two diverged
histories — that's Chapter 03's entire subject (merge commit vs squash vs rebase), and it's a
meaningfully bigger topic than this one diagram.

## 7. Remotes: `push` and `pull`, Precisely

A remote is just another copy of the repository, somewhere else — `origin` is the conventional name
for "the remote I cloned this from" (almost always GitHub, in this curriculum). `git push origin
main` uploads your local commits on `main` to that remote; `git pull` does the reverse — fetches the
remote's new commits and merges them into your current local branch. Neither command touches the
staging area — they operate purely at the repository/history level, moving *commits*, never
uncommitted changes.

## 8. The Pull Request Lifecycle, End to End

Putting Sections 3–7 together, here's the complete arc from "I want to make a change" to "it's
merged":

```
[1] Branch created         git checkout -b fix/readme-typo
[2] Commits made locally   the add -> commit cycle (Section 3), on that branch
[3] Branch pushed          git push origin fix/readme-typo
[4] PR opened               gh pr create (or the GitHub UI) — GitHub compares the branch to main
[5] Checks run               GitHub Actions workflows fire automatically (Sections 10-12 below)
[6] Review given             a human approves, or requests changes
[7] Merge becomes available  every required check + review is satisfied
[8] Merged                   GitHub combines the branch into main (Ch 03's strategies)
[9] Branch cleaned up        the merged branch is typically deleted; its commits live on in main
```

Every later chapter in this curriculum is, in one way or another, about steps 4–8 of this exact
diagram — Chapter 01 names this same arc "the Airlock," Chapters 08–13 go deep on step 5's
mechanics, and Chapters 14–17 build the automation that makes steps 7–8 happen without a human
clicking anything.

## 9. What a Successful Merge Actually Looks Like

In the GitHub UI, a successful merge shows a purple "Merged" badge instead of the green "Open" one.
In the *data* — the same PR object Chapter 04 goes deep on reading — success is marked by specific
fields, not just the PR's `state`:

```
state: "closed"              ← true for BOTH a merged PR and one closed WITHOUT merging
merged: true                 ← the field that actually distinguishes the two
merge_commit_sha: "7c4a9e8…" ← the new commit on main representing the merge (or the fast-forwarded tip)
merged_at: "2026-08-15T…"    ← when it happened
```

`state == "closed"` alone is not proof of anything — a PR someone closed without merging is *also*
`"closed"`. `merged: true` is the fact that actually matters, and it's exactly what any automation
you build later (including this curriculum's own gates) needs to check, never `state` alone.

## 10. What a GitHub Actions Workflow File Actually Is

Step [5] of Section 8's lifecycle — "checks run" — doesn't happen by magic. It happens because your
repository contains at least one **workflow file**: a plain YAML file, committed like any other
file in your repo, living under a specific directory GitHub watches automatically:

```
.github/
└── workflows/
    └── ci.yml          ← any .yml file here, GitHub discovers and runs automatically
```

There's no separate registration step — commit a correctly-shaped YAML file to that exact
directory, and GitHub starts watching for its trigger the moment the commit lands. That's the
entire mechanism behind "GitHub Actions" as a feature: files you write, GitHub executes.

## 11. Anatomy of a Minimal Workflow: `on:`, `jobs:`, `steps:`

Every workflow file, however large, is built from the same four pieces:

```yaml
name: CI                          # ← what it's called, in the Actions UI

on:                                # ← WHEN it runs
  pull_request:
    paths:
      - 'sandbox/**'

jobs:                              # ← WHAT it runs (one or more jobs)
  test:
    runs-on: ubuntu-latest         # ← which kind of machine
    steps:                         # ← an ORDERED list of commands/actions
      - name: Checkout
        uses: actions/checkout@v4
      - name: Run tests
        run: python -m pytest
```

Read top to bottom: `name:` is cosmetic (just a label). `on:` says what event makes this file run —
here, a pull request being opened or updated. `jobs:` contains one or more named jobs; this one has
a single job called `test`. Each job's `steps:` run in order, on one virtual machine — `uses:` runs
a pre-packaged action someone else wrote (`actions/checkout@v4` copies your repo's code onto that
machine); `run:` executes a raw shell command. This chapter's lab parses exactly this file and
prints each piece back out, so the shape is something you've seen work, not just read about.

### What the run looks like

When that file fires, the Actions tab renders it roughly like this (authored, realistic shape):

```
CI                                      ← the workflow's name: key
 ✓ test                        2m 04s   ← the job — the key you wrote under jobs:
     ✓ Set up job                  2s
     ✓ Checkout                    1s
     ✓ Run tests               1m 58s
     ✓ Complete job                0s
```

**What to notice:**

- You wrote two steps; the run shows four. GitHub adds `Set up job` and `Complete job` to
  **every** job automatically — `Set up job`'s log even lists the runner image and preinstalled
  tools (see §19's run-logs reference).
- The job displays as `test` — the identifier you chose as the key under `jobs:`; the
  `jobs.<job_id>.name` field exists precisely to give it a friendlier display name in the UI.
  Your own steps run in exactly the order listed under `steps:`, each with its own mark and
  duration.

## 12. How a Workflow Connects Back to the PR Lifecycle

The workflow above triggers on `pull_request` — meaning the moment step [3] of Section 8's
lifecycle happens (a branch is pushed and a PR is opened or updated against it), this file's `on:`
condition is satisfied, and GitHub runs its job automatically. The result — pass or fail — is what
step [5] ("checks run") actually produces, and it's what step [7] ("merge becomes available")
waits on. Nothing about this connection is custom or hidden: it's the direct, mechanical link
between a file sitting in your repo and a PR's checks tab lighting up.

## 13. ⚠️ ADVANCED: Amending vs a New Commit

> ⚠️ **ADVANCED TOPIC:** `git commit --amend` and why rewriting shared history is dangerous.
> **Skip on first read.**

`git commit --amend` replaces the most recent commit entirely with a new one (new snapshot, new
SHA) rather than adding a second commit after it — useful for fixing a typo in a commit message or
adding a forgotten file *before* that commit has been pushed and shared. Once a commit has been
pushed and others may have built on it, amending rewrites history other people already have, which
is exactly the class of problem Chapter 03 §10 covers in depth for rebase specifically. As a
beginner default: prefer a new commit over amending once anything is shared. (A related, finer-
grained tool worth knowing exists: `git add -p` stages only *part* of a file's changes, hunk by
hunk, rather than the whole file at once — the same working-directory-to-staging-area mechanism
from Section 3, just at finer granularity.) A parallel caution applies to workflow files: they
"execute for real" the moment they're committed under `.github/workflows/`, so a mistake there
isn't just a wrong lesson the way a typo elsewhere might be — `.github/instructions/
workflows.instructions.md` treats every file in that directory as load-bearing for exactly this
reason.

## 14. Practical Tips: A Command-to-Area Cheat Sheet

```
Command              Moves data...
────────────────────────────────────────────────────────────
git add <file>        working directory  →  staging area
git commit             staging area       →  repository (history)
git commit -a          (tracked files' working dir changes) → staged, then → history, in one step
git push               local repository   →  remote repository
git pull                remote repository  →  local repository (fetch + merge)
git status             shows what's in EACH of the three areas, right now
git diff                working directory  vs  staging area
git diff --staged       staging area       vs  last commit
```

A common early confusion belongs here too: someone edits a file, runs `git commit -m "..."`
directly (no `git add` first), and `git status` afterward still shows the file as modified. The
commit that just happened committed whatever was **already staged** from before — not the file's
brand-new edits, which were never added to the staging area at all. `git commit -a` stages every
already-*tracked* file's changes automatically before committing, but it still won't pick up a
brand-new, never-tracked file, which always needs an explicit `git add` at least once.

## 15. Your First Project: Walk the Whole Lifecycle Yourself

On a disposable local repo (never one you care about): create a file, watch `git status` describe
it as untracked, `git add` it, watch `git status` change, commit it, watch it go clean. Edit the
file again, run `git diff`, then commit the change. Create a branch, commit once more on it, switch
back to `main`, and merge — since nothing moved on `main` in the meantime, this will be a
fast-forward (Section 6), the simplest case there is. This chapter's lab script does exactly this
sequence in live mode against a real disposable repo, then prints the plain-language PR lifecycle
(Section 8), fetches a raw "successfully merged" PR object to show exactly which fields mark
success (Section 9), and parses a minimal real workflow file (Section 11) to print its four pieces
back out.

## 16. Common Pitfalls & Misconceptions

1. **"`git add .` and `git commit` are basically one action."** No — they move data through two
   distinct areas; anything staged but not yet committed is still just sitting in the index,
   uncommitted.

2. **"A branch is a copy of the project."** No — it's a single pointer to one commit. Branching is
   instantaneous specifically because nothing is copied.

3. **"A merged PR and a closed-without-merging PR look the same in the data."** They share
   `state: "closed"`, but only a real merge sets `merged: true` and a `merge_commit_sha` (Section
   9).

4. **"Every merge creates a new merge commit."** Not the fast-forward case (Section 6) — when
   nothing diverged, Git just moves the pointer. Chapter 03 covers the cases where a real combining
   decision is needed.

5. **"A workflow file needs to be registered somewhere before it'll run."** No — committing a
   correctly-shaped `.yml` file under `.github/workflows/` is the entire registration step; GitHub
   discovers it automatically (Section 10).

## 17. Key Takeaways

- **Three areas, one direction:** working directory → (`git add`) → staging area → (`git commit`) →
  repository history.
- **A branch is a movable pointer to a commit, not a copy of anything**, and the simplest merge
  (fast-forward) just moves that pointer — Chapter 03 covers what happens once that's not enough.
- **A successful PR merge is marked by `merged: true` plus a `merge_commit_sha`** — not by `state`
  alone, which is shared with PRs closed without merging.
- **A GitHub Actions workflow is just a YAML file** committed under `.github/workflows/`, with a
  name, a trigger (`on:`), and one or more jobs made of ordered steps — nothing more mysterious
  than that.
- **The workflow's trigger is what makes step [5] of the PR lifecycle ("checks run") actually
  happen** — a direct, mechanical link between a committed file and a PR's checks tab.

## 18. What's Next: Chapter 01 — Auto-Merge & The Airlock Principle

Chapter 01 takes the plain-language PR lifecycle from Section 8 and gives it this curriculum's own
governing vocabulary — the Airlock Principle — plus the specific, fail-closed design philosophy
every chapter after it builds on.

[→ Chapter 01: Auto-Merge & The Airlock Principle](chapter_01_airlock_principle.md)

## 19. Additional Resources

- **Pro Git, Chapter 1 — "Getting Started"** — https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control (foundational; not date-sensitive)
- **Pro Git, Chapter 2 — "Git Basics"** — https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository (foundational; not date-sensitive) — the canonical source for Sections 2–4
- **GitHub Docs, "About pull requests"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests (fetched 2026-08)
- **GitHub Docs, "About branches"** — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches (fetched 2026-08)
- **GitHub Docs, "Understanding GitHub Actions"** — https://docs.github.com/en/actions/get-started/understanding-github-actions (fetched 2026-08) — the source for Sections 10–12; Chapter 08 goes far deeper
- **GitHub Docs, "Using workflow run logs"** — https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs (fetched 2026-08) — source for §11's implicit `Set up job` / `Complete job` steps ("GitHub adds two additional steps to each job")
- **GitHub Docs, "Workflow syntax for GitHub Actions" — `jobs.<job_id>.name`** — https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (fetched 2026-08) — source for §11's job display-name note

## 20. Appendix A — Code Index

### A.1 — The Three Areas, a Merge, the PR Lifecycle, and a Workflow File (from Section 15)

**What the code does:** Walks a disposable repo through untracked → staged → committed, shows a
`git diff` before a second commit, performs the simplest possible merge (a fast-forward), then
prints the plain-language PR lifecycle, fetches a raw "successfully merged" PR object to show
exactly which fields mark success, and parses a minimal workflow file into its four basic pieces.

**ASCII flowchart:**

```
demonstrate_three_areas(repo)              → status at each of 3 stages
demonstrate_diff_and_second_commit(repo)   → diff, then a second commit's log
demonstrate_branch_and_merge(repo)         → branch, commit, fast-forward merge, log --all

PR_LIFECYCLE_STAGES                        → 9 stages, branch to cleanup
fetch_merged_pr_example()                  → raw PR object, merged: true
describe_successful_merge(pr)              → {state, merged, merge_commit_sha, merged_at}

describe_minimal_workflow(MINIMAL_WORKFLOW_YAML)
    → {name, trigger, job_id, runs_on, step_names}
```

See `labs/lab_00_fundamentals.py` for the full runnable version.
