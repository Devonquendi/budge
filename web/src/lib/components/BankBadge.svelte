<script lang="ts">
  import { badge, hue } from '../accounts'

  let { connection }: { connection: string } = $props()
</script>

<span class="badge" style:--hue={hue(connection)} aria-hidden="true">
  {badge(connection)}
</span>

<style>
  .badge {
    display: grid;
    place-items: center;
    flex: none;
    width: 1.4375rem;
    height: 1.4375rem;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-weight: 500;
    border-radius: 0.375rem;
    /* Mixing against the card keeps this readable in both themes. */
    background: color-mix(
      in oklch,
      oklch(0.7 0.12 var(--hue)) 22%,
      var(--pico-card-background-color)
    );
    color: color-mix(in oklch, oklch(0.7 0.12 var(--hue)) 70%, var(--pico-color));
  }
</style>
