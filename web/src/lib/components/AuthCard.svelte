<script lang="ts">
  import type { Snippet } from 'svelte'

  // The shell for every page you can reach without a dashboard: sign in, sign
  // up, and the two onboarding steps.
  let { width = '25rem', children }: { width?: string; children: Snippet } = $props()
</script>

<div class="frame">
  <div class="panel" style:--panel-width={width}>
    <p class="wordmark">budge</p>
    <div class="card body">
      {@render children()}
    </div>
  </div>
</div>

<style>
  .frame {
    display: grid;
    place-items: center;
    min-height: 100dvh;
    padding: 2.5rem 1rem 4rem;
  }

  .panel {
    width: 100%;
    max-width: var(--panel-width);
  }

  .wordmark {
    margin-bottom: 1.25rem;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
    text-align: center;
  }

  .body {
    display: flex;
    flex-direction: column;
    gap: 1.125rem;
    padding: clamp(1.5rem, 5vw, 2rem);
    box-shadow: var(--shadow-lift);
  }
</style>
