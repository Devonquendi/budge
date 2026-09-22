<script lang="ts">
  import { api, errorMessage, type Me } from './lib/api'
  import AppShell from './lib/components/AppShell.svelte'
  import AuthCard from './lib/components/AuthCard.svelte'
  import Link from './lib/components/Link.svelte'
  import { navigate, path } from './lib/router.svelte'
  import { Workspace, setWorkspace } from './lib/workspace.svelte'
  import ChooseAccounts from './routes/ChooseAccounts.svelte'
  import ConnectAkahu from './routes/ConnectAkahu.svelte'
  import Dashboard from './routes/Dashboard.svelte'
  import Login from './routes/Login.svelte'
  import Profile from './routes/Profile.svelte'
  import PublicRequest from './routes/PublicRequest.svelte'
  import Requests from './routes/Requests.svelte'
  import Settings from './routes/Settings.svelte'
  import Signup from './routes/Signup.svelte'
  import Transactions from './routes/Transactions.svelte'

  const SIGNED_OUT = ['/login', '/signup']
  const ONBOARDING = '/onboarding'
  const CHOOSE_ACCOUNTS = '/onboarding/accounts'
  const SIGNED_IN = ['/', '/transactions', '/requests', '/profile', '/settings']

  // Asking for money needs no bank, so these sit outside the onboarding gate.
  const WITHOUT_A_BANK = ['/requests', '/profile']

  /** The payer's page. Public, and the only route with a variable in it. */
  const SHARED_REQUEST = /^\/r\/([0-9a-z]+)$/

  let me = $state.raw<Me | null>(null)
  let ready = $state(false)
  let unreachable = $state('')

  /**
   * One store for the whole signed-in app: the sidebar shows a net balance and
   * a transaction count beside the nav, so this data outlives any one page.
   * A 409 from anywhere in it means the tokens went away underneath us.
   */
  const workspace = new Workspace(() => {
    me = me && { ...me, onboarded: false }
    navigate(ONBOARDING, { replace: true })
  })

  setWorkspace(workspace)

  /**
   * Sends the browser to a page the session can actually use. Only runs when
   * the session itself changes. Navigating around afterwards is the user's
   * business, not ours.
   */
  function land() {
    if (SHARED_REQUEST.test(path())) return
    if (!me) {
      if (!SIGNED_OUT.includes(path())) navigate('/login', { replace: true })
    } else if (!me.onboarded && !WITHOUT_A_BANK.includes(path())) {
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
      if (me?.onboarded) workspace.load()
    } catch (failure) {
      // Signed out is a normal answer api.me() folds into null, so anything
      // thrown here means the backend is unreachable. Say so, because without this
      // the app never reaches its first render and the page stays blank.
      unreachable = errorMessage(failure)
    }
    ready = true
  }

  function signedIn(user: Me) {
    me = user
    // Without a bank, requests are all there is to show.
    if (!user.onboarded) navigate('/requests', { replace: true })
    else {
      land()
      workspace.load()
    }
  }

  async function signedOut() {
    await api.logout()
    me = null
    land()
  }

  function connected() {
    me = me && { ...me, onboarded: true }
    // Accounts only: nothing is ticked yet, so a transaction fetch here covers
    // every account and is thrown away by the save at the end of step two.
    workspace.loadAccounts()
    navigate(CHOOSE_ACCOUNTS)
  }

  function disconnected() {
    me = me && { ...me, onboarded: false }
    navigate(ONBOARDING, { replace: true })
  }

  bootstrap()
</script>

{#if !ready}
  <!-- One frame of nothing beats a spinner that flashes: /auth/me is local. -->
{:else if unreachable}
  <AuthCard>
    <h1>Can't reach budge</h1>
    <p class="muted">The app loaded but the server didn't answer.</p>
    <p class="error">{unreachable}</p>
    <button type="button" onclick={() => location.reload()}>Try again</button>
  </AuthCard>
{:else if SHARED_REQUEST.test(path())}
  <PublicRequest token={SHARED_REQUEST.exec(path())?.[1] ?? ''} />
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
{:else if SIGNED_IN.includes(path())}
  <!--
    The one place the shell is applied. Routes render their own content and
    nothing else, so adding a page is a branch here plus a link in the sidebar
    not another copy of the wrapper. It also keeps one AppShell alive across
    navigation instead of tearing the sidebar down and rebuilding it per page.
  -->
  <AppShell
    email={me.email}
    name={me.name}
    onboarded={me.onboarded}
    onsignout={signedOut}
  >
    {#if path() === '/requests'}
      <Requests />
    {:else if path() === '/transactions'}
      <Transactions />
    {:else if path() === '/profile'}
      <Profile {me} onupdate={(next) => (me = next)} ondisconnect={disconnected} />
    {:else if path() === '/settings'}
      <Settings />
    {:else if me.onboarded}
      <Dashboard />
    {:else}
      <Requests />
    {/if}
  </AppShell>
{:else}
  <AuthCard>
    <h1>Not found</h1>
    <p class="muted">There's no page at <code>{path()}</code>.</p>
    <p><Link href="/">Back to your dashboard</Link></p>
  </AuthCard>
{/if}
