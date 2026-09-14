<script lang="ts">
  import { badge, hue } from '../accounts'
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
</script>

<Mark {logo} fallback={letters} tint="oklch(0.7 0.12 {hue(connection)})" />
