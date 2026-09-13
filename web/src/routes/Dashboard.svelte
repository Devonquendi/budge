<script lang="ts">
  import { api, ApiError, errorMessage, type Account } from '../lib/api'
  import AccountList from '../lib/components/AccountList.svelte'
  import AppShell from '../lib/components/AppShell.svelte'
  import Summary from '../lib/components/Summary.svelte'
  import { navigate } from '../lib/router.svelte'

  let { onsignout }: { onsignout: () => void } = $props()

  let accounts = $state.raw<Account[] | null>(null)
  let error = $state('')

  async function load() {
    try {
      accounts = await api.accounts()
    } catch (failure) {
      // 409 means the Akahu tokens are gone, so there is nothing to show yet.
      if (failure instanceof ApiError && failure.status === 409) {
        navigate('/onboarding', { replace: true })
      } else {
        error = errorMessage(failure)
      }
    }
  }

  load()
</script>

<AppShell {onsignout}>
  {#if accounts}
    <Summary {accounts} />
    <AccountList {accounts} />
  {:else if error}
    <p class="error">Couldn't load your accounts: {error}</p>
  {:else}
    <div class="skeleton" aria-busy="true" aria-label="Loading accounts">
      <span class="line total"></span>
      <span class="line"></span>
    </div>
  {/if}
</AppShell>

<style>
  .skeleton {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .line {
    height: 1.25rem;
    width: 12rem;
    border-radius: var(--radius-sm);
    background: var(--surface);
    animation: pulse 1.4s ease-in-out infinite;
  }

  .total {
    height: 4rem;
    width: 18rem;
  }

  @keyframes pulse {
    50% {
      opacity: 0.45;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .line {
      animation: none;
    }
  }
</style>
