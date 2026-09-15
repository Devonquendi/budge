<script lang="ts">
  import { badge, hue } from '../accounts'
  import { isDark } from '../theme.svelte'
  import Mark from './Mark.svelte'

  let {
    connection,
    logo,
    compact = false,
  }: {
    connection: string
    logo?: string | null
    /** For the small mark in the ledger, where three letters don't fit. */
    compact?: boolean
  } = $props()

  const letters = $derived(compact ? badge(connection).slice(0, 1) : badge(connection))

  // Same lightness ramp as the category accents, so a bank chip and a
  // category tag read as the same kind of colour.
  const tint = $derived(
    isDark()
      ? `oklch(0.8 0.11 ${hue(connection)})`
      : `oklch(0.56 0.14 ${hue(connection)})`,
  )
</script>

<Mark {logo} fallback={letters} {tint} />
