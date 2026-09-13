<script lang="ts">
  import { api, errorMessage, type Selection } from '../lib/api'
  import AccountPicker from '../lib/components/AccountPicker.svelte'
  import AppShell from '../lib/components/AppShell.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'

  let { email, onsignout }: { email: string; onsignout: () => void } = $props()

  let connected = $state(false)
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

  <section class="card">
    <header>
      <h2>Dashboard accounts</h2>
      <p class="muted">Only ticked accounts count towards your net balance.</p>
    </header>

    {#if !connected}
      <p class="muted">Connect Akahu below to choose accounts.</p>
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
      <p class="muted">Loading accounts…</p>
    {/if}
  </section>

  <section class="card">
    <header>
      <h2>Akahu connection</h2>
      <p class="muted">
        {connected
          ? 'Connected. Paste new tokens to replace the ones stored.'
          : 'Not connected yet.'}
      </p>
    </header>

    <form onsubmit={saveTokens}>
      <TokenFields bind:appToken bind:userToken />
      <button type="submit" disabled={savingTokens}>
        {savingTokens ? 'Checking…' : connected ? 'Replace tokens' : 'Connect'}
      </button>
    </form>
  </section>
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

  section {
    padding: clamp(1.25rem, 4vw, 1.75rem);
  }

  section + section {
    margin-top: 1.25rem;
  }

  section header {
    margin-bottom: 1.25rem;
  }

  h2 {
    font-size: 1.0625rem;
  }

  section header p {
    margin-top: 0.25rem;
    font-size: 0.875rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Buttons size to their label; everything above them fills the card. */
  form button {
    align-self: start;
  }

  .notice,
  .error {
    margin-bottom: 1.25rem;
  }
</style>
