<script lang="ts">
  // The mark and the name, together: the wordmark's own first letter, drawn as
  // a stem and a bowl. Two shapes is all a 16px browser tab can hold.
  let { size = '1.0625rem' }: { size?: string } = $props()
</script>

<span class="mark" style:--size={size}>
  <svg viewBox="0 0 32 32" aria-hidden="true">
    <rect class="tile" width="32" height="32" rx="8" />
    <g class="letter">
      <path d="M9.6 7.4v17.2" />
      <circle cx="17.3" cy="19.4" r="5.2" />
    </g>
  </svg>
  <span class="name">budge</span>
</span>

<style>
  .mark {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  svg {
    flex: none;
    width: var(--size);
    height: var(--size);
  }

  .tile {
    fill: var(--ctp-blue);
  }

  /* Stroked rather than filled: a drawn letter keeps its counter open at the
     size a favicon is actually seen at, where a set b would fill in. */
  .letter {
    fill: none;
    stroke: var(--ctp-on-blue);
    stroke-width: 3.4;
    stroke-linecap: round;
  }

  .name {
    /* Tracks the mark, so one size prop scales the pair together. */
    font-size: calc(var(--size) * 0.91);
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
  }
</style>
