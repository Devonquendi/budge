<script lang="ts">
  import { api, errorMessage, type Me } from '../lib/api'
  import Panel from '../lib/components/Panel.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'
  import { getWorkspace } from '../lib/workspace.svelte'

  let {
    me,
    onupdate,
    ondisconnect,
  }: { me: Me; onupdate: (me: Me) => void; ondisconnect: () => void } = $props()

  const workspace = getWorkspace()

  /** Matches the column the server stores it in. */
  const NAME_MAX = 60

  /**
   * Null until something is typed, which lets the field follow the saved name
   * until then and go back to following it after a save. The account picker
   * holds its edits the same way, and for the same reason: no effect syncing
   * a copy against the thing it was copied from.
   */
  let draft = $state.raw<string | null>(null)
  let savingName = $state(false)

  // Tokens stay out of sight until they're asked for: this card is a status
  // most of the time, and two empty boxes read like something needs filling in.
  let replacing = $state(false)
  let appToken = $state('')
  let userToken = $state('')
  let savingTokens = $state(false)

  let disconnecting = $state(false)
  let notice = $state('')
  let error = $state('')

  const syncedAt = new Intl.DateTimeFormat('en-NZ', {
    hour: 'numeric',
    minute: '2-digit',
  })

  const name = $derived(draft ?? me.name ?? '')
  const trimmed = $derived(name.trim())
  const nameDirty = $derived(trimmed !== (me.name ?? ''))

  async function saveName(event: SubmitEvent) {
    event.preventDefault()
    savingName = true
    notice = ''
    error = ''
    try {
      onupdate(await api.saveName(trimmed))
      // Back to following the saved name, so the button stops offering a save.
      draft = null
      notice = trimmed ? 'Name saved.' : 'Name cleared.'
    } catch (failure) {
      error = errorMessage(failure)
    } finally {
      savingName = false
    }
  }

  function stopReplacing() {
    replacing = false
    appToken = ''
    userToken = ''
  }

  async function saveTokens(event: SubmitEvent) {
    event.preventDefault()
    savingTokens = true
    notice = ''
    error = ''
    try {
      await workspace.reconnect(appToken, userToken)
      stopReplacing()
      notice = 'Akahu connection updated.'
    } catch (failure) {
      error = errorMessage(failure)
    } finally {
      savingTokens = false
    }
  }

  async function disconnect() {
    // Destructive and not obviously so from the button alone: this drops the
    // tokens and the account picks, and puts you back at step one.
    if (!confirm('Disconnect Akahu? Your tokens and account choices are deleted.')) {
      return
    }

    disconnecting = true
    notice = ''
    error = ''
    try {
      await workspace.disconnect()
      ondisconnect()
    } catch (failure) {
      error = errorMessage(failure)
      disconnecting = false
    }
  }
</script>

<div class="page">
  <h1>Profile</h1>

  {#if notice}<p class="notice">{notice}</p>{/if}
  {#if error}<p class="error">{error}</p>{/if}

  <div class="panels">
    <form onsubmit={saveName}>
      <Panel title="Account" padded>
        <p class="field">
          <span class="eyebrow">Email</span>
          <span class="value">{me.email}</span>
        </p>

        <div class="field">
          <label class="eyebrow" for="display-name">Name</label>
          <div class="row">
            <input
              id="display-name"
              type="text"
              maxlength={NAME_MAX}
              placeholder="What should we call you?"
              autocomplete="name"
              value={name}
              oninput={(event) => (draft = event.currentTarget.value)}
            />
            <button type="submit" disabled={savingName || !nameDirty}>
              {savingName ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </Panel>
    </form>

    <form onsubmit={saveTokens}>
      <Panel title="Akahu connection" padded>
        {#snippet action()}
          <span class="status">
            <span class="dot" aria-hidden="true"></span>Connected
          </span>
        {/snippet}

        <p class="synced muted">
          {#if workspace.loadedAt}
            Last synced {syncedAt.format(workspace.loadedAt)}
          {:else}
            Nothing synced yet
          {/if}
        </p>

        {#if replacing}
          <TokenFields bind:appToken bind:userToken inline />
        {/if}

        <div class="buttons">
          {#if replacing}
            <button type="submit" disabled={savingTokens}>
              {savingTokens ? 'Checking…' : 'Save tokens'}
            </button>
            <button
              type="button"
              class="secondary outline"
              onclick={stopReplacing}
              disabled={savingTokens}
            >
              Cancel
            </button>
          {:else}
            <button type="button" onclick={() => (replacing = true)}>
              Replace tokens
            </button>
            <button
              type="button"
              class="secondary outline"
              onclick={disconnect}
              disabled={disconnecting}
            >
              {disconnecting ? 'Disconnecting…' : 'Disconnect'}
            </button>
          {/if}
        </div>
      </Panel>
    </form>
  </div>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.6875rem;
    max-width: 38rem;
    margin-inline: auto;
  }

  h1 {
    margin: 0;
    line-height: 1.25;
  }

  /* One column: these are forms, and a second column only makes them narrower. */
  .panels {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }

  /* The form is only a wrapper: the panel inside it is the visible box. It
     still needs a box of its own, though: display:contents on a form is a
     known way to confuse assistive tech. */
  form {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0;
  }

  .value {
    font-family: var(--font-mono);
    font-size: var(--text-label);
    overflow-wrap: anywhere;
  }

  .row {
    display: flex;
    align-items: center;
    gap: 0.4375rem;
  }

  .row input {
    flex: 1;
    min-width: 0;
  }

  .synced {
    margin: 0;
    font-size: var(--text-meta);
  }

  .status {
    display: inline-flex;
    align-items: center;
    gap: 0.3125rem;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--ctp-green);
  }

  .dot {
    width: 0.375rem;
    height: 0.375rem;
    border-radius: 999px;
    background: currentColor;
  }

  .buttons {
    display: flex;
    gap: 0.4375rem;
    flex-wrap: wrap;
  }
</style>
