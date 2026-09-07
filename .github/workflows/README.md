# The Live Gates — Workflow → Chapter Map

Every file here **executes for real** against this repo's `sandbox/`. Read
`.github/instructions/workflows.instructions.md` before editing any of them. This README is
documentation only (the workflow tests glob `*.yml`, so it is never parsed as a workflow).

| Workflow                 | Role                                   | Trigger                                              | Chapter |
| ------------------------ | -------------------------------------- | ---------------------------------------------------- | ------- |
| `ci.yml`                 | Builds/tests `sandbox/app/`; the required check Gate 2 reads | `pull_request` (paths `sandbox/**`) · `workflow_dispatch` | Ch 08, 12 |
| `gate1-repo-health.yml`  | Gate 1 — repo readiness; enforces `allow_auto_merge` | `schedule` (`0 6 * * 1`) · `workflow_dispatch`  | Ch 14   |
| `gate2-pr-health.yml`    | Gate 2 — fail-closed read of CI's conclusion | `workflow_run` off `CI` (`completed`) — first hop only | Ch 15   |
| `gate3-score.yml`        | Gate 3 — pure risk score + check run + PR comment | `pull_request` (paths `sandbox/**`)         | Ch 16   |
| `automerge.yml`          | Queues `gh pr merge --auto --squash`; never merges directly | `pull_request` (paths `sandbox/**`) | Ch 17   |

How they chain without coordinating: Chapters 09 §8 (why Gate 2 stops at one `workflow_run`
hop), 17 (required status checks + native auto-merge do the sequencing), and 18 (why the
`paths: ['sandbox/**']` filter is a trust boundary, not a convenience).
