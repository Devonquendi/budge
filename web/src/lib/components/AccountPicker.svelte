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
    <li class="empty muted">Akahu returned no accounts for these tokens.</li>
  {/each}
</ul>

<style>
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  li + li {
    border-top: 1px solid var(--border);
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0.875rem;
    font-size: 1rem;
    font-weight: 400;
    color: var(--ink);
    cursor: pointer;
  }

  label:hover {
    background: var(--surface-sunken);
  }

  input {
    flex: none;
    width: 1.125rem;
    height: 1.125rem;
    accent-color: var(--accent);
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
