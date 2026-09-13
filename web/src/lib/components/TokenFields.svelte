<script lang="ts">
  // Bindable so the page holding the form owns the values; the tokens
  // themselves are never sent back from the server.
  let { appToken = $bindable(''), userToken = $bindable('') } = $props()
</script>

<label>
  App ID token
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
<label>
  User token
  <input
    type="password"
    name="user_token"
    placeholder="user_token_..."
    autocomplete="off"
    bind:value={userToken}
    required
  />
</label>
