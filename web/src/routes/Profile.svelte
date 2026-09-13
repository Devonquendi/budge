<script lang="ts">
  import { errorMessage } from '../lib/api'
  import Panel from '../lib/components/Panel.svelte'
  import TokenFields from '../lib/components/TokenFields.svelte'
  import { getWorkspace } from '../lib/workspace.svelte'

  let { email, ondisconnect }: { email: string; ondisconnect: () => void } = $props()

  const workspace = getWorkspace()

  let appToken = $state('')
  let userToken = $state('')
  let notice = $state('')
  let error = $state('')
  let savingTokens = $state(false)
  let disconnecting = $state(false)

  const asAt = new Intl.DateTimeFormat('en-NZ', { hour: 'numeric', minute: '2-digit' })

  async function saveTokens(event: SubmitEvent) {
    event.preventDefault()
    savingTokens = true
    notice = ''
    error = ''
    try {
      await workspace.reconnect(appToken, userToken)
      appToken = ''
      userToken = ''
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
    <h1>Profile</h1>
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
    <Panel title="Account" padded>
      <p class="field">
        <span class="eyebrow">Email</span>
        <span class="value">{email}</span>
      </p>
    </Panel>

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
  </div>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.6875rem;
    max-width: 44rem;
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
