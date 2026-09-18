/**
 * Which transactions have been split, and how those requests are going.
 *
 * A module because the marker belongs on every screen that lists transactions,
 * and each of them fetching per row would be a request per line of the ledger.
 * Loaded once, refreshed whenever something is sent or answered.
 */

import { api, type Settled, type SplitSummary } from './api'

const state = $state<{
  byId: Record<string, SplitSummary>
  settledBy: Record<string, Settled>
  loaded: boolean
}>({ byId: {}, settledBy: {}, loaded: false })

/** What this transaction asked for, if it was split. */
export function splitOf(transactionId: string): SplitSummary | undefined {
  return state.byId[transactionId]
}

/** What this transaction answered, if it settled a request. */
export function settledBy(transactionId: string): Settled | undefined {
  return state.settledBy[transactionId]
}

export function loaded(): boolean {
  return state.loaded
}

export async function load(): Promise<void> {
  // Both directions in one go: what a transaction asked for, and what it
  // answered. The ledger draws them on the same rows.
  try {
    const [summaries, settled] = await Promise.all([
      api.splitsByTransaction(),
      api.settlements(),
    ])
    state.byId = Object.fromEntries(summaries.map((one) => [one.transaction_id, one]))
    state.settledBy = Object.fromEntries(settled.map((one) => [one.transaction_id, one]))
  } catch {
    // A missing marker is a survivable outcome. The ledger still reads, and the
    // split still happened; losing a badge should not take a page down.
    state.byId = {}
    state.settledBy = {}
  }
  state.loaded = true
}

export function refresh(): Promise<void> {
  return load()
}
