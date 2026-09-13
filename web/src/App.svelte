<script lang="ts">
  import { api, errorMessage, type Me } from './lib/api'
  import AuthCard from './lib/components/AuthCard.svelte'
  import Link from './lib/components/Link.svelte'
  import { navigate, path } from './lib/router.svelte'
  import ChooseAccounts from './routes/ChooseAccounts.svelte'
  import ConnectAkahu from './routes/ConnectAkahu.svelte'
  import Dashboard from './routes/Dashboard.svelte'
  import Login from './routes/Login.svelte'
  import Settings from './routes/Settings.svelte'
  import Signup from './routes/Signup.svelte'
  import Transactions from './routes/Transactions.svelte'

  const SIGNED_OUT = ['/login', '/signup']
  const ONBOARDING = '/onboarding'
  const CHOOSE_ACCOUNTS = '/onboarding/accounts'

  let me = $state.raw<Me | null>(null)
  let ready = $state(false)
  let unreachable = $state('')

  /**
   * Sends the browser to a page the session can actually use. Only runs when
   * the session itself changes — navigating around afterwards is the user's
   * business, not ours.
   */
  function land() {
    if (!me) {
      if (!SIGNED_OUT.includes(path())) navigate('/login', { replace: true })
    } else if (!me.onboarded) {
      navigate(ONBOARDING, { replace: true })
    } else if (SIGNED_OUT.includes(path()) || path() === ONBOARDING) {
      // Step two stays reachable once connected, so reloading it mid-setup
      // doesn't dump you on the dashboard with every account switched on.
      navigate('/', { replace: true })
    }
  }

  async function bootstrap() {
    try {
      me = await api.me()
      land()
    } catch (failure) {
      // Signed out is a normal answer api.me() folds into null, so anything
      // thrown here means the backend is unreachable. Say so — without this
      // the app never reaches its first render and the page stays blank.
      unreachable = errorMessage(failure)
    }
    ready = true
  }

  function signedIn(user: Me) {
    me = user
    land()
  }

  async function signedOut() {
    await api.logout()
    me = null
    land()
  }

  function connected() {
    me = me && { ...me, onboarded: true }
    navigate(CHOOSE_ACCOUNTS)
  }

  bootstrap()
</script>

{#if !ready}
  <!-- One frame of nothing beats a spinner that flashes: /auth/me is local. -->
{:else if unreachable}
  <AuthCard>
    <hgroup>
      <h1>Can't reach budge</h1>
      <p class="muted">The app loaded but the server didn't answer.</p>
    </hgroup>
    <p class="error">{unreachable}</p>
    <button type="button" onclick={() => location.reload()}>Try again</button>
  </AuthCard>
{:else if !me}
  {#if path() === '/signup'}
    <Signup onsignin={signedIn} />
  {:else}
    <Login onsignin={signedIn} />
  {/if}
{:else if path() === ONBOARDING}
  <ConnectAkahu onconnected={connected} />
{:else if path() === CHOOSE_ACCOUNTS}
  <ChooseAccounts ondone={() => navigate('/', { replace: true })} />
{:else if path() === '/transactions'}
  <Transactions onsignout={signedOut} />
{:else if path() === '/settings'}
  <Settings onsignout={signedOut} />
{:else if path() === '/'}
  <Dashboard onsignout={signedOut} />
{:else}
  <AuthCard>
    <h1>Not found</h1>
    <p class="muted">There's no page at <code>{path()}</code>.</p>
    <p><Link href="/">Back to your dashboard</Link></p>
  </AuthCard>
{/if}
