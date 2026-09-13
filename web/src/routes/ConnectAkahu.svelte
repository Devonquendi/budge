<script lang="ts">
  import { api, errorMessage } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'

  let { onconnected }: { onconnected: () => void } = $props()

  let appToken = $state('')
  let userToken = $state('')
  let error = $state('')
  let busy = $state(false)

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      await api.connect(appToken, userToken)
      onconnected()
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }
</script>

<AuthCard width="28rem">
  <hgroup>
    <p class="eyebrow">Step 1 of 2</p>
    <h1>Connect your banks</h1>
  </hgroup>

  <form onsubmit={submit}>
    <TokenFields bind:appToken bind:userToken />

    {#if error}<p class="error">{error}</p>{/if}

    <button type="submit" disabled={busy}>{busy ? 'Checking…' : 'Connect'}</button>
  </form>
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
