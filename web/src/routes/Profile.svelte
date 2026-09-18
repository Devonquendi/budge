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

  let accountDraft = $state.raw<string | null>(null)
  let payoutNameDraft = $state.raw<string | null>(null)
  let savingPayout = $state(false)

  const payoutAccount = $derived(accountDraft ?? me.payout.account ?? '')
  const payoutName = $derived(payoutNameDraft ?? me.payout.name ?? '')

  async function savePayout(event: SubmitEvent) {
    event.preventDefault()
    savingPayout = true
    error = ''
    notice = ''
    try {
      const updated = await api.savePayout(payoutAccount.trim(), payoutName.trim())
      onupdate(updated)
      accountDraft = null
      payoutNameDraft = null
      notice = updated.payout.account
        ? updated.payout.verified
          ? 'Saved, and your bank confirms that account is yours.'
          : "Saved. We couldn't match it to a connected account, so nobody has checked it."
        : 'Cleared. Requests will have nowhere to point.'
    } catch (failure) {
      error = errorMessage(failure)
    }
    savingPayout = false
  }

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

    <form onsubmit={savePayout}>
      <Panel title="Getting paid" padded>
        {#if me.payout.revoked}
          <p class="error">
            This account no longer shows up among your connected accounts. Every request
            you send points at it, so check it before asking anyone else for money.
          </p>
        {/if}

        <div class="field">
          <label class="eyebrow" for="payout-account">Account number</label>
          <div class="row">
            <input
              id="payout-account"
              type="text"
              inputmode="numeric"
              placeholder="12-3400-4339250-00"
              value={payoutAccount}
              oninput={(event) => (accountDraft = event.currentTarget.value)}
            />
            <button type="submit" disabled={savingPayout}>
              {savingPayout ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>

        <div class="field">
          <label class="eyebrow" for="payout-name">Name on the account</label>
          <input
            id="payout-name"
            type="text"
            maxlength={NAME_MAX}
            placeholder="As your bank has it"
            value={payoutName}
            oninput={(event) => (payoutNameDraft = event.currentTarget.value)}
          />
        </div>

        <p class="muted hint">
          {#if me.payout.verified && !me.payout.revoked}
            Your bank lists this account, so requests say it's been checked.
          {:else}
            Goes on every request you send, with a reference, so people can pay you
            without asking how.
          {/if}
        </p>
      </Panel>
    </form>

    <form onsubmit={saveTokens}>
      <Panel title="Akahu connection" padded>
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
            <button
              type="button"
              class="tool"
              data-tooltip="Replace tokens"
              data-placement="left"
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
              data-tooltip="Disconnect accounts"
              data-placement="left"
              aria-label="Disconnect accounts"
              disabled={savingTokens || disconnecting}
              onclick={disconnect}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 7h16" />
                <path d="M9.5 7V5.4A1.4 1.4 0 0 1 10.9 4h2.2a1.4 1.4 0 0 1 1.4 1.4V7" />
                <path d="M6.6 7l.7 11.1a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9L17.4 7" />
                <path d="M10 11v5.4" />
                <path d="M14 11v5.4" />
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

  .hint {
    margin: 0.5rem 0 0;
    font-size: var(--text-meta);
    line-height: 1.45;
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

  /*
   * `.tools .tool`, not `.tool`: app.css sets `width: auto` on every button at
   * a specificity one class can't reach, which quietly left these narrower
   * than the square they're given.
   */
  .tools .tool {
    --fill: var(--ctp-subtext0);
    display: grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    border: 0;
    border-radius: 0.4375rem;
    background: var(--fill);
    /* The colour the palette keeps for ink on a filled accent: near-white in
       the light theme, near-black in the dark one, where the fills are pale. */
    color: var(--ctp-on-blue);
    transition: background-color 200ms ease;
  }

  .tools .tool:focus-visible:not(:disabled) {
    --fill: var(--ctp-text);
  }

  @media (hover: hover) {
    .tools .tool:hover:not(:disabled) {
      --fill: var(--ctp-text);
    }
  }

  /* Grey until you're on it, then red: this one deletes the connection. Mixing
     toward the text colour deepens the red in the light theme and lightens it
     in the dark one, which is the direction the palette's own hovers go. */
  .tools .tool.danger:focus-visible:not(:disabled) {
    --fill: color-mix(in srgb, var(--ctp-red) 75%, var(--ctp-text));
  }

  @media (hover: hover) {
    .tools .tool.danger:hover:not(:disabled) {
      --fill: color-mix(in srgb, var(--ctp-red) 75%, var(--ctp-text));
    }
  }

  .tools .tool:disabled {
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
