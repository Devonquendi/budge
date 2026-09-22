/**
 * Balances cross the wire as decimal strings ("1234.50") so no cents are lost
 * on the way. JavaScript has no decimal type, so everything here adds up in
 * integer cents and only divides at the moment of display.
 */

const ROUND_ABOVE_CENTS = 10_000_00

/** Cents in a decimal string. Anything finer than a cent is truncated. */
export function toCents(amount: string): number {
  const [whole, fraction = ''] = amount.split('.')
  const sign = whole.startsWith('-') ? -1 : 1
  return sign * (Math.abs(Number(whole)) * 100 + Number(`${fraction}00`.slice(0, 2)))
}

/** Cents in an amount someone typed: "45", "$45.20", "1,234.5". Null if it isn't one. */
export function parseCents(typed: string): number | null {
  const cleaned = typed.replace(/[$,\s]/g, '')
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null
  const cents = toCents(cleaned)
  return cents > 0 ? cents : null
}

/** Whole-cent shares that add back to the total, the odd cents on the first. */
export function splitCents(total: number, shares: number): number[] {
  const base = Math.trunc(total / shares)
  const over = total - base * shares
  return Array.from({ length: shares }, (_, index) => base + (index < over ? 1 : 0))
}

export function sumCents(amounts: string[]): number {
  return amounts.reduce((total, amount) => total + toCents(amount), 0)
}

/**
 * `round` drops the cents once a balance passes $10k, which is the "hide cents
 * on big balances" preference: past that size the cents are noise, and the
 * column of figures lines up better without them. Off by default, and never
 * applied to a transaction amount, where the cents are the point.
 */
export function formatCents(cents: number, currency: string, round = false): string {
  const whole = round && Math.abs(cents) >= ROUND_ABOVE_CENTS
  return new Intl.NumberFormat('en-NZ', {
    style: 'currency',
    currency,
    ...(whole ? { minimumFractionDigits: 0, maximumFractionDigits: 0 } : {}),
  }).format(cents / 100)
}

export function format(amount: string, currency: string, round = false): string {
  return formatCents(toCents(amount), currency, round)
}
