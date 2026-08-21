# sandbox/

This directory is the **only** place the live gate workflows watch. Every gate
workflow under `.github/workflows/` carries `paths: ['sandbox/**']`, so a PR that
touches only `learning_modules/`, `labs/`, or `notebooks/` never triggers the airlock
— only a PR that changes something in here does.

- `app/` — a trivial Python package. It exists purely so Gate 2 (CI) has something
  real to build and test; its content is not the point.
- `generated/` — throwaway files produced by `sandbox/generate_pr.py`, used to make
  PRs of an exact, known size for Gate 3 practice (Chapter 15 §hands-on). Safe to
  delete and regenerate at any time.
- `generate_pr.py` — `python sandbox/generate_pr.py --lines 120 --files 6` edits
  `generated/` until the working tree diff is approximately that size. You then
  `git commit`, `git push`, and `gh pr create` yourself — the script never commits
  or opens a PR on its own.
