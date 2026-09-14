<script lang="ts">
  import type { Transaction } from '../api'
  import { categoryColor } from '../categories'
  import { initial } from '../merchants'
  import Mark from './Mark.svelte'

  let { transaction }: { transaction: Transaction } = $props()
</script>

<!-- No logo leaves the initial of whatever the row is titled with, tinted by
     category so a row still says something about itself at a glance. -->
<Mark
  logo={transaction.merchant?.logo}
  fallback={initial(transaction.merchant?.name ?? transaction.description)}
  tint={categoryColor(transaction.category?.name)}
/>
