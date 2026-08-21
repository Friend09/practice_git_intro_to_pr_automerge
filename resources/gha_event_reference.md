# GitHub Actions Event Reference — The Never-Forget Cheatsheet

**Doc Reference:** GitHub Docs "Events that trigger workflows"
**Related Chapters:** [Chapter 09 — The Event Model](../learning_modules/chapter_09_event_model.md) · [Chapter 10 — Contexts, Expressions, Outputs & `needs`](../learning_modules/chapter_10_contexts_expressions.md) · [Chapter 17 — Wiring the Airlock](../learning_modules/chapter_17_wiring_the_airlock.md)

---

> **How to use this guide:** Jump to the [TL;DR table](#tldr-which-trigger-do-i-want)
> if you're mid-workflow and need an answer fast. Read the rest once, end to end, to
> build the mental model — every row below was hit for real building this
> curriculum's own five workflows.

---

## TL;DR — Which Trigger Do I Want?

| I want to... | Use | Not |
| --- | --- | --- |
| React to a PR being opened/updated | `pull_request` | `pull_request_target` (unsafe with untrusted forks — see below) |
| Run something on a schedule | `schedule` + `workflow_dispatch` (the dispatch is your manual-test escape hatch) | `schedule` alone — untestable without waiting |
| React to another workflow finishing | `workflow_run` | A second `pull_request` trigger hoping it "sees" the first workflow's result |
| Let a human trigger it on demand | `workflow_dispatch` | Nothing — always add this alongside anything else if testability matters |
| React to a PR from a fork with secrets available | Neither directly — see Chapter 18 (label-gate or `workflow_run` split pattern) | `pull_request_target` checking out the fork's code |

---

## Every Trigger This Curriculum Uses, Compared

| Event | Checked-out ref | Secrets available? | Fork PRs reach it? | Fires from `GITHUB_TOKEN`-authored actions? |
| --- | --- | --- | --- | --- |
| `pull_request` | The PR's merge commit (a synthetic test-merge, not the head commit — see Chapter 02) | No, for fork PRs | Yes | N/A — humans/bots pushing to a branch trigger this normally |
| `pull_request_target` | The **base** branch's code, not the PR's | Yes, always | Yes | N/A |
| `schedule` | Default branch only | Yes | N/A | N/A |
| `workflow_dispatch` | Whatever ref you specify at dispatch time | Yes | N/A (must be triggered by someone with write access) | N/A |
| `workflow_run` | The **default branch's** version of the listening workflow's own file (not the triggering run's ref — a real gotcha, see Chapter 17) | Yes | Indirectly, if the workflow it listens to also ran for a fork PR | **Yes** — this is precisely why it's the escape hatch for chaining automation-authored events (Chapter 07 §10, Chapter 17) |
| `check_suite` | N/A (reacts to check-run completion, doesn't check out code itself) | Yes | Depends on the check's origin | Yes |
| `repository_dispatch` | Whatever the payload specifies | Yes | N/A (requires a token to fire) | Generally no — same restriction family as other automation-authored events |

## The `pull_request_target` Footgun, In One Picture

```
pull_request:                          pull_request_target:
  checks out THE PR'S CODE               checks out THE BASE BRANCH'S CODE
  no secrets (fork PRs)                  secrets ALWAYS available
      │                                       │
      ▼                                       ▼
  safe to run untrusted code             DANGEROUS if you then explicitly
  with no secret exposure                checkout the PR's head AND have secrets
```

The danger isn't `pull_request_target` alone — it's `pull_request_target` **plus** a
step that explicitly checks out `github.event.pull_request.head.sha` while secrets
are present. That combination runs untrusted, attacker-controlled code with your
secrets attached. Chapter 18 covers the safe patterns.

## The `workflow_run` Chaining Trap, In One Picture

```
Workflow A (pull_request-triggered)  →  runs on the PR branch, head_sha = REAL PR SHA
        │
        │ completes
        ▼
Workflow B (workflow_run-triggered off A)  →  reads event.workflow_run.head_sha
                                                = still correct (first hop)
        │
        │ completes
        ▼
Workflow C (workflow_run-triggered off B)  →  reads event.workflow_run.head_sha
                                                = COLLAPSED TO MAIN'S SHA (second hop!)
```

Verified live building this curriculum's `automerge.yml` — see Chapter 17 for the
full incident and its fix (stop recomputing the verdict; use required status
checks + native auto-merge instead of chaining more than one hop deep).

## Every Trigger Needs a Path Filter If It Shares a Repo With Non-Automation Content

This repo is both curriculum and live lab (Chapter 01 §8). Every gate workflow here
carries:

```yaml
on:
  pull_request:
    paths:
      - 'sandbox/**'
```

so a PR editing `learning_modules/` never wakes the airlock. See
`.github/instructions/workflows.instructions.md`.
