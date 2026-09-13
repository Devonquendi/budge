/**
 * The display preferences on the settings page. They only change how things are
 * drawn, so they live in the browser rather than the database — nothing here is
 * worth a round trip, and a stale value costs nothing.
 *
 * The theme is deliberately not one of these: it has to be applied before the
 * first paint to avoid a flash, so it keeps its own module.
 */

const KEY = 'budge-prefs'

export type Prefs = {
  /** Break the ledger into a heading per day, the way a statement reads. */
  groupByDay: boolean
  /** Round balances over $10k to whole dollars. */
  hideCents: boolean
}

const DEFAULTS: Prefs = { groupByDay: false, hideCents: false }

function read(): Prefs {
  try {
    const stored = localStorage.getItem(KEY)
    if (!stored) return DEFAULTS
    const parsed: unknown = JSON.parse(stored)
    if (typeof parsed !== 'object' || parsed === null) return DEFAULTS
    // Field by field, so an older shape (or a hand-edited one) can't put a
    // non-boolean into the object every component reads.
    const saved = parsed as Partial<Record<keyof Prefs, unknown>>
    return {
      groupByDay: typeof saved.groupByDay === 'boolean' ? saved.groupByDay : DEFAULTS.groupByDay,
      hideCents: typeof saved.hideCents === 'boolean' ? saved.hideCents : DEFAULTS.hideCents,
    }
  } catch {
    // Unavailable or unparseable — the defaults are a fine answer.
    return DEFAULTS
  }
}

const current = $state<Prefs>(read())

/** Read in a template or a `$derived` and it stays live. */
export function prefs(): Prefs {
  return current
}

export function setPref<K extends keyof Prefs>(key: K, value: Prefs[K]): void {
  current[key] = value
  try {
    localStorage.setItem(KEY, JSON.stringify(current))
  } catch {
    // Ignore — the preference just won't survive a reload.
  }
}
