<script lang="ts">
  import { typeLabel } from '../accounts'
  import type { Account } from '../api'
  import { format } from '../money'

  // Props in, event out: the page owns the selection, this just draws it.
  let {
    accounts,
    included,
    onchange,
  }: {
    accounts: Account[]
    included: string[]
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
        <span class="who">
          <span class="name">{account.name}</span>
          <span class="meta muted">
            {account.connection_name} · {typeLabel(account.type)}
          </span>
        </span>
        <span class="balance numeric">
          {format(account.balance_current, account.currency)}
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
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: var(--pico-border-radius);
    overflow: hidden;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    /* Pico shrink-wraps labels; these are rows, so they fill the card. */
    width: 100%;
    margin: 0;
    padding: 0.75rem 0.875rem;
    font-size: 1rem;
    font-weight: 400;
    color: var(--pico-color);
    cursor: pointer;
  }

  label:hover {
    background: var(--ctp-mantle);
  }

  input {
    flex: none;
    margin: 0;
  }

  .who {
    display: flex;
    flex-direction: column;
    min-width: 0;
    margin-right: auto;
  }

  .name {
    font-weight: 600;
  }

  .meta {
    font-size: 0.8125rem;
    line-height: 1.35;
  }

  .balance {
    font-size: 0.9375rem;
    white-space: nowrap;
  }

  .empty {
    padding: 1.5rem;
    text-align: center;
  }
</style>
