/**
 * A colour per spending category, so the same kind of spending is the same
 * colour everywhere it appears — the ledger's tags and the dashboard's bars.
 *
 * Every colour is a Catppuccin accent named as a custom property rather than a
 * literal, so the mapping holds in both themes without a second table.
 */

/** The accents worth spending on a category, in a fixed order the hash indexes. */
const ACCENTS = [
  '--ctp-green',
  '--ctp-mauve',
  '--ctp-sky',
  '--ctp-peach',
  '--ctp-pink',
  '--ctp-lavender',
  '--ctp-yellow',
  '--ctp-teal',
] as const

/**
 * Akahu's NZFCC names, matched on a substring so "Groceries & supermarkets"
 * and "Groceries" land on the same colour. Order matters: the first hit wins.
 */
const NAMED: [pattern: string, accent: string][] = [
  ['income', '--ctp-green'],
  ['salary', '--ctp-green'],
  ['grocer', '--ctp-green'],
  ['supermarket', '--ctp-green'],
  ['rent', '--ctp-lavender'],
  ['mortgage', '--ctp-lavender'],
  ['housing', '--ctp-lavender'],
  ['utilit', '--ctp-sky'],
  ['power', '--ctp-sky'],
  ['internet', '--ctp-sky'],
  ['phone', '--ctp-sky'],
  ['transport', '--ctp-mauve'],
  ['travel', '--ctp-mauve'],
  ['subscription', '--ctp-mauve'],
  ['fuel', '--ctp-peach'],
  ['petrol', '--ctp-peach'],
  ['parking', '--ctp-peach'],
  ['dining', '--ctp-pink'],
  ['restaurant', '--ctp-pink'],
  ['cafe', '--ctp-pink'],
  ['takeaway', '--ctp-pink'],
  ['household', '--ctp-yellow'],
  ['home', '--ctp-yellow'],
  ['health', '--ctp-teal'],
  ['medical', '--ctp-teal'],
]

/** The custom property holding this category's colour. */
export function categoryAccent(name: string | null | undefined): string {
  if (!name) return '--ctp-overlay0'

  const lower = name.toLowerCase()
  for (const [pattern, accent] of NAMED) {
    if (lower.includes(pattern)) return accent
  }

  // Nothing recognised: pick from the accents by name, so an unmapped category
  // still keeps one stable colour rather than changing between renders.
  let total = 0
  for (const character of lower) total = (total * 31 + character.charCodeAt(0)) % 997
  return ACCENTS[total % ACCENTS.length]
}

/** The colour itself, ready for a `background` or `color`. */
export function categoryColor(name: string | null | undefined): string {
  return `var(${categoryAccent(name)})`
}
