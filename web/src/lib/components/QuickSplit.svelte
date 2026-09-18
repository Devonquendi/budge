<script lang="ts">
  import { api, errorMessage, type ChargeRequest, type Transaction } from '../api'
  import { formatCents, toCents } from '../money'
  import { refresh } from '../people.svelte'
  import { shareUrl } from '../requests'
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
        chosen.map((email) => ({ email })),
        includeMe,
        transaction.id,
      )
      // Anyone new is a contact now, so the next split offers them as a chip.
      await refresh()
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
    <form onsubmit={send}>
      <div class="who">
        <span class="eyebrow">Who owes a share of {title}</span>
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
