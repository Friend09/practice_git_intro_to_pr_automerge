# Chapter 04: Reading PR Data

**Reading Time:** ~45 minutes
**Prerequisites:** Chapter 02 (Refs & PRs)
**Practice Notebook:** `notebooks/practice_04.ipynb`
**Reference Notebook:** `notebooks/lab_04_pr_data.ipynb`
**Script:** `labs/lab_04_pr_data.py`
**Doc Reference:** GitHub REST API -- Pulls
**Depth:** Core

---

## Beginner's Guide

**What to focus on first:** Sections 3–8. This is the vocabulary every gate in Phase 3 is built
directly on top of.

**What to SKIP on first read:** Section 10 (GraphQL vs REST trade-offs for bulk reads). Return once
you've felt the REST N+1 pain yourself.

**Key concepts in plain English:**

- **`gh pr view`:** The `gh` CLI's read for one PR, human-friendly by default, machine-friendly
  with `--json`.
- **`gh api`:** A raw, general-purpose HTTP client for any REST endpoint, authenticated with
  whatever token `gh` is configured with — the escape hatch when a purpose-built `gh pr ...`
  subcommand doesn't expose a field you need.
- **Pagination:** GitHub's list endpoints never return "everything" in one response — they return
  a bounded page (capped at 100 items) plus a signal for whether more exist.
- **Normalization:** Converting GitHub's raw, deeply-nested JSON into this repo's flat, typed
  `PRMetadata` — the shape every gate actually consumes.
- **The 300-file cap:** The `/pulls/{n}/files` endpoint — the one place a PR's *individual changed
  files* live — silently stops listing files past 300, a fact with real consequences for Gate 3.

**Your prior knowledge connection:** If you've ever called a REST API and had to check for a
`next_page` link or an `X-RateLimit-Remaining` header, pagination here works the same way — it's
not a GitHub-specific concept, just GitHub-specific numbers.

---

> **🔬 Automation Engineer's Lens:** The single most common way a gate produces a wrong verdict
> isn't a logic bug — it's reading truncated data and not noticing. A PR with 340 changed files
> queried via `/pulls/{n}/files` silently returns only the first 300, and code that assumes "the
> list I got back is the whole list" will undercount critical-path hits on exactly the PRs where
> getting that count right matters most (the huge ones).

---

> **🚦 Native vs Custom:** Reading is 100% native — `gh pr view`, `gh pr list`, and `gh api` are
> all GitHub-provided tools; you write zero code to fetch data that already exists. What you build
> is the **normalization layer**: turning GitHub's raw JSON shape into `PRMetadata`, the flat
> dataclass every gate in this curriculum actually operates on. Chapter 07 goes further into
> *writing* data back (comments, check runs); this chapter is read-only.

---

## What You'll Learn

- The difference between `gh pr view` (purpose-built) and `gh api` (general-purpose)
- How to fetch a single PR's raw object and normalize it into `PRMetadata`
- How `gh pr list` works, and what its `--limit` flag actually controls
- What pagination is, concretely: 100-item page caps and `Link` header `rel="next"` semantics
- The 300-file cap on `/pulls/{n}/files` and why it matters for Gate 3's critical-path detection
- When to reach for `gh api --paginate` instead of hand-rolling page-following logic

---

## Table of Contents

- [Chapter 04: Reading PR Data](#chapter-04-reading-pr-data)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. Two Read Paths: Purpose-Built vs General-Purpose](#1-two-read-paths-purpose-built-vs-general-purpose)
  - [2. Why Both Exist](#2-why-both-exist)
  - [3. `gh pr view`: Reading One PR](#3-gh-pr-view-reading-one-pr)
  - [4. `gh api`: Reading Anything](#4-gh-api-reading-anything)
  - [5. `gh pr list`: Reading Many PRs](#5-gh-pr-list-reading-many-prs)
  - [6. From Raw JSON to `PRMetadata`](#6-from-raw-json-to-prmetadata)
  - [7. What Pagination Actually Is](#7-what-pagination-actually-is)
  - [8. Two Concrete Ceilings: the 100-Item Page Cap and the 300-File Cap](#8-two-concrete-ceilings-the-100-item-page-cap-and-the-300-file-cap)
  - [9. ⚠️ ADVANCED: `gh api --paginate` vs Hand-Rolled Link Following](#9-️-advanced-gh-api---paginate-vs-hand-rolled-link-following)
  - [10. ⚠️ ADVANCED: REST N+1 vs a Single GraphQL Query](#10-️-advanced-rest-n1-vs-a-single-graphql-query)
  - [11. ⚠️ ADVANCED: Rate Limits While Paginating](#11-️-advanced-rate-limits-while-paginating)
  - [12. Case Study: Undercounting Critical-Path Hits](#12-case-study-undercounting-critical-path-hits)
  - [13. Case Study: `--json` Saves an `gh api` Round Trip](#13-case-study---json-saves-an-gh-api-round-trip)
  - [14. Practical Tips: Choosing `--json` Fields](#14-practical-tips-choosing---json-fields)
  - [15. Your First Project: Fetch, Normalize, Paginate](#15-your-first-project-fetch-normalize-paginate)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 05 — Branch Protection \& Rulesets](#18-whats-next-chapter-05--branch-protection--rulesets)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — Fetch, Normalize, List, Paginate (from Section 15)](#a1--fetch-normalize-list-paginate-from-section-15)

---

## 1. Two Read Paths: Purpose-Built vs General-Purpose

`gh` gives you two ways to read the same underlying data:

```
gh pr view 101 --json mergeable,additions        gh api repos/{o}/{r}/pulls/101
        │                                                   │
        ▼                                                   ▼
  Purpose-built for PRs. Field names are          General HTTP client. Field names
  gh's own vocabulary (camelCase JSON keys).       are the REST API's raw vocabulary
                                                     (also camelCase for this endpoint,
                                                     but not guaranteed elsewhere).
```

Both hit the same GitHub backend. The difference is ergonomics, not capability.

## 2. Why Both Exist

`gh pr view --json` is faster to write for the common case and validates your field names against
a known schema — typo a field and it errors immediately rather than silently returning `null`.
`gh api` exists for everything `gh`'s purpose-built subcommands don't expose: less common
endpoints, endpoints added to the API before `gh` added a wrapper for them, or raw access when you
need the exact REST response shape rather than `gh`'s reshaped version.

## 3. `gh pr view`: Reading One PR

```bash
gh pr view 101 --repo owner/name --json number,title,additions,deletions,changedFiles,mergeable
```

Notice the field names: `changedFiles`, not `changed_files`. `gh`'s `--json` flag uses its own
camelCase vocabulary, which does **not** always match the raw REST field names one-to-one — a
detail that trips people up moving between `gh pr view --json` output and `gh api` output for the
"same" data.

## 4. `gh api`: Reading Anything

```bash
gh api repos/owner/name/pulls/101
```

This hits `GET /repos/{owner}/{repo}/pulls/{pull_number}` directly and returns the REST API's raw
JSON — `changed_files` (snake_case), `mergeable_state`, `head.sha`, `base.sha`, exactly as
documented in GitHub's REST reference. When a chapter or lab in this curriculum needs a field
`gh pr view --json` doesn't expose, `gh api` is the fallback, and this repo's `pr_automerge`
package always uses this raw shape as its "ground truth" input to normalization (Section 6).

## 5. `gh pr list`: Reading Many PRs

```bash
gh pr list --repo owner/name --state open --limit 100 --json number,title,state
```

`--limit` caps how many results `gh` will assemble for you — `gh` itself follows pagination
internally up to that limit, so you don't hand-roll paging logic for this specific subcommand.
Requesting more than exist just returns however many are actually open.

## 6. From Raw JSON to `PRMetadata`

Every gate in this curriculum consumes `pr_automerge.models.PRMetadata`, not raw GitHub JSON.
Normalizing means picking the handful of fields gates actually need and flattening nested
structures:

```
raw["head"]["ref"]         →  PRMetadata.head
raw["base"]["ref"]         →  PRMetadata.base
raw["additions"]           →  PRMetadata.additions
raw["deletions"]           →  PRMetadata.deletions
raw["changed_files"]       →  PRMetadata.changed_files
(computed separately)      →  PRMetadata.critical_path_hits   (Section 8)
```

Keeping this normalization in exactly one function (`normalize_pr` in this chapter's lab) means
every gate downstream sees the same shape, regardless of whether the data originally came from
`gh pr view`, `gh api`, or a fixture file in tests.

## 7. What Pagination Actually Is

GitHub's list endpoints (`GET /pulls`, `GET /pulls/{n}/files`, `GET /pulls/{n}/reviews`, and
dozens more) never return an unbounded result set. Each response is one **page**, plus an HTTP
`Link` header naming the URL for the next page, if one exists:

```
Link: <https://api.github.com/...&page=2>; rel="next", <...&page=5>; rel="last"
```

No `Link` header (or no `rel="next"` entry) means you've read the last page. This is a standard
REST pagination pattern, not something GitHub invented — the concrete numbers in Section 8 are
what's GitHub-specific.

## 8. Two Concrete Ceilings: the 100-Item Page Cap and the 300-File Cap

Two different ceilings matter here, and they're easy to conflate:

**The 100-item page cap** applies to every REST list endpoint — `per_page` never goes above 100,
regardless of how large you request it. `gh pr list --limit 250` doesn't fail — `gh` transparently
issues multiple 100-item page requests and assembles the combined result for you. Hand-rolling this
yourself with `gh api` means checking the `Link` header after every request and re-issuing against
the `rel="next"` URL until it's absent.

**The 300-file hard ceiling** is sharper and easy to miss: `GET /repos/{o}/{r}/pulls/{n}/files` —
the endpoint that lists which *individual files* a PR touched — stops returning results after
**300 files**, full stop, even if you paginate correctly. There is no further page beyond that
point; the data simply isn't retrievable through this endpoint for a PR that large. This is exactly
why Gate 3's risk model (Chapter 16) treats `changed_files` (a plain count field on the PR object
itself, unaffected by this cap) and `critical_path_hits` (which *requires* the capped files list)
as two independently sourced numbers — and why a PR that touches 300+ files should already be well
past Gate 3's hard line-count ceiling before this cap becomes the limiting factor.

```
per_page cap:      100 items   →  applies to EVERY list endpoint, paginate past it freely
files-list cap:    300 files   →  applies ONLY to /pulls/{n}/files, NO page exists past it
```

## 9. ⚠️ ADVANCED: `gh api --paginate` vs Hand-Rolled Link Following

> ⚠️ **ADVANCED TOPIC:** Letting `gh` follow pagination for you automatically.
> **Skip on first read** — return once you've hand-rolled a `Link` header parser once, to feel why
> this flag exists.

```bash
gh api --paginate repos/owner/name/pulls/101/files
```

The `--paginate` flag tells `gh api` to follow `Link: rel="next"` automatically and concatenate
every page's JSON array into one combined output — the same thing `gh pr list --limit` does
internally, but available for *any* `gh api` call, not just the subcommands that already wrap it.
Reach for `--paginate` before hand-rolling a `Link`-header loop; it's the same logic, already
tested, for free.

## 10. ⚠️ ADVANCED: REST N+1 vs a Single GraphQL Query

> ⚠️ **ADVANCED TOPIC:** Why fetching many PRs' full detail via REST is slow, and GraphQL's fix.
> **Skip on first read** — return once you're fetching detail for more than a handful of PRs at
> once and feel the round-trip cost.

`gh pr list` gives you a *summary* per PR. Getting each PR's `mergeable_state`, review count, and
check-run status via REST means one additional `gh api` call **per PR** — an N+1 pattern that gets
slow past a few dozen PRs. GraphQL's single-query, nested-field model (Chapter 07 covers this in
depth) lets you request exactly the same combined shape in one HTTP round trip instead of N+1. This
curriculum's own gate workflows never hit this problem (they operate on one PR at a time), but any
tooling that scores *every open PR* in a repo at once should reach for GraphQL specifically to
avoid it.

## 11. ⚠️ ADVANCED: Rate Limits While Paginating

> ⚠️ **ADVANCED TOPIC:** Watching the rate-limit budget disappear mid-paginate.
> **Skip on first read.**

`GITHUB_TOKEN` gets 5,000 requests/hour (Chapter 11 covers token identities and their distinct
limits in full). Each page of a paginated response is a separate request against that budget —
paginating through 300 files at 100/page is 3 requests, cheap; but a script that re-fetches full
file lists for every PR in a repo with thousands of open PRs, every run, can burn through the
budget in ways a single-PR gate never will. `gh api` responses include `X-RateLimit-Remaining` in
every response, which is the field to watch, not the vaguer `x-ratelimit-limit`.

## 12. Case Study: Undercounting Critical-Path Hits

A 340-file automated dependency-bump PR touches `pr_automerge/scoring.py` (a critical path) as
file #312 in GitHub's listing order. A naive Gate 3 implementation that reads
`/pulls/{n}/files` expecting "the complete file list" gets only the first 300 — critical-path hit
#312 is silently absent from that response, and the PR's risk score comes back lower than it
should. The fix isn't a smarter pagination loop (Section 8 established there's no further page to
fetch) — it's checking `changed_files` (uncapped, on the PR object itself) against `300` *before*
trusting any critical-path count computed from the files endpoint, and treating "at or above the
cap" as an automatic critical-path hit in its own right.

## 13. Case Study: `--json` Saves an `gh api` Round Trip

A workflow step originally called `gh api repos/{o}/{r}/pulls/{n}` just to read `mergeable_state`,
then separately called `gh pr view {n} --json additions,deletions` for size data — two calls where
one would do, because both fields are available from `gh pr view --json` directly
(`mergeStateStatus`, `additions`, `deletions` are all valid `--json` field names). Checking
`gh pr view --json --help`'s full field list before reaching for `gh api` is a cheap habit that
saves a rate-limit unit and a network round trip every time it applies.

## 14. Practical Tips: Choosing `--json` Fields

```
Before writing `gh api ...`, check:
──────────────────────────────────────
[ ] gh pr view --json --help   -- does a purpose-built field already cover this?
[ ] Field name is camelCase (gh's own vocabulary), not the REST API's snake_case
[ ] Request ONLY the fields you need -- smaller payload, fewer things that can be null
[ ] If the field truly isn't there, THEN reach for `gh api repos/{o}/{r}/pulls/{n}`
```

## 15. Your First Project: Fetch, Normalize, Paginate

Against a real PR on the sandbox repo:

```bash
gh api repos/<owner>/<repo>/pulls/<N> | python -c "import json,sys; d=json.load(sys.stdin); print(d['mergeable_state'])"
gh pr list --repo <owner>/<repo> --limit 100 --json number,title,state
```

Then run this chapter's lab script in live mode and compare its normalized `PRMetadata` output
against the raw JSON you just printed by hand — confirm every field made the trip correctly.

## 16. Common Pitfalls & Misconceptions

1. **"`gh pr view --json` and `gh api` return the same field names."** No — `gh`'s `--json` flag
   uses its own camelCase vocabulary (`changedFiles`), which differs from the REST API's raw
   snake_case (`changed_files`).

2. **"A list endpoint eventually returns everything if I ask for enough pages."** True for most
   endpoints — but `/pulls/{n}/files` has a hard 300-file ceiling with no further page beyond it.

3. **"Pagination is something GitHub invented."** No — it's a standard `Link`-header REST pattern.
   The 100-item and 300-file numbers are GitHub-specific; the mechanism isn't.

4. **"I should normalize inline, wherever I happen to need `PRMetadata`."** Keep normalization in
   one function. Every gate needs the exact same shape; duplicating the mapping logic is how one
   gate silently drifts from another's understanding of the same PR.

5. **"`gh api --paginate` is slower than hand-rolling it myself."** It issues the same number of
   requests either way — it just does the `Link`-header following for you, correctly, every time.

## 17. Key Takeaways

- **Two read paths, same data:** `gh pr view --json` (purpose-built, its own field vocabulary) and
  `gh api` (general-purpose, raw REST vocabulary).
- **Normalize once:** every gate consumes `PRMetadata`, never raw JSON directly — keep the mapping
  in one function.
- **100-item page cap** on every list endpoint; **300-file hard ceiling** specifically on
  `/pulls/{n}/files`, with no page beyond it.
- **`gh api --paginate`** follows `Link: rel="next"` automatically — reach for it before hand-
  rolling the loop.
- **Rate limits are consumed per page**, not per logical request — a naive "refetch everything
  every run" script pays for that in a way a single-PR gate never does.

## 18. What's Next: Chapter 05 — Branch Protection & Rulesets

Chapter 05 moves from *reading* PR data to the repo-level configuration that decides which checks
are even required before a merge — branch protection and rulesets — which is what Gate 1
(Chapter 14) verifies is actually turned on.

[→ Chapter 05: Branch Protection & Rulesets](chapter_05_branch_protection.md)

## 19. Additional Resources

- **GitHub REST API, "Pull requests"** — https://docs.github.com/en/rest/pulls/pulls (fetched 2026-08)
- **GitHub REST API, "List pull requests files"** — https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files (fetched 2026-08) — see the 300-file note
- **GitHub Docs, "Using pagination in the REST API"** — https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api (fetched 2026-08)
- **GitHub CLI Manual, "gh api"** — https://cli.github.com/manual/gh_api (fetched 2026-08) — see `--paginate`

## 20. Appendix A — Code Index

### A.1 — Fetch, Normalize, List, Paginate (from Section 15)

**What the code does:** Fetches one PR's raw object and normalizes it into `PRMetadata`, then
lists several PRs and splits that list into page-sized chunks to illustrate pagination shape.

**ASCII flowchart:**

```
fetch_single_pr(repo, n) → raw dict
        │
        ▼
normalize_pr(raw) → PRMetadata

list_open_prs(repo) → [summary, summary, ...]
        │
        ▼
paginate_in_chunks(items, page_size=5) → [[page1], [page2], ...]
```

See `labs/lab_04_pr_data.py` for the full runnable version.
