# budge

A personal finance dashboard built on [Akahu](https://developers.akahu.nz).

- `backend/`: FastAPI, SQLModel, Neon Postgres
- `web/`: Svelte 5 + Vite

Both deploy as one Vercel project, so `/api` and the app share an origin.

## Getting started

[mise](https://mise.jdx.dev) manages every tool this project needs: Python, uv,
node, pnpm, prek and the Vercel CLI. Install it, then:

```sh
mise trust
mise install
```

Secrets are not in the repo:

1. Copy `.env.example` to `.env` and fill it in.
2. Run `vercel link`, then `vercel env pull` to write `.env.local`, which holds
   `DATABASE_URL`. This needs access to the Vercel project.

## Tasks

```sh
mise dev      # both dev servers
mise api      # FastAPI alone, on :8000
mise web      # Vite alone, on :5173
mise check    # type-check both services
mise build    # production build of the web app
```

Vite proxies `/api` to the backend in dev, matching how Vercel routes in
production, which also keeps the session cookie working.
