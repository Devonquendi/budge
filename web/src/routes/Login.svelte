<script lang="ts">
  import { api, errorMessage, type Me } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
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
  <hgroup>
    <h1>Welcome back</h1>
    <p class="muted">Sign in to see where your money is.</p>
  </hgroup>

  <form onsubmit={submit}>
    <label>
      Email
      <input
        type="email"
        autocomplete="email"
        bind:value={email}
        required
        {@attach (node) => node.focus()}
      />
    </label>
    <label>
      Password
      <input
        type="password"
        autocomplete="current-password"
        bind:value={password}
        required
      />
    </label>

    {#if error}<p class="error">{error}</p>{/if}

    <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
  </form>

  <p class="muted footer">No account? <Link href="/signup">Sign up</Link></p>
</AuthCard>

<style>
  hgroup p {
    margin-top: 0.375rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .footer {
    font-size: 0.875rem;
    text-align: center;
  }
</style>
