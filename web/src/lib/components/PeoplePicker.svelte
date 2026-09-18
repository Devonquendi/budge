<script lang="ts">
  import type { Contact, Group } from '../api'
  import { contacts, groups, label, load, loaded } from '../people.svelte'

  // Everyone you split with, as things to tap. The free-text field stays for
  // the person who isn't in the list yet, because the first time you ask
  // somebody they are never in the list yet.
  let {
    chosen = $bindable([]),
    autofocus = false,
  }: {
    /** Email addresses, which is what a request is addressed to. */
    chosen: string[]
    autofocus?: boolean
  } = $props()

  let typed = $state('')
  let adding = $state(false)

  if (!loaded()) load()

  const known = $derived(new Set(contacts().map((c) => c.email)))

  // Anyone typed in who isn't a contact yet still needs a chip, or picking
  // them would look like nothing happened.
  const extras = $derived(chosen.filter((email) => !known.has(email)))

  function toggle(email: string) {
    chosen = chosen.includes(email)
      ? chosen.filter((one) => one !== email)
      : [...chosen, email]
  }

  function addGroup(group: Group) {
    const emails = group.members.map((member) => member.email)
    const all = emails.every((email) => chosen.includes(email))
    chosen = all
      ? chosen.filter((email) => !emails.includes(email))
      : [...new Set([...chosen, ...emails])]
  }

  function commitTyped() {
    const entries = typed
      .split(/[\n,;\s]+/)
      .map((entry) => entry.trim().toLowerCase())
      .filter((entry) => entry.includes('@'))
    if (entries.length) chosen = [...new Set([...chosen, ...entries])]
    typed = ''
    adding = false
  }

  function chipFor(email: string): Contact | { email: string; name: null } {
    return contacts().find((c) => c.email === email) ?? { email, name: null }
  }
</script>

<div class="picker">
  {#if groups().length}
    <div class="row">
      {#each groups() as group (group.id)}
        {@const all =
          group.members.length > 0 &&
          group.members.every((member) => chosen.includes(member.email))}
        <button
          type="button"
          class={['chip', 'group', { on: all }]}
          aria-pressed={all}
          onclick={() => addGroup(group)}
        >
          {group.name}
          <span class="count">{group.members.length}</span>
        </button>
      {/each}
    </div>
  {/if}

  <div class="row">
    {#each contacts() as contact (contact.id)}
      <button
        type="button"
        class={['chip', { on: chosen.includes(contact.email) }]}
        aria-pressed={chosen.includes(contact.email)}
        onclick={() => toggle(contact.email)}
      >
        {#if contact.favourite}<span class="star" aria-hidden="true">★</span>{/if}
        {label(contact)}
      </button>
    {/each}

    {#each extras as email (email)}
      <button
        type="button"
        class="chip on"
        aria-pressed="true"
        onclick={() => toggle(email)}
      >
        {label(chipFor(email))}
      </button>
    {/each}

    {#if adding}
      <input
        bind:value={typed}
        placeholder="their@email.com"
        onblur={commitTyped}
        onkeydown={(event) => {
          if (event.key === 'Enter' || event.key === ',') {
            event.preventDefault()
            commitTyped()
          }
        }}
        {@attach (node) => node.focus()}
      />
    {:else}
      <button type="button" class="chip add" onclick={() => (adding = true)}>
        + Someone else
      </button>
    {/if}
  </div>

  {#if autofocus && !contacts().length && !adding}
    <p class="muted hint">Nobody in your list yet. Add someone and they stay.</p>
  {/if}
</div>

<style>
  .picker {
    display: flex;
    flex-direction: column;
    gap: 0.3125rem;
    min-width: 0;
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .chip {
    width: auto;
    margin: 0;
    padding: 0.1875rem 0.5rem;
    border-radius: 999px;
    font-size: var(--text-meta);
    font-weight: 500;
    background: transparent;
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    color: var(--pico-muted-color);
  }

  .chip:hover:not(.on) {
    border-color: var(--ctp-overlay0);
    color: var(--pico-color);
  }

  /* Picked is a filled chip: at a glance you should be able to count who is
     being asked without reading any of the names. */
  .on {
    background: var(--ctp-green);
    border-color: var(--ctp-green);
    color: var(--ctp-base);
  }

  .group {
    border-style: dashed;
  }

  .count {
    opacity: 0.7;
  }

  .star {
    font-size: 0.6875em;
  }

  .add {
    border-style: dashed;
  }

  input {
    width: 12rem;
    margin: 0;
    padding: 0.125rem 0.5rem;
    font-size: var(--text-meta);
  }

  .hint {
    margin: 0;
    font-size: var(--text-meta);
  }
</style>
