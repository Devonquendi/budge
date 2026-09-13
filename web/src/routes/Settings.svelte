<script lang="ts">
  import { api, errorMessage, type Selection } from '../lib/api'
  import AccountPicker from '../lib/components/AccountPicker.svelte'
  import AppShell from '../lib/components/AppShell.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'

  let { email, onsignout }: { email: string; onsignout: () => void } = $props()

  // Null until the first load answers. Without the third state the page
  // claims you aren't connected for as long as the request takes.
  let connected = $state<boolean | null>(null)
  let selection = $state.raw<Selection | null>(null)
  let included = $state.raw<string[]>([])
  let notice = $state('')
  let error = $state('')

  let appToken = $state('')
  let userToken = $state('')
  let savingAccounts = $state(false)
  let savingTokens = $state(false)

  async function load() {
    try {
      connected = (await api.connection()).connected
      if (!connected) return
      selection = await api.selection()
      included = selection.included
    } catch (failure) {
      error = errorMessage(failure)
    }
  }

  async function saveAccounts(event: SubmitEvent) {
    event.preventDefault()
    savingAccounts = true
    notice = ''
    error = ''
    try {
      selection = await api.saveSelection(included)
      included = selection.included
      notice = 'Dashboard accounts saved.'
    } catch (failure) {
      error = errorMessage(failure)
    } finally {
      savingAccounts = false
    }
  }

  async function saveTokens(event: SubmitEvent) {
    event.preventDefault()
    savingTokens = true
    notice = ''
    error = ''
    try {
      await api.connect(appToken, userToken)
      appToken = ''
      userToken = ''
      connected = true
      // New tokens mean a new set of accounts to choose from.
      selection = await api.selection()
      included = selection.included
      notice = 'Akahu connection updated.'
    } catch (failure) {
      error = errorMessage(failure)
    } finally {
      savingTokens = false
    }
  }

  load()
</script>

<AppShell {onsignout}>
  <hgroup>
    <h1>Settings</h1>
    <p class="muted">Signed in as {email}</p>
  </hgroup>

  {#if notice}<p class="notice">{notice}</p>{/if}
  {#if error}<p class="error">{error}</p>{/if}

  <article>
    <header>
      <h2>Dashboard accounts</h2>
    </header>

    {#if connected === null}
      <p aria-busy="true">Loading&hellip;</p>
    {:else if !connected}
      <p class="muted">Not connected.</p>
    {:else if selection}
      <form onsubmit={saveAccounts}>
        <AccountPicker
          accounts={selection.accounts}
          {included}
          onchange={(next) => (included = next)}
        />
        <button type="submit" disabled={savingAccounts}>
          {savingAccounts ? 'Saving…' : 'Save accounts'}
        </button>
      </form>
    {:else}
      <p aria-busy="true">Loading&hellip;</p>
    {/if}
  </article>

  <article>
    <header>
      <h2>Akahu connection</h2>
      {#if connected === null}
        <p aria-busy="true">Loading&hellip;</p>
      {:else}
        <p class="muted">{connected ? 'Connected' : 'Not connected'}</p>
      {/if}
    </header>

    <form onsubmit={saveTokens}>
      <TokenFields bind:appToken bind:userToken />
      <button type="submit" disabled={savingTokens}>
        {savingTokens ? 'Checking…' : connected ? 'Replace tokens' : 'Connect'}
      </button>
    </form>
  </article>
</AppShell>

<style>
  hgroup {
    margin-bottom: 2rem;
  }

  h1 {
    font-size: clamp(1.625rem, 5vw, 2rem);
  }

  hgroup p {
    margin-top: 0.25rem;
  }

  article {
    border: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  h2 {
    font-size: 1.0625rem;
    margin-bottom: 0.25rem;
  }

  article header p {
    font-size: 0.875rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Pico makes submit buttons full-width, which suits a sign-in form but not
     a settings card. Everything above them still fills the card. */
  form button {
    width: auto;
    align-self: start;
  }

</style>
