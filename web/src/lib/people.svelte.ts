/**
 * The contacts and groups the picker draws itself from.
 *
 * A module rather than per-component state: the picker appears on every
 * transaction row on two pages, and each of them fetching the same list would
 * be a request per row. Loaded once, refreshed when something changes it.
 */

import { api, type Contact, type Group } from './api'

const state = $state<{ contacts: Contact[]; groups: Group[]; loaded: boolean }>({
  contacts: [],
  groups: [],
  loaded: false,
})

export function contacts(): Contact[] {
  return state.contacts
}

export function groups(): Group[] {
  return state.groups
}

export function loaded(): boolean {
  return state.loaded
}

export async function load(): Promise<void> {
  try {
    const people = await api.people()
    state.contacts = people.contacts
    state.groups = people.groups
  } catch {
    // An empty picker is a survivable outcome: the free-text field still works,
    // and a failure here should not take a page down.
    state.contacts = []
    state.groups = []
  }
  state.loaded = true
}

/** Call after anything that files a contact, so the picker catches up. */
export function refresh(): Promise<void> {
  return load()
}

/** What to call someone: their name, or the part of their email before the @. */
export function label(person: { email: string; name?: string | null }): string {
  return person.name || person.email.split('@')[0]
}

/**
 * Addresses turned into payees, named wherever we know the name.
 *
 * The picker knows what everyone is called, so a request should carry it: it
 * is what the payee list reads back, and what lets a credit be matched to the
 * right person when two of them owe the same amount.
 */
export function named(emails: string[]): { email: string; name: string }[] {
  const byEmail = new Map(state.contacts.map((one) => [one.email, one]))
  return emails.map((email) => ({ email, name: byEmail.get(email)?.name ?? '' }))
}
