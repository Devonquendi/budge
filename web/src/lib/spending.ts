/**
 * What this month's money went on, by category.
 *
 * A pure function rather than something the breakdown panel keeps to itself:
 * the panel draws the bars, and the card's header states the total, so both
 * need the same numbers from the same place.
 */

import type { Transaction } from './api'
import { toCents } from './money'

export type Slice = { name: string; cents: number }

const UNCATEGORISED = 'Uncategorised'

/** Money out this calendar month in one currency, biggest category first. */
export function monthlySpend(
  transactions: Transaction[],
  currency: string,
  now = new Date(),
): Slice[] {
  const month = now.getMonth()
  const year = now.getFullYear()

  const totals = new Map<string, number>()

  for (const transaction of transactions) {
    if (transaction.currency !== currency) continue

    // Money in isn't spending, and neither is a zero.
    const cents = toCents(transaction.amount)
    if (cents >= 0) continue

    const date = new Date(transaction.date)
    if (date.getMonth() !== month || date.getFullYear() !== year) continue

    const name = transaction.category?.name ?? UNCATEGORISED
    totals.set(name, (totals.get(name) ?? 0) + Math.abs(cents))
  }

  return [...totals]
    .map(([name, cents]) => ({ name, cents }))
    .sort((a, b) => b.cents - a.cents)
}

export function totalSpend(slices: Slice[]): number {
  return slices.reduce((sum, slice) => sum + slice.cents, 0)
}
