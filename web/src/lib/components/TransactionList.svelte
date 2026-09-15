<script lang="ts">
  import type { Snippet } from 'svelte'
  import type { Account, Transaction } from '../api'
  import { categoryColor } from '../categories'
  import { format, toCents } from '../money'
  import BankBadge from './BankBadge.svelte'
  import MerchantBadge from './MerchantBadge.svelte'

  let {
    transactions,
    accounts = [],
    grouped = false,
    footer,
  }: {
    transactions: Transaction[]
    /** Only for the bank mark beside the account column; the name is on the row. */
    accounts?: Account[]
    /** Break the rows into a heading per day, the way a bank statement reads. */
    grouped?: boolean
    footer?: Snippet
  } = $props()

  const byId = $derived(new Map(accounts.map((account) => [account.id, account])))

  const dayFormat = new Intl.DateTimeFormat('en-NZ', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })
  const shortFormat = new Intl.DateTimeFormat('en-NZ', {
    day: '2-digit',
    month: 'short',
  })

  type Day = { key: string; label: string; rows: Transaction[] }

  const days = $derived.by((): Day[] => {
    const groups = new Map<string, Day>()

    for (const transaction of transactions) {
      const date = new Date(transaction.date)
      const key = date.toDateString()
      let day = groups.get(key)
      if (!day) {
        day = { key, label: dayFormat.format(date), rows: [] }
        groups.set(key, day)
      }
      day.rows.push(transaction)
    }

    return [...groups.values()]
  })

  /** The merchant if Akahu or Genie named one, else the bank's own line. */
  function title(transaction: Transaction): string {
    return transaction.merchant?.name ?? transaction.description
  }

  function subtitle(transaction: Transaction): string {
    return transaction.merchant ? transaction.description : ''
  }

  function categoryName(transaction: Transaction): string {
    return transaction.category?.name ?? 'Uncategorised'
  }

  /** Why this row is tagged the way it is: Akahu's word, Genie's guess, or neither. */
  function categoryHint(transaction: Transaction): string {
    const { category } = transaction
    if (!category) return 'No category'
    if (category.source !== 'genie') return 'Categorised by Akahu'
    return `Genie's guess, ${confidencePercent(transaction)}% confident`
  }

  /**
   * Only meaningful for a guess. Printed on the tag itself, not just in the
   * title: a title is a hover tooltip, and touch has no hover to reveal it.
   */
  function confidencePercent(transaction: Transaction): number {
    return Math.round((transaction.category?.confidence ?? 0) * 100)
  }
</script>

{#snippet row(transaction: Transaction)}
  {@const cents = toCents(transaction.amount)}
  {@const account = byId.get(transaction.account_id)}
  <li>
    <span class="who">
      <MerchantBadge {transaction} />
      <span class="text">
        <span class="name">{title(transaction)}</span>
        {#if subtitle(transaction)}
          <span class="desc">{subtitle(transaction)}</span>
        {/if}
      </span>
    </span>

    <span class="meta">
      <span class="date numeric">
        {shortFormat.format(new Date(transaction.date))}
      </span>
      <span class="tag-cell">
        <span
          class={['tag', { guess: transaction.category?.source === 'genie' }]}
          style:--accent={categoryColor(transaction.category?.name)}
          title={categoryHint(transaction)}
        >
          {categoryName(transaction)}
          {#if transaction.category?.source === 'genie'}
            <span class="confidence">· {confidencePercent(transaction)}%</span>
          {/if}
        </span>
      </span>
      <span class="account" title={transaction.account_name}>
        {#if account}
          <BankBadge
            connection={account.connection_name}
            logo={account.connection_logo}
            compact
          />
        {/if}
        <span class="label">{transaction.account_name}</span>
      </span>
    </span>

    <span class={['amount', 'numeric', { incoming: cents > 0 }]}>
      {cents > 0 ? '+' : ''}{format(transaction.amount, transaction.currency)}
    </span>
  </li>
{/snippet}

<section>
  {#if transactions.length === 0}
    <p class="empty muted">No transactions</p>
  {:else if grouped}
    {#each days as day (day.key)}
      <h2 class="eyebrow day">{day.label}</h2>
      <ul>
        {#each day.rows as transaction (transaction.id)}
          {@render row(transaction)}
        {/each}
      </ul>
    {/each}
  {:else}
    <div class="head" aria-hidden="true">
      <span class="who">Merchant</span>
      <span class="meta">
        <span class="date">Date</span>
        <span class="tag-cell">Category</span>
        <span class="account">Account</span>
      </span>
      <span class="amount">Amount</span>
    </div>
    <ul>
      {#each transactions as transaction (transaction.id)}
        {@render row(transaction)}
      {/each}
    </ul>
  {/if}

  {#if footer}
    <footer>{@render footer()}</footer>
  {/if}
</section>

<style>
  section {
    overflow: hidden;
    background: var(--pico-card-background-color);
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  /*
   * Phone layout: the merchant and the amount share the first line, and
   * everything else (date, category, account) runs along a second. The
   * column head is meaningless here, so it's hidden until there are columns.
   */
  .head {
    display: none;
  }

  li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.125rem 0.625rem;
    padding: 0.4375rem 0.6875rem;
  }

  /* Only between rows of the same day: the day heading brings its own rule. */
  li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .who {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 0;
    margin-right: auto;
    /*
     * flex-basis 0, not auto: with auto, a long nowrap description gives this
     * item a huge hypothetical width, and flex-wrap decides line breaks on
     * that hypothetical size before shrinking is applied. That pushed .amount
     * onto its own line even though .who had room to shrink into. Basis 0
     * sidesteps the hypothetical size entirely.
     */
    flex: 1 1 0%;
  }

  .text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .name {
    font-weight: 500;
    line-height: 1.35;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .desc {
    font-size: var(--text-micro);
    line-height: 1.3;
    color: var(--ctp-overlay0);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    width: 100%;
    order: 3;
  }

  .date {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ctp-overlay0);
  }

  .account {
    display: flex;
    align-items: center;
    /* Pinned to the row's right edge, under the amount above it, rather than
       drifting with the category tag's width. */
    margin-left: auto;
    --mark-size: 1.375rem;
  }

  /*
   * The mark carries the account; the name (still on the span's title) only
   * pushed the row's other content around, at every width, since it varies
   * far more in length than a date or a category ever does.
   */
  .account .label {
    display: none;
  }

  .tag {
    display: inline-block;
    padding: 0.0625rem 0.4375rem;
    font-size: var(--text-micro);
    font-weight: 500;
    line-height: 1.5;
    border-radius: 999px;
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent);
  }

  /* Genie's confidence, printed rather than left in the title: a dashed
     border alone doesn't say what it means, and touch has no hover to ask. */
  .confidence {
    font-weight: 400;
    opacity: 0.75;
  }

  /* Genie matched on the description alone, so it's a guess, not a fact. */
  .guess {
    border: var(--pico-border-width) dashed
      color-mix(in srgb, var(--accent) 45%, transparent);
    padding-block: 0;
  }

  .amount {
    flex: none;
    font-weight: 600;
    white-space: nowrap;
  }

  .incoming {
    color: var(--ctp-green);
  }

  h2.day {
    margin: 0;
    padding: 0.375rem 0.6875rem;
    background: var(--ctp-recessed);
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  section > h2.day:first-child {
    border-top: 0;
  }

  .empty {
    padding-block: 2rem;
    text-align: center;
  }

  footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4375rem 0.6875rem;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
    background: var(--ctp-recessed);
  }

  /*
   * Once there's width for it, the rows become real columns. `display: contents`
   * dissolves the .meta wrapper so its three children line up as siblings of
   * the merchant and the amount, and `order` puts the date back at the front.
   */
  @media (min-width: 46rem) {
    .head {
      display: flex;
      align-items: center;
      gap: 0.625rem;
      padding: 0.3125rem 0.6875rem;
      border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
      background: var(--ctp-recessed);
      font-family: var(--font-mono);
      font-size: var(--text-micro);
      font-weight: 500;
      line-height: 1;
      letter-spacing: 0.09em;
      text-transform: uppercase;
      color: var(--pico-muted-color);
    }

    li {
      flex-wrap: nowrap;
      gap: 0.625rem;
    }

    .head .meta,
    li .meta {
      display: contents;
    }

    .head .who,
    li .who {
      order: 2;
    }

    li .text {
      flex-direction: row;
      align-items: baseline;
      gap: 0.4375rem;
    }

    /* The mark the rows carry, so the head sits over its own column. */
    .head .who {
      padding-left: 1.9375rem;
    }

    .date {
      flex: none;
      width: 3rem;
      order: 1;
    }

    .tag-cell {
      flex: none;
      width: 8rem;
      order: 3;
    }

    .account {
      flex: none;
      width: 4rem;
      order: 4;
      justify-content: center;
      /* Its own column here, not the row's trailing edge. */
      margin-left: 0;
    }

    .amount {
      flex: none;
      width: 5.375rem;
      text-align: right;
      order: 5;
    }
  }
</style>
