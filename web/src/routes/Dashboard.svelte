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
    <!-- aria-busy is Pico's spinner; no markup of our own needed. -->
    <p aria-busy="true">Loading&hellip;</p>
  {/if}
</AppShell>
