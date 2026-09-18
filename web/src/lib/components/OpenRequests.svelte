<script lang="ts">
  import { api, errorMessage, type Inbox } from '../api'
  import { formatCents } from '../money'
  import Link from './Link.svelte'
  import { look } from '../requests'

  // What money is in flight, on the screen people open first. Not a second
  // requests page: the two figures and the few names, and a way through to the
  // rest of it.
  let inbox = $state.raw<Inbox | null>(null)
  let error = $state('')

  const SHOWN = 4

  const owed = $derived(
    (inbox?.sent ?? [])
      .filter((r) => r.state !== 'confirmed' && r.state !== 'cancelled')
      .slice(0, SHOWN),
  )
  const owing = $derived(
    (inbox?.received ?? [])
      .filter((r) => r.state !== 'confirmed' && r.state !== 'cancelled')
      .slice(0, SHOWN),
  )

  async function load() {
    try {
      inbox = await api.requests()
    } catch (failure) {
      error = errorMessage(failure)
    }
  }

  load()
</script>

{#if error}
  <p class="error line">{error}</p>
{:else if inbox}
  <div class="totals">
    <p>
      <span class="eyebrow">To collect</span>
      <span class="figure numeric"
        >{formatCents(inbox.to_collect.outstanding, 'NZD')}</span
      >
    </p>
    <p>
      <span class="eyebrow">To pay</span>
      <span class="figure numeric">{formatCents(inbox.to_pay.outstanding, 'NZD')}</span>
    </p>
  </div>

  {#if owed.length || owing.length}
    <ul>
      {#each owed as request (request.id)}
        <li>
          <span class="who">{request.payee_name ?? request.payee_email}</span>
          <span class="what muted">{request.title}</span>
          <span class={['pill', look(request.state).tone]}
            >{look(request.state).label}</span
          >
          <span class="sum numeric">{formatCents(request.amount_cents, 'NZD')}</span>
        </li>
      {/each}
      {#each owing as request (request.id)}
        <li>
          <span class="who">{request.from_name}</span>
          <span class="what muted">{request.title}</span>
          <span class={['pill', look(request.state).tone]}
            >{look(request.state).label}</span
          >
          <span class="sum numeric out">-{formatCents(request.amount_cents, 'NZD')}</span>
        </li>
      {/each}
    </ul>
  {:else}
    <p class="line muted">Nothing outstanding either way.</p>
  {/if}
{:else}
  <p class="line muted">Loading…</p>
{/if}

<style>
  .totals {
    display: flex;
    gap: 0.75rem;
    padding: 0.625rem 0.6875rem;
  }

  .totals p {
    flex: 1;
    margin: 0;
  }

  .eyebrow {
    display: block;
  }

  .figure {
    display: block;
    margin-top: 0.1875rem;
    font-size: 1.125rem;
    font-weight: 600;
    line-height: 1.1;
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3125rem 0.6875rem;
    font-size: var(--text-meta);
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .who {
    flex: none;
    font-weight: 600;
  }

  .what {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .pill {
    flex: none;
    padding: 0.0625rem 0.375rem;
    border-radius: 999px;
    font-size: var(--text-micro);
    background: var(--ctp-surface0);
    color: var(--pico-muted-color);
  }

  .claimed {
    background: color-mix(in oklab, var(--ctp-yellow) 22%, transparent);
    color: var(--ctp-yellow);
  }

  .bad {
    background: color-mix(in oklab, var(--ctp-red) 20%, transparent);
    color: var(--ctp-red);
  }

  .sum {
    flex: none;
    font-weight: 600;
  }

  .out {
    color: var(--pico-muted-color);
  }

  .line {
    margin: 0;
    padding: 0.625rem 0.6875rem;
    font-size: var(--text-meta);
  }
</style>
