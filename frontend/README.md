# React frontend

Instructions are the parent repo readme.

## Deployment

This frontend is hosted on **Cloudflare Pages** (project `refget`), which is
**git-connected** to this repo and builds automatically on every push:

- push to **`master`** → Production build → **https://refget.databio.org** (live)
- push to any other branch (e.g. `dev`) → Preview build at `<hash>.refget.pages.dev`

So shipping a change to the live site = fast-forward `master` to `dev`
(`git push origin dev:master`). There is no GitHub Action or release involved
for the frontend — that's the API server (`seqcolapi.databio.org`, on AWS ECS),
which is separate.

## House Web UI Standard

This app follows the shared gen2 standard: TypeScript, the utility-first CSS in
`src/styles/`, and BEM components. No Bootstrap, no Tailwind, no inline styles.

`npm run lint:styles` runs `scripts/web-style-guard.mjs`, which enforces all of
that -- frozen `utilities.css`/`modal.css`, class resolution, banned
dependencies. It runs as the first step of `npm run build`, so the Cloudflare
Pages build fails on a drift just as CI does.

To refresh the standard's files after the skill changes, run the skill's
installer rather than editing them here:

```bash
node <workspaces>/.claude/supplemental-skills/dev/web-design-style/web-style-sync.mjs --path .
```

The Pages build Node version is pinned via `.node-version` (repo root +
`frontend/`); bump it when the build toolchain needs a newer Node (e.g. Vite 8
requires Node ≥20.19/22.12). Check builds with
`wrangler pages deployment list --project-name refget`.
