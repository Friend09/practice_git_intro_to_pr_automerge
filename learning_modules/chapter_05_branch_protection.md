# Chapter 05: Branch Protection & Rulesets

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 03 (Merge Strategies)
**Practice Notebook:** `notebooks/practice_05.ipynb`
**Reference Notebook:** `notebooks/lab_05_branch_protection.ipynb`
**Script:** `labs/lab_05_branch_protection.py`
**Doc Reference:** GitHub Docs "About protected branches", "Rulesets"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8, and especially Section 8 — a real bug this curriculum's
own build hit, not a hypothetical.

**What to SKIP on first read:** Section 11 (rulesets vs classic branch protection, in depth).
Classic protection is enough to follow the rest of this curriculum; return to rulesets once you're
managing protection across many repos.

**Key concepts in plain English:**

- **Branch protection:** Repo-level rules restricting what can happen to a specific branch (usually
  `main`) — no direct pushes, required status checks, required reviews, and more.
- **Required status check:** A named check (matched by string, e.g. `"test"`) that must report
  `success` before GitHub will allow a merge into a protected branch — by anyone, human or bot.
- **`enforce_admins`:** Whether repo admins are *exempt* from these rules. `false` (the default) —
  meaning admins bypass them — is what let this curriculum's own maintainer push chapters straight
  to `main` throughout the build.
- **Ruleset:** GitHub's newer, more flexible protection mechanism — can target multiple branches by
  pattern, layers with classic protection, and supports finer-grained bypass lists.
- **Administration permission:** The specific permission scope required to *read or write* the full
  branch protection configuration — distinct from, and stricter than, `contents: write`.

**Your prior knowledge connection:** If you've ever been blocked from pushing straight to `main` on
a shared repo and had to open a PR instead, you've already experienced branch protection in effect
— this chapter is about the mechanism and, specifically, about what your *automation's* token can
and can't see about it.

---

> **🔬 Automation Engineer's Lens:** The most expensive branch-protection bug isn't misconfigured
> rules — it's a gate that assumes it can *read* the configuration and silently gets a 403 it never
> checks for. Section 8's discovery is exactly this: `GITHUB_TOKEN` cannot call the full protection
> endpoint at all, regardless of `permissions:` block contents, because that endpoint requires
> Administration permission specifically. A gate written against the wrong endpoint doesn't fail
> loudly — it fails with a 403 that, if uncaught, can be misread as "protection isn't configured."

---

> **🚦 Native vs Custom:** Branch protection itself is entirely native — configured via repo
> settings or `gh api`, enforced by GitHub's own merge machinery, not your code. What you build is
> the *check* your automation runs to confirm protection is actually configured the way you expect
> before trusting the rest of your pipeline — and, as Section 8 covers, choosing the right endpoint
> to ask that question with the token you actually have.

---

## What You'll Learn

- What branch protection actually restricts, mechanically
- How required status checks are matched — by string name, not by workflow file
- The real difference between the light `protected: true/false` read and the full protection object
- Why `GITHUB_TOKEN` gets a 403 reading full protection detail, verified against a real repo
- What a ruleset is and how it differs from classic branch protection
- How this repo's own Gate 1 reads protection status without ever hitting the 403

---

## Table of Contents

- [Chapter 05: Branch Protection \& Rulesets](#chapter-05-branch-protection--rulesets)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What Branch Protection Restricts](#1-what-branch-protection-restricts)
  - [2. Required Status Checks Are Matched By Name](#2-required-status-checks-are-matched-by-name)
  - [3. Configuring Protection](#3-configuring-protection)
  - [4. `enforce_admins`: Who's Actually Bound By the Rules](#4-enforce_admins-whos-actually-bound-by-the-rules)
  - [5. Two Ways to Ask "Is This Branch Protected?"](#5-two-ways-to-ask-is-this-branch-protected)
  - [6. The Light Read: `GET /branches/{branch}`](#6-the-light-read-get-branchesbranch)
  - [7. The Full Read: `GET /branches/{branch}/protection`](#7-the-full-read-get-branchesbranchprotection)
  - [8. The Real Bug: `GITHUB_TOKEN` and Administration Permission](#8-the-real-bug-github_token-and-administration-permission)
  - [9. ⚠️ ADVANCED: Rulesets vs Classic Protection](#9-️-advanced-rulesets-vs-classic-protection)
  - [10. ⚠️ ADVANCED: Bypass Lists in Rulesets](#10-️-advanced-bypass-lists-in-rulesets)
  - [11. ⚠️ ADVANCED: Protection and `allow_force_pushes`](#11-️-advanced-protection-and-allow_force_pushes)
  - [12. Case Study: Gate 1's Actual Design (Chapter 14, Previewed)](#12-case-study-gate-1s-actual-design-chapter-14-previewed)
  - [13. Case Study: A Bot Push Rejected on Protected `main`](#13-case-study-a-bot-push-rejected-on-protected-main)
  - [14. Practical Tips: Configuring Protection With `gh api`](#14-practical-tips-configuring-protection-with-gh-api)
  - [15. Your First Project: Compare Both Reads Yourself](#15-your-first-project-compare-both-reads-yourself)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 06 — Native Auto-Merge vs Your Own Merge Call](#18-whats-next-chapter-06--native-auto-merge-vs-your-own-merge-call)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Light vs Full Protection Reads (from Section 5)](#a1--light-vs-full-protection-reads-from-section-5)

---

## 1. What Branch Protection Restricts

Branch protection is a repo-level policy object attached to a branch (or branch pattern), and it
can restrict, among other things: direct pushes (force everything through a PR), which status
checks must pass first, whether reviews are required and how many, whether force-pushes or
deletions are allowed at all, and whether admins are exempt from any of the above. None of this is
enforced by your code — it's enforced by GitHub's merge machinery itself, the same machinery that
decides whether `gh pr merge` (auto or direct) succeeds.

## 2. Required Status Checks Are Matched By Name

A required status check is identified purely by its **string name** (the `context` in the classic
API, or the check name for GitHub Checks) — not by which workflow file, job, or even repository
produced it. `"test"` as a required check matches *any* check run or commit status reported with
exactly that name, from any source. This is deliberate flexibility (you can require a check from an
external CI system with no `.github/workflows/` file at all) and also the reason a workflow rename
silently breaks required-check enforcement — Chapter 12 covers this failure mode directly.

## 3. Configuring Protection

```bash
gh api -X PUT repos/{owner}/{repo}/branches/main/protection \
  -F required_status_checks[strict]=true \
  -F 'required_status_checks[contexts][]=test' \
  -F 'required_status_checks[contexts][]=gate2-pr-health' \
  -F 'required_status_checks[contexts][]=gate3-risk-score' \
  -F enforce_admins=false \
  -F required_pull_request_reviews='null' \
  -F restrictions='null'
```

`strict: true` additionally requires the branch to be up to date with its base before merging (this
is what produces `mergeable_state: "behind"` from Chapter 02 §8). This repo's own sandbox uses
exactly these three required check names.

## 4. `enforce_admins`: Who's Actually Bound By the Rules

`enforce_admins: false` (the default) means repo admins bypass every protection rule above — direct
pushes, required checks, everything. `enforce_admins: true` removes that exemption, binding
literally everyone including admins. This single setting is why a repo maintainer can push
curriculum content straight to `main` (as this repo's own commit history shows for chapters 01, 06,
07, 16) while a bot's push — with no admin exemption — gets flatly rejected (Section 13).

## 5. Two Ways to Ask "Is This Branch Protected?"

There are two entirely different API reads here, and conflating them is Section 8's whole point:

```
GET /repos/{o}/{r}/branches/{branch}
        │
        ▼
{"protected": true}   ← a boolean. That's it. GITHUB_TOKEN CAN read this.

GET /repos/{o}/{r}/branches/{branch}/protection
        │
        ▼
{full config: required checks, enforce_admins, reviews, ...}   ← GITHUB_TOKEN CANNOT read this.
```

## 6. The Light Read: `GET /branches/{branch}`

This endpoint's response includes a plain `protected: true/false` boolean alongside the branch's
basic metadata (name, latest commit SHA). It answers exactly one question — "is *some* protection
configured at all?" — with none of the detail about what's actually enforced. Critically, this
endpoint only requires `contents: read`, which `GITHUB_TOKEN` has in every workflow by default.

## 7. The Full Read: `GET /branches/{branch}/protection`

This endpoint returns the entire protection configuration — required check contexts,
`enforce_admins`, review requirements, force-push/deletion settings. It requires **Administration**
permission on the repository. This is a distinct, stricter permission scope from `contents: write`
or `pull-requests: write` — and `GITHUB_TOKEN` cannot be granted Administration permission at all,
regardless of what your workflow's `permissions:` block declares.

## 8. The Real Bug: `GITHUB_TOKEN` and Administration Permission

This is not a hypothetical — it's discovery #1 in this repo's own `notes/IMPROVEMENTS_SUMMARY.md`
Live-Repo Verification Log, found while building `gate1-repo-health.yml`. The first version of that
workflow called the full protection endpoint directly:

```
gh api repos/{o}/{r}/branches/main/protection
        │
        ▼
HTTP 403 -- even with `permissions: { contents: write }` declared in the workflow YAML
```

The fix was architectural, not a permissions tweak: Gate 1 doesn't need the full configuration, it
only needs to know protection is turned on at all. Switching to the light endpoint (Section 6)
resolved it completely, using a token `GITHUB_TOKEN` already has by default.

```
required check?  ──▶  registered as a required status check name (Section 3), verified
                        indirectly: if it's required and missing, the merge itself fails --
                        Gate 1 doesn't need to read the requirement list to depend on it
```

## 9. ⚠️ ADVANCED: Rulesets vs Classic Protection

> ⚠️ **ADVANCED TOPIC:** GitHub's newer ruleset system and how it layers with classic protection.
> **Skip on first read** — classic protection (Sections 1–8) is sufficient for the rest of this
> curriculum.

Rulesets are GitHub's newer protection mechanism: instead of one config attached to one branch,
a ruleset targets branches by *pattern* (`main`, `release/*`), can apply repo-wide or
org-wide, and layers additively with classic branch protection — the strictest applicable rule from
either system wins. Rulesets also support finer-grained bypass permissions (specific teams or apps,
not just "all admins"). This repo uses classic protection because a single-branch, single-repo
setup doesn't yet need pattern-based targeting — rulesets earn their complexity at multi-repo scale.

## 10. ⚠️ ADVANCED: Bypass Lists in Rulesets

> ⚠️ **ADVANCED TOPIC:** Fine-grained bypass permissions rulesets support that classic protection
> doesn't.
> **Skip on first read.**

Classic protection's only bypass control is the blunt `enforce_admins` boolean — admins are either
all exempt or all bound. Rulesets support a bypass *list*: specific teams, specific GitHub Apps, or
specific roles, each independently toggleable. This matters once your automation itself needs to
bypass a rule (say, a release bot that must force-push a release branch) without exempting every
human admin from every other rule too — something classic protection has no way to express.

## 11. ⚠️ ADVANCED: Protection and `allow_force_pushes`

> ⚠️ **ADVANCED TOPIC:** Why force-push protection matters even with required checks configured.
> **Skip on first read.**

Required status checks alone don't prevent history rewriting. Without `allow_force_pushes: false`,
someone with push access can force-push a branch that changes what `main`'s history looks like
entirely, potentially discarding commits (including ones a required check already validated)
without ever going through a PR at all. This is a separate protection axis from required checks —
both need to be configured for the airlock to actually hold.

## 12. Case Study: Gate 1's Actual Design (Chapter 14, Previewed)

Gate 1's real implementation (`pr_automerge.gates.evaluate_gate1`) takes `protection_configured:
bool` as a plain input — a design choice made directly because of Section 8's discovery. It never
attempts to read *which* checks are required or whether reviews are configured; it only needs the
light `protected` boolean, sourced exactly as Section 6 describes. Chapter 14 builds the full
workflow around this function; this chapter is where the endpoint choice behind it was decided.

## 13. Case Study: A Bot Push Rejected on Protected `main`

This repo's own `gate1-repo-health.yml` originally tried to commit a `readiness.json` badge
straight to `main`. Branch protection rejected it outright:

```
! [remote rejected] main -> main (protected branch hook declined)
GH006: Required status check "test" is expected.
```

Unlike a human admin (who bypasses protection by default, per Section 4's `enforce_admins: false`),
the Actions bot identity gets **no such exemption** — it's bound by every rule exactly like a
non-admin human would be. The fix was to publish the badge to a dedicated, unprotected
`gate-status` branch instead of trying to commit to `main` directly — this is discovery #2 in the
Live-Repo Verification Log.

## 14. Practical Tips: Configuring Protection With `gh api`

```
Setting up protection on a new repo -- order matters
──────────────────────────────────────────────────────
[ ] Decide required check NAMES first (Section 2 -- matched by string)
[ ] gh api -X PUT .../protection with required_status_checks.contexts set
[ ] enforce_admins: false, unless you specifically want admins bound too
[ ] allow_force_pushes: false, allow_deletions: false
[ ] Confirm with the LIGHT read (Section 6) -- GITHUB_TOKEN can verify this worked
[ ] Confirm with the FULL read (Section 7) ONLY if you have a PAT/App token handy
```

## 15. Your First Project: Compare Both Reads Yourself

Against a repo you admin:

```bash
gh api repos/<owner>/<repo>/branches/main --jq .protected
gh api repos/<owner>/<repo>/branches/main/protection
```

Run the first with `GITHUB_TOKEN` inside a workflow and watch it succeed; run the second the same
way and watch it 403. Then run the second with your own authenticated `gh` session (which has your
full user permissions, not `GITHUB_TOKEN`'s restricted set) and watch it succeed.

## 16. Common Pitfalls & Misconceptions

1. **"`GITHUB_TOKEN` with `contents: write` can read anything about the repo."** No — Section 8 is
   a direct counterexample. Administration permission is a separate, stricter scope.

2. **"A required check is tied to the workflow file that produces it."** No — it's matched purely
   by string name (Section 2). Renaming the job (not just the file) breaks the match.

3. **"Repo admins are always exempt from branch protection."** Only if `enforce_admins: false`
   (the default) — and even then, only *human* admins with that exemption apply to them; the
   Actions bot identity is never exempt (Section 13).

4. **"Rulesets replace branch protection."** No — they layer with it. The strictest applicable rule
   from either system wins; you don't have to migrate off classic protection to use rulesets.

5. **"If protection read fails, protection probably isn't configured."** No — a 403 on the full
   endpoint (Section 7) is *expected* for `GITHUB_TOKEN` regardless of whether protection exists.
   Use the light endpoint (Section 6) to actually answer that question.

## 17. Key Takeaways

- **Branch protection is enforced natively** by GitHub's merge machinery — your code checks
  configuration, never enforces the rule itself.
- **Required checks match by string name**, not by workflow file — a rename breaks the match
  silently (Chapter 12).
- **Two different reads exist:** the light `protected` boolean (`GITHUB_TOKEN` can read it) and the
  full protection object (`GITHUB_TOKEN` cannot, regardless of `permissions:` declared).
- **`enforce_admins: false` exempts human admins, never bots** — an Actions bot identity is always
  bound by protection rules.
- **Gate 1 is built around the light read specifically** because of this chapter's real, verified
  403 discovery — not as a hypothetical design choice.

## 18. What's Next: Chapter 06 — Native Auto-Merge vs Your Own Merge Call

Chapter 06 picks up exactly where branch protection leaves off: what actually happens when a PR's
required checks all pass, and the precise difference between GitHub's native auto-merge feature and
calling the merge endpoint yourself.

[→ Chapter 06: Native Auto-Merge vs Your Own Merge Call](chapter_06_native_automerge.md)

## 19. Additional Resources

- **GitHub Docs, "About protected branches"** — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches (fetched 2026-08)
- **GitHub Docs, "About rulesets"** — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets (fetched 2026-08)
- **GitHub REST API, "Get branch protection"** — https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection (fetched 2026-08) — see the required permission note
- **GitHub REST API, "Get a branch"** — https://docs.github.com/en/rest/branches/branches#get-a-branch (fetched 2026-08) — the light `protected` field this repo's Gate 1 actually uses

## 20. Appendix A — Code Index

### A.1 — Light vs Full Protection Reads (from Section 5)

**What the code does:** Reads a branch's light `protected` boolean (the endpoint `GITHUB_TOKEN`
can call), then attempts the full protection object (the endpoint it can't), printing both results
side by side.

**ASCII flowchart:**

```
check_protected_light(repo)  →  GET /branches/main            → {"protected": true}
fetch_protection_detail(repo) →  GET /branches/main/protection → full config (or 403 for GITHUB_TOKEN)
        │
        ▼
required_check_names(detail) → ["test", "gate2-pr-health", "gate3-risk-score"]
```

See `labs/lab_05_branch_protection.py` for the full runnable version.
