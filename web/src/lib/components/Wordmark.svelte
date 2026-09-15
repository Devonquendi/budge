<script lang="ts">
  // The mark and the name, together: the wordmark's own first letter, drawn as
  // a stem and a bowl. Two shapes is all a 16px browser tab can hold.
  let { size = '1.0625rem' }: { size?: string } = $props()
</script>

<span class="mark" style:--size={size}>
  <svg viewBox="0 0 32 32" aria-hidden="true">
    <rect class="tile" width="32" height="32" rx="8" />
    <rect class="letter" x="7.1" y="4.6" width="4.4" height="22.8" rx="2.2" />
    <circle class="letter" cx="19.9" cy="20.4" r="6.6" />
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

  .letter {
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
