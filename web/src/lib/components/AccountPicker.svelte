<script lang="ts">
  import { NICKNAME_MAX, accountName, typeLabel } from '../accounts'
  import type { Account } from '../api'
  import { format, toCents } from '../money'
  import { prefs } from '../prefs.svelte'
  import BankBadge from './BankBadge.svelte'

  // Props in, event out: the page owns the selection, this just draws it.
  let {
    accounts,
    included,
    onchange,
    onrename,
  }: {
    accounts: Account[]
    included: string[]
    onchange: (included: string[]) => void
    /** Settings passes this to get a rename button per row; onboarding doesn't. */
    onrename?: (id: string, nickname: string) => Promise<void>
  } = $props()

  let editing = $state<string | null>(null)
  let draft = $state('')
  let saving = $state(false)

  function toggle(id: string, checked: boolean) {
    onchange(checked ? [...included, id] : included.filter((other) => other !== id))
  }

  function open(account: Account) {
    editing = account.id
    draft = account.nickname ?? ''
  }

  async function rename(account: Account) {
    if (!onrename) return

    saving = true
    try {
      await onrename(account.id, draft.trim())
      editing = null
    } catch {
      // The page puts the message up. The row stays open to try again.
    } finally {
      saving = false
    }
  }
</script>

<ul>
  {#each accounts as account (account.id)}
    <li>
      {#if editing === account.id}
        <!-- Not a form: the settings page already wraps this list in one, and
             a nested form is dropped by the browser rather than nested. -->
        <div class="rename">
          <BankBadge
            connection={account.connection_name}
            logo={account.connection_logo}
          />
          <input
            type="text"
            maxlength={NICKNAME_MAX}
            placeholder={account.name}
            aria-label="Name for {account.name}"
            bind:value={draft}
            onkeydown={(event) => {
              if (event.key === 'Enter') {
                // Otherwise it submits the page's form and saves the ticks.
                event.preventDefault()
                rename(account)
              } else if (event.key === 'Escape') {
                editing = null
              }
            }}
            {@attach (node) => {
              node.focus()
              node.select()
            }}
          />
          <button type="button" disabled={saving} onclick={() => rename(account)}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            type="button"
            class="secondary outline"
            onclick={() => (editing = null)}
          >
            Cancel
          </button>
        </div>
      {:else}
        <label>
          <input
            type="checkbox"
            checked={included.includes(account.id)}
            onchange={(event) => toggle(account.id, event.currentTarget.checked)}
          />

          <BankBadge
            connection={account.connection_name}
            logo={account.connection_logo}
          />

          <span class="who">
            <span class="name">{accountName(account)}</span>
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

        {#if onrename}
          <button
            type="button"
            class="pencil"
            data-tooltip="Rename"
            data-placement="left"
            aria-label="Rename {accountName(account)}"
            onclick={() => open(account)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4.5 19.5h4L19 9a2.83 2.83 0 0 0-4-4L4.5 15.5v4Z" />
              <path d="M14 6l4 4" />
            </svg>
          </button>
        {/if}
      {/if}
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

  li {
    display: flex;
    align-items: center;
  }

  li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  @media (hover: hover) {
    li:not(.empty):hover {
      background: var(--ctp-recessed);
    }
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.5625rem;
    /* Pico shrink-wraps labels; these are rows, so they fill the card. */
    flex: 1;
    min-width: 0;
    margin: 0;
    padding: 0.375rem 0.6875rem;
    font-size: var(--text-body);
    font-weight: 400;
    line-height: 1.45;
    color: var(--pico-color);
    cursor: pointer;
  }

  [type='checkbox'] {
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

  /* Visible rather than hover-only, which hides it outright on a touchscreen,
     but quiet enough that a column of them doesn't read as a column of icons. */
  .pencil {
    display: grid;
    place-items: center;
    flex: none;
    width: 1.5rem;
    height: 1.5rem;
    margin-right: 0.4375rem;
    padding: 0;
    border: 0;
    border-radius: 0.375rem;
    background: transparent;
    opacity: 0.55;
  }

  .pencil:focus-visible {
    opacity: 1;
    background: var(--ctp-surface0);
  }

  @media (hover: hover) {
    .pencil:hover {
      opacity: 1;
      background: var(--ctp-surface0);
    }
  }

  .pencil svg {
    width: 0.8125rem;
    height: 0.8125rem;
    fill: none;
    stroke: var(--pico-muted-color);
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  /* --ctp-text, not --pico-color: .pencil is a button, so Pico rebinds
     --pico-color to --pico-primary-inverse there, which made the hover
     stroke near-invisible against the hover background in both themes. */
  @media (hover: hover) {
    .pencil:hover svg {
      stroke: var(--ctp-text);
    }
  }

  /* Pico sizes tooltips for prose, which shouts over rows this tight. */
  .pencil::before {
    padding: 0.1875rem 0.375rem;
    font-size: var(--text-meta);
  }

  .rename {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.375rem 0.6875rem;
  }

  .rename input {
    flex: 1;
    min-width: 0;
  }

  .empty {
    justify-content: center;
    padding: 1.25rem;
  }
</style>
