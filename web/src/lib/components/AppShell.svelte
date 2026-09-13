<script lang="ts">
  import type { Snippet } from 'svelte'
  import { formatCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import { isDark, toggleTheme } from '../theme.svelte'
  import { getWorkspace } from '../workspace.svelte'
  import Link from './Link.svelte'
  import Wordmark from './Wordmark.svelte'

  let {
    email,
    onsignout,
    children,
  }: { email: string; onsignout: () => void; children: Snippet } = $props()

  const workspace = getWorkspace()

  // A count beside each nav item, so the sidebar says how much is behind a page
  // before you open it. Blank rather than zero while the first load is running —
  // "0 transactions" and "not loaded yet" are different things.
  const counts = $derived({
    dashboard: workspace.ready ? String(workspace.dashboardAccounts.length) : '',
    transactions: workspace.transactions.length
      ? String(workspace.transactions.length)
      : '',
  })
</script>

<div class="layout">
  <aside>
    <Link href="/" class="brand"><Wordmark /></Link>

    <nav>
      <Link href="/">
        Dashboard
        <span class="count numeric">{counts.dashboard}</span>
      </Link>
      <Link href="/transactions">
        Transactions
        <span class="count numeric">{counts.transactions}</span>
      </Link>
      <Link href="/settings">
        Settings
        <span class="count"></span>
      </Link>
    </nav>

    {#if workspace.totals.length}
      <div class="net">
        {#each workspace.totals as total (total.currency)}
          <p class="eyebrow">
            Net balance{#if workspace.totals.length > 1}&nbsp;· {total.currency}{/if}
          </p>
          <p class="figure numeric">
            {formatCents(total.net, total.currency, prefs().hideCents)}
          </p>
        {/each}
        <p class="muted meta">
          {workspace.dashboardAccounts.length}
          {workspace.dashboardAccounts.length === 1 ? 'account' : 'accounts'}
          {#if workspace.connectionCount}· {workspace.connectionCount}
            {workspace.connectionCount === 1 ? 'bank' : 'banks'}{/if}
        </p>
      </div>
    {/if}

    <div class="foot">
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
        <button type="button" class="secondary outline signout" onclick={onsignout}>
          Log out
        </button>
      </div>
      <p class="email" title={email}>{email}</p>
    </div>
  </aside>

  <main>{@render children()}</main>
</div>

<style>
  /*
   * Narrow first: the sidebar is a top bar that scrolls away, and the balance
   * card is hidden because the dashboard's own tiles already carry those
   * numbers. It becomes a real sidebar once there's width to spare.
   */
  .layout {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    min-height: 100dvh;
    background: var(--ctp-mantle);
  }

  aside {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 0.875rem;
    padding: 0.625rem max(0.875rem, env(safe-area-inset-left))
      0.625rem max(0.875rem, env(safe-area-inset-right));
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
    /* Rows scroll underneath this, so it can't be transparent. */
    background: color-mix(in srgb, var(--ctp-mantle) 88%, transparent);
    backdrop-filter: blur(12px);
  }

  /* Three items fit one row on a phone; a narrower one scrolls rather than
     wrapping each item onto its own line. */
  nav::-webkit-scrollbar {
    display: none;
  }

  aside :global(.brand) {
    color: var(--pico-color);
    text-decoration: none;
    padding: 0 0.25rem;
  }

  nav {
    display: flex;
    order: 3;
    gap: 0.0625rem;
    width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  nav :global(a) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
    padding: 0.375rem 0.5rem;
    font-size: var(--text-label);
    font-weight: 500;
    line-height: 1.4;
    color: var(--pico-muted-color);
    text-decoration: none;
    border-radius: 0.4375rem;
  }

  nav :global(a:hover) {
    color: var(--pico-color);
    background: var(--ctp-surface0);
  }

  nav :global(a[aria-current='page']) {
    color: var(--pico-color);
    background: var(--ctp-surface0);
  }

  /* Pushed to the right edge of the item, the way a folder shows its size. */
  .count {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ctp-overlay0);
  }

  /* The anchor belongs to Link, so the whole tail has to be global — scoped by
     the `nav` in front of it, which is ours. */
  nav :global(a[aria-current='page'] .count) {
    color: var(--pico-muted-color);
  }

  .net {
    display: none;
    padding: 0.5625rem 0.625rem;
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
    background: var(--pico-card-background-color);
  }

  .net p {
    margin: 0;
  }

  .figure {
    margin-top: 0.25rem !important;
    font-size: 1.0625rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }

  /* Only the second currency onwards needs separating from the one above. */
  .net .eyebrow + .figure ~ .eyebrow {
    margin-top: 0.5rem !important;
  }

  .meta {
    margin-top: 0.125rem !important;
    font-size: var(--text-meta);
    line-height: 1.3;
  }

  .foot {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-left: auto;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .actions button {
    white-space: nowrap;
  }

  .icon {
    display: grid;
    place-items: center;
    flex: none;
    width: 1.6875rem;
    height: 1.6875rem;
    padding: 0;
  }

  .icon svg {
    width: 0.875rem;
    height: 0.875rem;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .email {
    display: none;
    margin: 0;
    padding: 0 0.1875rem;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    line-height: 1.3;
    color: var(--ctp-overlay0);
    overflow: hidden;
    text-overflow: ellipsis;
  }

  main {
    flex: 1;
    min-width: 0;
    padding: 0.8125rem max(0.875rem, env(safe-area-inset-right)) 2rem
      max(0.875rem, env(safe-area-inset-left));
  }

  @media (min-width: 52rem) {
    .layout {
      flex-direction: row;
      align-items: stretch;
    }

    aside {
      position: sticky;
      top: 0;
      align-self: flex-start;
      flex: none;
      flex-wrap: nowrap;
      flex-direction: column;
      align-items: stretch;
      gap: 0.875rem;
      width: 12.125rem;
      height: 100dvh;
      padding: 0.8125rem 0.6875rem;
      border-bottom: 0;
      border-right: var(--pico-border-width) solid var(--pico-card-border-color);
      overflow-y: auto;
    }

    aside :global(.brand) {
      padding: 0.125rem 0.4375rem 0.25rem;
    }

    nav {
      order: 0;
      flex-direction: column;
    }

    .net {
      display: block;
    }

    .foot {
      /* Pinned to the bottom of the column, whatever is above it. */
      margin-top: auto;
      margin-left: 0;
      flex-direction: column;
      align-items: stretch;
      gap: 0.4375rem;
    }

    .actions .signout {
      flex: 1;
    }

    .email {
      display: block;
    }

    main {
      padding: 0.8125rem 1.125rem 2rem;
    }
  }
</style>
