# Chapter 22: Buy vs Build

**Reading Time:** ~35 minutes
**Prerequisites:** Chapter 17 (Wiring the Airlock)
**Practice Notebook:** `notebooks/practice_22.ipynb`
**Reference Notebook:** `notebooks/lab_22_buy_vs_build.ipynb`
**Script:** `labs/lab_22_buy_vs_build.py`
**Doc Reference:** Mergify / Kodiak / Renovate docs
**Depth:** ⭐ Optional Deep-Dive

---

## Beginner's Guide

**What to focus on first:** Sections 3–6 — the honest feature comparison and the weighted
heuristic, which is this chapter's actual payload.

**What to SKIP on first read:** Section 10 (vendor lock-in exit costs in detail). Return only if
you're actually evaluating a specific vendor contract.

**Key concepts in plain English:**

- **Third-party PR-automation tools:** Vendor-hosted or GitHub-App-based tools (Mergify, Kodiak)
  that implement auto-merge-adjacent policies via a configuration file, no custom code required.
- **Config-driven DSL:** The policy language these tools expose — expressive for common patterns
  (require N approvals, merge when labeled), but bounded by whatever the vendor decided to support.
- **Vendor lock-in:** The cost of depending on a third party's continued existence, pricing, and
  feature set — a real cost, not a hypothetical one, distinct from setup effort.
- **The weighted heuristic:** This chapter's own decision tool — a small set of factors (custom
  logic needs, repo count, in-house expertise, budget), each nudging toward buy or build.
- **Renovate, as a partial counter-example:** A dependency-update bot, not a general merge-policy
  tool — included here because it's the most common "I already use a buy tool for something
  adjacent" case teams have, worth distinguishing from Mergify/Kodiak's broader scope.

**Your prior knowledge connection:** If you've ever weighed a SaaS observability platform against
running your own Prometheus/Grafana stack, this is the exact same trade-off — setup effort and
ongoing cost against control, customizability, and no vendor dependency — applied to PR automation
specifically.

---

> **🔬 Automation Engineer's Lens:** The honest answer to "should I have built this curriculum's
> three-gate system instead of installing Mergify" is: **it depends entirely on whether Gate 3's
> custom risk-scoring formula (Chapter 16) is something you actually need.** If a config-driven
> "merge when 2 approvals + all checks pass" policy is sufficient, this entire curriculum's build
> effort was solving a problem a third-party tool already solves, for free, in an afternoon. The
> value of everything built here is specifically the custom risk model — that's the one piece no
> off-the-shelf tool can give you unmodified.

---

> **🚦 Native vs Custom:** This chapter is unusual — it's not about a GitHub-native feature at all,
> but about the decision of whether to adopt an *external* vendor's product instead of building on
> GitHub's native primitives yourself (which is what Chapters 01–21 taught). The "native vs custom"
> question here is really "GitHub-native-plus-your-code vs third-party-product" — a different axis
> from every other chapter's callout.

---

## What You'll Learn

- What third-party PR-automation tools (Mergify, Kodiak) actually offer out of the box
- The honest trade-offs: setup effort, hosting, customizability, vendor lock-in, cost, debuggability
- A weighted decision heuristic for a specific team's own situation
- Why this curriculum's specific value is Gate 3's custom risk model, not the other two gates
- Where Renovate fits (dependency updates specifically, not general merge policy)
- How to reconsider this decision later if your team's situation changes

---

## Table of Contents

- [Chapter 22: Buy vs Build](#chapter-22-buy-vs-build)
  - [Beginner's Guide](#beginners-guide)
  - [What You'll Learn](#what-youll-learn)
  - [Table of Contents](#table-of-contents)
  - [1. What "Buy" Actually Means Here](#1-what-buy-actually-means-here)
  - [2. What These Tools Offer Out of the Box](#2-what-these-tools-offer-out-of-the-box)
  - [3. The Feature Comparison, Honestly](#3-the-feature-comparison-honestly)
  - [4. Where This Curriculum's Value Actually Concentrates](#4-where-this-curriculums-value-actually-concentrates)
  - [5. The Weighted Heuristic](#5-the-weighted-heuristic)
  - [6. Running the Heuristic on Two Different Teams](#6-running-the-heuristic-on-two-different-teams)
  - [7. Renovate: A Different Category](#7-renovate-a-different-category)
  - [8. A Hybrid Approach](#8-a-hybrid-approach)
  - [9. ⚠️ ADVANCED: Config-DSL Expressiveness Limits](#9-️-advanced-config-dsl-expressiveness-limits)
  - [10. ⚠️ ADVANCED: Vendor Lock-In Exit Costs](#10-️-advanced-vendor-lock-in-exit-costs)
  - [11. ⚠️ ADVANCED: Self-Hosting a Third-Party Tool's Open-Source Core](#11-️-advanced-self-hosting-a-third-party-tools-open-source-core)
  - [12. Case Study: A Team That Should Have Bought](#12-case-study-a-team-that-should-have-bought)
  - [13. Case Study: A Team That Should Have Built](#13-case-study-a-team-that-should-have-built)
  - [14. Practical Tips: Revisiting the Decision Later](#14-practical-tips-revisiting-the-decision-later)
  - [15. Your First Project: Score Your Own Team](#15-your-first-project-score-your-own-team)
  - [16. Common Pitfalls \& Misconceptions](#16-common-pitfalls--misconceptions)
  - [17. Key Takeaways](#17-key-takeaways)
  - [18. What's Next: Chapter 23 — Capstone](#18-whats-next-chapter-23--capstone)
  - [19. Additional Resources](#19-additional-resources)
  - [20. Appendix A — Code Index](#20-appendix-a--code-index)
    - [A.1 — The Comparison Table and the Heuristic (from Section 15)](#a1--the-comparison-table-and-the-heuristic-from-section-15)

---

## 1. What "Buy" Actually Means Here

"Buy" doesn't necessarily mean paying money — most of these tools have generous free tiers,
especially for open-source repos. It means adopting a third party's *product* (a GitHub App you
install, configured via a YAML policy file you write) instead of building and operating your own
workflows and scoring logic. The cost isn't primarily financial; it's the trade-offs in Section 3.

## 2. What These Tools Offer Out of the Box

Mergify and Kodiak both implement, natively and immediately: merging when a configurable set of
conditions holds (N approvals, all checks green, specific labels present/absent), queue-style
serialization (Chapter 20's merge-queue concept, often available even on repos without GitHub's
own native queue), and a management UI for visibility into merge decisions — all without writing a
single line of workflow YAML or Python.

## 3. The Feature Comparison, Honestly

| Dimension | Custom Build (this curriculum) | Third-Party Tool | Setup Effort |
| --- | --- | --- | --- |
| Setup effort | High — the full curriculum's build | Minimal — install + config file | Minimal (buy) / High (build) |
| Hosting | Self-hosted, your own Actions minutes | Vendor-hosted | Minimal (buy) |
| Custom risk-scoring logic | Fully custom, any formula | Bounded by the vendor's config DSL | Moderate (build, once) |
| Multi-repo rollout | Manual per-repo, or reusable workflows (Ch 21) | Native, one install covers an org | Minimal (buy) |
| Vendor lock-in | None | Real — pricing/feature/continuity risk | — |
| Cost | Actions minutes (often free) | Often free for OSS, paid for private/org | — |
| Debuggability | Full — your own code and logs | Limited to the vendor's own exposed logs | — |

## 4. Where This Curriculum's Value Actually Concentrates

Gates 1 and 2 (repo readiness, CI health) are close to what any competent third-party tool already
offers as a built-in condition type — "require these checks," "require the repo to be in a good
state" are common config-DSL primitives. **Gate 3's specific risk-scoring formula (Chapter 16) is
the one piece that's genuinely hard to replicate in a third-party tool's config language** — a
weighted linear combination of lines/files/critical-path-hits, with a hard ceiling layered on top,
is more expressive than most merge-policy DSLs are designed to support. If your team's actual need
stops at Gates 1–2's level of sophistication, most of this curriculum's build effort was solving an
already-solved problem.

## 5. The Weighted Heuristic

```python
def recommend(factors: BuyBuildFactors) -> dict:
    build_score = 0
    buy_score = 0
    if factors.needs_custom_risk_model:      build_score += 2   # strongest signal
    else:                                     buy_score += 1
    if factors.rolling_out_to_many_repos:     buy_score += 2    # strongest signal
    else:                                      build_score += 1
    if factors.has_in_house_actions_expertise: build_score += 1
    else:                                       buy_score += 1
    if not factors.budget_for_a_paid_tool:      build_score += 1
    return {"recommendation": "build" if build_score >= buy_score else "buy", ...}
```

The two heaviest-weighted factors — needing genuinely custom scoring logic, and rolling out across
many repos — are deliberately weighted more than the other two, because they're the factors most
likely to make either choice actively wrong rather than just less convenient.

## 6. Running the Heuristic on Two Different Teams

A team shaped like this repo's own curriculum sandbox (needs custom scoring, single repo, has
in-house Actions expertise, no budget for a paid tool) scores **build=5, buy=0** — strongly
favoring exactly what this curriculum built. A team rolling a simple "require 2 approvals + green
CI" policy out across dozens of repos, with no custom scoring need and no existing Actions
expertise, scores **build=0, buy=4** — strongly favoring a third-party tool instead. Same
heuristic, opposite conclusions, because the underlying situations are genuinely different.

## 7. Renovate: A Different Category

Renovate (and Dependabot) solve a narrower, different problem: automatically opening PRs for
dependency updates, with their own merge-policy configuration layered on top specifically for
*that* PR type. It's not a general-purpose merge-policy tool the way Mergify/Kodiak are — a team
using Renovate for dependency PRs and this curriculum's own three-gate system for everything else
isn't contradicting itself; they're solving two different problems with two different appropriately
-scoped tools.

## 8. A Hybrid Approach

Nothing prevents combining both: a third-party tool handling the common-case policy (approvals,
labels, basic check requirements) for most PRs, alongside a custom Gate 3-style risk check
specifically for the PRs that need it — published as its own required status check (Chapter 12),
which any merge-policy tool, native or third-party, can be configured to respect. This isn't an
all-or-nothing decision; the two approaches compose through the same required-check mechanism
Chapter 17 already relies on.

## 9. ⚠️ ADVANCED: Config-DSL Expressiveness Limits

> ⚠️ **ADVANCED TOPIC:** Where exactly a config-driven policy language stops being able to express
> what you need.
> **Skip on first read** — return once you've actually hit a DSL's expressiveness ceiling.

Most merge-policy DSLs support boolean combinations of conditions (labels, approval counts, check
names) and simple numeric comparisons (a PR under N lines). What they typically *can't* express:
a weighted combination of multiple continuous factors with a configurable formula (Gate 3's exact
shape), stateful logic that depends on historical PR patterns (Chapter 19's calibration), or
anything requiring an external data source the tool's own webhook payload doesn't already include.
If your policy needs land past this boundary, that's the concrete signal build has won regardless
of the other heuristic factors.

## 10. ⚠️ ADVANCED: Vendor Lock-In Exit Costs

> ⚠️ **ADVANCED TOPIC:** What it actually costs to leave a third-party tool later.
> **Skip on first read.**

Migrating off a third-party merge-policy tool later means translating its config-DSL policy back
into either another vendor's DSL or a custom build — a real, non-trivial migration cost that scales
with how much policy logic accumulated in the vendor's format over time. This cost is asymmetric:
adopting a third-party tool is nearly free to start, but the exit cost grows the longer and more
deeply a team depends on it. This is a real factor even when the immediate feature comparison
(Section 3) favors buying.

## 11. ⚠️ ADVANCED: Self-Hosting a Third-Party Tool's Open-Source Core

> ⚠️ **ADVANCED TOPIC:** A middle path between fully vendor-hosted and fully custom.
> **Skip on first read.**

Some third-party tools (Mergify has historically had open-source roots) can, in principle, be
self-hosted rather than using the vendor's hosted SaaS offering — trading away some of Section 2's
"minimal setup" convenience in exchange for removing Section 3's hosting-dependency and some of
Section 10's lock-in risk, while still getting the config-DSL's expressiveness ceiling from Section
9. Whether this is practical depends entirely on the specific tool's current licensing and
self-hosting support, which changes over time — verify current status before counting on it.

## 12. Case Study: A Team That Should Have Bought

A five-person team wants "require 2 approvals and a green build before merge, plus auto-merge once
both hold" — exactly the shape a third-party tool's default config template already provides.
Spending engineering time building and maintaining a custom three-gate system, as this curriculum
does, for a policy this simple would be solving an already-solved problem — the heuristic's own
Section 6 second example is built around exactly this shape of team.

## 13. Case Study: A Team That Should Have Built

A team whose merge policy genuinely depends on a weighted combination of PR size, historical
author reliability, and which specific internal services a change touches — a formula no
third-party DSL was designed to express, and one that needs periodic recalibration against real
outcome data (Chapter 19). This is this curriculum's own Gate 3, generalized — the shape of need
that justifies the build effort this whole curriculum represents.

## 14. Practical Tips: Revisiting the Decision Later

```
Signals it's time to reconsider this decision
──────────────────────────────────────────────
[ ] Bought: repeatedly hitting the config DSL's expressiveness ceiling (Section 9)
[ ] Bought: the vendor's pricing or roadmap has changed in a way that affects you
[ ] Built: maintenance burden is consistently exceeding what a config file would have cost
[ ] Built: rolling out to enough new repos that reusable workflows (Ch 21) aren't keeping pace
```

## 15. Your First Project: Score Your Own Team

Run this chapter's lab with `BuyBuildFactors` set to your own team's actual situation — not this
repo's, not a hypothetical — and read the printed reasons, not just the final recommendation. If a
reason feels wrong for your context, that's a sign the heuristic's weights (Section 5) need
adjusting for your specific situation, not that the tool is broken.

## 16. Common Pitfalls & Misconceptions

1. **"Building your own is always more 'serious' engineering."** No — for a policy a config-DSL
   already expresses well, building custom is solving an already-solved problem, not a sign of
   rigor.

2. **"Buying means giving up all customization."** Not entirely — most third-party tools support a
   real range of conditions; the limit is specifically continuous, weighted, formula-driven logic
   (Section 9), not customization in general.

3. **"This curriculum's build was 'wasted' if a third-party tool could do most of it."** Not for
   its actual purpose — this is a *learning* curriculum; the value was never purely "avoid building
   what Mergify already does," it's understanding the mechanics underneath both options.

4. **"Once you buy, you can't also build a custom piece."** Section 8's hybrid approach is common
   in practice — most required-check-based systems compose fine with a third-party tool handling
   the rest.

5. **"The decision, once made, never needs revisiting."** Team situations change — Section 14's
   signals are worth checking periodically, not just once at initial adoption.

## 17. Key Takeaways

- **This curriculum's specific build value concentrates in Gate 3's custom risk model** — Gates 1–2
  are close to what a third-party tool's config DSL already offers.
- **The comparison is genuinely honest, not built to favor either side** — setup effort and
  multi-repo rollout favor buying; custom logic and full debuggability favor building.
- **The weighted heuristic gives different teams different correct answers** — there's no universal
  right choice, only a right choice for a specific team's actual situation.
- **Renovate solves a narrower, different problem** (dependency PRs) than general merge-policy
  tools — not a substitute comparison for Mergify/Kodiak.
- **Buy and build compose** — a third-party tool handling common cases alongside a custom required
  check for the cases that need it is a legitimate hybrid, not a contradiction.

## 18. What's Next: Chapter 23 — Capstone

Chapter 23, the capstone, pulls every chapter's pieces together into one end-to-end exercise: build,
wire, and fire the complete airlock against this repo's own live sandbox, from a cold start.

[→ Chapter 23: Capstone](chapter_23_capstone.md)

## 19. Additional Resources

- **Mergify Documentation** — https://docs.mergify.com/ (fetched 2026-08)
- **Kodiak Documentation** — https://kodiakhq.com/docs (fetched 2026-08)
- **Renovate Documentation** — https://docs.renovatebot.com/ (fetched 2026-08)
- **This repo's own** `pr_automerge/scoring.py` — the exact custom logic Section 4 argues is this curriculum's real value

## 20. Appendix A — Code Index

### A.1 — The Comparison Table and the Heuristic (from Section 15)

**What the code does:** Encodes the feature comparison as structured data and implements a
weighted buy-vs-build heuristic, returning a typed recommendation with an explicit rationale list.

**ASCII flowchart:**

```
FEATURE_COMPARISON → printed dimension-by-dimension table

recommend(BuyBuildFactors(...))
    → weighted scoring across 4 factors
    → {"recommendation": "build" | "buy", "build_score": ..., "buy_score": ..., "reasons": [...]}
```

See `labs/lab_22_buy_vs_build.py` for the full runnable version.
