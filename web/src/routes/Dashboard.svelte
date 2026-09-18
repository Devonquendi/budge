<script lang="ts">
  import AccountList from '../lib/components/AccountList.svelte'
  import Link from '../lib/components/Link.svelte'
  import MerchantBadge from '../lib/components/MerchantBadge.svelte'
  import Panel from '../lib/components/Panel.svelte'
  import QuickSplit from '../lib/components/QuickSplit.svelte'
  import SpendingBreakdown from '../lib/components/SpendingBreakdown.svelte'
  import Summary from '../lib/components/Summary.svelte'
  import { categoryColor } from '../lib/categories'
  import { format, formatCents, toCents } from '../lib/money'
  import { navigate } from '../lib/router.svelte'
  import { monthlySpend, totalSpend } from '../lib/spending'
  import { stage } from '../lib/split.svelte'
  import { getWorkspace } from '../lib/workspace.svelte'

  const workspace = getWorkspace()

  const RECENT = 9

  // Most bills get noticed here rather than on the ledger, so the same one-row
  // split lives on this card. One at a time, as on the ledger.
  let splitting = $state('')

  const asAt = new Intl.DateTimeFormat('en-NZ', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  })

  const shortDate = new Intl.DateTimeFormat('en-NZ', {
    day: '2-digit',
    month: 'short',
  })

  const recent = $derived(workspace.transactions.slice(0, RECENT))

  /**
   * The breakdown covers one currency. With more than one in play that's the
   * one with the most accounts behind it, and the card's header names it.
   */
  const primary = $derived(
    [...workspace.totals].sort((a, b) => b.count - a.count)[0]?.currency ?? 'NZD',
  )

  const spend = $derived(monthlySpend(workspace.transactions, primary))
</script>

<div class="page">
  <div class="head">
    <div class="titles">
      <h1>Dashboard</h1>
      <p class="muted sub">
        {#if workspace.loadedAt}
          Balances as at {asAt.format(workspace.loadedAt)}
        {:else}
          Loading your balances&hellip;
        {/if}
      </p>
    </div>
    <button
      type="button"
      class="secondary outline"
      onclick={() => workspace.load()}
      disabled={workspace.loadingAccounts || workspace.loadingTransactions}
    >
      {workspace.loadingAccounts || workspace.loadingTransactions
        ? 'Refreshing…'
        : 'Refresh'}
    </button>
  </div>

  {#if workspace.accountsError}
    <p class="error">Couldn't load your accounts: {workspace.accountsError}</p>
  {/if}

  {#if workspace.ready}
    <Summary
      totals={workspace.totals}
      accounts={workspace.dashboardAccounts}
      transactions={workspace.transactions}
    />

    <div class="panels">
      <div class="stack">
        <Panel title="Accounts">
          {#snippet action()}
            <Link href="/settings" class="more">Manage</Link>
          {/snippet}

          <AccountList accounts={workspace.dashboardAccounts} />

          {#snippet footer()}
            {#if workspace.hiddenCount > 0}
              <span>
                {workspace.hiddenCount}
                {workspace.hiddenCount === 1 ? 'account' : 'accounts'} hidden from dashboard
              </span>
            {:else}
              <span>Every account is on the dashboard</span>
            {/if}
          {/snippet}
        </Panel>

        <Panel title="Spending this month" padded>
          {#snippet action()}
            <span class="total numeric">
              {formatCents(totalSpend(spend), primary)}
            </span>
          {/snippet}

          <SpendingBreakdown slices={spend} currency={primary} />
        </Panel>
      </div>

      <div class="stack">
        <Panel title="Recent activity">
          {#snippet action()}
            <Link href="/transactions" class="more">All transactions</Link>
          {/snippet}

          <ul class="recent">
            {#each recent as transaction (transaction.id)}
              {@const cents = toCents(transaction.amount)}
              <li>
                <MerchantBadge {transaction} />
                <span class="what">
                  {transaction.merchant?.name ?? transaction.description}
                </span>
                <span class="when numeric">
                  {shortDate.format(new Date(transaction.date))}
                </span>
                <span
                  class="cat"
                  style:--accent={categoryColor(transaction.category?.name)}
                >
                  {transaction.category?.name ?? 'Uncategorised'}
                </span>
                <span class={['sum', 'numeric', { incoming: cents > 0 }]}>
                  {cents > 0 ? '+' : ''}{format(transaction.amount, transaction.currency)}
                </span>
                <span class="act">
                  {#if cents < 0}
                    <button
                      type="button"
                      class="secondary outline"
                      aria-expanded={splitting === transaction.id}
                      onclick={() =>
                        (splitting = splitting === transaction.id ? '' : transaction.id)}
                    >
                      Split
                    </button>
                  {/if}
                </span>
              </li>

              {#if splitting === transaction.id}
                <li class="opened">
                  <QuickSplit
                    {transaction}
                    onclose={() => (splitting = '')}
                    onfull={(picked) => {
                      splitting = ''
                      stage(picked)
                      navigate('/requests')
                    }}
                  />
                </li>
              {/if}
            {:else}
              <li class="none muted">
                {workspace.transactionsError || 'No transactions yet'}
              </li>
            {/each}
          </ul>
        </Panel>
      </div>
    </div>
  {:else if !workspace.accountsError}
    <p aria-busy="true">Loading&hellip;</p>
  {/if}
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    /* Wide enough for two columns of ledger rows and no wider: past this the
       numbers drift so far from their labels that the page stops reading.
       Centred, so the spare width falls either side rather than all of it
       piling up to the right of the page. */
    max-width: 60rem;
    margin-inline: auto;
  }

  .head {
    display: flex;
    align-items: flex-end;
    gap: 0.875rem;
    flex-wrap: wrap;
  }

  .titles {
    margin-right: auto;
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

  /*
   * Two columns, or one until there is room for two. 26rem is what a digest
   * row needs before the merchant names start ellipsing: the date, category
   * and amount columns are fixed, so everything a narrow column costs comes
   * out of the name.
   *
   * The panels are grouped into stacks rather than placed individually because
   * grid rows are as tall as their tallest cell: on its own, a short panel next
   * to the ledger would leave the gap under it empty.
   */
  .panels {
    display: grid;
    /* min() because the minimum in minmax() is a floor, not a wish: a bare
       26rem is wider than a phone and pushes the page sideways. */
    grid-template-columns: repeat(auto-fit, minmax(min(26rem, 100%), 1fr));
    gap: 0.625rem;
    align-items: start;
  }

  .stack {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
    min-width: 0;
  }

  .panels :global(.more) {
    font-size: var(--text-meta);
    font-weight: 500;
    text-decoration: none;
    white-space: nowrap;
  }

  .total {
    font-family: var(--font-mono);
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  .recent {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .recent li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.6875rem;
  }

  .recent li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .act {
    flex: none;
    /* Held open whether or not the row has a button, so the amounts above and
       below it stay in one column. */
    min-width: 3.25rem;
    text-align: right;
  }

  .act button {
    padding: 0.125rem 0.4375rem;
    font-size: var(--text-micro);
  }

  .recent li.opened {
    display: block;
    padding: 0;
  }

  /* Fixed widths from here to the amount, so the date and the figure line up
     down the card however long the category is. */
  .when {
    flex: none;
    width: 3rem;
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    white-space: nowrap;
    color: var(--ctp-overlay0);
  }

  .what {
    min-width: 0;
    margin-right: auto;
    font-size: var(--text-label);
    font-weight: 500;
    line-height: 1.35;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* A tint of the category's colour rather than a full tag: this is a digest,
     and a column of pills would shout over the amounts. */
  .cat {
    flex: none;
    width: 6rem;
    font-size: var(--text-meta);
    color: var(--accent);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .sum {
    flex: none;
    width: 5.5rem;
    text-align: right;
    font-size: var(--text-label);
    font-weight: 600;
  }

  .incoming {
    color: var(--ctp-green);
  }

  .recent li.none {
    justify-content: center;
    padding-block: 1.5rem;
    font-size: var(--text-label);
  }

  @media (max-width: 26rem) {
    .cat {
      display: none;
    }
  }
</style>
