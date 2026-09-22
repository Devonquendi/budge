<script lang="ts">
  import type { ChargeRequest } from '../api'
  import { formatCents } from '../money'
  import { look, payeeCanDecline, payeeCanPay, shareUrl } from '../requests'

  let {
    request,
    side,
    onact,
    busy = false,
  }: {
    request: ChargeRequest
    /** 'sent' shows who owes it; 'received' shows who is asking. */
    side: 'sent' | 'received'
    onact: (action: string) => void
    busy?: boolean
  } = $props()

  const badge = $derived(look(request.state))
  const who = $derived(
    side === 'sent'
      ? request.payee_name || request.payee_email
      : `${request.from_name} asked`,
  )

  let copied = $state(false)

  async function copy() {
    await navigator.clipboard.writeText(shareUrl(request.token))
    copied = true
    setTimeout(() => (copied = false), 1500)
  }
</script>

<article>
  <div class="head">
    <div>
      <p class="title">{request.title}</p>
      <p class="who muted">{who}</p>
    </div>
    <p class="amount numeric">{formatCents(request.amount_cents, 'NZD')}</p>
  </div>

  <div class="foot">
    <span class={['pill', badge.tone]}>{badge.label}</span>

    {#if side === 'sent'}
      <button type="button" class="secondary outline" onclick={copy}>
        {copied ? 'Copied' : 'Copy link'}
      </button>
      {#if request.state === 'marked_paid'}
        <button type="button" disabled={busy} onclick={() => onact('confirm')}>
          It arrived
        </button>
      {/if}
      {#if request.state !== 'cancelled' && request.state !== 'confirmed'}
        <button
          type="button"
          class="secondary outline"
          disabled={busy}
          onclick={() => onact('cancel')}
        >
          Cancel
        </button>
      {/if}
      {#if request.state === 'cancelled' || request.state === 'confirmed'}
        <button
          type="button"
          class="secondary outline"
          disabled={busy}
          onclick={() => onact('reopen')}
        >
          Reopen
        </button>
      {/if}
    {:else}
      {#if payeeCanPay(request.state)}
        <button type="button" disabled={busy} onclick={() => onact('mark-paid')}>
          I've paid this
        </button>
      {/if}
      {#if payeeCanDecline(request.state)}
        <button
          type="button"
          class="secondary outline"
          disabled={busy}
          onclick={() => onact('decline')}
        >
          Not mine
        </button>
      {/if}
    {/if}
  </div>
</article>

<style>
  article {
    padding: 0.75rem 0.875rem;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  article:last-child {
    border-bottom: none;
  }

  .head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .title {
    margin: 0;
    font-weight: 600;
    line-height: 1.3;
  }

  .who {
    margin: 0.125rem 0 0;
    font-size: var(--text-meta);
  }

  .amount {
    margin: 0;
    font-weight: 600;
    white-space: nowrap;
  }

  .foot {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.375rem;
    margin-top: 0.5rem;
  }

  .pill {
    padding: 0.125rem 0.4375rem;
    border-radius: 999px;
    font-size: var(--text-meta);
    font-weight: 500;
  }

  .open {
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

  button {
    width: auto;
    margin: 0;
    margin-left: auto;
    padding: 0.25rem 0.625rem;
    font-size: var(--text-meta);
  }

  /* Only the first button pushes right; the rest sit next to it. */
  .foot button ~ button {
    margin-left: 0;
  }
</style>
