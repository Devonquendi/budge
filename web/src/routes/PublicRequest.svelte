<script lang="ts">
  import { api, errorMessage, type ChargeRequest } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import Link from '../lib/components/Link.svelte'
  import PayDetails from '../lib/components/PayDetails.svelte'
  import { formatCents } from '../lib/money'
  import { check, hasBank } from '../lib/demo.svelte'
  import { look, payeeCanAct } from '../lib/requests'
  import { navigate } from '../lib/router.svelte'

  // The one page in the app that works with no account at all. Whoever holds
  // the link is the payer: that is the whole authentication story here, and it
  // is deliberate. A request is not a secret, it is an ask.
  let { token }: { token: string } = $props()

  let charge = $state.raw<ChargeRequest | null>(null)
  let error = $state('')
  let busy = $state(true)
  let note = $state('')

  const badge = $derived(charge && look(charge.state))

  async function load() {
    try {
      charge = await api.requestByToken(token)
    } catch (failure) {
      error = errorMessage(failure)
    }
    await check()
    busy = false
  }

  async function act(action: 'mark-paid' | 'decline') {
    busy = true
    error = ''
    try {
      charge = await api.asPayee(token, action, note)
      note = ''
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  load()
</script>

<AuthCard width="23rem">
  {#if busy && !charge}
    <p class="muted">Looking that up…</p>
  {:else if !charge}
    <h1>No such request</h1>
    <p class="muted">That link doesn't point at anything. Check it and try again.</p>
    {#if error}<p class="error">{error}</p>{/if}
  {:else}
    <p class="eyebrow">{charge.from_name} is asking for</p>
    <p class="amount numeric">{formatCents(charge.amount_cents, 'NZD')}</p>
    <p class="what">
      Your share of <strong>{charge.title}</strong>, which came to
      {formatCents(charge.bill_total_cents, 'NZD')}.
    </p>

    <p class={['pill', badge?.tone]}>{badge?.label}</p>

    {#if charge.pay_to && payeeCanAct(charge.state)}
      <div class="how">
        <PayDetails payTo={charge.pay_to} cents={charge.amount_cents} />
      </div>
    {:else if payeeCanAct(charge.state)}
      <p class="muted small">
        {charge.from_name} hasn't said where to pay yet. Settle it however you usually do, then
        say so below.
      </p>
    {/if}

    {#if payeeCanAct(charge.state)}
      <label>
        <span>Anything to add?</span>
        <input bind:value={note} maxlength="200" placeholder="Paid it this morning" />
      </label>
      {#if hasBank() && charge.pay_to && charge.state === 'open'}
        <div class="one-tap">
          <button
            type="button"
            disabled={busy}
            onclick={() => navigate(`/bank/${token}`)}
          >
            Pay {formatCents(charge.amount_cents, 'NZD')} now
          </button>
        </div>
        <p class="muted small">Approve it in your bank. Takes one tap.</p>
      {/if}

      <div class="actions">
        {#if charge.state === 'open'}
          <button
            type="button"
            class="secondary outline"
            disabled={busy}
            onclick={() => act('mark-paid')}
          >
            {hasBank() ? 'I paid another way' : "I've paid this"}
          </button>
        {/if}
        <button
          type="button"
          class="secondary outline"
          disabled={busy}
          onclick={() => act('decline')}
        >
          This isn't mine
        </button>
      </div>
      <p class="muted small">
        {charge.from_name} still has to confirm the money arrived. Nothing here moves it.
      </p>
    {:else if charge.state === 'confirmed'}
      <p class="muted small">{charge.from_name} confirmed this arrived. Nothing to do.</p>
    {:else}
      <p class="muted small">This request was cancelled.</p>
    {/if}

    {#if error}<p class="error">{error}</p>{/if}
  {/if}

  {#snippet below()}
    <Link href="/login">Sign in to budge</Link>
  {/snippet}
</AuthCard>

<style>
  h1 {
    margin: 0 0 0.25rem;
    font-size: 1rem;
  }

  .amount {
    margin: 0.25rem 0 0;
    font-size: 1.75rem;
    font-weight: 600;
    line-height: 1.1;
  }

  .what {
    margin: 0.375rem 0 0;
    font-size: var(--text-label);
    line-height: 1.45;
  }

  .pill {
    display: inline-block;
    margin: 0.625rem 0 0;
    padding: 0.125rem 0.4375rem;
    border-radius: 999px;
    font-size: var(--text-meta);
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

  .how {
    margin-top: 0.75rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0.875rem 0 0;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--pico-muted-color);
  }

  label input {
    margin: 0;
  }

  /* app.css pins every button to width: auto at a specificity this cannot
     reach, so the row stretches the button rather than the button itself. */
  .one-tap {
    display: flex;
    margin-top: 0.875rem;
  }

  .one-tap button {
    flex: 1;
    margin: 0;
    font-size: var(--text-body);
    font-weight: 600;
  }

  .actions {
    display: flex;
    gap: 0.375rem;
    margin-top: 0.5rem;
  }

  .actions button {
    width: auto;
    flex: 1;
    margin: 0;
    font-size: var(--text-label);
  }

  .small {
    margin: 0.625rem 0 0;
    font-size: var(--text-meta);
    line-height: 1.4;
  }
</style>
