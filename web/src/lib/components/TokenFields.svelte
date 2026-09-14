<script lang="ts">
  // Bindable so the page holding the form owns the values; the tokens
  // themselves are never sent back from the server.
  let { appToken = $bindable(''), userToken = $bindable(''), inline = false } = $props()
</script>

<label class={{ inline }}>
  <span>App ID token</span>
  <input
    type="text"
    name="app_token"
    placeholder="app_token_..."
    autocomplete="off"
    spellcheck="false"
    bind:value={appToken}
    required
  />
</label>
<label class={{ inline }}>
  <span>User token</span>
  <input
    type="password"
    name="user_token"
    placeholder="user_token_..."
    autocomplete="off"
    bind:value={userToken}
    required
  />
</label>

<style>
  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--pico-muted-color);
  }

  input {
    font-family: var(--font-mono);
  }

  /*
   * Beside the field rather than above it: two stacked pairs is a lot of
   * vertical space for a card that's mostly about the buttons underneath.
   * Only where there's width for it — on a phone they stack regardless.
   */
  @media (min-width: 30rem) {
    .inline {
      display: grid;
      grid-template-columns: 5.5rem 1fr;
      align-items: center;
      gap: 0.5625rem;
    }
  }
</style>
