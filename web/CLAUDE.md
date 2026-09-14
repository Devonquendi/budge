# web

Plain Svelte 5 and Vite, not SvelteKit. `src/routes/` is an ordinary folder with
no routing behaviour of its own: the router is `src/lib/router.svelte.ts` and the
table is the `{#if}` chain in `src/App.svelte`. Adding a page means a component, a
branch there, and a link in `AppShell`.

Money crosses the wire as decimal strings and is added up in integer cents by
`src/lib/money.ts`. Never do float arithmetic on an amount.

## Comments

The root rule applies. Here that usually means a Pico or browser behaviour
that would look like a mistake.
