<script lang="ts">
  import { api, errorMessage, type ChargeRequest } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import { formatCents } from '../lib/money'
  import { navigate } from '../lib/router.svelte'

  /**
   * A bank that does not exist, so one-tap can be shown before there is a real
   * one to tap.
   *
   * Nothing here moves money and nothing here talks to a bank. Approving does
   * exactly what the payer pressing "I've paid this" does, because in the demo
   * the claim is what puts the money in the other person's feed. It exists to
   * show the shape of the flow: leave the request, approve in your bank, come
   * back settled.
   *
   * Only reachable while the demo is switched on. Off it, the route is a dead
   * end, which is the point: this must never stand between anyone and a real
   * payment.
   */
  let { token }: { token: string } = $props()

  let charge = $state.raw<ChargeRequest | null>(null)
  let busy = $state(true)
  let error = $state('')

  async function load() {
    try {
      const [request, personas] = await Promise.all([
        api.requestByToken(token),
        api.personas(),
      ])
      if (!personas.length) {
        error = 'There is no stand-in bank on this deployment.'
      } else {
        charge = request
      }
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  async function approve() {
    busy = true
    try {
      await api.asPayee(token, 'mark-paid', 'Approved in the stand-in bank')
      navigate(`/r/${token}`)
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }

  load()
</script>

<AuthCard width="22rem">
  <p class="bank">Kowhai Bank</p>

  {#if busy && !charge}
    <p class="muted">Loading…</p>
  {:else if error}
    <p class="error">{error}</p>
    <button
      type="button"
      class="secondary outline"
      onclick={() => navigate(`/r/${token}`)}
    >
      Back to the request
    </button>
  {:else if charge}
    <p class="lead">Approve this payment?</p>
    <p class="amount numeric">{formatCents(charge.amount_cents, 'NZD')}</p>

    <dl>
      <div>
        <dt>To</dt>
        <dd>{charge.pay_to?.name ?? charge.from_name}</dd>
      </div>
      {#if charge.pay_to}
        <div>
          <dt>Account</dt>
          <dd class="numeric">{charge.pay_to.account}</dd>
        </div>
        <div>
          <dt>Reference</dt>
          <dd>{charge.pay_to.reference}</dd>
        </div>
      {/if}
      <div>
        <dt>From</dt>
        <dd>Everyday account</dd>
      </div>
    </dl>

    <div class="actions">
      <button type="button" disabled={busy} onclick={approve}>
        {busy ? 'Approving…' : 'Approve'}
      </button>
      <button
        type="button"
        class="secondary outline"
        disabled={busy}
        onclick={() => navigate(`/r/${token}`)}
      >
        Cancel
      </button>
    </div>

    <p class="warn">
      This is not a bank. Nothing is moving. It stands in for the approval screen a real
      bank would show, so the rest of the flow can be seen end to end.
    </p>
  {/if}
</AuthCard>

<style>
  .bank {
    margin: 0 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
    font-size: var(--text-label);
    font-weight: 700;
    letter-spacing: 0.01em;
  }

  .lead {
    margin: 0;
    font-size: var(--text-label);
    color: var(--pico-muted-color);
  }

  .amount {
    margin: 0.125rem 0 0.625rem;
    font-size: 1.75rem;
    font-weight: 600;
    line-height: 1.1;
  }

  dl {
    margin: 0;
  }

  dl div {
    display: flex;
    gap: 0.5rem;
    padding: 0.1875rem 0;
    font-size: var(--text-meta);
  }

  dl div + div {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  dt {
    flex: none;
    width: 5rem;
    color: var(--pico-muted-color);
  }

  dd {
    margin: 0;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 600;
  }

  .actions {
    display: flex;
    gap: 0.375rem;
    margin-top: 0.875rem;
  }

  .actions button {
    flex: 1;
    width: auto;
    margin: 0;
  }

  .warn {
    margin: 0.75rem 0 0;
    font-size: var(--text-meta);
    line-height: 1.4;
    color: var(--pico-muted-color);
  }
</style>
