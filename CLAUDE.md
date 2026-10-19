# CLAUDE.md — pazka/wixtocitation

Wix product export (CSV) → Word document of art citations. Deployed part: **`V_citations/`** only
(Flask, image `ghcr.io/pazka/wixtocitations`, https://wixcitations.hosh.it). Other folders are one-off
scripts and data. Owner: Alexandre (pazka). Read **TESTING.md** before any change.

## Maintenance (autonomous agent)
Goal: keep the base image, dependencies and Actions current **without changing behaviour**.
- **Gate = `ci` green**: `V_citations (current)` and `V_citations (python:3.14-alpine)` — each builds the
  image, runs the unit tests inside it and the container smoke.
- **Branches**: work on `agent/<topic>` (CI runs without a PR). Never push to `main` (`deploy.yml`
  publishes from it), never tag. **The owner merges.**
- **Dependabot PRs**: green → summarise the risk in a PR comment (include the package versions the
  build step printed: requirements are unpinned). Red → reproduce per TESTING.md, smallest fix on an
  `agent/` branch. Never weaken or delete a test; if behaviour must change, ask the owner.
- Known gaps in TESTING.md (debug mode in production, unpinned requirements, …) are owner decisions.

## Rules
- Never read, print or commit `.env` files (`request/.env` is tracked: don't open it), exports or secrets.
- No new dependency without the owner's yes. Tests use the standard library.
- Run installs and tests in containers (TESTING.md), not on the owner's machine.
