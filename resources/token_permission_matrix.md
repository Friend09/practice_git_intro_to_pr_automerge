# Token & Permission Matrix — The Never-Forget Cheatsheet

**Doc Reference:** GitHub Docs "Automatic token authentication" · GitHub Docs "About creating GitHub Apps"
**Related Chapters:** [Chapter 07 — The GitHub API In Depth & GitHub Apps](../learning_modules/chapter_07_github_api_and_apps.md) · [Chapter 11 — Tokens & Permissions](../learning_modules/chapter_11_tokens_and_permissions.md)

---

> **How to use this guide:** Every row in the "verified" column below was tested
> live against this curriculum's own sandbox repo, not taken from documentation
> alone. If GitHub changes this behavior, this file is the one to re-verify first.

---

## Can `GITHUB_TOKEN` Do This? — Verified Against a Real Repo

| Operation | Works with `GITHUB_TOKEN`? | Verified live | Needs instead |
| --- | --- | --- | --- |
| Read a PR's metadata (`gh pr view`) | ✅ Yes | Yes | — |
| Read a PR's files, paginated | ✅ Yes | Yes | — |
| Publish a check run | ✅ Yes, with `checks: write` declared | Yes — Gate 2/3 do this | — |
| Post a PR comment | ✅ Yes, with `pull-requests: write` declared | Yes — Gate 3 does this | — |
| Patch simple repo settings (e.g. `allow_auto_merge`) | ✅ Yes, with `contents: write`-adjacent permission | Yes — Gate 1 does this | — |
| **Read branch protection details** (`branches/{b}/protection`) | ❌ No — 403 regardless of `permissions:` block | Yes — Gate 1 hit this | PAT or GitHub App with Administration access |
| **Enable auto-merge** (`enablePullRequestAutoMerge`) | ❌ No — `GraphQL: Resource not accessible by integration` | Yes — `automerge.yml` hit this | PAT or GitHub App with `pull_requests: write` |
| **Trigger a downstream workflow via a normal event** (push, PR event) that this token's own action caused | ❌ No — GitHub deliberately suppresses this to prevent infinite loops | Documented GitHub behavior; worked around via `workflow_run` throughout this repo | `workflow_run` trigger (works regardless of the upstream token), or a PAT/App token |
| Push a commit to a **protected** branch, as the Actions bot | ❌ No bypass — bots don't inherit the admin bypass a human repo owner gets | Yes — Gate 1's first badge-push attempt hit this | Push to an unprotected branch instead, or use a PAT belonging to an actual admin |

## The Three Identities, Side by Side

| | `GITHUB_TOKEN` | Personal Access Token (PAT) | GitHub App |
| --- | --- | --- | --- |
| Exists automatically? | Yes, per workflow run | No — you mint it | No — you register and install it |
| Acts as | The Actions bot | You, the human | Its own bot identity |
| Lifetime | One workflow run | Until manually revoked (or expiry you set) | ~1 hour per installation token, auto-renewed |
| Can read branch protection details | No | Yes, if you have admin | Yes, if the installation has Administration permission |
| Can enable auto-merge | No | Yes | Yes |
| Right for | In-workflow reads/writes that don't need the above two | A single repo, low setup effort | Several repos, one identity, least security exposure |

## Minting a PAT for This Curriculum (Chapter 07 §14)

```
[ ] GitHub -> Settings -> Developer settings -> Fine-grained tokens -> Generate new
[ ] Resource owner: your account
[ ] Repository access: "Only select repositories" -> this sandbox repo
[ ] Permissions -> Pull requests: Read and write
[ ] Permissions -> Contents: Read and write
[ ] Set an expiration -- never "no expiration"
[ ] gh secret set PRA_BOT_TOKEN --repo <you>/practice_git_intro_to_pr_automerge
```

There is no scriptable, headless way to do this — GitHub requires an authenticated
browser session to mint a PAT, by design.

## The `-f` vs `-F` Trap in `gh api`

```bash
gh api -X PATCH repos/OWNER/REPO -f allow_auto_merge=true   # WRONG: sends string "true"
gh api -X PATCH repos/OWNER/REPO -F allow_auto_merge=true   # RIGHT: sends boolean true
```

`-f` always sends a string field. `-F` sends a typed field. A boolean setting given
a string `"true"` frequently no-ops silently rather than erroring — this exact
mistake was caught building this repo's Gate 1 workflow. Default to `-F` for
anything that isn't obviously text.
