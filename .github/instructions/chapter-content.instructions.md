---
description: "Enforce chapter structure and formatting conventions for the Intro to PR Auto-Merge learning modules. Use when: editing, creating, or reviewing files in learning_modules/. Ensures consistent header metadata, beginner's guide, Automation Engineer's lens, Native-vs-Custom callout, doc references, and 20-section structure. Auto-applies to all markdown files under learning_modules/."
applyTo: "learning_modules/**/*.md"
---

# Chapter Content Conventions

These rules apply to every markdown file under `learning_modules/`. They enforce structural
guardrails on **any** edit — section additions, typo fixes, or content updates.

## Required Header Block

Every chapter must start with this metadata block:

```markdown
# Chapter XX: Title

**Reading Time:** ~NN minutes
**Prerequisites:** Chapter N (topic), Chapter M (topic) — or "None"
**Practice Notebook:** `notebooks/practice_XX.ipynb` — or "— (reading-only chapter)"
**Reference Notebook:** `notebooks/lab_XX_<topic>.ipynb` — or "— (pair pending generation)"
**Script:** `labs/lab_XX_topic.py` — or "— (notebook-only)"
**Doc Reference:** GitHub Docs § ... · Pro Git Ch N — or "GitHub Actions Docs" for Phase 2+
**Depth:** Core | ⭐ Optional Deep-Dive
```

## Required Structural Elements

1. **Beginner's Guide** — immediately after the `---` separator; must include:
   - What to focus on first (section numbers)
   - What to SKIP on first read
   - Key concepts in plain English (3–5 bullet definitions)
   - Your prior knowledge connection ("If you've written a CI workflow before, this is familiar because…")

2. **Automation Engineer's Lens** — callout connecting the chapter concept to production cost when it goes wrong:

   ```markdown
   > **🔬 Automation Engineer's Lens:** ...
   ```

3. **Native vs Custom** — explicit principled answer to "does GitHub already do this, or must I build it?":

   ```markdown
   > **🚦 Native vs Custom:** ...
   ```

4. **What You'll Learn** — bullet list of 6–8 learning objectives

5. **Table of Contents** — 20 numbered sections linking to anchors

6. **20-Section Structure**:
   - Sections 1–2: Introduction and motivation (why this matters for auto-merge)
   - Sections 3–8: Core mechanics with ASCII diagrams
   - Sections 9–12: Advanced topics (mark with `⚠️ ADVANCED TOPIC:`)
   - Sections 13–15: Case studies, comparisons, practical tips
   - Section 16: Common pitfalls & misconceptions
   - Section 17: Key takeaways (5–7 bullet points)
   - Section 18: What's next (link to next chapter)
   - Section 19: Additional resources (docs, RFCs, tools) — each with a dated URL
   - Section 20: Appendix A — Code Index

## Domain-Specific Content Rules

- **Comparison tables:** Every section comparing two or more approaches (e.g. `pull_request` vs
  `pull_request_target`, native auto-merge vs DIY merge) must include a qualitative trade-off table
  across: Setup Effort, Control, Failure Visibility, Security Exposure, Maintenance Burden.
  **Never use star ratings.** Use these two vocabularies: quality axes (Control, Failure
  Visibility) use **Weak / Fair / Moderate / Strong / Excellent**; cost axes (Setup Effort,
  Security Exposure, Maintenance Burden) use **Minimal / Low / Moderate / High / Very High**
  (higher = harder to operate). Cell format: `Level — brief note` (2–5 words, e.g.
  `High — needs a PAT and a rotation policy`).
- **Event/trigger diagrams:** ASCII art showing PR opened → event → workflow → job → step → outcome
- **Concrete numbers:** rate limits (1,000/hr per repo for `GITHUB_TOKEN` in Actions; 5,000/hr
  for a PAT), cron schedules (`0 6 * * 1`), page
  sizes (100/page; 3,000-file cap on /pulls/{n}/files), timeouts (seconds), thresholds (numeric) — never vague qualifiers
  like "fast" or "usually"
- **YAML references:** Link to the chapter's companion workflow (see `.github/workflows/README.md`)
- **Code-mechanism connection:** Every code example must name the exact `gh` subcommand or REST
  endpoint used

## Content Style

- **Analogies first**: Every abstract concept gets a plain-language analogy before technical depth
  (the Airlock Principle is the repo's governing metaphor — reuse it, don't invent competing ones)
- **Your experience is relevant**: Reference "if you've set up a CI pipeline / branch protection
  before…" to connect new concepts to the reader's existing knowledge
- **Reading time**: Target 35–50 minutes per chapter (up to 60 for the capstone)
- **Optional deep-dive chapters** (marked with ⭐ in README): Can be longer — readers are warned
  in the header

## Code Placement (Critical)

- **< 15 lines** (Python or YAML): Keep inline in the section
- **20+ lines**: Move to Appendix A with:
  1. Plain English summary of what the code does
  2. ASCII flowchart of the logic
  3. Reference link: `See [Appendix A: Code Index](#20-appendix-a-code-index)`
- **Never move**: Pseudocode, config snippets, or simple 1–2 line examples
- **Notebooks**: Full exploratory code lives in the paired notebook set —
  `notebooks/lab_XX_<topic>.ipynb` for the runnable reference and `notebooks/practice_XX.ipynb`
  for the blank-code companion

## Formula Formatting

- Blank lines before and after `$$` blocks (used sparingly — most of this domain is not
  mathematical, but the Gate 3 scoring formula is)
- Add "In plain English:" before every formula
- Include a numerical example after every formula, using the running PR-size worked example
  (see Chapter 16) wherever possible

## The Worked Trace Pattern (Depth Standard)

Diagrams that only show *what exists* (layers, refs, gates) are not enough. Every core-mechanics
section must show *transformation*: this input → this command/event → this exact output. Six
devices; apply them wherever a concept is demonstrated:

1. **Bracket** — every demonstrated command or event gets a named state before, the exact
   command/event, and the state after. Never show a command without both states. (Model:
   Chapter 03 §2–5 — one shared starting commit graph, per-strategy resulting graphs.)
2. **Version labels** — label the *data*, not just the boxes: `vA`/`vB` on file or JSON
   versions, primes on rewritten commits (`C'`), and the literal fixture-spine SHAs
   (head `a1b2c3d4e5f6…`, base `0f1e2d3c4b5a…`, PR #101).
3. **"What to notice:"** — 2–4 bullets immediately after every shown output, pointing at the
   exact tokens that matter. Never leave the reader to derive the lesson from raw output.
4. **Fixture spine** — worked data comes from `fixtures/` (the mutually-consistent PR #101
   story). Inline trimmed excerpts ≤19 lines; ≥20 lines go to Appendix A.2+ per the Code
   Placement rules. Authored payloads with no fixture (e.g. event payloads) must reuse the
   PR #101 spine SHAs so every chapter tells one story.
5. **Engine trace** — when a machine evaluates something, show its own trace verbatim:
   `##[debug] Evaluating: success() => true`, real `git log --graph` output, real `git status`
   output, real API error JSON. (Model: Chapter 18 §3's exact resulting shell line.)
6. **Spot-the-diff** — for security and failure topics: present a near-identical good/bad pair
   and let the reader find the delta before the reveal.

**Applicability:** devices 1 and 3 are mandatory for every demonstrated command/output; 2, 4,
5, 6 only where they naturally fit. Do not force all six into every section.

**Placement guardrails:** never insert or renumber a `## N.` numbered section header, and never
touch the §16–20 headers (structure tests pin them). Renaming a §1–15 header is allowed only for
a substantive correction, and only with its Table of Contents anchor updated in the same edit
(the ToC is manually maintained and untested — it drifts silently). New depth content goes
in-place inside existing sections, in `###` subsections, or in Appendix A.2+. Keep additions
to roughly 60–80 lines per chapter per editing pass, and bump the `**Reading Time:**` header
if warranted. Behavioral claims sourced from books or memory must be verified against current
GitHub docs and cited with a dated URL in §19.
