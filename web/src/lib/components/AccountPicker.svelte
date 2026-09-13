<script lang="ts">
  import { typeLabel } from '../accounts'
  import type { Account } from '../api'
  import { format, toCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import BankBadge from './BankBadge.svelte'

  // Props in, event out: the page owns the selection, this just draws it.
  let {
    accounts,
    included,
    badges = false,
    onchange,
  }: {
    accounts: Account[]
    included: string[]
    /** Onboarding shows the bank badge; settings has the room but not the need. */
    badges?: boolean
    onchange: (included: string[]) => void
  } = $props()

  function toggle(id: string, checked: boolean) {
    onchange(checked ? [...included, id] : included.filter((other) => other !== id))
  }
</script>

<ul>
  {#each accounts as account (account.id)}
    <li>
      <label>
        <input
          type="checkbox"
          checked={included.includes(account.id)}
          onchange={(event) => toggle(account.id, event.currentTarget.checked)}
        />

        {#if badges}
          <BankBadge connection={account.connection_name} />
        {/if}

        <span class="who">
          <span class="name">{account.name}</span>
          <span class="meta muted">
            {account.connection_name} · {typeLabel(account.type)}
          </span>
        </span>

        <span
          class={[
            'balance',
            'numeric',
            { negative: toCents(account.balance_current) < 0 },
          ]}
        >
          {format(account.balance_current, account.currency, prefs().hideCents)}
        </span>
      </label>
    </li>
  {:else}
    <li class="empty muted">No accounts</li>
  {/each}
</ul>

<style>
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.5625rem;
    /* Pico shrink-wraps labels; these are rows, so they fill the card. */
    width: 100%;
    margin: 0;
    padding: 0.375rem 0.6875rem;
    font-size: var(--text-body);
    font-weight: 400;
    line-height: 1.45;
    color: var(--pico-color);
    cursor: pointer;
  }

  label:hover {
    background: var(--ctp-recessed);
  }

  input {
    flex: none;
  }


  .who {
    display: flex;
    flex-direction: column;
    min-width: 0;
    margin-right: auto;
  }

  .name {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .meta {
    font-size: var(--text-meta);
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .balance {
    white-space: nowrap;
  }

  .negative {
    color: var(--ctp-red);
  }

  .empty {
    padding: 1.25rem;
    text-align: center;
  }
</style>
