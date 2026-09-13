<script lang="ts">
  import { errorMessage } from '../lib/api'
  import AccountPicker from '../lib/components/AccountPicker.svelte'
  import Panel from '../lib/components/Panel.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'
  import { prefs, setPref } from '../lib/prefs.svelte'
  import { followSystem, followsSystem, isDark, setTheme } from '../lib/theme.svelte'
  import { getWorkspace } from '../lib/workspace.svelte'

  let { ondisconnect }: { ondisconnect: () => void } = $props()

  const workspace = getWorkspace()

  /**
   * Null until something is ticked, which is what lets the list follow the
   * saved set while it's still loading — and go back to following it after a
   * save — without an effect syncing the two.
   */
  let edits = $state.raw<string[] | null>(null)
  let notice = $state('')
  let error = $state('')

  let appToken = $state('')
  let userToken = $state('')
  let savingAccounts = $state(false)
  let savingTokens = $state(false)
  let disconnecting = $state(false)

  const saved = $derived(workspace.included)
  const included = $derived(edits ?? saved)

  const dirty = $derived(
    edits !== null &&
      (edits.length !== saved.length || edits.some((id) => !saved.includes(id))),
  )

  const asAt = new Intl.DateTimeFormat('en-NZ', { hour: 'numeric', minute: '2-digit' })

  async function saveAccounts(event: SubmitEvent) {
    event.preventDefault()
    savingAccounts = true
    notice = ''
    error = ''
    try {
      await workspace.saveSelection(included)
      // Back to following the saved set, so the footer stops claiming edits.
      edits = null
      notice = 'Dashboard accounts saved.'
    } catch (failure) {
      error = errorMessage(failure)
    } finally {
      savingAccounts = false
    }
  }

  async function saveTokens(event: SubmitEvent) {
    event.preventDefault()
    savingTokens = true
    notice = ''
    error = ''
    try {
      await workspace.reconnect(appToken, userToken)
      appToken = ''
      userToken = ''
      edits = null
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
  <div class="titles">
    <h1>Settings</h1>
    <p class="muted sub">
      <!-- The separator carries its own spaces: Svelte trims whitespace at
           the block boundary, which would run "connected" into the dot. -->
      Akahu connected{#if workspace.loadedAt}{' · '}last synced {asAt.format(
          workspace.loadedAt,
        )}{/if}
    </p>
  </div>

  {#if notice}<p class="notice">{notice}</p>{/if}
  {#if error}<p class="error">{error}</p>{/if}

  <div class="panels">
    <form onsubmit={saveAccounts}>
      <Panel title="Dashboard accounts">
        {#snippet action()}
          <span class="of numeric">
            {included.length} of {workspace.accounts.length}
          </span>
        {/snippet}

        {#if workspace.ready}
          <AccountPicker
            accounts={workspace.accounts}
            {included}
            onchange={(next) => (edits = next)}
          />
        {:else}
          <p class="loading" aria-busy="true">Loading&hellip;</p>
        {/if}

        {#snippet footer()}
          <span>{dirty ? 'Unsaved changes' : 'All changes saved'}</span>
          <button type="submit" disabled={savingAccounts || !dirty}>
            {savingAccounts ? 'Saving…' : 'Save'}
          </button>
        {/snippet}
      </Panel>
    </form>

    <div class="column">
      <form onsubmit={saveTokens}>
        <Panel title="Akahu connection" padded>
          {#snippet action()}
            <span class="status">
              <span class="dot" aria-hidden="true"></span>Connected
            </span>
          {/snippet}

          <TokenFields bind:appToken bind:userToken inline />

          <div class="buttons">
            <button type="submit" disabled={savingTokens || disconnecting}>
              {savingTokens ? 'Checking…' : 'Replace tokens'}
            </button>
            <button
              type="button"
              class="secondary outline"
              onclick={disconnect}
              disabled={savingTokens || disconnecting}
            >
              {disconnecting ? 'Disconnecting…' : 'Disconnect'}
            </button>
          </div>
        </Panel>
      </form>

      <Panel title="Preferences">
        <div class="prefs">
          <label>
            <input
              type="checkbox"
              checked={followsSystem()}
              onchange={(event) => {
                // Unticking has to land somewhere, so it pins whatever is
                // already on screen rather than flipping the lights.
                if (event.currentTarget.checked) followSystem()
                else setTheme(isDark() ? 'dark' : 'light')
              }}
            />
            <span>Follow system theme</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={prefs().groupByDay}
              onchange={(event) =>
                setPref('groupByDay', event.currentTarget.checked)}
            />
            <span>Group transactions by day</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={prefs().hideCents}
              onchange={(event) => setPref('hideCents', event.currentTarget.checked)}
            />
            <span>Hide cents on balances over $10k</span>
          </label>
        </div>
      </Panel>
    </div>
  </div>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.6875rem;
    max-width: 56rem;
  }

  h1 {
    margin: 0;
    line-height: 1.25;
  }

  .sub {
    margin: 0.125rem 0 0;
    font-size: var(--text-label);
    line-height: 1.4;
  }

  .panels {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr));
    gap: 0.625rem;
    align-items: start;
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
    min-width: 0;
  }

  /* The form is only a wrapper — the panel inside it is the visible box. It
     still needs a box of its own, though: display:contents on a form is a
     known way to confuse assistive tech. */
  form {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .of {
    font-family: var(--font-mono);
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
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

  .prefs {
    display: flex;
    flex-direction: column;
  }

  .prefs label {
    display: flex;
    align-items: center;
    gap: 0.5625rem;
    width: 100%;
    margin: 0;
    padding: 0.4375rem 0.6875rem;
    font-size: var(--text-body);
    font-weight: 400;
    line-height: 1.45;
    cursor: pointer;
  }

  .prefs label + label {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .prefs label:hover {
    background: var(--ctp-recessed);
  }

  .loading {
    margin: 0;
    padding: 1.25rem;
    text-align: center;
  }
</style>
