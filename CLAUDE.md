# budge

A personal finance app built on [Akahu](https://developers.akahu.nz/llms.txt).

## Orientation

Two services, one Vercel project:

- `backend/`: FastAPI app
- `web/`: Svelte + Vite app

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

## Conventions

- Dependencies go through `uv add` and `pnpm add`, never hand-edited manifests.
- Tools are pinned in `mise.toml`; add them with `mise use --pin <tool>@latest`.
- `prek` runs on commit. `prek run --all-files` to run it by hand.

## Documentation

Markdown is not scratch space. Don't create, expand or restructure `CLAUDE.md`,
`README.md` or any other markdown file unless asked. Say what you think is
missing and let me decide. Two descriptions of one thing drift apart, and the
code is the one that can't.

Never use em dashes: not in code, comments, markdown or commit messages.

## Comments

Keep them short. Comment what the code can't say, and never restate the line
beneath it: a named function, constant or type is already its own description.
Prefer deleting a stale comment to updating it.

## Tech stack

- [Vercel](https://vercel.com/llms.txt)
- [Neon](https://neon.com/docs/llms.txt)
- [Svelte](https://svelte.dev/llms.txt)
- [Vite](https://vite.dev/llms.txt)
