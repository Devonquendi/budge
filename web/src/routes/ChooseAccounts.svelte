<script lang="ts">
  import { api, ApiError, errorMessage, type Selection } from '../lib/api'
  import AccountPicker from '../lib/components/AccountPicker.svelte'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import { navigate } from '../lib/router.svelte'

  let { ondone }: { ondone: () => void } = $props()

  let selection = $state.raw<Selection | null>(null)
  let included = $state.raw<string[]>([])
  let error = $state('')
  let busy = $state(false)

  async function load() {
    try {
      selection = await api.selection()
      included = selection.included
    } catch (failure) {
      // The tokens went away between pages — start onboarding over.
      if (failure instanceof ApiError && failure.status === 409) {
        navigate('/onboarding', { replace: true })
      } else {
        error = errorMessage(failure)
      }
    }
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      await api.saveSelection(included)
      ondone()
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }

  load()
</script>

<AuthCard width="34rem">
  <hgroup>
    <p class="eyebrow">Step 2 of 2</p>
    <h1>Pick your accounts</h1>
    <p class="muted">These are the ones your dashboard adds up. You can change them later.</p>
  </hgroup>

  {#if selection}
    <form onsubmit={submit}>
      <AccountPicker
        accounts={selection.accounts}
        {included}
        onchange={(next) => (included = next)}
      />

      {#if error}<p class="error">{error}</p>{/if}

      <button type="submit" disabled={busy}>{busy ? 'Saving…' : 'Finish setup'}</button>
    </form>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <p class="muted">Loading accounts…</p>
  {/if}
</AuthCard>

<style>
  h1 {
    margin-block: 0.375rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
</style>
