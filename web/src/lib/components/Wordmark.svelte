<script lang="ts">
  // The mark and the name, together: the wordmark's own first letter, drawn as
  // a stem and a bowl. Two shapes is all a 16px browser tab can hold.
  let { size = '1.0625rem' }: { size?: string } = $props()
</script>

<span class="mark" style:--size={size}>
  <svg viewBox="0 0 32 32" aria-hidden="true">
    <rect class="tile" width="32" height="32" rx="8" />
    <path
      class="letter"
      fill-rule="evenodd"
      d="M10.4 4.4a2.3 2.3 0 0 0-2.3 2.3v12.9a8.4 8.4 0 1 0 4.6-7.5V6.7a2.3 2.3 0 0 0-2.3-2.3Zm6.1 11.2a3.8 3.8 0 1 0 0 7.6 3.8 3.8 0 0 0 0-7.6Z"
    />
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

  /* One outline with the counter punched out of it, rather than a stem drawn
     beside a circle: in a b the stem is the bowl's left wall, and two shapes
     that merely touch read as two shapes. */
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
