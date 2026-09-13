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

  // Blank rather than zero until the first load answers — "no transactions"
  // and "not loaded yet" shouldn't look the same.
  const counts = $derived({
    dashboard: workspace.ready ? String(workspace.dashboardAccounts.length) : '',
    transactions: workspace.transactions.length
      ? String(workspace.transactions.length)
      : '',
  })
</script>

<!--
  Rendered twice, in the sidebar on a phone and in the content bar on a desktop,
  because the two layouts want them in different parents. Only ever one is
  displayed, so the hidden copy stays out of the accessibility tree.
-->
{#snippet actions()}
  <div class="actions">
    <label class="theme">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20.5 14.2A8.7 8.7 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7Z" />
      </svg>
      <input
        type="checkbox"
        role="switch"
        checked={isDark()}
        onchange={toggleTheme}
        aria-label="Dark theme"
      />
    </label>
    <button type="button" class="secondary outline" onclick={onsignout}>Log out</button>
  </div>
{/snippet}

<div class="layout">
  <aside>
    <Link href="/" class="brand"><Wordmark /></Link>

    <div class="beside-brand">{@render actions()}</div>

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

    <p class="email" title={email}>{email}</p>
  </aside>

  <div class="column">
    <header class="topbar">{@render actions()}</header>
    <main>{@render children()}</main>
  </div>
</div>

<style>
  /*
   * Narrow first: the sidebar is a top bar, and the balance card is hidden
   * because the dashboard's own tiles already carry those numbers. It becomes
   * a real sidebar once there's width to spare.
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
    padding: 0.625rem max(0.875rem, env(safe-area-inset-left)) 0.625rem
      max(0.875rem, env(safe-area-inset-right));
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
    background: color-mix(in srgb, var(--ctp-mantle) 88%, transparent);
    backdrop-filter: blur(12px);
  }

  aside :global(.brand) {
    padding: 0 0.25rem;
    color: var(--pico-color);
    text-decoration: none;
  }

  .beside-brand {
    margin-left: auto;
  }

  nav {
    display: flex;
    order: 3;
    gap: 0.0625rem;
    width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
  }

  nav::-webkit-scrollbar {
    display: none;
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

  nav :global(a:hover),
  nav :global(a[aria-current='page']) {
    color: var(--pico-color);
    background: var(--ctp-surface0);
  }

  .count {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--count-fg, var(--ctp-overlay0));
  }

  /* Svelte rejects :global() mid-selector, so rather than globalising .count
     itself the active link passes the colour down. */
  nav :global(a[aria-current='page']) {
    --count-fg: var(--pico-muted-color);
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

  .net .figure {
    margin-top: 0.25rem;
    font-size: 1.0625rem;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }

  /* Only a second currency onwards follows a figure, and only it needs the gap. */
  .net .figure + .eyebrow {
    margin-top: 0.5rem;
  }

  .net .meta {
    margin-top: 0.125rem;
    font-size: var(--text-meta);
    line-height: 1.3;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .actions button {
    white-space: nowrap;
  }

  /* The moon says what the switch is for; the switch says which way it's set. */
  .theme {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin: 0;
    padding: 0 0.125rem;
    cursor: pointer;
  }

  .theme svg {
    width: 0.875rem;
    height: 0.875rem;
    flex: none;
    fill: none;
    stroke: var(--pico-muted-color);
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .theme input {
    cursor: pointer;
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

  .column {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }

  .topbar {
    display: none;
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

    .beside-brand {
      display: none;
    }

    nav {
      order: 0;
      flex-direction: column;
    }

    .net {
      display: block;
    }

    .email {
      display: block;
      margin-top: auto;
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      justify-content: flex-end;
      padding: 0.5rem 1.125rem;
      border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
      background: color-mix(in srgb, var(--ctp-mantle) 88%, transparent);
      backdrop-filter: blur(12px);
    }

    main {
      padding: 0.8125rem 1.125rem 2rem;
    }
  }
</style>
