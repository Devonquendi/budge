<script lang="ts">
  import { api, errorMessage, type ChargeRequest, type Inbox } from '../lib/api'
  import Panel from '../lib/components/Panel.svelte'
  import RequestRow from '../lib/components/RequestRow.svelte'
  import { formatCents } from '../lib/money'
  import { shareUrl } from '../lib/requests'

  let inbox = $state.raw<Inbox | null>(null)
  let error = $state('')
  let busy = $state(false)

  let title = $state('')
  let amount = $state('')
  let people = $state('')
  let includeMe = $state(true)
  let justCreated = $state.raw<ChargeRequest[]>([])

  // One address per line or comma, so a flat can be pasted in whole.
  const payees = $derived(
    people
      .split(/[\n,]/)
      .map((entry) => entry.trim())
      .filter(Boolean),
  )

  const share = $derived(
    amount && payees.length
      ? Math.round(
          (Number(amount.replace(/[^0-9.]/g, '')) * 100) /
            (payees.length + (includeMe ? 1 : 0)),
        )
      : 0,
  )

  async function load() {
    try {
      inbox = await api.requests()
    } catch (failure) {
      error = errorMessage(failure)
    }
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      justCreated = await api.splitBill(
        title,
        amount,
        payees.map((email) => ({ email })),
        includeMe,
      )
      title = ''
      amount = ''
      people = ''
      await load()
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  async function act(request: ChargeRequest, side: 'sent' | 'received', action: string) {
    busy = true
    error = ''
    try {
      if (side === 'sent') {
        await api.asCreator(request.id, action as 'confirm' | 'cancel' | 'reopen')
      } else {
        await api.asPayee(request.token, action as 'mark-paid' | 'decline')
      }
      await load()
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  load()
</script>

<div class="page">
  <div class="totals">
    <Panel title="To collect" padded>
      <p class="figure numeric">
        {formatCents(inbox?.to_collect.outstanding ?? 0, 'NZD')}
      </p>
      <p class="muted meta">
        {inbox?.sent.length ?? 0} sent · {formatCents(
          inbox?.to_collect.settled ?? 0,
          'NZD',
        )} settled
      </p>
    </Panel>
    <Panel title="To pay" padded>
      <p class="figure numeric">{formatCents(inbox?.to_pay.outstanding ?? 0, 'NZD')}</p>
      <p class="muted meta">
        {inbox?.received.length ?? 0} received · {formatCents(
          inbox?.to_pay.settled ?? 0,
          'NZD',
        )} settled
      </p>
    </Panel>
  </div>

  <Panel title="Ask for money" padded>
    <form onsubmit={submit}>
      <label>
        <span>What for</span>
        <input bind:value={title} placeholder="Power, August" required maxlength="80" />
      </label>
      <label>
        <span>Total</span>
        <input bind:value={amount} placeholder="$186.40" required inputmode="decimal" />
      </label>
      <label class="wide">
        <span>Who owes a share</span>
        <textarea
          bind:value={people}
          rows="2"
          placeholder="neve@example.com, tipene@example.com"
          required></textarea>
      </label>
      <label class="check">
        <input type="checkbox" bind:checked={includeMe} />
        <span>Count me as one of the shares</span>
      </label>

      <p class="preview muted">
        {#if share > 0}
          {payees.length}
          {payees.length === 1 ? 'person' : 'people'} at about {formatCents(share, 'NZD')} each.
          Any odd cent stays with you.
        {:else}
          Split to the exact cent, with the remainder rounded onto your own share.
        {/if}
      </p>

      <button type="submit" disabled={busy || !payees.length}>
        {busy ? 'Sending…' : 'Send requests'}
      </button>
    </form>

    {#if justCreated.length}
      <div class="fresh">
        <p class="eyebrow">Send these links</p>
        {#each justCreated as request (request.token)}
          <p class="link">
            <span class="muted">{request.payee_email}</span>
            <code>{shareUrl(request.token)}</code>
          </p>
        {/each}
      </div>
    {/if}
  </Panel>

  {#if error}<p class="error">{error}</p>{/if}

  <div class="columns">
    <Panel title="Owed to you">
      {#if inbox?.sent.length}
        {#each inbox.sent as request (request.id)}
          <RequestRow
            {request}
            side="sent"
            {busy}
            onact={(action) => act(request, 'sent', action)}
          />
        {/each}
      {:else}
        <p class="empty muted">Nothing outstanding.</p>
      {/if}
    </Panel>

    <Panel title="You've been asked">
      {#if inbox?.received.length}
        {#each inbox.received as request (request.id)}
          <RequestRow
            {request}
            side="received"
            {busy}
            onact={(action) => act(request, 'received', action)}
          />
        {/each}
      {:else}
        <p class="empty muted">Nobody's asking you for anything.</p>
      {/if}
    </Panel>
  </div>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .figure {
    margin: 0.3125rem 0 0;
    font-size: 1.375rem;
    font-weight: 600;
    line-height: 1.1;
  }

  .meta {
    margin: 0.1875rem 0 0;
    font-size: var(--text-meta);
  }

  .totals,
  .columns {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
    gap: 0.75rem;
  }

  form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr));
    gap: 0.5rem;
    align-items: end;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--pico-muted-color);
  }

  .wide,
  .check,
  .preview,
  form button {
    grid-column: 1 / -1;
  }

  .check {
    flex-direction: row;
    align-items: center;
    gap: 0.4375rem;
  }

  .check input {
    width: auto;
    margin: 0;
  }

  input,
  textarea {
    margin: 0;
  }

  .preview {
    margin: 0;
    font-size: var(--text-meta);
  }

  form button {
    width: auto;
    justify-self: start;
    margin: 0;
  }

  .fresh {
    margin-top: 0.875rem;
    padding-top: 0.75rem;
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  .link {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin: 0 0 0.25rem;
    font-size: var(--text-meta);
  }

  code {
    font-size: var(--text-meta);
  }

  .empty {
    padding: 0.75rem 0.875rem;
    margin: 0;
    font-size: var(--text-meta);
  }
</style>
