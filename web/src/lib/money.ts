/**
 * Balances cross the wire as decimal strings ("1234.50") so no cents are lost
 * on the way. JavaScript has no decimal type, so everything here adds up in
 * integer cents and only divides at the moment of display.
 */

/** Cents in a decimal string. Anything finer than a cent is truncated. */
export function toCents(amount: string): number {
  const [whole, fraction = ''] = amount.split('.')
  const sign = whole.startsWith('-') ? -1 : 1
  return sign * (Math.abs(Number(whole)) * 100 + Number(`${fraction}00`.slice(0, 2)))
}

export function sumCents(amounts: string[]): number {
  return amounts.reduce((total, amount) => total + toCents(amount), 0)
}

export function formatCents(cents: number, currency: string): string {
  return new Intl.NumberFormat('en-NZ', { style: 'currency', currency }).format(
    cents / 100,
  )
}

export function format(amount: string, currency: string): string {
  return formatCents(toCents(amount), currency)
}
