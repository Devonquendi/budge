<script lang="ts">
  import { api, errorMessage, type Me } from '../lib/api'
  import AuthCard from '../lib/components/AuthCard.svelte'
  import Link from '../lib/components/Link.svelte'

  let { onsignin }: { onsignin: (me: Me) => void } = $props()

  let email = $state('')
  let password = $state('')
  // ?invite=<code> prefills the field, so a shared link just works.
  let inviteCode = $state(
    new URLSearchParams(window.location.search).get('invite') ?? '',
  )
  let error = $state('')
  let busy = $state(false)

  async function submit(event: SubmitEvent) {
    event.preventDefault()
    busy = true
    error = ''
    try {
      onsignin(await api.signup(email, password, inviteCode))
    } catch (failure) {
      error = errorMessage(failure)
      busy = false
    }
  }
</script>

<AuthCard>
  <h1>Create an account</h1>

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
        autocomplete="new-password"
        bind:value={password}
        required
      />
    </label>
    <label>
      Invite code
      <input type="text" bind:value={inviteCode} required />
    </label>

    {#if error}<p class="error">{error}</p>{/if}

    <button type="submit" disabled={busy}>
      {busy ? 'Creating account…' : 'Create account'}
    </button>
  </form>

  <p class="muted footer">
    Already have an account? <Link href="/login">Sign in</Link>
  </p>
</AuthCard>

<style>
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
