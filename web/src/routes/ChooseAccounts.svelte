<script lang="ts">
  import { errorMessage } from '../lib/api'
  import AccountPicker from '../lib/components/AccountPicker.svelte'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import { getWorkspace } from '../lib/workspace.svelte'

  let { ondone }: { ondone: () => void } = $props()

  const workspace = getWorkspace()

  // Everything starts ticked, which is what the server already answers with
  // before anything has been chosen.
  let edits = $state.raw<string[] | null>(null)
  let error = $state('')
  let busy = $state(false)

  const included = $derived(edits ?? workspace.included)

  const banks = $derived(
    new Set(workspace.accounts.map((account) => account.connection_name)).size,
  )

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      await workspace.saveSelection(included)
      ondone()
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }
</script>

<AuthCard width="32.5rem" padded={false} step={{ current: 2, total: 2 }}>
  <form onsubmit={submit}>
    <header>
      <h1>Choose your accounts</h1>
      <p class="muted sub">
        {#if workspace.ready}
          Akahu found {workspace.accounts.length}
          {workspace.accounts.length === 1
            ? 'account'
            : 'accounts'}{#if banks > 1}{` across ${banks} banks`}{/if}. Pick the
          ones you want on your dashboard — you can change this later.
        {:else}
          Looking up your accounts&hellip;
        {/if}
      </p>
    </header>

    <div class="list">
      {#if workspace.ready}
        <AccountPicker
          accounts={workspace.accounts}
          {included}
          badges
          onchange={(next) => (edits = next)}
        />
      {:else}
        <p class="loading" aria-busy="true">Loading&hellip;</p>
      {/if}
    </div>

    {#if error}<p class="error problem">{error}</p>{/if}

    <footer>
      <span class="picked">
        {included.length} of {workspace.accounts.length} selected
      </span>
      <button type="submit" disabled={busy || !workspace.ready}>
        {busy ? 'Saving…' : 'Continue'}
      </button>
    </footer>
  </form>
</AuthCard>

<style>
  header {
    padding: 0.6875rem 0.8125rem;
    border-bottom: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  h1 {
    margin: 0;
    font-size: 0.96875rem;
    line-height: 1.3;
  }

  .sub {
    margin: 0.1875rem 0 0;
    font-size: var(--text-label);
    line-height: 1.4;
  }

  /* Long lists scroll inside the card rather than pushing Continue off-screen. */
  .list {
    max-height: 20rem;
    overflow-y: auto;
  }

  .loading {
    margin: 0;
    padding: 1.5rem;
    text-align: center;
  }

  .problem {
    margin: 0.5rem 0.8125rem;
  }

  footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5625rem 0.8125rem;
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
    background: var(--ctp-recessed);
  }

  .picked {
    margin-right: auto;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }
</style>
