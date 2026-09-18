/**
 * One transaction, on its way from the ledger to the request form.
 *
 * Splitting happens on a different page from the one you spot the transaction
 * on, and the amount and the merchant have to survive the trip. A module holds
 * them rather than the URL: the router is six flat paths with no query handling,
 * and a bill's details have no business being in a link anyway.
 *
 * Deliberately not persisted. Losing it on reload leaves the form on screen with
 * its fields visible, which is a worse outcome than nothing and a better one
 * than a stale prefill from something you looked at yesterday.
 */

import type { Transaction } from './api'

export type Staged = {
  /** Akahu's id, stored on the bill so a request can point back at the spend. */
  transactionId: string
  title: string
  /** Always positive: the bill is what was spent, not the sign of the row. */
  amount: string
  date: string
}

const state = $state<{ pending: Staged | null }>({ pending: null })

/** Marks a transaction as the one being split, for the request form to pick up. */
export function stage(transaction: Transaction): void {
  state.pending = {
    transactionId: transaction.id,
    title: transaction.merchant?.name ?? transaction.description,
    amount: transaction.amount.replace('-', ''),
    date: transaction.date,
  }
}

/** The staged transaction, cleared as it is handed over so it is used once. */
export function take(): Staged | null {
  const pending = state.pending
  state.pending = null
  return pending
}
