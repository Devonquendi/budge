/** Presentation helpers shared by anything that draws an Akahu account. */

const TYPE_LABELS: Record<string, string> = {
  CHECKING: 'Checking',
  SAVINGS: 'Savings',
  CREDITCARD: 'Credit card',
  LOAN: 'Loan',
  KIWISAVER: 'KiwiSaver',
  INVESTMENT: 'Investment',
  TERMDEPOSIT: 'Term deposit',
  FOREIGN: 'Foreign currency',
  WALLET: 'Wallet',
  REWARDS: 'Rewards',
}

export function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type.charAt(0) + type.slice(1).toLowerCase()
}

/** Two or three letters for a connection's badge: "Kiwibank" -> "KIW", "Kiwi Bank" -> "KB". */
export function badge(connection: string): string {
  const words = connection.trim().split(/\s+/)
  if (words.length > 1) return words.slice(0, 2).map((word) => word[0]).join('').toUpperCase()
  return connection.slice(0, 3).toUpperCase()
}

/** A stable hue per connection, so each bank keeps the same colour. */
export function hue(connection: string): number {
  let total = 0
  for (const character of connection) total = (total * 31 + character.charCodeAt(0)) % 360
  return total
}
