<script lang="ts">
  import { api, errorMessage, type Contact, type Group } from '../lib/api'
  import Panel from '../lib/components/Panel.svelte'
  import { contacts, groups, label, load } from '../lib/people.svelte'

  let error = $state('')
  let busy = $state(false)

  let newEmail = $state('')
  let newName = $state('')

  // The group being edited, or a blank one being built. Null means neither.
  let editing = $state.raw<Group | null>(null)
  let groupName = $state('')
  let groupMembers = $state<string[]>([])

  load()

  async function run(work: () => Promise<unknown>) {
    busy = true
    error = ''
    try {
      await work()
      await load()
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = false
  }

  function addPerson(event: SubmitEvent) {
    event.preventDefault()
    const email = newEmail.trim().toLowerCase()
    const name = newName.trim()
    newEmail = ''
    newName = ''
    return run(() => api.addContact(email, name))
  }

  function startGroup(group: Group | null) {
    editing = group
    groupName = group?.name ?? ''
    groupMembers = group?.members.map((member) => member.email) ?? []
  }

  function saveGroup(event: SubmitEvent) {
    event.preventDefault()
    const members = groupMembers.map((email) => ({ email }))
    const name = groupName.trim() || 'Group'
    const current = editing
    startGroup(null)
    return run(() =>
      current
        ? api.updateGroup(current.id, name, members)
        : api.createGroup(name, members),
    )
  }

  function inGroup(email: string): boolean {
    return groupMembers.includes(email)
  }

  function toggleMember(email: string) {
    groupMembers = inGroup(email)
      ? groupMembers.filter((one) => one !== email)
      : [...groupMembers, email]
  }

  function asked(contact: Contact): string {
    if (!contact.last_asked_at) return 'Never asked'
    return `Last asked ${new Date(contact.last_asked_at).toLocaleDateString('en-NZ', {
      day: 'numeric',
      month: 'short',
    })}`
  }
</script>

<div class="page">
  {#if error}<p class="error">{error}</p>{/if}

  <Panel title="Groups" padded>
    {#if groups().length}
      <ul class="groups">
        {#each groups() as group (group.id)}
          <li>
            <span class="name">{group.name}</span>
            <span class="muted who">
              {group.members.map((member) => label(member)).join(', ') || 'Nobody yet'}
            </span>
            <button
              type="button"
              class="secondary outline"
              onclick={() => startGroup(group)}
            >
              Edit
            </button>
            <button
              type="button"
              class="secondary outline"
              disabled={busy}
              onclick={() => run(() => api.deleteGroup(group.id))}
            >
              Delete
            </button>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="muted empty">
        No groups yet. A group is the people you ask together: a flat, a trip, a car.
      </p>
    {/if}

    {#if editing !== null || groupName || groupMembers.length}
      <form class="group-form" onsubmit={saveGroup}>
        <label>
          <span class="field">Name</span>
          <input bind:value={groupName} placeholder="The flat" required />
        </label>
        <div class="members">
          <span class="field">Who's in it</span>
          <div class="chips">
            {#each contacts() as contact (contact.id)}
              <button
                type="button"
                class={['chip', { on: inGroup(contact.email) }]}
                aria-pressed={inGroup(contact.email)}
                onclick={() => toggleMember(contact.email)}
              >
                {label(contact)}
              </button>
            {/each}
            {#if !contacts().length}
              <span class="muted">Add someone below first.</span>
            {/if}
          </div>
        </div>
        <div class="buttons">
          <button type="submit" disabled={busy}>
            {editing ? 'Save group' : 'Create group'}
          </button>
          <button
            type="button"
            class="secondary outline"
            onclick={() => startGroup(null)}
          >
            Cancel
          </button>
        </div>
      </form>
    {:else}
      <button type="button" class="secondary outline" onclick={() => (groupName = ' ')}>
        New group
      </button>
    {/if}
  </Panel>

  <Panel title="People">
    {#if contacts().length}
      <ul class="people">
        {#each contacts() as contact (contact.id)}
          <li>
            <button
              type="button"
              class={['star', { on: contact.favourite }]}
              aria-pressed={contact.favourite}
              aria-label={contact.favourite ? 'Remove favourite' : 'Make favourite'}
              disabled={busy}
              onclick={() => run(() => api.favourite(contact.id, !contact.favourite))}
            >
              {contact.favourite ? '★' : '☆'}
            </button>
            <span class="name">{label(contact)}</span>
            <span class="muted email">{contact.email}</span>
            <span class="muted when">{asked(contact)}</span>
            <button
              type="button"
              class="secondary outline"
              disabled={busy}
              onclick={() => run(() => api.removeContact(contact.id))}
            >
              Remove
            </button>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="muted empty">
        Nobody yet. Anyone you ask for money lands here on their own.
      </p>
    {/if}

    {#snippet footer()}
      <form class="add" onsubmit={addPerson}>
        <input
          type="email"
          bind:value={newEmail}
          placeholder="their@email.com"
          required
        />
        <input bind:value={newName} placeholder="Name (optional)" />
        <button type="submit" disabled={busy}>Add</button>
      </form>
    {/snippet}
  </Panel>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .people li,
  .groups li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4375rem 0.6875rem;
  }

  .groups li {
    padding-inline: 0;
  }

  .people li + li,
  .groups li + li {
    border-top: var(--pico-border-width) solid var(--ctp-divider);
  }

  .name {
    font-weight: 600;
  }

  .email,
  .who,
  .when {
    font-size: var(--text-meta);
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .who,
  .email {
    flex: 1 1 8rem;
  }

  .when {
    flex: none;
  }

  li button {
    width: auto;
    margin: 0;
    padding: 0.125rem 0.5rem;
    font-size: var(--text-meta);
  }

  .people li > button:last-child,
  .groups li > button:nth-last-child(2) {
    margin-left: auto;
  }

  .star {
    flex: none;
    padding: 0;
    background: none;
    border: none;
    font-size: 1rem;
    line-height: 1;
    color: var(--pico-muted-color);
  }

  .star.on {
    color: var(--ctp-yellow);
  }

  .empty {
    margin: 0;
    padding: 0.75rem 0.6875rem;
    font-size: var(--text-meta);
  }

  .add,
  .group-form,
  .buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .add {
    padding: 0.5rem 0.6875rem;
    align-items: center;
  }

  .add input {
    flex: 1 1 10rem;
    margin: 0;
  }

  .add button,
  .buttons button {
    width: auto;
    margin: 0;
  }

  .group-form {
    flex-direction: column;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: var(--pico-border-width) solid var(--pico-card-border-color);
  }

  .group-form input {
    margin: 0;
  }

  .field {
    display: block;
    margin-bottom: 0.25rem;
    font-size: var(--text-meta);
    font-weight: 500;
    color: var(--pico-muted-color);
  }

  .chips {
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
    background: transparent;
    border: var(--pico-border-width) solid var(--pico-card-border-color);
    color: var(--pico-muted-color);
  }

  .chip.on {
    background: var(--ctp-green);
    border-color: var(--ctp-green);
    color: var(--ctp-base);
  }
</style>
