<script lang="ts">
  import { api, errorMessage, type Me } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import DemoPersonas from '../lib/components/DemoPersonas.svelte'
  import Link from '../lib/components/Link.svelte'

  let { onsignin }: { onsignin: (me: Me) => void } = $props()

  let email = $state('')
  let password = $state('')
  let error = $state('')
  let busy = $state(false)

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      onsignin(await api.login(email, password))
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }
</script>

<AuthCard>
  <h1>Welcome back</h1>
  <p class="muted sub">Sign in to see your balances.</p>

  <form onsubmit={submit}>
    <label>
      <span>Email</span>
      <input
        type="email"
        autocomplete="email"
        placeholder="you@example.com"
        bind:value={email}
        required
        {@attach (node) => node.focus()}
      />
    </label>
    <label>
      <span>Password</span>
      <input
        type="password"
        autocomplete="current-password"
        bind:value={password}
        required
      />
    </label>

    {#if error}<p class="error">{error}</p>{/if}

    <button type="submit" class="go" disabled={busy}>
      {busy ? 'Signing in…' : 'Sign in'}
    </button>
  </form>

  <DemoPersonas {onsignin} />

  {#snippet below()}
    No account? <Link href="/signup">Sign up</Link>
  {/snippet}
</AuthCard>

<style>
  h1 {
    margin: 0;
    font-size: 1rem;
    line-height: 1.3;
  }

  .sub {
    margin: 0.1875rem 0 0.875rem;
    font-size: var(--text-label);
    line-height: 1.4;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 0.5625rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--pico-muted-color);
  }

  /* The one button on the page, so it gets the full width. */
  .go {
    width: 100%;
    margin-top: 0.1875rem;
    font-size: var(--text-body);
    font-weight: 600;
  }
</style>
