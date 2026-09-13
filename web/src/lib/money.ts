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

export function sumCents(amounts: string[]): number {
  return amounts.reduce((total, amount) => total + toCents(amount), 0)
}

/**
 * `round` drops the cents once a balance passes $10k, which is the "hide cents
 * on big balances" preference: past that size the cents are noise, and the
 * column of figures lines up better without them. Off by default, and never
 * applied to a transaction amount — there the cents are the point.
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
