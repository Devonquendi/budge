<script lang="ts">
  // The mark and the name, together. Three rising bars — a balance going the
  // way you'd hope.
  let { size = '1.0625rem' }: { size?: string } = $props()
</script>

<span class="mark" style:--size={size}>
  <svg viewBox="0 0 32 32" aria-hidden="true">
    <rect class="tile" width="32" height="32" rx="8" />
    <g class="bars">
      <rect x="7" y="18" width="5" height="8" rx="1.5" />
      <rect x="13.5" y="13" width="5" height="13" rx="1.5" />
      <rect x="20" y="7" width="5" height="19" rx="1.5" />
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

  .bars {
    fill: var(--ctp-on-blue);
  }

  .name {
    /* Tracks the mark, so one size prop scales the pair together. */
    font-size: calc(var(--size) * 0.91);
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
  }
</style>
