<script lang="ts">
  import type { Snippet } from 'svelte'
  import { isDark, toggleTheme } from '../theme.svelte'
  import Link from './Link.svelte'

  let { onsignout, children }: { onsignout: () => void; children: Snippet } = $props()
</script>

<header class="topbar">
  <div class="bar">
    <Link href="/" class="wordmark">budge</Link>

    <nav>
      <Link href="/">Dashboard</Link>
      <Link href="/transactions">Transactions</Link>
      <Link href="/settings">Settings</Link>
    </nav>

    <div class="actions">
      <button
        type="button"
        class="secondary outline icon"
        onclick={toggleTheme}
        aria-label={isDark() ? 'Switch to light theme' : 'Switch to dark theme'}
      >
        {#if isDark()}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4.25" />
            <path
              d="M12 2.5v2.2M12 19.3v2.2M21.5 12h-2.2M4.7 12H2.5M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6M18.7 18.7l-1.6-1.6M6.9 6.9L5.3 5.3"
            />
          </svg>
        {:else}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20.5 14.2A8.7 8.7 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7Z" />
          </svg>
        {/if}
      </button>
      <button type="button" class="secondary outline" onclick={onsignout}>Log out</button>
    </div>
  </div>
</header>

<main>{@render children()}</main>

<style>
  .topbar {
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
    background: color-mix(in srgb, var(--ctp-mantle) 82%, transparent);
    backdrop-filter: blur(12px);
  }

  /* Same measure as main, so the wordmark lines up with the page heading. */
  .bar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
    max-width: 56rem;
    margin-inline: auto;
    padding: 0.875rem clamp(1rem, 4vw, 2.5rem);
  }

  .bar :global(.wordmark) {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
    color: var(--pico-color);
    text-decoration: none;
    margin-right: auto;
  }

  nav {
    display: flex;
    gap: 0.25rem;
    order: 3;
    width: 100%;
  }

  nav :global(a) {
    padding: 0.3125rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--pico-muted-color);
    text-decoration: none;
    border-radius: 999px;
  }

  nav :global(a:hover) {
    color: var(--pico-color);
    background: var(--pico-card-background-color);
  }

  nav :global(a[aria-current='page']) {
    color: var(--pico-primary-inverse);
    background: var(--pico-primary-background);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .actions button {
    margin-bottom: 0;
    white-space: nowrap;
  }

  .icon {
    display: grid;
    place-items: center;
    padding: 0;
    width: 2.5rem;
    height: 2.5rem;
  }

  .icon svg {
    width: 1.125rem;
    height: 1.125rem;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  main {
    max-width: 56rem;
    margin-inline: auto;
    padding: clamp(1.5rem, 5vw, 3rem) clamp(1rem, 4vw, 2.5rem) 4rem;
  }

  /* Room for the nav to sit inline once there is any. */
  @media (min-width: 40rem) {
    nav {
      order: 0;
      width: auto;
      margin-right: auto;
    }

    .bar :global(.wordmark) {
      margin-right: 0;
    }
  }
</style>
