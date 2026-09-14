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
        <!-- Connected and broken are the same glyph with the bar whole or
             snapped, so the pair reads as one idea and its undoing. -->
        <div class="connection">
          <p class="synced">
            <span class="dot" aria-hidden="true"></span>
            {#if workspace.loadedAt}
              Last synced {syncedAt.format(workspace.loadedAt)}
            {:else}
              Nothing synced yet
            {/if}
          </p>

          <span class="tools">
            <span class="tool status" data-tooltip="Connected" data-placement="top">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 17H7A5 5 0 0 1 7 7h2" />
                <path d="M15 7h2a5 5 0 0 1 0 10h-2" />
                <path d="M8 12h8" />
              </svg>
            </span>

            <button
              type="button"
              class="tool"
              data-tooltip="Replace tokens"
              data-placement="top"
              aria-label="Replace tokens"
              aria-expanded={replacing}
              aria-controls="akahu-tokens"
              onclick={() => (replacing ? stopReplacing() : (replacing = true))}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4.5 19.5h4L19 9a2.83 2.83 0 0 0-4-4L4.5 15.5v4Z" />
                <path d="M14 6l4 4" />
              </svg>
            </button>

            <button
              type="button"
              class="tool danger"
              data-tooltip="Disconnect"
              data-placement="top"
              aria-label="Disconnect Akahu"
              disabled={savingTokens || disconnecting}
              onclick={disconnect}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 17H7A5 5 0 0 1 7 7h2" />
                <path d="M15 7h2a5 5 0 0 1 0 10h-2" />
                <path d="M8 12h2.5M13.5 12H16" />
              </svg>
            </button>
          </span>
        </div>

        {#if replacing}
          <div id="akahu-tokens" class="tokens">
            <TokenFields bind:appToken bind:userToken inline />

            <div class="buttons">
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
            </div>
          </div>
        {/if}
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

  .connection {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .synced {
    display: flex;
    align-items: center;
    gap: 0.4375rem;
    margin: 0 auto 0 0;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
  }

  .dot {
    flex: none;
    width: 0.4375rem;
    height: 0.4375rem;
    border-radius: 999px;
    background: var(--ctp-green);
  }

  .tools {
    display: inline-flex;
    align-items: center;
    gap: 0.3125rem;
  }

  .tool {
    display: grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    border-radius: 0.4375rem;
    background: var(--pico-card-background-color);
    color: var(--pico-muted-color);
  }

  .tool:hover:not(:disabled, .status) {
    background: var(--ctp-surface0);
    color: var(--pico-color);
  }

  /* A border shorthand, not just a colour: Pico turns the bottom border of a
     tooltip on a non-control into a dotted underline. */
  .tool.status {
    border: var(--pico-border-width) solid
      color-mix(in srgb, var(--ctp-green) 40%, transparent);
    color: var(--ctp-green);
    cursor: default;
  }

  .tool.danger {
    color: var(--ctp-red);
    border-color: color-mix(in srgb, var(--ctp-red) 35%, transparent);
  }

  .tool.danger:hover:not(:disabled) {
    background: color-mix(in srgb, var(--ctp-red) 14%, transparent);
    color: var(--ctp-red);
  }

  .tool:disabled {
    opacity: 0.45;
  }

  .tools svg {
    width: 1.0625rem;
    height: 1.0625rem;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.9;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  /* Pico sizes tooltips for prose, which shouts over a card header. */
  .tools [data-tooltip]::before {
    padding: 0.1875rem 0.375rem;
    font-size: var(--text-meta);
  }

  .tokens {
    display: flex;
    flex-direction: column;
    gap: 0.5625rem;
  }

  .buttons {
    display: flex;
    gap: 0.4375rem;
    flex-wrap: wrap;
  }
</style>
