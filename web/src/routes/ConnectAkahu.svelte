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

<AuthCard width="24rem" padded={false} step={{ current: 1, total: 2 }}>
  <header>
    <h1>Connect your banks</h1>
    <p class="muted sub">
      Budge reads your balances through Akahu. Paste the two tokens from your
      Akahu app.
    </p>
  </header>

  <form onsubmit={submit}>
    <TokenFields bind:appToken bind:userToken />

    {#if error}<p class="error">{error}</p>{/if}

    <button type="submit" class="go" disabled={busy}>
      {busy ? 'Checking…' : 'Connect'}
    </button>
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

  form {
    display: flex;
    flex-direction: column;
    gap: 0.5625rem;
    padding: 0.6875rem 0.8125rem 0.8125rem;
  }

  .go {
    width: 100%;
    margin-top: 0.1875rem;
    font-weight: 600;
  }
</style>
