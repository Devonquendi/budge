/** Presentation helpers for the merchant behind a transaction. */

/**
 * The letter on a merchant's mark when Akahu had no logo for it. The first
 * character that is a letter or a digit, so "4 Square" keeps its 4 and
 * "*SPOTIFY" doesn't end up as an asterisk.
 */
export function initial(name: string): string {
  return (name.match(/[a-z0-9]/i)?.[0] ?? '?').toUpperCase()
}
