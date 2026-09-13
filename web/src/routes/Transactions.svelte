<script lang="ts">
  import { api, ApiError, errorMessage, type History } from '../lib/api'
  import AppShell from '../lib/components/AppShell.svelte'
  import TransactionList from '../lib/components/TransactionList.svelte'
  import { navigate } from '../lib/router.svelte'

  let { onsignout }: { onsignout: () => void } = $props()

  const RANGES = [
    { days: 30, label: '30 days' },
    { days: 90, label: '3 months' },
    { days: 365, label: '12 months' },
  ]

  const DEFAULT_DAYS = 90

  let days = $state(DEFAULT_DAYS)
  let history = $state.raw<History | null>(null)
  let error = $state('')
  let loading = $state(false)

  // How many of the range got a name put to them. Without this the page looks
  // fully categorised as long as you don't scroll.
  const coverage = $derived.by(() => {
    const rows = history?.transactions ?? []
    return { total: rows.length, named: rows.filter((row) => row.category).length }
  })

  async function load(range: number) {
    days = range
    loading = true
    error = ''
    try {
      history = await api.transactions(range)
    } catch (failure) {
      // 409 means the Akahu tokens are gone, so there is nothing to show yet.
      if (failure instanceof ApiError && failure.status === 409) {
        navigate('/onboarding', { replace: true })
      } else {
        error = errorMessage(failure)
      }
    }
    loading = false
  }

  load(DEFAULT_DAYS)
</script>

<AppShell {onsignout}>
  <h1>What came in and what went out</h1>

  <div class="controls" role="group" aria-label="Date range">
    {#each RANGES as range (range.days)}
      <button
        type="button"
        class={range.days === days ? '' : 'secondary outline'}
        aria-pressed={range.days === days}
        onclick={() => load(range.days)}
      >
        {range.label}
      </button>
    {/each}
  </div>

  {#if history}
    {#if coverage.total}
      <p class="coverage muted">
        {coverage.named}/{coverage.total} classified
      </p>
    {/if}

    <div class={{ stale: loading }}>
      <TransactionList transactions={history.transactions} />
    </div>
  {:else if error}
    <p class="error">Couldn't load your transactions: {error}</p>
  {:else}
    <p aria-busy="true">Loading&hellip;</p>
  {/if}
</AppShell>

<style>
  h1 {
    font-size: clamp(1.625rem, 5vw, 2rem);
    margin-bottom: 1.5rem;
  }

  .controls {
    margin-bottom: 1.5rem;
  }

  .controls button {
    margin-bottom: 0;
    font-size: 0.875rem;
  }

  .coverage {
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
  }

  /* Dim the old rows while a new range loads, rather than blanking the page. */
  .stale {
    opacity: 0.4;
    transition: opacity 0.15s;
  }
</style>
