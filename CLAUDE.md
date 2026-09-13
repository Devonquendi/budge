# budge

A personal finance app built on [Akahu](https://developers.akahu.nz/llms.txt).

## Orientation

Two services, one Vercel project:

- `backend/` — FastAPI app
- `web/` — Svelte + Vite app

## Dev tools

All dev tools used in this project are managed by [mise](mise.jdx.dev/llms.txt). Common
mise CLI commands include:

- `mise use <dep>@<version>`: Add a mise-managed dependency to the project
- `mise install`: Install project dependencies
- `mise up`: Update project dependencies

Unless otherwise specified, all dev tools listed below are managed by mise:

- [prek](https://prek.j178.dev/llms.txt)
- [uv](https://docs.astral.sh/uv/llms.txt)
- [pnpm](https://pnpm.io/motivation)
- [Vercel CLI](https://vercel.com/get-started.md)

Project dependencies are managed by `uv` and `pnpm`. Add and remove them with
`uv add`/`uv remove` and `pnpm add`/`pnpm remove` — never by hand-editing
`pyproject.toml`, `uv.lock`, `package.json` or `pnpm-lock.yaml`.

## Tech stack

- [Vercel](https://vercel.com/llms.txt)
- [Neon](https://neon.com/docs/llms.txt)
- [Svelte](https://svelte.dev/llms.txt)
- [Vite](https://vite.dev/llms.txt)
