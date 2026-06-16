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

The Pages build Node version is pinned via `.node-version` (repo root +
`frontend/`); bump it when the build toolchain needs a newer Node (e.g. Vite 8
requires Node ≥20.19/22.12). Check builds with
`wrangler pages deployment list --project-name refget`.
