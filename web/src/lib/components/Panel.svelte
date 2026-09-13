<script lang="ts">
  import type { Snippet } from 'svelte'

  // The card the whole layout is built from: a titled header, a body that is
  // either a flush list or padded content, and an optional footer strip.
  let {
    title,
    padded = false,
    action,
    children,
    footer,
  }: {
    title: string
    /** Off for a list that runs edge to edge, on for anything with prose or fields. */
    padded?: boolean
    /** Sits at the right of the header: a link, a count, a status dot. */
    action?: Snippet
    children: Snippet
    footer?: Snippet
  } = $props()
</script>

<section>
  <header>
    <h2>{title}</h2>
    {#if action}{@render action()}{/if}
  </header>

  <div class={['body', { padded }]}>{@render children()}</div>

  {#if footer}
    <footer>{@render footer()}</footer>
  {/if}
</section>

<style>
  section {
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
  }

  header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4375rem 0.6875rem;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  h2 {
    /* Pushes anything else in the header to the right edge. */
    margin: 0 auto 0 0;
    font-size: var(--text-section);
    line-height: 1.3;
  }

  .body {
    min-width: 0;
  }

  .padded {
    display: flex;
    flex-direction: column;
    gap: 0.5625rem;
    padding: 0.625rem 0.6875rem 0.6875rem;
  }

  footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4375rem 0.6875rem;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
    background: var(--ctp-recessed);
  }
</style>
