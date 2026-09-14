<script lang="ts">
  import TransactionList from '../lib/components/TransactionList.svelte'
  import { formatCents, toCents } from '../lib/money'
  import { prefs } from '../lib/prefs.svelte'
  import { RANGES, getWorkspace } from '../lib/workspace.svelte'

  const workspace = getWorkspace()

  const PAGE = 25

  const ALL_CATEGORIES = 'All categories'
  const ALL_ACCOUNTS = 'All accounts'

  let search = $state('')
  let category = $state(ALL_CATEGORIES)
  let account = $state(ALL_ACCOUNTS)
  let shown = $state(PAGE)

  const spanFormat = new Intl.DateTimeFormat('en-NZ', {
    day: 'numeric',
    month: 'short',
  })

  /** Every category present in the window, so the filter can't offer a dead option. */
  const categories = $derived([
    ALL_CATEGORIES,
    ...[
      ...new Set(workspace.transactions.map((t) => t.category?.name ?? 'Uncategorised')),
    ].sort(),
  ])

  const accounts = $derived([
    ALL_ACCOUNTS,
    ...[...new Set(workspace.transactions.map((t) => t.account_name))].sort(),
  ])

  const filtered = $derived.by(() => {
    const needle = search.trim().toLowerCase()

    return workspace.transactions.filter((transaction) => {
      if (category !== ALL_CATEGORIES) {
        if ((transaction.category?.name ?? 'Uncategorised') !== category) return false
      }
      if (account !== ALL_ACCOUNTS && transaction.account_name !== account) return false
      if (!needle) return true

      // Both the merchant and the bank's own line, since which one you
      // remember depends on the transaction.
      const merchant = transaction.merchant?.name?.toLowerCase() ?? ''
      return (
        merchant.includes(needle) ||
        transaction.description.toLowerCase().includes(needle)
      )
    })
  })

  const visible = $derived(filtered.slice(0, shown))

  /**
   * In, out and net across everything the filters left, not just what's on
   * screen. Split by currency and never summed across them, the same rule the
   * account totals follow. A figure adding NZD to AUD would mean nothing.
   */
  const flows = $derived.by(() => {
    const byCurrency = new Map<string, { incoming: number; outgoing: number }>()

    for (const transaction of filtered) {
      let flow = byCurrency.get(transaction.currency)
      if (!flow) {
        flow = { incoming: 0, outgoing: 0 }
        byCurrency.set(transaction.currency, flow)
      }

      const cents = toCents(transaction.amount)
      if (cents > 0) flow.incoming += cents
      else flow.outgoing += cents
    }

    return [...byCurrency].map(([currency, flow]) => ({
      currency,
      ...flow,
      net: flow.incoming + flow.outgoing,
    }))
  })

  /** The dates the window actually covers, which is tidier than "last 90 days". */
  const span = $derived.by(() => {
    if (filtered.length === 0) return ''
    const dates = filtered.map((t) => new Date(t.date).getTime())
    const from = spanFormat.format(new Date(Math.min(...dates)))
    const to = spanFormat.format(new Date(Math.max(...dates)))
    return from === to ? from : `${from} – ${to}`
  })

  function refilter(change: () => void) {
    change()
    shown = PAGE
  }
</script>

<div class="page">
  <div class="titles">
    <h1>Transactions</h1>
    <p class="muted sub">
      {#if workspace.transactionsError}
        Couldn't load your transactions
      {:else if filtered.length}
        {filtered.length}
        {filtered.length === 1 ? 'transaction' : 'transactions'}
        {#if span}· {span}{/if}
      {:else}
        No transactions in this range
      {/if}
    </p>
  </div>

  <div class="controls">
    <div class="segmented" role="group" aria-label="Date range">
      {#each RANGES as range (range.days)}
        <button
          type="button"
          class={range.days === workspace.days ? 'on' : ''}
          aria-pressed={range.days === workspace.days}
          onclick={() => refilter(() => workspace.loadTransactions(range.days))}
        >
          {range.label}
        </button>
      {/each}
    </div>

    <input
      type="search"
      class="search"
      placeholder="Search merchant"
      aria-label="Search merchant"
      value={search}
      oninput={(event) => {
        const { value } = event.currentTarget
        refilter(() => (search = value))
      }}
    />

    <select
      aria-label="Filter by category"
      value={category}
      onchange={(event) => {
        const { value } = event.currentTarget
        refilter(() => (category = value))
      }}
    >
      {#each categories as name (name)}
        <option>{name}</option>
      {/each}
    </select>

    <select
      aria-label="Filter by account"
      value={account}
      onchange={(event) => {
        const { value } = event.currentTarget
        refilter(() => (account = value))
      }}
    >
      {#each accounts as name (name)}
        <option>{name}</option>
      {/each}
    </select>

    <div class="flows">
      {#each flows as flow (flow.currency)}
        <p class="flow">
          {#if flows.length > 1}<span class="currency">{flow.currency}</span>{/if}
          <span
            >In <b class="numeric in">{formatCents(flow.incoming, flow.currency)}</b
            ></span
          >
          <span>
            Out <b class="numeric"
              >{formatCents(Math.abs(flow.outgoing), flow.currency)}</b
            >
          </span>
          <span>
            Net
            <b class="numeric">
              {flow.net > 0 ? '+' : ''}{formatCents(flow.net, flow.currency)}
            </b>
          </span>
        </p>
      {/each}
    </div>
  </div>

  {#if workspace.transactionsError}
    <p class="error">Couldn't load your transactions: {workspace.transactionsError}</p>
  {:else if workspace.transactions.length === 0 && workspace.loadingTransactions}
    <p aria-busy="true">Loading&hellip;</p>
  {:else}
    <div class={{ stale: workspace.loadingTransactions }}>
      <TransactionList transactions={visible} grouped={prefs().groupByDay}>
        {#snippet footer()}
          <span class="count">
            Showing {visible.length} of {filtered.length}
          </span>
          {#if visible.length < filtered.length}
            <button
              type="button"
              class="secondary outline"
              onclick={() => (shown += PAGE)}
            >
              Load more
            </button>
          {/if}
        {/snippet}
      </TransactionList>
    </div>
  {/if}
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.6875rem;
  }

  h1 {
    margin: 0;
    line-height: 1.25;
  }

  .sub {
    margin: 0.125rem 0 0;
    font-size: var(--text-label);
    line-height: 1.4;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  /*
   * A pill group rather than three buttons: it reads as one choice. The role
   * is worth keeping for screen readers, but Pico styles [role=group] as a bar
   * of joined, full-width buttons, hence the four undos below.
   */
  .segmented {
    display: flex;
    gap: 0.125rem;
    width: auto;
    margin-bottom: 0;
    padding: 0.125rem;
    background: var(--ctp-surface0);
    border-radius: var(--pico-border-radius);
  }

  .segmented > button {
    flex: 0 0 auto;
    padding: 0.25rem 0.625rem;
    border: 0;
    border-radius: 0.375rem;
    background: transparent;
    /*
     * --ctp-*, not --pico-color: inside a button Pico rebinds --pico-color to
     * --pico-primary-inverse, so reading it here paints the label near-white
     * on the near-white active pill.
     */
    color: var(--ctp-subtext0);
    box-shadow: none;
  }

  .segmented > button:hover {
    color: var(--ctp-text);
  }

  .segmented > button.on {
    background: var(--pico-card-background-color);
    color: var(--ctp-text);
    box-shadow: 0 1px 2px color-mix(in srgb, var(--ctp-crust) 45%, transparent);
  }

  .search {
    flex: 1;
    min-width: 9rem;
    max-width: 16rem;
  }

  select {
    width: auto;
  }

  .flows {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.125rem;
    margin-left: auto;
  }

  .flow {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin: 0;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  .currency {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ctp-overlay0);
  }

  .flows b {
    font-weight: 600;
    color: var(--pico-color);
  }

  .flows .in {
    color: var(--ctp-green);
  }

  .count {
    margin-right: auto;
  }

  /* Dim the old rows while a new range loads, rather than blanking the page. */
  .stale {
    opacity: 0.4;
    transition: opacity 0.15s;
  }

  /* On a phone the summary gets its own line rather than squeezing the search
     box down to nothing. */
  @media (max-width: 40rem) {
    /* Its own row: sharing one with a select leaves it too narrow to read the
       placeholder, let alone a query. */
    .search {
      flex: 1 1 100%;
      max-width: none;
    }

    select {
      flex: 1 1 8rem;
    }

    .flows {
      width: 100%;
      margin-left: 0;
      align-items: stretch;
    }

    .flow {
      justify-content: space-between;
    }
  }
</style>
