# Chapter 11: Tokens & Permissions

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 07 (The GitHub API & Apps), Chapter 10 (Contexts & Expressions)
**Practice Notebook:** `notebooks/practice_11.ipynb`
**Reference Notebook:** `notebooks/lab_11_tokens_and_permissions.ipynb`
**Script:** `labs/lab_11_tokens_and_permissions.py`
**Doc Reference:** GitHub Docs "Automatic token authentication"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8, and keep the
[token permission matrix](../resources/token_permission_matrix.md) open in a second tab — this
chapter narrates it, the resource is the reference you'll actually return to.

**What to SKIP on first read:** Section 11 (GitHub App installation-token lifecycle in depth).
Return once you're actually minting an App installation token.

**Key concepts in plain English:**

- **`GITHUB_TOKEN`:** A token GitHub mints automatically for every workflow run, scoped by the
  `permissions:` block, and destroyed when the job ends.
- **Permission scope:** A named capability (`contents`, `pull-requests`, `checks`, ...) that can be
  set to `none`, `read`, or `write` — the *ceiling* on what a token can do this run.
- **Personal Access Token (PAT):** A token you mint yourself, acting as *you*, lasting until you
  revoke it or it expires — the escape hatch for anything `GITHUB_TOKEN` structurally cannot do.
- **GitHub App:** A separate, installable bot identity with its own permission grant, minting
  short-lived installation tokens — the right tool once automation spans more than one repo.
- **The no-downstream-trigger rule:** GitHub deliberately suppresses a `GITHUB_TOKEN`-authored
  action from firing another normal event trigger, to prevent infinite automation loops.

**Your prior knowledge connection:** If you've ever scoped an API key to the minimum permissions it
actually needs (rather than handing out an admin key everywhere), you already understand the
philosophy behind `permissions:` — this chapter is about GitHub's specific implementation of that
same instinct, plus the handful of things no scope on `GITHUB_TOKEN` can ever unlock.

---

> **🔬 Automation Engineer's Lens:** Every "why won't this work" ticket in this domain that turns
> out to be a token problem follows the same shape: someone assumes `permissions: { X: write }` in
> the YAML is sufficient, when the actual blocker is a capability `GITHUB_TOKEN` cannot hold at any
> permission level — Administration access, or `enablePullRequestAutoMerge`. No amount of YAML
> tuning fixes those; only a PAT or App token does. Knowing which category a failure falls into
> before debugging saves hours.

---

> **🚦 Native vs Custom:** `GITHUB_TOKEN`'s existence, scoping, and lifecycle are entirely native —
> you declare a `permissions:` block, GitHub mints and destroys the token around it. What you build
> is the judgment call: recognizing when a task needs a PAT or App token instead, and — since
> minting either requires an authenticated browser session GitHub deliberately doesn't let you
> automate — building your automation to fail loudly and clearly when that token is absent, rather
> than pretending the gap doesn't exist.

---

## What You'll Learn

- What `GITHUB_TOKEN` is, when it's minted, and when it's destroyed
- How `permissions:` scopes work, and what setting a scope to `none` actually restricts
- The three real capabilities `GITHUB_TOKEN` cannot hold at any permission level, verified live
- The three token identities side by side — `GITHUB_TOKEN`, PAT, GitHub App — and when each fits
- The `-f` vs `-F` encoding trap in `gh api`, and why it silently no-ops instead of erroring
- Why this repo's `automerge.yml` fails loudly rather than silently when `PRA_BOT_TOKEN` is missing

---

## Table of Contents

- [Chapter 11: Tokens \& Permissions](#chapter-11-tokens--permissions)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. `GITHUB_TOKEN`'s Lifecycle](#1-github_tokens-lifecycle)
  - [2. `permissions:` Scopes](#2-permissions-scopes)
  - [3. What "Least Privilege" Means Here, Concretely](#3-what-least-privilege-means-here-concretely)
  - [4. Three Things `GITHUB_TOKEN` Cannot Do, Verified](#4-three-things-github_token-cannot-do-verified)
  - [5. Personal Access Tokens](#5-personal-access-tokens)
  - [6. GitHub Apps as an Identity](#6-github-apps-as-an-identity)
  - [7. The Three Identities, Side by Side](#7-the-three-identities-side-by-side)
  - [8. Choosing an Identity for a New Task](#8-choosing-an-identity-for-a-new-task)
  - [9. ⚠️ ADVANCED: The `-f` vs `-F` Encoding Trap](#9-️-advanced-the--f-vs--f-encoding-trap)
  - [10. ⚠️ ADVANCED: The No-Downstream-Trigger Rule, Precisely](#10-️-advanced-the-no-downstream-trigger-rule-precisely)
  - [11. ⚠️ ADVANCED: GitHub App Installation Token Lifecycle](#11-️-advanced-github-app-installation-token-lifecycle)
  - [12. Case Study: `automerge.yml`'s Honest Failure Mode](#12-case-study-automergeymls-honest-failure-mode)
  - [13. Case Study: A Boolean Setting That Silently No-Opped](#13-case-study-a-boolean-setting-that-silently-no-opped)
  - [14. Practical Tips: Diagnosing a Permission Failure](#14-practical-tips-diagnosing-a-permission-failure)
  - [15. Your First Project: Try Every Operation, Note What Fails](#15-your-first-project-try-every-operation-note-what-fails)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 12 — Status Checks, Check Runs \& Commit Statuses](#18-whats-next-chapter-12--status-checks-check-runs--commit-statuses)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Permission Matrix and the -f/-F Trap (from Section 15)](#a1--the-permission-matrix-and-the--f-f-trap-from-section-15)

---

## 1. `GITHUB_TOKEN`'s Lifecycle

GitHub mints a fresh `GITHUB_TOKEN` automatically at the start of **every** workflow run — no
setup, no secret to configure. It's scoped by that run's `permissions:` block, available to every
step as `${{ secrets.GITHUB_TOKEN }}` or implicitly to `gh`/`actions/checkout`, and it's destroyed
as the job using it finishes. There is no way to extend its lifetime past one run.

### How Long "One Run" Actually Is

Concretely, per GitHub's docs (fetched 2026-08): the token **expires when the job finishes** — the
bound is per-*job*, not per-workflow, so each job's token dies with that job. If a job never
finishes cleanly, an effective maximum lifetime kicks in instead: on a GitHub-hosted runner a job
can execute for at most 6 hours — the same ceiling the `timeout-minutes:` job setting defaults to
(`Default: 360` minutes) — so a `GITHUB_TOKEN` there can never outlive 6 hours. Only on a
self-hosted runner, where jobs may run longer, can the token be refreshed — and even then for no
more than 24 hours total. Never design automation that stashes a `GITHUB_TOKEN` for later use;
"later" is measured in hours at best.

## 2. `permissions:` Scopes

```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
```

Each named scope (`contents`, `pull-requests`, `checks`, `issues`, `actions`, and more) can be set
to `none`, `read`, or `write` independently. Omitting `permissions:` entirely gives every scope a
GitHub-configured default (historically broad `read`/`write`, tightened over time) — explicitly
declaring the block, naming only what's actually needed, is the safer and more auditable pattern
this repo's own workflows follow throughout.

## 3. What "Least Privilege" Means Here, Concretely

`ci.yml` (Chapter 08 §7) declares only `contents: read` — it never writes anything, so it never
gets `write` on anything. Gate 3's workflow needs `pull-requests: write` (to post a comment) and
`checks: write` (to publish a check run) — nothing more. A workflow with `permissions: write-all`
"just to be safe" is the opposite of safe: it hands every step in that job every capability
`GITHUB_TOKEN` can structurally hold, whether any step needs it or not.

## 4. Three Things `GITHUB_TOKEN` Cannot Do, Verified

No `permissions:` configuration, at any scope, unlocks these three — each verified live against
this repo's own sandbox while building its gate workflows:

```
1. Read full branch protection detail  (needs Administration permission — Ch 05 §8)
2. Enable native auto-merge             (enablePullRequestAutoMerge is withheld — Ch 06 §9)
3. Push to a protected branch as a bot  (bots get no admin bypass — Ch 05 §13)
```

These aren't bugs to work around with cleverer YAML — they're deliberate platform restrictions.
The fix in every case is the same: a PAT or GitHub App token (Sections 5–6).

### What an Ordinary Scope-Missing 403 Looks Like

To recognize those three structural blocks, you first need to know the *fixable* failure they must
be distinguished from. State before — the job's `permissions:` block grants read-only access:

```yaml
permissions:
  contents: read        # pull-requests: not listed → none
```

A step then tries to post a Gate 3 comment on PR #101
(REST: `POST /repos/{owner}/{repo}/issues/{number}/comments`):

```bash
gh api repos/OWNER/REPO/issues/101/comments -f body="Gate 3 risk: 5.9 <= 70.0 — PASS"
```

State after — `gh` exits non-zero and relays the API's own error body:

```
gh: Resource not accessible by integration (HTTP 403)
{
  "message": "Resource not accessible by integration",
  "documentation_url": "https://docs.github.com/rest/issues/comments#create-an-issue-comment"
}
```

**What to notice:**

- **"not accessible by integration"** — the *integration* is the Actions app that minted this run's
  `GITHUB_TOKEN`. That exact phrase is the fingerprint of a `GITHUB_TOKEN` scope problem (a PAT
  refused the same way says "not accessible by personal access token" instead).
- The `documentation_url` names the exact endpoint refused — hold it against the `permissions:`
  block above and the missing scope reads right off: commenting needs `pull-requests: write` (§3).
- Here the fix is one YAML line. The three operations above return this *same* 403 — but no
  `permissions:` line ever fixes them. Telling the two categories apart is §14's first checkbox.

## 5. Personal Access Tokens

A PAT acts as **you** — minted through an authenticated browser session
(Settings → Developer settings → Fine-grained tokens), scoped to specific repos and permissions,
lasting until it expires or you revoke it. Once minted, it's stored as a repo secret (this repo
uses `PRA_BOT_TOKEN`) and referenced in workflow YAML wherever `GITHUB_TOKEN` would otherwise be
used. The full minting checklist lives in the
[token permission matrix](../resources/token_permission_matrix.md#minting-a-pat-for-this-curriculum-chapter-07-14).

## 6. GitHub Apps as an Identity

A GitHub App is a separate, installable bot identity (Chapter 07 covers registering and installing
one in depth) with its own permission grant, independent of any human's personal permissions.
Installation tokens are minted on demand, short-lived (about an hour), and auto-renewed — no
manual rotation the way a PAT eventually needs. For automation spanning multiple repositories under
one identity with tightly scoped, auditable permissions, an App is the better-engineered choice;
this curriculum's single-repo sandbox uses a PAT instead because the extra setup an App requires
isn't earning its cost at this scale.

## 7. The Three Identities, Side by Side

| Property | `GITHUB_TOKEN` | Personal Access Token | GitHub App | Setup Effort |
| --- | --- | --- | --- | --- |
| Exists automatically | Yes, per run | No — you mint it | No — you register and install it | Minimal (token) / Moderate (App) |
| Acts as | The Actions bot | You, the human | Its own bot identity | — |
| Lifetime | One workflow run | Until revoked/expiry | ~1 hour per token, auto-renewed | Low (PAT needs manual rotation) / Minimal (App auto-renews) |
| Can read branch protection | No | Yes, if you have admin | Yes, if installed with Administration | — |
| Can enable auto-merge | No | Yes | Yes | — |
| Best fit | In-workflow reads/writes needing nothing above | A single repo, low setup effort | Several repos, one identity, tightest scoping | — |

## 8. Choosing an Identity for a New Task

```
Does the task need ONLY what GITHUB_TOKEN can hold (Section 4's three exceptions aside)?
    │yes                                          │no
    ▼                                              ▼
Use GITHUB_TOKEN, scope permissions: minimally    How many repos does this span?
                                                        │one                │several
                                                        ▼                    ▼
                                                  PAT (low setup)      GitHub App (Ch 07)
```

## 9. ⚠️ ADVANCED: The `-f` vs `-F` Encoding Trap

> ⚠️ **ADVANCED TOPIC:** A real, live-caught bug in this repo's own Gate 1 build.
> **Skip on first read** — return the first time a `gh api -X PATCH` call seems to silently do
> nothing.

```bash
gh api -X PATCH repos/OWNER/REPO -f allow_auto_merge=true   # WRONG: sends the STRING "true"
gh api -X PATCH repos/OWNER/REPO -F allow_auto_merge=true   # RIGHT: sends the BOOLEAN true
```

`-f` always sends a string field, regardless of what it looks like. `-F` sends a typed field —
`gh` infers boolean/integer/string from the value. A boolean API field given the string `"true"`
frequently accepts the request (HTTP 200) but silently leaves the setting unchanged, because the
API's schema expects an actual boolean and a string doesn't satisfy it the way you'd hope. This
exact mistake was caught building this repo's `gate1-repo-health.yml`. Default to `-F` for anything
that isn't obviously text.

## 10. ⚠️ ADVANCED: The No-Downstream-Trigger Rule, Precisely

> ⚠️ **ADVANCED TOPIC:** Exactly which actions this rule suppresses.
> **Skip on first read** — Chapter 09 §9 already introduced this; this section adds the precise
> mechanics.

GitHub suppresses normal event triggering specifically for actions taken *using* the default
`GITHUB_TOKEN` — a commit pushed, a PR opened, a release published, all performed by that run's own
token. This does **not** apply to a PAT or App token: an action taken with one of those *can*
trigger downstream events normally, because from GitHub's perspective it's indistinguishable from a
human or a third-party integration acting. This is a second, independent reason (beyond Sections
4–6) a PAT/App token is sometimes required — not because `GITHUB_TOKEN` lacks a permission, but
because you specifically need the resulting action to trigger something else.

### A Sibling Guard: Workflow Approval for Fork PRs

The no-downstream-trigger rule isn't the platform's only deliberate brake. A PR from a fork
arrives carrying workflow-triggering code written by a stranger, and public repos were burned by
exactly that — fork PRs crafted to mine cryptocurrency on GitHub's runners or to exfiltrate
secrets. So repository settings (Settings → Actions → General) offer three escalating approval
requirements for fork-PR workflow runs (option names verified 2026-08):

1. **Require approval for first-time contributors who are new to GitHub** — narrowest; targets the
   throwaway-account attack profile.
2. **Require approval for first-time contributors** — anyone with no commit or PR yet merged into
   this repo.
3. **Require approval for all external contributors** — everyone who isn't a member or owner.

A run held by this guard doesn't fail — it sits pending with an **"Awaiting approval"** label until
a maintainer with write access approves it (runs still waiting after 30 days are deleted). If a
fork PR's checks seem to have never started, look for that label before debugging trigger YAML
(Chapter 13's checklist).

## 11. ⚠️ ADVANCED: GitHub App Installation Token Lifecycle

> ⚠️ **ADVANCED TOPIC:** How an App's short-lived tokens actually get minted.
> **Skip on first read** — return once you're building App-based automation yourself (Chapter 07).

An installed GitHub App doesn't hand out one long-lived token — your automation exchanges the
App's own private key for a fresh installation access token (valid ~1 hour) each time it's needed,
via a signed JWT. This means there's no single secret to leak with unlimited lifetime — the worst
exposure window for a compromised installation token is bounded to under an hour, a meaningfully
different risk profile from a PAT that's valid until someone remembers to revoke it.

## 12. Case Study: `automerge.yml`'s Honest Failure Mode

This repo's `automerge.yml` needs to call `enablePullRequestAutoMerge` — Section 4 already
established `GITHUB_TOKEN` cannot. Rather than silently no-op (leaving a human to wonder why PRs
never auto-merge) or crash uninformatively, the workflow checks for a `PRA_BOT_TOKEN` secret first
and, if absent, writes a clear job-summary message naming exactly what's missing and why — "by
design," per this repo's own tracker. This is the practical answer to "what do I do about a task
that structurally needs a token I can't automate minting" (Section 5's last sentence): fail loud
and specific, don't fail silent.

## 13. Case Study: A Boolean Setting That Silently No-Opped

Section 9's `-f`/`-F` trap, as it actually happened: an early version of `gate1-repo-health.yml`
patched `allow_auto_merge` using `-f allow_auto_merge=true`. The API call returned success. The
setting did not change. Debugging took longer than it should have precisely *because* the call
"worked" — no error, no non-zero exit code, just a setting that quietly stayed `false`. The fix was
one character: `-f` to `-F`.

## 14. Practical Tips: Diagnosing a Permission Failure

```
gh/API call failed or silently no-opped -- which category is it?
──────────────────────────────────────────────────────────────────
[ ] Check the exact error. 403 with a permission-scope name? -> add that scope to permissions:
[ ] 403/GraphQL error naming Administration or enablePullRequestAutoMerge specifically?
    -> Section 4 -- no permissions: fix exists, you need a PAT/App token
[ ] Call "succeeded" but nothing changed? -> check -f vs -F (Section 9)
[ ] Downstream workflow didn't fire after this action? -> Section 10, use workflow_run or a PAT
```

## 15. Your First Project: Try Every Operation, Note What Fails

Against a real repo, attempt each operation in Section 4's list with the default `GITHUB_TOKEN`
inside a workflow run, and separately with your own authenticated `gh` session. Confirm the exact
three failures this chapter predicts, and confirm every other operation (reading PR data, posting a
comment, publishing a check run) succeeds with `GITHUB_TOKEN` alone, correctly scoped.

## 16. Common Pitfalls & Misconceptions

1. **"If I grant enough `permissions:` scopes, `GITHUB_TOKEN` can do anything."** No — Section 4's
   three capabilities are withheld regardless of scope. This is a platform restriction, not a
   configuration gap.

2. **"`-f` and `-F` are interchangeable shorthand."** No — `-f` always sends a string; `-F` sends a
   typed value. A boolean field given a string can silently no-op instead of erroring.

3. **"A PAT is always the answer when `GITHUB_TOKEN` isn't enough."** Often, yes for a single repo
   — but a GitHub App is the better-engineered choice once automation spans multiple repos or needs
   auto-rotating short-lived tokens.

4. **"My bot's action should trigger the next workflow the same way a human's would."** Not with
   `GITHUB_TOKEN` — Section 10's no-downstream-trigger rule specifically suppresses this. A PAT or
   App token, or the `workflow_run` trigger (Chapter 09 §7), are the two ways around it.

5. **"Omitting `permissions:` entirely is safe because I'm not writing anything."** It hands every
   step the platform-default scope set, whether or not any step needs it — declare the block
   explicitly, even to grant nothing beyond `contents: read`.

## 17. Key Takeaways

- **`GITHUB_TOKEN` is minted fresh per run, scoped by `permissions:`, and destroyed as each job
  finishes** — no configuration extends its lifetime.
- **Three capabilities are withheld from `GITHUB_TOKEN` at any permission level, verified live**:
  reading full branch protection, enabling auto-merge, and bypassing protection as a bot.
- **`-f` vs `-F` is a real, silent failure mode** — `-f` always sends a string; use `-F` for
  anything typed.
- **A PAT acts as you; a GitHub App is its own identity** — PAT for a single repo and low setup
  cost, App for multi-repo scope and auto-rotating tokens.
- **Fail loud when a required token is missing** — this repo's `automerge.yml` names the exact gap
  in its job summary rather than silently no-oping.

## 18. What's Next: Chapter 12 — Status Checks, Check Runs & Commit Statuses

Chapter 12 covers what a gate actually *publishes* once its token can write — check runs vs the
older commit-status API, and how both connect back to the required-check matching Chapter 05
described.

[→ Chapter 12: Status Checks, Check Runs & Commit Statuses](chapter_12_status_checks.md)

## 19. Additional Resources

- **GitHub Docs, "Automatic token authentication"** — https://docs.github.com/en/actions/security-guides/automatic-token-authentication (fetched 2026-08)
- **GitHub Docs, "Assigning permissions to jobs"** — https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs (fetched 2026-08)
- **GitHub Docs, "Managing your personal access tokens"** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens (fetched 2026-08)
- **GitHub Docs, "GITHUB_TOKEN" (concepts)** — token expiry at job end, 6h GitHub-hosted / 24h self-hosted ceilings (§1) — https://docs.github.com/en/actions/concepts/security/github_token (fetched 2026-08)
- **GitHub Docs, "Actions limits"** — the 6-hour job execution limit (§1) — https://docs.github.com/en/actions/reference/limits (fetched 2026-08)
- **GitHub Docs, "Workflow syntax"** — `timeout-minutes` `Default: 360` (§1) — https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (fetched 2026-08)
- **GitHub Docs, "Managing GitHub Actions settings for a repository"** — the three fork-PR approval option names (§10) — https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository (fetched 2026-08)
- **GitHub Docs, "Approving workflow runs from public forks"** — "Awaiting approval" label, 30-day auto-delete (§10) — https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/approving-workflow-runs-from-public-forks (fetched 2026-08)
- **GitHub Community discussion #108369** — the verbatim "Resource not accessible by integration" 403 body (§4) — https://github.com/orgs/community/discussions/108369 (fetched 2026-08)
- **This repo's own** [`resources/token_permission_matrix.md`](../resources/token_permission_matrix.md) — every row verified live against this repo's own sandbox

## 20. Appendix A — Code Index

### A.1 — The Permission Matrix and the -f/-F Trap (from Section 15)

**What the code does:** Encodes the operation matrix and token-identity comparison as structured
data, and simulates how `-f` vs `-F` encode the same CLI argument differently.

**ASCII flowchart:**

```
check_operation("enable_auto_merge") → {"github_token_works": False, "needs_instead": "PAT or App..."}

encode_gh_api_field("-f", "true") → "true"  (str  -- WRONG for a boolean field)
encode_gh_api_field("-F", "true") → True    (bool -- RIGHT)
```

See `labs/lab_11_tokens_and_permissions.py` for the full runnable version.
