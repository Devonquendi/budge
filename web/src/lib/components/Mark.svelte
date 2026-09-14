<script lang="ts">
  // The square in front of a name: the provider's logo when there is one, and
  // a tinted monogram when there isn't. One component, so the fallback and the
  // broken-image handling are the same wherever a mark appears.
  let {
    logo,
    fallback,
    tint,
  }: {
    logo: string | null | undefined
    /** One to three letters, drawn when there is no logo. */
    fallback: string
    /** The monogram's colour. */
    tint: string
  } = $props()

  // Akahu doesn't host a logo for every provider or merchant, and a URL that
  // 404s draws a broken image. Remembering which one failed falls back for
  // good, and forgets on its own once a different logo arrives.
  let broken = $state<string | null>(null)
  const src = $derived(logo && logo !== broken ? logo : null)
</script>

{#if src}
  <img
    class="mark"
    {src}
    alt=""
    loading="lazy"
    onerror={() => (broken = logo ?? null)}
  />
{:else}
  <span class="mark monogram" style:--tint={tint} aria-hidden="true">{fallback}</span>
{/if}

<style>
  .mark {
    flex: none;
    width: var(--mark-size, 1.4375rem);
    height: var(--mark-size, 1.4375rem);
    border-radius: 0.375rem;
  }

  /* Bank and merchant logos are drawn to sit on white, so the chip carries one
     rather than letting the dark theme swallow half of them. */
  img {
    object-fit: contain;
    padding: 0.0625rem;
    background: #fff;
    border: var(--pico-border-width) solid var(--ctp-divider);
  }

  .monogram {
    display: grid;
    place-items: center;
    overflow: hidden;
    font-family: var(--font-mono);
    /* Tied to the square rather than the type scale: a smaller mark carries
       the same letters and would otherwise spill out of itself. */
    font-size: calc(var(--mark-size, 1.4375rem) * 0.46);
    font-weight: 500;
    /* Mixing against the card keeps this readable in both themes. */
    background: color-mix(in oklch, var(--tint) 22%, var(--pico-card-background-color));
    color: color-mix(in oklch, var(--tint) 70%, var(--pico-color));
  }
</style>
