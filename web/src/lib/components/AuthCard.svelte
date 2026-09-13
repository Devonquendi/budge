<script lang="ts">
  import type { Snippet } from 'svelte'
  import Wordmark from './Wordmark.svelte'

  // The shell for every page you can reach without a dashboard: sign in, sign
  // up, and the two onboarding steps.
  let {
    width = '20.5rem',
    padded = true,
    step,
    children,
    below,
  }: {
    width?: string
    /** Off when the card holds a flush list of its own, like the account picker. */
    padded?: boolean
    /** Onboarding replaces the wordmark with its progress through the steps. */
    step?: { current: number; total: number }
    children: Snippet
    /** Small print under the card — the "no account?" line. */
    below?: Snippet
  } = $props()
</script>

<div class="frame">
  <div class="panel" style:--panel-width={width}>
    {#if step}
      <p class="step">
        <span>Step {step.current} of {step.total}</span>
        <span class="track" aria-hidden="true">
          <span class="fill" style:width="{(step.current / step.total) * 100}%"></span>
        </span>
      </p>
    {:else}
      <p class="brand"><Wordmark size="1rem" /></p>
    {/if}

    <div class={['card', { padded }]}>{@render children()}</div>

    {#if below}
      <p class="below muted">{@render below()}</p>
    {/if}
  </div>
</div>

<style>
  .frame {
    display: grid;
    place-items: center;
    min-height: 100dvh;
    padding: 1.5rem max(1rem, env(safe-area-inset-left)) 3rem
      max(1rem, env(safe-area-inset-right));
    background: var(--ctp-mantle);
  }

  .panel {
    width: 100%;
    max-width: var(--panel-width);
  }

  .brand {
    display: flex;
    justify-content: center;
    margin: 0 0 0.875rem;
  }

  .step {
    display: flex;
    align-items: center;
    gap: 0.4375rem;
    margin: 0 0 0.625rem;
    font-family: var(--font-mono);
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  .track {
    display: block;
    flex: 1;
    height: 0.1875rem;
    overflow: hidden;
    border-radius: 999px;
    background: var(--ctp-surface0);
  }

  .fill {
    display: block;
    height: 100%;
    background: var(--ctp-blue);
  }

  .card {
    overflow: hidden;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: 0.625rem;
  }

  .padded {
    padding: 1rem;
  }

  .below {
    margin: 0.625rem 0 0;
    text-align: center;
    font-size: var(--text-label);
  }
</style>
