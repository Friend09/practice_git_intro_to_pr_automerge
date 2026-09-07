# Chapter 07: The GitHub API In Depth & GitHub Apps

**Reading Time:** ~55 minutes
**Prerequisites:** Chapter 04 (Reading PR Data), Chapter 06 (Native Auto-Merge vs Your Own Merge Call)
**Practice Notebook:** `notebooks/practice_07.ipynb`
**Reference Notebook:** `notebooks/lab_07_api_and_apps.ipynb`
**Script:** `labs/lab_07_api_and_apps.py`
**Doc Reference:** GitHub REST API overview · GitHub Docs "About creating GitHub Apps" · GitHub Docs "Differences between GitHub Apps and OAuth apps"
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8 (reading and writing through the API) and Section 11
(what a GitHub App actually is). Those carry the two things you asked to have covered explicitly:
pulling/pushing data through the API, and what an App buys you.

**What to SKIP on first read:** Section 10 (webhook delivery internals). Return once you're
building something that reacts to events outside of Actions entirely.

**Key concepts in plain English:**

- **REST API:** GitHub's primary automation surface — URLs like
  `GET /repos/{owner}/{repo}/pulls/{number}` that return JSON. `gh api` is a thin, authenticated
  wrapper around exactly this.
- **GraphQL API:** A second GitHub API, used for a handful of operations REST doesn't expose
  (`enablePullRequestAutoMerge` from Chapter 06 is one). You'll use it rarely, but you now know why
  it exists.
- **Pagination:** GitHub never returns "everything" in one response for a list endpoint — large
  results are split into pages you must explicitly walk.
- **Personal Access Token (PAT):** A credential tied to *your* GitHub account. Anything it can do,
  it does *as you*.
- **GitHub App:** A credential tied to an *installation* — not a person. It has its own identity,
  its own scoped permissions, and can be installed on many repos or an entire organization at
  once.

**Your prior knowledge connection:** If you've ever called a REST API with `curl` and a bearer
token, `gh api` is that, with GitHub's auth already handled. The GitHub App material is the part
most likely to be new — it's less "another way to call the API" and more "a different kind of
identity to call it as."

---

> **🔬 Automation Engineer's Lens:** The single biggest reason PR-automation projects stall past a
> proof-of-concept is identity, not code. A script that authenticates as *you* works fine until you
> go on vacation, change jobs, or someone asks "why does this bot post as Raghu?" GitHub Apps exist
> specifically to solve that — the identity survives you.

---

> **🚦 Native vs Custom:** Reading and writing PR data — comments, labels, check runs, diffs — is
> 100% native: GitHub's REST/GraphQL API is the only interface, and you're never reimplementing
> anything, only calling it correctly (pagination, rate limits, the right endpoint). Multi-repo
> orchestration is where the "build vs configure" line actually falls: a GitHub App is GitHub's own
> feature for scoped, portable automation identity; anything beyond installing and authenticating
> as one — the actual gate logic — is still yours to write.

---

## What You'll Learn

- The shape of the GitHub REST API well enough to navigate docs for any endpoint you haven't used yet
- How to paginate a large result set correctly, and why "it worked on my 3-item test" hides a bug
- How to push data back to GitHub — comments, labels, check runs — not just read it
- What GraphQL is for on GitHub, and when you're forced to reach for it
- What a GitHub App actually is, structurally, and how it differs from a PAT and from `GITHUB_TOKEN`
- Why a GitHub App is the right tool the moment you automate more than one repository
- How to mint the credentials this curriculum's later chapters assume you have

---

## Table of Contents

- [Chapter 07: The GitHub API In Depth \& GitHub Apps](#chapter-07-the-github-api-in-depth--github-apps)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Why This Chapter Exists](#1-why-this-chapter-exists)
  - [2. The Shape of the REST API](#2-the-shape-of-the-rest-api)
  - [3. Reading Data: GET Requests, in Depth](#3-reading-data-get-requests-in-depth)
  - [4. Pagination: Why "It Worked" Isn't Enough](#4-pagination-why-it-worked-isnt-enough)
  - [5. Rate Limits](#5-rate-limits)
  - [6. Writing Data: POST, PATCH, and the Endpoints That Change Things](#6-writing-data-post-patch-and-the-endpoints-that-change-things)
  - [7. Publishing a Check Run](#7-publishing-a-check-run)
  - [8. When You're Forced Into GraphQL](#8-when-youre-forced-into-graphql)
  - [9. ⚠️ ADVANCED: `gh api` vs a Raw HTTP Client](#9-️-advanced-gh-api-vs-a-raw-http-client)
  - [10. ⚠️ ADVANCED: Webhooks, Briefly](#10-️-advanced-webhooks-briefly)
  - [11. What a GitHub App Actually Is](#11-what-a-github-app-actually-is)
  - [12. Three Identities Compared](#12-three-identities-compared)
  - [13. Case Study: One Bot, Twelve Repos](#13-case-study-one-bot-twelve-repos)
  - [14. Practical Tips: Minting a PAT for This Curriculum](#14-practical-tips-minting-a-pat-for-this-curriculum)
  - [15. Your First Project: Read, Then Write](#15-your-first-project-read-then-write)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 08 — Actions Anatomy](#18-whats-next-chapter-08--actions-anatomy)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Paginated Fetch With Truncation Handling (from Section 4)](#a1--paginated-fetch-with-truncation-handling-from-section-4)
    - [A.2 — Publishing a Check Run (from Section 7)](#a2--publishing-a-check-run-from-section-7)

---

## 1. Why This Chapter Exists

Chapter 04 already showed you `gh pr view --json` for reading one PR's basics. That's a fraction
of the API surface this curriculum actually leans on: Gate 3 (Chapter 16) fetches full diff
metadata with pagination; Gate 2 (Chapter 15) publishes check runs, which is a *write*, not a
read; and the moment you want one bot identity managing gates across more than a single sandbox
repo, a personal token stops being the right tool. This chapter is the missing middle: how the API
actually works, end to end, and what a GitHub App buys you once "one repo" becomes "several."

## 2. The Shape of the REST API

Every GitHub REST endpoint follows the same pattern: an HTTP verb, a URL rooted at
`https://api.github.com`, and a JSON body in and/or out.

```
GET    /repos/{owner}/{repo}/pulls/{number}          read one PR
GET    /repos/{owner}/{repo}/pulls/{number}/files     read one PR's changed files (paginated)
POST   /repos/{owner}/{repo}/issues/{number}/comments write a comment (PRs are issues, API-wise)
PATCH  /repos/{owner}/{repo}                          change a repo setting
PUT    /repos/{owner}/{repo}/pulls/{number}/merge     merge a PR directly (Chapter 06)
POST   /repos/{owner}/{repo}/check-runs               publish a check run (Chapter 12)
```

`gh api <path>` is a thin, already-authenticated wrapper around exactly this — `gh api
repos/{o}/{r}/pulls/5` is the same request as `curl -H "Authorization: Bearer $TOKEN"
https://api.github.com/repos/{o}/{r}/pulls/5`.

## 3. Reading Data: GET Requests, in Depth

Beyond `gh pr view --json <fields>`, the general tool is `gh api`:

```bash
gh api repos/OWNER/REPO/pulls/101 --jq '{title, additions, deletions, changed_files}'
```

Against the running PR #101 example (head `a1b2c3d4e5f6…` — the trimmed raw response lives in
`fixtures/pr_raw_pull.json`), this prints:

```json
{"title":"fix: correct typo in sandbox README","additions":2,"deletions":1,"changed_files":1}
```

**What to notice:**

- The raw `GET /pulls/101` response is a ~90-field JSON object; `--jq` reshaped it to exactly the
  4 fields you asked for. That reshaping *is* the point of `--jq`.
- `additions=2, deletions=1, changed_files=1` are the same numbers Gate 3 (Chapter 16) feeds its
  risk formula — this one GET is the read half of the whole scoring pipeline.

`--jq` filters the response server-side-feeling (actually client-side, but before it hits your
terminal) so you're not parsing a full JSON blob by hand for three fields. This is the pattern
every lab script in this curriculum uses via `pr_automerge.gh_client.run_gh`.

## 4. Pagination: Why "It Worked" Isn't Enough

List endpoints — like a PR's changed files — never return everything in one response. GitHub caps
each page (commonly 30 by default, up to 100 with `per_page=100`) and tells you there's more via
the response's `Link` header, not the JSON body itself.

```
Request 1: GET .../files?per_page=100&page=1  →  100 files, Link: rel="next"
Request 2: GET .../files?per_page=100&page=2  →  100 files, Link: rel="next"
Request 3: GET .../files?per_page=100&page=3  →  40 files,  no rel="next"
                                                      ↓
                                            240 files total
```

A PR under 100 files "just works" with a single unpaginated call — which is exactly what makes
this bug so common: it passes every test you write against a small PR, then silently under-reports
on the first PR that touches 150 files. `gh api --paginate` handles this for you; Chapter 16's
Gate 3 relies on it (and additionally handles GitHub's hard 3,000-file truncation ceiling on
`/pulls/{n}/files`, which pagination alone doesn't solve).

## 5. Rate Limits

Every token has a budget. `GITHUB_TOKEN` inside Actions gets roughly 1,000 requests per hour per
repository; an authenticated PAT or App installation token gets roughly 5,000 per hour (GitHub
Apps can get considerably more at scale — see Section 11).

| Token type | Primary limit | Scope |
| --- | --- | --- |
| `GITHUB_TOKEN` in Actions | 1,000 requests/hr | per repository |
| PAT (classic or fine-grained) | 5,000 requests/hr | per account |
| GitHub App installation token | 5,000 requests/hr baseline | per installation — +50/hr per repo and per org user above 20 of each, capped at 12,500/hr (15,000/hr on Enterprise Cloud) |

Check your remaining budget with:

```bash
gh api rate_limit --jq '.resources.core | {limit, remaining, reset}'
```

A workflow that loops over every PR in a large repo without checking this can burn its hourly
budget and start failing mid-run — with an error that looks nothing like "you're out of quota"
unless you know to look for it.

## 6. Writing Data: POST, PATCH, and the Endpoints That Change Things

Everything so far has read data. Gate 3 (Chapter 16) also *writes*: it posts a PR comment with
the score breakdown, and publishes a check run. The shape is the same as reading, with a body:

```bash
gh api -X POST repos/OWNER/REPO/issues/5/comments -f body="Gate 3: risk=66.0, merge"
gh api -X PATCH repos/OWNER/REPO -F allow_auto_merge=true
```

`-f` sends a string field; `-F` sends a typed field (so `true` is a boolean, not the string
`"true"`) — a distinction that has caused real, silent bugs in this exact curriculum's build (a
boolean setting that silently stayed a no-op string until `-F` was used correctly).

## 7. Publishing a Check Run

A check run is how Gates 2 and 3 report their verdict in a form branch protection can require.
It's a write to `/repos/{owner}/{repo}/check-runs`:

```bash
gh api repos/OWNER/REPO/check-runs \
  -f name=gate3-risk-score \
  -f head_sha=$SHA \
  -f status=completed \
  -f conclusion=success \
  -f "output[title]=Gate 3: PASS" \
  -f "output[summary]=risk=66.0 <= threshold=70"
```

GitHub answers the POST with the created check run — trimmed here to the four fields that matter
(from `fixtures/check_run_response.json`; Chapter 12 §5 walks the full response):

```json
{
  "id": 900123456,
  "name": "gate3-risk-score",
  "status": "completed",
  "conclusion": "success"
}
```

**What to notice:**

- The `id` (`900123456`) is what Appendix A.2's helper returns — you'd need it to PATCH this
  check run later (e.g. `in_progress` → `completed`).
- Branch protection matches on `name` (`gate3-risk-score`), not on the id — the name is the
  contract between this POST and the required-checks list (Chapter 05).

Chapter 12 goes deeper on check runs specifically (their full lifecycle, `in_progress` vs
`completed`); this section is here so you recognize the pattern the first time you see it, in
Section 6's write examples and in Gate 2/3's actual workflow YAML.

## 8. When You're Forced Into GraphQL

Almost everything in this curriculum uses REST. GraphQL shows up exactly once: enabling
auto-merge (Chapter 06 §9) is a GraphQL-only mutation with no REST equivalent. `gh pr merge --auto`
hides this from you — but knowing it's GraphQL underneath explains why its error message
(`GraphQL: Resource not accessible by integration`) looks different from every REST 403 you've
seen elsewhere in this curriculum.

## 9. ⚠️ ADVANCED: `gh api` vs a Raw HTTP Client

> ⚠️ **ADVANCED TOPIC:** When to reach for `requests`/`httpx` in Python instead of shelling out to
> `gh`.
> **Skip on first read** — the labs in this curriculum use `gh` exclusively.

`gh api` is the right default inside a shell script or a workflow step. Once your logic is
substantial Python (as Gate 3's scoring is), calling `gh` via `subprocess` — as
`pr_automerge.gh_client.run_gh` does — keeps GitHub's own token/auth handling rather than
reimplementing it, at the cost of a subprocess call per API request. A direct HTTP client
(`httpx`, GitHub's own `PyGithub`) trades that subprocess overhead for you owning auth headers and
retry logic yourself. For this curriculum's scale, the subprocess cost is irrelevant; the
simplicity of reusing `gh`'s auth is worth it.

### A Third Way: `actions/github-script`

Inside a workflow there's a third option alongside `gh` and a raw HTTP client: the
`actions/github-script` action (current major: `@v9`) hands your JavaScript a pre-authenticated
Octokit client (`github`) and the event context (`context`) — no token wiring, no JSON parsing:

```yaml
- name: Post Gate 3 comment on PR #101
  uses: actions/github-script@v9
  with:
    script: |
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: 101,
        body: "Gate 3: risk=66.0 <= threshold=70 — merge",
      });
```

That's the whole trade in one line: `gh` gives you shell-native calls, an HTTP client gives you
full control, and `github-script` gives you an authenticated client and the event payload for
free — but only inside a workflow step.

## 10. ⚠️ ADVANCED: Webhooks, Briefly

> ⚠️ **ADVANCED TOPIC:** Reacting to GitHub events outside of Actions entirely.
> **Skip on first read** — this curriculum's gates all run inside Actions, which receives events
> internally; you never touch a webhook directly for anything built here.

A webhook is GitHub POSTing an event payload to a URL you control, outside of Actions entirely —
the mechanism a standalone bot service (not running as a workflow) would use to learn "a PR just
opened." GitHub Actions' own event triggers (Chapter 09) are, under the hood, GitHub's internal
consumption of these same event types; you don't manage the delivery yourself. You'd reach for raw
webhooks only if you were building automation that lives outside GitHub Actions — a standalone
service, for instance.

## 11. What a GitHub App Actually Is

A GitHub App is a distinct kind of GitHub identity — not a user, not a repository setting. It has:

- **Its own identity** — appears as `your-app-name[bot]` in commits, comments, and check runs, not
  as any human account.
- **Its own scoped permissions** — you declare exactly what it can touch (e.g. `pull_requests:
  write`, `checks: write`) at the App level, independent of any human's access.
- **An installation model** — you *install* it onto one repo, several repos, or an entire
  organization. One App, many installations, each scoped independently.
- **Short-lived installation tokens** — your automation exchanges the App's private key for a
  token valid roughly an hour at a time, rather than a long-lived PAT sitting in a secret
  indefinitely.

```
GitHub App (created once)
    │
    ├── installed on repo A  →  installation token A (scoped to A)
    ├── installed on repo B  →  installation token B (scoped to B)
    └── installed on repo C  →  installation token C (scoped to C)
```

This is what makes an App the right answer for "automate across many repos": one piece of
automation logic, one App, and each installation only ever sees the repo it was installed on —
no single token with blanket access to everything.

## 12. Three Identities Compared

| Identity | Setup Effort | Control | Failure Visibility | Security Exposure | Maintenance Burden |
| --- | --- | --- | --- | --- | --- |
| `GITHUB_TOKEN` | Minimal — exists automatically per workflow run | Weak — fixed scope set, cannot enable auto-merge or read branch protection (Ch 06, Ch 14) | Excellent — errors are immediate, in-run | Minimal — expires when the job ends | Minimal — nothing to rotate |
| Personal Access Token (PAT) | Low — one token, minted once | Strong — whatever scopes you grant it | Fair — tied to a human account, easy to forget it exists | High — acts as the person, until manually revoked | High — tied to a person who may leave, rotate manually |
| GitHub App | High — register the App, generate a private key, install it per repo | Excellent — scoped per installation, per permission | Strong — visibly posts as its own bot identity | Low — short-lived tokens, scoped per install | Moderate — one private key to protect, but no human tied to it |

## 13. Case Study: One Bot, Twelve Repos

A platform team wants this curriculum's three-gate airlock running identically across twelve
service repos. A PAT means either one person's token with access to all twelve (a single point of
failure and an audit nightmare), or twelve separate PATs to manage. A GitHub App means one
registration, installed on all twelve repos, each installation getting its own short-lived token
scoped only to that repo — and if the App is ever compromised, revoking it kills exactly its
access, not a human's entire account.

## 14. Practical Tips: Minting a PAT for This Curriculum

This curriculum's own `automerge.yml` (Chapter 06 §9) needs a token that can enable auto-merge,
since `GITHUB_TOKEN` cannot. For a single sandbox repo, a fine-grained PAT is the pragmatic choice
(a full GitHub App is more setup than a one-repo lab justifies — Section 11's comparison still
applies once you're automating more than one):

```
Minting a fine-grained PAT for PRA_BOT_TOKEN
──────────────────────────────────────────────
[ ] GitHub -> Settings -> Developer settings -> Fine-grained tokens -> Generate new
[ ] Resource owner: your account
[ ] Repository access: "Only select repositories" -> this sandbox repo
[ ] Permissions -> Pull requests: Read and write
[ ] Permissions -> Contents: Read and write (if it will also push, per Gate 1)
[ ] Set an expiration -- do not choose "no expiration"
[ ] Generate, copy the token immediately (shown once)
[ ] gh secret set PRA_BOT_TOKEN --repo <you>/practice_git_intro_to_pr_automerge
```

This is inherently a browser action — there is no scriptable, headless way to mint a PAT, by
design (GitHub requires you to be present, logged in, to create one).

## 15. Your First Project: Read, Then Write

Against the sandbox repo: `gh api repos/<you>/practice_git_intro_to_pr_automerge/pulls --jq
'.[].number'` to list open PRs (a read), then `gh api -X POST
repos/<you>/practice_git_intro_to_pr_automerge/issues/<N>/comments -f body="hello from the API"`
on one of them (a write). Watch the comment appear on the PR. This is the entire API surface this
curriculum uses, demonstrated in two commands.

## 16. Common Pitfalls & Misconceptions

1. **"`gh api` and `curl` to the REST API are different things."** They're not — `gh api` is a
   convenience wrapper with your auth already attached. Anything you can do with one, you can do
   with the other.

2. **"If my test PR has 5 files, pagination doesn't matter."** It matters the day someone opens a
   150-file PR, which your 5-file test will never catch (Section 4).

3. **"A PAT is basically the same as a GitHub App, just older."** No — a PAT acts *as a person*.
   An App is its own distinct, scoped identity. This is a difference in kind, not vintage.

4. **"GitHub Apps are only for published, public integrations."** No — you can register and use a
   private App entirely for your own team's internal automation, never publishing it.

5. **"`-f` and `-F` in `gh api` are interchangeable."** They're not — `-f` sends a string, `-F`
   sends a typed value. Sending `-f allow_auto_merge=true` sets the string `"true"`, which most
   boolean fields will silently reject or ignore rather than error on.

## 17. Key Takeaways

- **The REST API is the workhorse; GraphQL is the rare exception** — you'll hit it exactly once in
  this curriculum, for enabling auto-merge.
- **Pagination bugs are invisible until a large PR exposes them** — always paginate list endpoints,
  even when your test data doesn't need it yet.
- **Reading and writing are the same shape** — verb, URL, JSON — writing just adds a body.
- **A GitHub App is a distinct identity, not a bigger PAT** — scoped per installation, no human
  tied to it, the right tool the moment you're automating more than one repo.
- **This curriculum uses a PAT, not an App** — because a single sandbox repo doesn't yet justify an
  App's setup cost; Section 11's comparison tells you when that trade-off flips.

## 18. What's Next: Chapter 08 — Actions Anatomy

Chapter 08 shifts from "how to talk to GitHub's API" to "how GitHub Actions itself is structured"
— workflows, jobs, steps, and runners — the mechanics every gate workflow in this curriculum is
built from.

[→ Chapter 08: Actions Anatomy](chapter_08_actions_anatomy.md)

## 19. Additional Resources

- **GitHub REST API overview** — https://docs.github.com/en/rest (fetched 2026-08)
- **GitHub Docs, "About creating GitHub Apps"** — https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps (fetched 2026-08)
- **GitHub Docs, "Differences between GitHub Apps and OAuth apps"** — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps (fetched 2026-08)
- **GitHub Docs, "Rate limits for the REST API"** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api (fetched 2026-08)
- **GitHub CLI manual, `gh api`** — https://cli.github.com/manual/gh_api (fetched 2026-09; note: `gh api` has no `--repo`/`-R` flag — the repo comes from `{owner}/{repo}` placeholders or the literal path)
- **GitHub Docs, "REST API endpoints for check runs" (create response fields, `PATCH …/check-runs/{id}`)** — https://docs.github.com/en/rest/checks/runs (fetched 2026-08)
- **`actions/github-script` README (current major version, `github`/`context` objects)** — https://github.com/actions/github-script (fetched 2026-08)

## 20. Appendix A — Code Index

### A.1 — Paginated Fetch With Truncation Handling (from Section 4)

**What the code does:** Walks every page of a PR's changed-files list, stopping cleanly at
GitHub's 3,000-file cap on `/pulls/{n}/files` rather than assuming the list is complete.

**ASCII flowchart:**

```
page = 1
loop:
    fetch page N (per_page=100)
    accumulate files
    if fewer than 100 returned OR total >= 3000: stop, flag possible truncation
    else: page += 1
```

See `pr_automerge/gh_client.py` → `run_gh()` and `labs/lab_04_pr_data.py` (Chapter 04) for the
full implementation this chapter builds on.

### A.2 — Publishing a Check Run (from Section 7)

**What the code does:** Wraps the `POST /check-runs` call from Section 7 into a reusable helper
with typed name/sha/conclusion/summary arguments.

**ASCII flowchart:**

```
Inputs: repo, name, head_sha, conclusion, title, summary
    ↓
gh api repos/{repo}/check-runs
    -f name=... -f head_sha=... -f status=completed
    -f conclusion=... -f output[title]=... -f output[summary]=...
    ↓
Output: the created check-run's id
```

See `labs/lab_07_api_and_apps.py` → function `publish_check_run()` for the full implementation,
reused directly by Gate 2 and Gate 3's workflow YAML.
