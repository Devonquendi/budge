<script lang="ts">
  import { api, errorMessage, type Me, type Persona } from '../api'

  // Only rendered where the backend says demo is on, which is anywhere but
  // production. In production /demo/personas answers with an empty list and
  // this draws nothing.
  let {
    onsignin,
    lead = false,
  }: {
    onsignin: (me: Me) => void
    /** Top of the page rather than an afterthought under the password box. */
    lead?: boolean
  } = $props()

  let personas = $state.raw<Persona[]>([])
  let error = $state('')
  let busy = $state('')

  async function load() {
    try {
      personas = await api.personas()
    } catch {
      // A missing demo endpoint is not worth a message on a sign-in page.
      personas = []
    }
  }

  async function signIn(persona: Persona) {
    busy = persona.email
    error = ''
    try {
      onsignin(await api.demoSession(persona.email))
    } catch (failure) {
      error = errorMessage(failure)
      busy = ''
    }
  }

  load()
</script>

{#if personas.length}
  <div class={['demo', { lead }]}>
    {#if !lead}
      <p class="eyebrow">Or look around as someone made up</p>
    {/if}
    <ul>
      {#each personas as persona (persona.email)}
        <li>
          <button
            type="button"
            class="secondary outline"
            disabled={!!busy}
            onclick={() => signIn(persona)}
          >
            <span class="name">{persona.name}</span>
            <span class="blurb muted">{persona.blurb}</span>
          </button>
        </li>
      {/each}
    </ul>
    {#if error}<p class="error">{error}</p>{/if}
  </div>
{/if}

<style>
  .demo {
    margin-top: 0.875rem;
    padding-top: 0.75rem;
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  /* Nothing above it to be separated from. */
  .lead {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
  }

  .lead ul {
    margin-top: 0;
  }

  ul,
  li {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  ul {
    margin-top: 0.5rem;
  }

  /* app.css pins every button to width: auto at a specificity this can't
     reach, so the row stretches the button rather than the button itself. */
  li {
    display: flex;
  }

  li + li {
    margin-top: 0.25rem;
  }

  button {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 0.0625rem;
    padding: 0.4375rem 0.5625rem;
    text-align: left;
  }

  .name {
    font-size: var(--text-label);
    font-weight: 600;
  }

  .blurb {
    font-size: var(--text-meta);
    line-height: 1.35;
  }
</style>
