<script lang="ts">
  import Link from './Link.svelte'

  let { email, onsignout }: { email: string; onsignout: () => void } = $props()

  let open = $state(false)
  let root = $state.raw<HTMLElement | null>(null)
  let trigger = $state.raw<HTMLButtonElement | null>(null)

  const initial = $derived(email.trim().charAt(0).toUpperCase() || '?')

  /**
   * A disclosure, not a `role="menu"`: an ARIA menu owes its children
   * menuitem semantics and arrow-key navigation, and a switch isn't a valid
   * menuitem. A button that expands a panel is the honest description.
   */
  function close(returnFocus = false) {
    open = false
    if (returnFocus) trigger?.focus()
  }
</script>

<svelte:window
  onkeydown={(event) => {
    if (open && event.key === 'Escape') close(true)
  }}
  onpointerdown={(event) => {
    // The trigger lives inside root, so its own click toggles rather than
    // closing and immediately reopening.
    if (open && root && !root.contains(event.target as Node)) close()
  }}
/>

<div class="root" bind:this={root}>
  <button
    type="button"
    class="avatar"
    bind:this={trigger}
    onclick={() => (open = !open)}
    aria-expanded={open}
    aria-label="Account menu for {email}"
  >
    {initial}
  </button>

  {#if open}
    <div class="panel">
      <div class="who">
        <span class="avatar big" aria-hidden="true">{initial}</span>
        <span class="email" title={email}>{email}</span>
      </div>

      <Link href="/profile" class="row" onclick={() => close()}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="8" r="3.6" />
          <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
        </svg>
        <span class="label">Profile</span>
      </Link>

      <Link href="/settings" class="row" onclick={() => close()}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="3.2" />
          <path
            d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 7 19.4a1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H1a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 2.6 7a1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H7a1.7 1.7 0 0 0 1-1.5V1a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.2 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"
            transform="translate(1.4 1.4) scale(0.88)"
          />
        </svg>
        <span class="label">Settings</span>
      </Link>

      <button type="button" class="row" onclick={onsignout}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" />
        </svg>
        <span class="label">Log out</span>
      </button>
    </div>
  {/if}
</div>

<style>
  .root {
    position: relative;
    display: flex;
  }

  /* .root .avatar, not .avatar: app.css resets every button to width:auto at a
     higher specificity, which collapses the circle into an oval. */
  .root .avatar {
    display: grid;
    place-items: center;
    flex: none;
    width: 1.75rem;
    height: 1.75rem;
    padding: 0;
    border: 0;
    border-radius: 999px;
    background: var(--ctp-blue);
    color: var(--ctp-on-blue);
    font-size: var(--text-meta);
    font-weight: 600;
    line-height: 1;
    cursor: pointer;
  }

  .root .avatar:hover {
    background: var(--ctp-blue-hover);
  }

  .root .big {
    width: 2rem;
    height: 2rem;
    font-size: var(--text-label);
    cursor: default;
  }

  .panel {
    position: absolute;
    top: calc(100% + 0.4375rem);
    right: 0;
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 0.0625rem;
    width: max-content;
    min-width: 12.5rem;
    max-width: min(16rem, calc(100vw - 1.75rem));
    padding: 0.3125rem;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: 0.625rem;
    box-shadow: 0 6px 20px color-mix(in srgb, var(--ctp-crust) 30%, transparent);
  }

  .who {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.4375rem 0.5rem;
    border-bottom: var(--pico-border-width) solid var(--ctp-divider);
    margin-bottom: 0.1875rem;
  }

  .email {
    min-width: 0;
    font-family: var(--font-mono);
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* One shape for every line in the panel, whether it's a label, a link or a
     button — they only differ in what they do. */
  .root :global(.row) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    margin: 0;
    padding: 0.375rem 0.4375rem;
    border: 0;
    border-radius: 0.4375rem;
    background: transparent;
    /* --ctp-text, not --pico-color: Pico rebinds that to primary-inverse inside
       a button and to primary inside a link, so the row would come out white on
       white in one case and blue in the other. */
    color: var(--ctp-text);
    font-size: var(--text-label);
    font-weight: 500;
    line-height: 1.4;
    text-align: left;
    text-decoration: none;
    cursor: pointer;
  }

  .root :global(.row:hover) {
    background: var(--ctp-recessed);
  }

  .root :global(.row svg) {
    width: 0.875rem;
    height: 0.875rem;
    flex: none;
    fill: none;
    stroke: var(--pico-muted-color);
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .label {
    margin-right: auto;
  }
</style>
