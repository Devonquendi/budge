<script lang="ts">
  import { api, errorMessage, type ChargeRequest, type Transaction } from '../api'
  import { formatCents, toCents } from '../money'
  import { named, refresh } from '../people.svelte'
  import { refresh as refreshSplits, splitOf } from '../splits.svelte'
  import { look, shareUrl } from '../requests'
  import PeoplePicker from './PeoplePicker.svelte'

  // Splitting where you spotted the spend, without losing your place in the
  // ledger. The full form is one click away for anything this can't do:
  // a different amount, a different description, splitting part of a bill.
  let {
    transaction,
    onclose,
    onfull,
  }: {
    transaction: Transaction
    onclose: () => void
    /** Hands the transaction to the request page instead. */
    onfull: (transaction: Transaction) => void
  } = $props()

  let chosen = $state<string[]>([])
  let includeMe = $state(true)
  let busy = $state(false)
  let error = $state('')
  let sent = $state.raw<ChargeRequest[]>([])
  let copied = $state(false)

  const title = $derived(transaction.merchant?.name ?? transaction.description)

  // What was already asked for this transaction, so asking again is a decision
  // rather than a guess. Opening a blank form over the top of four outstanding
  // requests is how somebody ends up owing for one coffee twice.
  const already = $derived(splitOf(transaction.id))

  let copiedShare = $state(0)

  async function copyShare(share: { id: number; token: string }) {
    await navigator.clipboard.writeText(shareUrl(share.token))
    copiedShare = share.id
    setTimeout(() => (copiedShare = 0), 1500)
  }
  const total = $derived(Math.abs(toCents(transaction.amount)))

  const share = $derived(
    chosen.length ? Math.round(total / (chosen.length + (includeMe ? 1 : 0))) : 0,
  )

  async function send(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      sent = await api.splitBill(
        title,
        String(total / 100),
        named(chosen),
        includeMe,
        transaction.id,
      )
      // Anyone new is a contact now, so the next split offers them as a chip,
      // and the row this came from should say it has been split.
      await refresh()
      await refreshSplits()
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  async function copyLinks() {
    await navigator.clipboard.writeText(
      sent
        .map((request) => `${request.payee_email} ${shareUrl(request.token)}`)
        .join('\n'),
    )
    copied = true
    setTimeout(() => (copied = false), 1500)
  }
</script>

<div class="quick">
  {#if sent.length}
    <p class="done">
      <strong>Asked {sent.length} {sent.length === 1 ? 'person' : 'people'}</strong>
      for {formatCents(sent[0].amount_cents, 'NZD')} each.
      <button type="button" class="secondary outline" onclick={copyLinks}>
        {copied ? 'Copied' : 'Copy links'}
      </button>
      <button type="button" class="secondary outline" onclick={onclose}>Done</button>
    </p>
  {:else}
    {#if already}
      <div class="already">
        <p class="eyebrow">
          Already asked · {formatCents(already.outstanding_cents, 'NZD')} of
          {formatCents(already.asked_cents, 'NZD')} still owed
        </p>
        <ul>
          {#each already.shares as share (share.id)}
            <li>
              <span class="name">{share.who}</span>
              <span class="numeric">{formatCents(share.amount_cents, 'NZD')}</span>
              <span class={['pill', look(share.state).tone]}
                >{look(share.state).label}</span
              >
              <button
                type="button"
                class="secondary outline"
                onclick={() => copyShare(share)}
              >
                {copiedShare === share.id ? 'Copied' : 'Link'}
              </button>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <form onsubmit={send}>
      <div class="who">
        <span class="eyebrow">
          {already ? 'Ask someone else for' : 'Who owes a share of'}
          {title}
        </span>
        <PeoplePicker bind:chosen autofocus />
      </div>

      <label class="me">
        <input type="checkbox" bind:checked={includeMe} />
        <span>Count me</span>
      </label>

      <button type="submit" disabled={busy || !chosen.length}>
        {busy ? 'Sending…' : `Send${chosen.length ? ` to ${chosen.length}` : ''}`}
      </button>

      <p class="sum muted">
        {#if share > 0}
          {formatCents(share, 'NZD')} each out of {formatCents(total, 'NZD')}. Any odd
          cent stays with you.
        {:else}
          {formatCents(total, 'NZD')} to split. Split to the exact cent.
        {/if}
        <button type="button" class="link" onclick={() => onfull(transaction)}>
          More options
        </button>
        <button type="button" class="link" onclick={onclose}>Cancel</button>
      </p>

      {#if error}<p class="error">{error}</p>{/if}
    </form>
  {/if}
</div>

<style>
  .quick {
    padding: 0.5rem 0.6875rem 0.625rem;
    background: var(--ctp-recessed);
  }

  form {
    display: flex;
    flex-wrap: wrap;
    align-items: end;
    gap: 0.5rem;
  }

  .already {
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  .already ul {
    margin: 0.3125rem 0 0;
    padding: 0;
    list-style: none;
  }

  .already li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4375rem;
    padding: 0.125rem 0;
    font-size: var(--text-meta);
  }

  .already .name {
    font-weight: 600;
  }

  .already button {
    width: auto;
    margin: 0 0 0 auto;
    padding: 0.0625rem 0.4375rem;
    font-size: var(--text-micro);
  }

  .pill {
    padding: 0.0625rem 0.375rem;
    border-radius: 999px;
    font-size: var(--text-micro);
    font-weight: 500;
    background: var(--ctp-surface0);
    color: var(--pico-muted-color);
  }

  .claimed {
    background: color-mix(in oklab, var(--ctp-yellow) 22%, transparent);
    color: var(--ctp-yellow);
  }

  .good {
    background: color-mix(in oklab, var(--ctp-green) 22%, transparent);
    color: var(--ctp-green);
  }

  .bad {
    background: color-mix(in oklab, var(--ctp-red) 20%, transparent);
    color: var(--ctp-red);
  }

  .who {
    display: flex;
    flex: 1 1 14rem;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0;
    min-width: 0;
  }

  .me {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin: 0 0 0.4375rem;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  .me input {
    margin: 0;
  }

  form > button[type='submit'] {
    margin: 0 0 0.1875rem;
  }

  .sum,
  .done {
    flex-basis: 100%;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: var(--text-meta);
  }

  /* A button that reads as a link: these are asides, not actions of equal
     weight to Send. */
  .link {
    padding: 0;
    background: none;
    border: none;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
    text-decoration: underline;
  }

  .done button {
    padding: 0.125rem 0.5rem;
    font-size: var(--text-meta);
  }

  .error {
    flex-basis: 100%;
    margin: 0;
    font-size: var(--text-meta);
  }
</style>
