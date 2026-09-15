<script lang="ts">
  import type { Snippet } from 'svelte'
  import { formatCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import { isDark, toggleTheme } from '../theme.svelte'
  import { getWorkspace } from '../workspace.svelte'
  import Link from './Link.svelte'
  import ProfileMenu from './ProfileMenu.svelte'
  import Wordmark from './Wordmark.svelte'

  let {
    email,
    name,
    onsignout,
    children,
  }: {
    email: string
    name: string | null
    onsignout: () => void
    children: Snippet
  } = $props()

  const workspace = getWorkspace()

  // Blank rather than zero until the first load answers. "No transactions"
  // and "not loaded yet" shouldn't look the same.
  const counts = $derived({
    dashboard: workspace.ready ? String(workspace.dashboardAccounts.length) : '',
    transactions: workspace.transactions.length
      ? String(workspace.transactions.length)
      : '',
  })

  // Narrow screens get a hamburger. Past the breakpoint the same <nav> is the
  // sidebar and is always on screen, so this stops meaning anything.
  let navOpen = $state(false)
  let shell = $state.raw<HTMLElement | null>(null)
</script>

<svelte:window
  onkeydown={(event) => {
    if (navOpen && event.key === 'Escape') navOpen = false
  }}
  onpointerdown={(event) => {
    if (navOpen && shell && !shell.contains(event.target as Node)) navOpen = false
  }}
/>

<!--
  Rendered twice, in the sidebar on a phone and in the content bar on a desktop,
  because the two layouts want them in different parents. Only ever one is
  displayed, so the hidden copy stays out of the accessibility tree.
-->
{#snippet actions()}
  <div class="actions">
    <label class="theme">
      {#if isDark()}
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20.5 14.2A8.7 8.7 0 1 1 9.8 3.5a7 7 0 0 0 10.7 10.7Z" />
        </svg>
      {:else}
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="4.25" />
          <path
            d="M12 2.5v2.2M12 19.3v2.2M21.5 12h-2.2M4.7 12H2.5M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6M18.7 18.7l-1.6-1.6M6.9 6.9L5.3 5.3"
          />
        </svg>
      {/if}
      <input
        type="checkbox"
        role="switch"
        checked={isDark()}
        onchange={toggleTheme}
        aria-label="Dark theme"
      />
    </label>

    <ProfileMenu {email} {name} {onsignout} />
  </div>
{/snippet}

<div class="layout">
  <aside bind:this={shell}>
    <button
      type="button"
      class="hamburger"
      aria-expanded={navOpen}
      aria-controls="main-nav"
      aria-label={navOpen ? 'Close menu' : 'Open menu'}
      onclick={() => (navOpen = !navOpen)}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        {#if navOpen}
          <path d="M6.5 6.5l11 11M17.5 6.5l-11 11" />
        {:else}
          <path d="M4 7h16M4 12h16M4 17h16" />
        {/if}
      </svg>
    </button>

    <Link href="/" class="brand" onclick={() => (navOpen = false)}>
      <Wordmark />
    </Link>

    <div class="beside-brand">{@render actions()}</div>

    <nav id="main-nav" class={{ open: navOpen }}>
      <Link href="/" onclick={() => (navOpen = false)}>
        Dashboard
        <span class="count numeric">{counts.dashboard}</span>
      </Link>
      <Link href="/transactions" onclick={() => (navOpen = false)}>
        Transactions
        <span class="count numeric">{counts.transactions}</span>
      </Link>
      <Link href="/settings" onclick={() => (navOpen = false)}>
        Settings
        <span class="count"></span>
      </Link>
    </nav>

    {#if workspace.totals.length}
      <div class={['net', { open: navOpen }]}>
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
    /* Longhand throughout: the shorthand's clockwise order had these two swapped. */
    padding-block: calc(0.625rem + env(safe-area-inset-top)) 0.625rem;
    padding-inline: max(0.875rem, env(safe-area-inset-left))
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

  /*
   * The panel the hamburger opens. Gone rather than hidden when closed, so it
   * stays out of the accessibility tree and off the tab order too. At the
   * breakpoint it is the sidebar and is always on screen.
   */
  nav {
    display: none;
    order: 3;
    flex-direction: column;
    gap: 0.0625rem;
    width: 100%;
  }

  nav.open {
    display: flex;
  }

  .hamburger {
    display: grid;
    place-items: center;
    flex: none;
    width: 1.875rem;
    height: 1.875rem;
    padding: 0;
    border: 0;
    border-radius: 0.4375rem;
    background: transparent;
  }

  @media (hover: hover) {
    .hamburger:hover {
      background: var(--ctp-surface0);
    }
  }

  .hamburger svg {
    width: 1.125rem;
    height: 1.125rem;
    fill: none;
    stroke: var(--pico-color);
    stroke-width: 1.8;
    stroke-linecap: round;
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

  nav :global(a[aria-current='page']) {
    color: var(--pico-color);
    background: var(--ctp-surface0);
  }

  @media (hover: hover) {
    nav :global(a:hover) {
      color: var(--pico-color);
      background: var(--ctp-surface0);
    }
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
    width: 100%;
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
    background: var(--pico-card-background-color);
  }

  /* Worth the room once the menu is open; the rest of the time the dashboard's
     own tiles already carry the same number. */
  .net.open {
    display: block;
    order: 4;
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
    gap: 0.5rem;
  }

  .theme {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin: 0;
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

  /*
   * The switch shows the mode rather than whether a feature is on: a pale sky
   * with a low sun, or a night sky with a pale moon. Safe to read the palette
   * for it: the checked state and the dark palette are the same condition, so
   * these two blocks never evaluate against the wrong theme.
   */
  .theme input {
    --pico-switch-background-color: var(--ctp-surface1);
    --pico-border-color: var(--ctp-surface1);
    --pico-switch-color: var(--ctp-yellow);
    cursor: pointer;
  }

  .theme input:checked {
    --pico-switch-checked-background-color: var(--ctp-crust);
    --pico-border-color: var(--ctp-surface1);
    --pico-switch-color: var(--ctp-lavender);
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
    padding-block: 0.8125rem calc(2rem + env(safe-area-inset-bottom));
    padding-inline: max(0.875rem, env(safe-area-inset-left))
      max(0.875rem, env(safe-area-inset-right));
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
      padding-block: calc(0.8125rem + env(safe-area-inset-top))
        calc(0.8125rem + env(safe-area-inset-bottom));
      padding-inline: max(0.6875rem, env(safe-area-inset-left)) 0.6875rem;
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

    .hamburger {
      display: none;
    }

    nav {
      display: flex;
      order: 0;
    }

    .net {
      display: block;
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      justify-content: flex-end;
      padding-block: calc(0.5rem + env(safe-area-inset-top)) 0.5rem;
      padding-inline: 1.125rem max(1.125rem, env(safe-area-inset-right));
      border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
      background: color-mix(in srgb, var(--ctp-mantle) 88%, transparent);
      backdrop-filter: blur(12px);
    }

    main {
      padding-block: 0.8125rem calc(2rem + env(safe-area-inset-bottom));
      padding-inline: 1.125rem max(1.125rem, env(safe-area-inset-right));
    }
  }
</style>
