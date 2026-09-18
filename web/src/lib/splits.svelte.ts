/**
 * Which transactions have been split, and how those requests are going.
 *
 * A module because the marker belongs on every screen that lists transactions,
 * and each of them fetching per row would be a request per line of the ledger.
 * Loaded once, refreshed whenever something is sent or answered.
 */

import { api, type SplitSummary } from './api'

const state = $state<{ byId: Record<string, SplitSummary>; loaded: boolean }>({
  byId: {},
  loaded: false,
})

export function splitOf(transactionId: string): SplitSummary | undefined {
  return state.byId[transactionId]
}

export function loaded(): boolean {
  return state.loaded
}

export async function load(): Promise<void> {
  try {
    const summaries = await api.splitsByTransaction()
    state.byId = Object.fromEntries(summaries.map((one) => [one.transaction_id, one]))
  } catch {
    // A missing marker is a survivable outcome. The ledger still reads, and the
    // split still happened; losing a badge should not take a page down.
    state.byId = {}
  }
  state.loaded = true
}

export function refresh(): Promise<void> {
  return load()
}
